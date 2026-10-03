import pytest


@pytest.fixture(autouse=True)
def isolate_provider_configuration(monkeypatch):
    """Tests never inherit a real local credential or contact its provider."""
    monkeypatch.delenv("LLM_API_KEY", raising=False)
    monkeypatch.setenv("LLM_BASE_URL", "https://provider.test/v1")
    monkeypatch.setenv("LLM_MODEL", "test-model")
    monkeypatch.setenv("LLM_RESPONSE_FORMAT", "json_object")
