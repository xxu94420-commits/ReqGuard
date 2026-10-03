import os

from dotenv import load_dotenv


def test_local_env_never_overrides_deployed_key(tmp_path, monkeypatch):
    local = tmp_path / ".env"
    local.write_text(
        'LLM_API_KEY="local-placeholder"\nLLM_MODEL="configured-model"\n', encoding="utf-8"
    )
    monkeypatch.setenv("LLM_API_KEY", "deployment-placeholder")
    monkeypatch.delenv("LLM_MODEL", raising=False)
    load_dotenv(local, override=False)
    assert os.environ["LLM_API_KEY"] == "deployment-placeholder"
    assert os.environ["LLM_MODEL"] == "configured-model"
