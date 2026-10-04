"""Black-box checks must target disposable loopback services, never the public demo."""

import os
from urllib.parse import urlsplit

import httpx
import pytest


def local_url(name, default):
    value = os.environ.get(name, default)
    parsed = urlsplit(value)
    if parsed.scheme != "http" or parsed.hostname not in {
        "127.0.0.1",
        "localhost",
        "::1",
    }:
        raise ValueError(
            f"{name} must be an HTTP loopback URL for an isolated test instance"
        )
    return value.rstrip("/")


@pytest.fixture
def api():
    with httpx.Client(
        base_url=local_url("QA_API_URL", "http://127.0.0.1:8080"),
        timeout=30,
        trust_env=False,
    ) as client:
        assert client.get("/api/health").status_code == 200
        yield client


@pytest.fixture
def requirement(api):
    response = api.post(
        "/api/requirements",
        json={
            "title": "QA isolated requirement",
            "description": "用户登录后尽快优化导出。",
            "type": "feature",
            "priority": "high",
            "source": "qa",
            "owner": "qa",
            "project": "disposable-quality-suite",
        },
    )
    assert response.status_code == 201, response.text
    return response.json()
