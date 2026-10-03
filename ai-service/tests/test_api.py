import json

import httpx
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_schema_and_no_key_fallback(monkeypatch):
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    assert client.post("/evaluate", json={"text": ""}).status_code == 422
    assert client.post("/evaluate", json={"text": "描述", "unknown": True}).status_code == 422
    result = client.post("/evaluate", json={"text": "尽快优化", "mode": "llm-enhanced"}).json()
    assert result["mode"] == "rule-only"
    assert result["fallback_reason"] == "missing_api_key"


def mock_provider(monkeypatch, content):
    monkeypatch.setenv("LLM_API_KEY", "fake-test-key")

    async def post(self, *args, **kwargs):
        return httpx.Response(
            200,
            request=httpx.Request("POST", "https://provider.test"),
            json={"choices": [{"message": {"content": content}}]},
        )

    monkeypatch.setattr(httpx.AsyncClient, "post", post)


def test_llm_schema_invalid_or_fabricated_falls_back(monkeypatch):
    for content in [
        "not json",
        '{"findings":[],"suggestions":[],"extra":1}',
        json.dumps(
            {
                "findings": [
                    {
                        "id": "x",
                        "dimension": "scope",
                        "kind": "conflict",
                        "message": "冲突",
                        "evidence": "不存在的文本",
                        "confidence": 0.9,
                    }
                ],
                "suggestions": [],
            }
        ),
    ]:
        mock_provider(monkeypatch, content)
        result = client.post("/evaluate", json={"text": "尽快优化", "mode": "llm-enhanced"}).json()
        assert result["mode"] == "rule-only"
        assert result["fallback_reason"] == "provider_or_schema_error"
        assert "fake-test-key" not in str(result)


def test_valid_llm_and_duplicate_merge(monkeypatch):
    finding = {
        "id": "x",
        "dimension": "scope",
        "kind": "conflict",
        "message": "请确认范围",
        "evidence": "优化",
        "confidence": 0.95,
        "needs_confirmation": False,
    }
    mock_provider(
        monkeypatch,
        json.dumps(
            {
                "findings": [finding, finding],
                "suggestions": [
                    {
                        "id": "x",
                        "kind": "acceptance",
                        "text": "Given [待确认] When [待确认] Then [待确认]",
                    }
                ],
            }
        ),
    )
    result = client.post("/evaluate", json={"text": "尽快优化", "mode": "llm-enhanced"}).json()
    assert result["mode"] == "llm-enhanced"
    semantic = [f for f in result["findings"] if f["source"] == "llm"]
    assert len(semantic) == 1
    assert semantic[0]["confidence"] == 0.8
    assert semantic[0]["needs_confirmation"] is True


def test_provider_timeout_returns_original_rule_snapshot(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "fake-test-key")

    async def timeout(self, *args, **kwargs):
        raise httpx.ReadTimeout("provider text must never be stored")

    monkeypatch.setattr(httpx.AsyncClient, "post", timeout)
    enhanced = client.post("/evaluate", json={"text": "优化", "mode": "llm-enhanced"}).json()
    baseline = client.post("/evaluate", json={"text": "优化"}).json()
    assert enhanced["mode"] == "rule-only"
    assert enhanced["quality_score"] == baseline["quality_score"]
    assert enhanced["findings"] == baseline["findings"]
    assert "provider text" not in str(enhanced)


def test_invalid_configuration_never_sends_key(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "fake-test-key")

    async def must_not_send(*args, **kwargs):
        raise AssertionError("Invalid destination must not receive credentials")

    monkeypatch.setattr(httpx.AsyncClient, "post", must_not_send)
    for url in [
        "",
        "http://remote.example/v1",
        "https://user:password@remote.example/v1",
        "https://remote.example/v1?key=secret",
        "https://[broken",
    ]:
        monkeypatch.setenv("LLM_BASE_URL", url)
        result = client.post("/evaluate", json={"text": "优化", "mode": "llm-enhanced"}).json()
        assert result["mode"] == "rule-only"
        assert result["fallback_reason"] == "invalid_provider_configuration"
        assert "fake-test-key" not in str(result)


def test_http_diagnostics_do_not_expose_provider_body(monkeypatch):
    monkeypatch.setenv("LLM_API_KEY", "fake-test-key")
    for status, reason in [
        (401, "provider_authentication_failed"),
        (404, "provider_model_or_endpoint_not_found"),
        (429, "provider_rate_or_quota_limit"),
    ]:

        async def post(self, *args, **kwargs):
            return httpx.Response(
                status,
                request=httpx.Request("POST", "https://provider.test"),
                text="sensitive-provider-body",
            )

        monkeypatch.setattr(httpx.AsyncClient, "post", post)
        result = client.post("/evaluate", json={"text": "优化", "mode": "llm-enhanced"}).json()
        assert result["fallback_reason"] == reason
        assert "sensitive-provider-body" not in str(result)
