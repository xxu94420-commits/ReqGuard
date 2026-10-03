"""Check the public demo gateway without printing login secrets."""

import os
import time

import httpx

base = os.environ.get("DEMO_BASE_URL", "http://127.0.0.1:10000")
auth = (os.environ.get("DEMO_USERNAME", "reqguard"), os.environ["DEMO_PASSWORD"])
with httpx.Client(base_url=base, timeout=10) as client:
    for attempt in range(90):
        try:
            if client.get("/healthz").status_code == 200:
                break
        except httpx.HTTPError:
            pass
        time.sleep(2)
    else:
        raise RuntimeError("Demo did not become healthy")
    redirect = client.get("/")
    assert redirect.status_code == 302
    assert redirect.headers["location"] == "/login"
    login_page = client.get("/login")
    assert login_page.status_code == 200
    assert "www-authenticate" not in login_page.headers
    assert client.get("/_auth").status_code == 404
    for path in ["/api/health", "/api/requirements", "/api/benchmark"]:
        assert client.get(path).status_code == 401, path
    assert client.get("/api/requirements", auth=(auth[0], "wrong")).status_code == 401
    response = client.get("/", auth=auth)
    assert response.status_code == 200
    assert "ReqGuard" in response.text
    assert response.headers["x-frame-options"] == "DENY"
    assert client.get("/api/health", auth=auth).status_code == 200
    login = client.post("/login", data={"username": auth[0], "password": "wrong"})
    assert login.status_code == 401
    login = client.post("/login", data={"username": auth[0], "password": auth[1]})
    assert login.status_code == 303
    cookie = login.headers["set-cookie"]
    assert "HttpOnly" in cookie and "Secure" in cookie and "SameSite=Strict" in cookie
    headers = {"Cookie": cookie.split(";", 1)[0]}
    assert client.get("/api/requirements", headers=headers).status_code == 200
    assert (
        client.get(
            "/api/requirements", headers={"Cookie": "__Host-reqguard_session=bad"}
        ).status_code
        == 401
    )
    assert (
        client.post(
            "/api/requirements",
            headers={**headers, "Origin": "https://evil.example"},
            json={},
        ).status_code
        == 403
    )
    assert client.post("/logout", headers=headers).status_code == 303
    assert client.get("/api/requirements", headers=headers).status_code == 401
print(
    "Demo health, unauthenticated rejection, wrong password and authenticated access passed"
)
