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
    for path in ["/", "/api/health", "/api/requirements", "/api/benchmark"]:
        assert client.get(path).status_code == 401, path
    assert client.get("/api/requirements", auth=(auth[0], "wrong")).status_code == 401
    response = client.get("/", auth=auth)
    assert response.status_code == 200
    assert "ReqGuard" in response.text
    assert response.headers["x-frame-options"] == "DENY"
    assert client.get("/api/health", auth=auth).status_code == 200
print(
    "Demo health, unauthenticated rejection, wrong password and authenticated access passed"
)
