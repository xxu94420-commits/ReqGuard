"""Single-container demo supervisor. Internal services never bind public ports."""

import os
from pathlib import Path
import re
import signal
import subprocess
import time


def configure(env):
    port = int(env.get("PORT", "10000"))
    if not 1024 <= port <= 65535:
        raise ValueError("Invalid PORT")
    username = env.get("DEMO_USERNAME", "")
    password = env.get("DEMO_PASSWORD", "")
    if (
        not re.fullmatch(r"[A-Za-z0-9_-]{1,40}", username)
        or len(password) < 16
        or "\n" in password
        or "\r" in password
    ):
        raise ValueError("Set DEMO_USERNAME and DEMO_PASSWORD (at least 16 characters)")
    config = Path("/srv/deploy/nginx.conf").read_text(encoding="utf-8")
    Path("/tmp/reqguard-nginx.conf").write_text(
        config.replace("__PORT__", str(port)), encoding="utf-8"
    )


def main():
    env = dict(os.environ)
    configure(env)
    auth_env = dict(env)
    auth_env.pop("LLM_API_KEY", None)
    # The child services do not need access to the browser login credential.
    env.pop("DEMO_PASSWORD", None)
    env.pop("DEMO_USERNAME", None)
    env["PORT"] = "8080"
    env["AI_SERVICE_URL"] = "http://127.0.0.1:8000"
    env["DATABASE_URL"] = (
        "jdbc:h2:file:/srv/data/reqguard;MODE=PostgreSQL;DATABASE_TO_LOWER=TRUE"
    )
    env["DATABASE_USER"] = "sa"
    env["DATABASE_PASSWORD"] = ""
    children = []
    stopping = False

    def stop(*_):
        nonlocal stopping
        stopping = True

    signal.signal(signal.SIGTERM, stop)
    signal.signal(signal.SIGINT, stop)
    try:
        children.append(
            subprocess.Popen(
                ["/srv/venv/bin/python", "/srv/deploy/auth.py"], env=auth_env
            )
        )
        children.append(
            subprocess.Popen(
                [
                    "/srv/venv/bin/python",
                    "-m",
                    "uvicorn",
                    "app.main:app",
                    "--app-dir",
                    "/srv/ai-service",
                    "--host",
                    "127.0.0.1",
                    "--port",
                    "8000",
                ],
                env=env,
            )
        )
        java_env = dict(env)
        java_env.pop("LLM_API_KEY", None)
        children.append(
            subprocess.Popen(
                [
                    "java",
                    "-Xms32m",
                    "-Xmx160m",
                    "-XX:MaxMetaspaceSize=128m",
                    "-XX:ReservedCodeCacheSize=32m",
                    "-XX:+UseSerialGC",
                    "-Xss256k",
                    "-jar",
                    "/srv/app.jar",
                    "--server.address=127.0.0.1",
                    "--server.tomcat.threads.max=16",
                    "--server.tomcat.threads.min-spare=2",
                ],
                env=java_env,
            )
        )
        nginx_env = dict(env)
        nginx_env.pop("LLM_API_KEY", None)
        children.append(
            subprocess.Popen(
                [
                    "nginx",
                    "-c",
                    "/tmp/reqguard-nginx.conf",
                    "-g",
                    "daemon off;",
                ],
                env=nginx_env,
            )
        )
        while not stopping:
            if any(child.poll() is not None for child in children):
                raise RuntimeError(
                    "A demo service stopped; restarting container is required"
                )
            time.sleep(0.5)
    finally:
        for child in children:
            if child.poll() is None:
                child.terminate()
        for child in children:
            try:
                child.wait(timeout=10)
            except subprocess.TimeoutExpired:
                child.kill()
                child.wait()


if __name__ == "__main__":
    main()
