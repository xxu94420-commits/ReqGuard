"""One real-provider request using synthetic text, never prints keys or provider bodies."""

import asyncio
import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai-service"))
from app.models import EvaluateRequest  # noqa: E402
from app.semantic import evaluate  # noqa: E402 -- also loads repository-local .env

SYNTHETIC_TEXT = (
    "连接验证专用虚构需求：访客无需登录即可查看报表，但同一报表必须登录才能查看。"
    "目标：查询2秒内返回；输入报表编号，输出标题。仅查询，不支持修改。"
    "验收：Given访客 When查询 Then展示报表。异常：超时返回错误。"
)


async def check():
    missing = [
        name
        for name in ("LLM_API_KEY", "LLM_BASE_URL", "LLM_MODEL")
        if not os.getenv(name, "").strip()
    ]
    if missing:
        print(
            json.dumps(
                {
                    "status": "not_configured",
                    "missing_fields": missing,
                    "message": "请在仓库根目录.env填写配置；API Key不要发到聊天或提交Git。",
                },
                ensure_ascii=False,
            )
        )
        return 2
    result = await evaluate(EvaluateRequest(text=SYNTHETIC_TEXT, mode="llm-enhanced"))
    semantic_count = sum(f.source == "llm" for f in result.findings)
    suggestion_count = sum(s.source == "llm" for s in result.suggestions)
    connected = result.mode == "llm-enhanced"
    print(
        json.dumps(
            {
                "status": "connected" if connected else "fallback",
                "mode": result.mode,
                "model": result.model,
                "prompt_version": result.prompt_version,
                "latency_ms": result.latency_ms,
                "fallback_reason": result.fallback_reason,
                "llm_findings": semantic_count,
                "llm_suggestions": suggestion_count,
                "schema_and_evidence_validated": connected,
                "note": "这是连接验证，不是模型准确率评测。仅发送脚本内虚构需求。",
            },
            ensure_ascii=False,
        )
    )
    return 0 if connected else 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(check()))
