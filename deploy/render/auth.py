"""Loopback-only login gateway for the shared, non-production Render demo."""

import base64
import hashlib
import hmac
from http.cookies import SimpleCookie
from http.server import BaseHTTPRequestHandler, HTTPServer
import os
import secrets
import time
from urllib.parse import parse_qs

COOKIE = "__Host-reqguard_session"
TTL = 8 * 60 * 60
PAGE = """<!doctype html><html lang="zh-CN"><meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>登录 · ReqGuard</title><style>
body{font:16px system-ui;background:#f4f7f4;color:#203b32;margin:0;
display:grid;place-items:center;min-height:100vh}main{background:white;padding:32px;
border-radius:16px;width:min(360px,80vw);box-shadow:0 8px 30px #203b3214}
input,button{box-sizing:border-box;width:100%;padding:12px;margin:8px 0 18px;
font:inherit;border:1px solid #ccd8d0;border-radius:8px}button{background:#41765a;
color:white;cursor:pointer}p{line-height:1.6;color:#65786d}.error{color:#a52e2e}</style>
<main><h1>ReqGuard</h1><p>需求质量评估与复盘工作台</p>__ERROR__
<form method="post" action="/login"><label>账号<input name="username"
autocomplete="username" required maxlength="40"></label><label>密码
<input name="password" type="password" autocomplete="current-password" required
maxlength="256"></label><button type="submit">登录工作台</button></form>
<p>个人演示环境。数据会随免费实例休眠或重启清空。</p></main></html>"""


class Sessions:
    def __init__(self, username, password):
        self.username = username
        self.password_digest = hashlib.sha256(password.encode()).digest()
        self.tokens = {}

    def credentials(self, username, password):
        return hmac.compare_digest(
            username.encode(), self.username.encode()
        ) and hmac.compare_digest(
            hashlib.sha256(password.encode()).digest(), self.password_digest
        )

    def issue(self):
        now = time.time()
        self.tokens = {
            key: expiry for key, expiry in self.tokens.items() if expiry > now
        }
        if len(self.tokens) >= 128:
            del self.tokens[next(iter(self.tokens))]
        token = secrets.token_urlsafe(32)
        self.tokens[hashlib.sha256(token.encode()).digest()] = now + TTL
        return token

    def valid(self, token):
        key = hashlib.sha256(token.encode()).digest()
        return self.tokens.get(key, 0) > time.time()

    def revoke(self, token):
        self.tokens.pop(hashlib.sha256(token.encode()).digest(), None)


class Handler(BaseHTTPRequestHandler):
    def log_message(self, *_):
        pass  # Never log credentials, cookies, login bodies or URL queries.

    def reply(self, status, body=b"", headers=None):
        self.send_response(status)
        self.send_header("Cache-Control", "no-store")
        self.send_header("Content-Length", str(len(body)))
        for name, value in (headers or {}).items():
            self.send_header(name, value)
        self.end_headers()
        self.wfile.write(body)

    def token(self):
        try:
            cookies = SimpleCookie(self.headers.get("Cookie", ""))
            return cookies[COOKIE].value if COOKIE in cookies else ""
        except Exception:
            return ""

    def same_origin(self):
        origin = self.headers.get("Origin", "")
        return not origin or origin == "https://" + self.headers.get("Host", "")

    def authenticated(self):
        if self.server.sessions.valid(self.token()):
            return True
        # Preserve existing command-line Basic Auth support without a browser challenge.
        try:
            header = self.headers.get("Authorization", "")
            if not header.startswith("Basic ") or len(header) > 2048:
                return False
            username, password = (
                base64.b64decode(header[6:], validate=True).decode().split(":", 1)
            )
            return self.server.sessions.credentials(username, password)
        except (ValueError, UnicodeError):
            return False

    def do_GET(self):
        if self.path == "/login":
            body = PAGE.replace("__ERROR__", "").encode()
            self.reply(200, body, {"Content-Type": "text/html; charset=utf-8"})
        elif self.path == "/_auth":
            if not self.same_origin():
                self.reply(403)
            else:
                self.reply(204 if self.authenticated() else 401)
        else:
            self.reply(404)

    def do_POST(self):
        if not self.same_origin():
            self.reply(403)
            return
        if self.path == "/logout":
            self.server.sessions.revoke(self.token())
            self.reply(
                303,
                headers={
                    "Location": "/login",
                    "Set-Cookie": f"{COOKIE}=; Path=/; Max-Age=0; HttpOnly; Secure; SameSite=Strict",
                },
            )
            return
        if self.path != "/login":
            self.reply(404)
            return
        try:
            size = int(self.headers.get("Content-Length", "0"))
            if size <= 0 or size > 4096:
                self.reply(400)
                return
            self.connection.settimeout(5)
            data = parse_qs(self.rfile.read(size).decode(), max_num_fields=4)
            username = data.get("username", [""])[0]
            password = data.get("password", [""])[0]
        except (ValueError, UnicodeError, TimeoutError):
            self.reply(400)
            return
        if not self.server.sessions.credentials(username, password):
            body = PAGE.replace(
                "__ERROR__", '<p class="error">账号或密码不正确。</p>'
            ).encode()
            self.reply(401, body, {"Content-Type": "text/html; charset=utf-8"})
            return
        token = self.server.sessions.issue()
        self.reply(
            303,
            headers={
                "Location": "/",
                "Set-Cookie": f"{COOKIE}={token}; Path=/; Max-Age={TTL}; HttpOnly; Secure; SameSite=Strict",
            },
        )


def main():
    server = HTTPServer(("127.0.0.1", 9000), Handler)
    server.sessions = Sessions(os.environ["DEMO_USERNAME"], os.environ["DEMO_PASSWORD"])
    server.serve_forever()


if __name__ == "__main__":
    main()
