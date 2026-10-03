import importlib.util
from pathlib import Path
import threading

import httpx
import pytest

spec = importlib.util.spec_from_file_location(
    "demo_auth", Path(__file__).resolve().parents[2] / "deploy/render/auth.py"
)
auth = importlib.util.module_from_spec(spec)
spec.loader.exec_module(auth)


def test_session_expiry_tampering_and_revocation(monkeypatch):
    sessions = auth.Sessions("demo", "test-only-strong-password")
    assert sessions.credentials("demo", "test-only-strong-password")
    assert not sessions.credentials("demo", "incorrect")
    assert not sessions.credentials("other", "test-only-strong-password")
    token = sessions.issue()
    assert sessions.valid(token)
    assert not sessions.valid(token + "tampered")
    sessions.revoke(token)
    assert not sessions.valid(token)
    token = sessions.issue()
    now = auth.time.time()
    monkeypatch.setattr(auth.time, "time", lambda: now + auth.TTL + 1)
    assert not sessions.valid(token)


@pytest.fixture
def gateway():
    server = auth.HTTPServer(("127.0.0.1", 0), auth.Handler)
    server.sessions = auth.Sessions("demo", "test-only-strong-password")
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    with httpx.Client(
        base_url=f"http://127.0.0.1:{server.server_port}",
        headers={"Host": "demo.example"},
    ) as client:
        yield client
    server.shutdown()
    server.server_close()
    thread.join()


def test_login_cookie_access_csrf_and_logout(gateway):
    assert gateway.get("/_auth").status_code == 401
    page = gateway.get("/login")
    assert page.status_code == 200
    assert "www-authenticate" not in page.headers
    assert gateway.post("/login", data={"username": "demo", "password": "wrong"}).status_code == 401
    data = {"username": "demo", "password": "test-only-strong-password"}
    assert (
        gateway.post("/login", data=data, headers={"Origin": "https://evil.example"}).status_code
        == 403
    )
    response = gateway.post("/login", data=data, headers={"Origin": "https://demo.example"})
    assert response.status_code == 303
    assert response.headers["location"] == "/"
    cookie = response.headers["set-cookie"]
    for flag in ["HttpOnly", "Secure", "SameSite=Strict", "Path=/"]:
        assert flag in cookie
    # Test transport is loopback HTTP: send the secure cookie explicitly for unit verification.
    headers = {"Cookie": cookie.split(";", 1)[0]}
    assert gateway.get("/_auth", headers=headers).status_code == 204
    assert (
        gateway.get(
            "/_auth",
            headers={**headers, "X-Original-Method": "POST", "Origin": "https://evil.example"},
        ).status_code
        == 403
    )
    assert gateway.post("/logout", headers=headers).status_code == 303
    assert gateway.get("/_auth", headers=headers).status_code == 401


def test_basic_auth_and_malformed_input(gateway):
    assert gateway.get("/_auth", auth=("demo", "test-only-strong-password")).status_code == 204
    assert gateway.get("/_auth", headers={"Authorization": "Basic !!!"}).status_code == 401
    assert gateway.post("/login", content=b"x" * 4097).status_code == 400


def test_ajax_login_returns_cookie_without_redirect(gateway):
    response = gateway.post(
        "/login",
        data={"username": "demo", "password": "test-only-strong-password"},
        headers={"Accept": "application/json", "Origin": "https://demo.example"},
    )
    assert response.status_code == 200
    assert response.json() == {"status": "authenticated"}
    assert "location" not in response.headers
    cookie = response.headers["set-cookie"].split(";", 1)[0]
    assert gateway.get("/_auth", headers={"Cookie": cookie}).status_code == 204
