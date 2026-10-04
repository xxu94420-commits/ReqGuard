"""Create one bounded fixture outside the timed performance workload."""

import httpx

from conftest import local_url

with httpx.Client(
    base_url=local_url("QA_API_URL", "http://127.0.0.1:8080"), trust_env=False
) as client:
    result = client.post(
        "/api/requirements",
        json={
            "title": "QA performance fixture",
            "description": "用户登录后导出订单。",
            "type": "feature",
            "priority": "low",
            "source": "qa",
            "owner": "qa",
            "project": "disposable-performance-suite",
        },
    )
    result.raise_for_status()
    print(result.json()["id"])
