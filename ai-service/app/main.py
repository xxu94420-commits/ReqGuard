import json
from pathlib import Path

from fastapi import FastAPI

from .models import EvaluateRequest, Evaluation
from .semantic import evaluate

app = FastAPI(title="ReqGuard AI", version="0.1.0")


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/evaluate", response_model=Evaluation)
async def run_evaluation(request: EvaluateRequest):
    return await evaluate(request)


@app.get("/benchmark")
def benchmark():
    path = Path(__file__).resolve().parents[2] / "dataset" / "results.json"
    if not path.exists():
        return {"status": "not_run", "message": "运行 scripts/evaluate.py 后生成真实评测"}
    return json.loads(path.read_text(encoding="utf-8"))
