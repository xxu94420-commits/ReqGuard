"""Opt-in real AI integration check; persists only a clearly synthetic demo requirement."""

import argparse
import json

import httpx

from check_llm import SYNTHETIC_TEXT

parser = argparse.ArgumentParser()
parser.add_argument("--base-url", default="http://127.0.0.1:8080")
args = parser.parse_args()

with httpx.Client(base_url=args.base_url, timeout=40) as client:
    created = client.post(
        "/api/requirements",
        json={
            "title": "真实AI连接演示：虚构报表权限冲突",
            "description": SYNTHETIC_TEXT,
            "type": "feature",
            "priority": "medium",
            "source": "ai-smoke",
            "owner": "演示用户",
            "project": "ReqGuard AI Demo",
        },
    )
    created.raise_for_status()
    requirement_id = created.json()["id"]
    response = client.post(
        f"/api/requirements/{requirement_id}/evaluations",
        json={
            "version": 1,
            "mode": "llm-enhanced",
        },
    )
    response.raise_for_status()
    evaluation = response.json()
    result = evaluation["payload"]
    report = {
        "requirement_id": requirement_id,
        "evaluation_id": evaluation["id"],
        "mode": result["mode"],
        "model": result["model"],
        "prompt_version": result["prompt_version"],
        "latency_ms": result["latency_ms"],
        "fallback_reason": result["fallback_reason"],
        "llm_findings": sum(f["source"] == "llm" for f in result["findings"]),
        "llm_suggestions": sum(s["source"] == "llm" for s in result["suggestions"]),
    }
    print(json.dumps(report, ensure_ascii=False))
    assert result["mode"] == "llm-enhanced", "真实AI未成功增强，请检查安全错误码"
    assert all(f["needs_confirmation"] for f in result["findings"])
    history = client.get(f"/api/requirements/{requirement_id}")
    history.raise_for_status()
    assert any(row["id"] == evaluation["id"] for row in history.json()["records"])
