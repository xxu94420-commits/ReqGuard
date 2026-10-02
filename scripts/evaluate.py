"""Reproducible multilabel metrics, no model accuracy claims."""

import hashlib
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "ai-service"))
from app.models import EvaluateRequest  # noqa: E402
from app.rules import evaluate_rules  # noqa: E402

MAPPING = {
    "missing_user_scenario": "missing_user",
    "missing_acceptance_criteria": "missing_acceptance",
    "unmeasurable_goal": "missing_measurability",
    "missing_edge_cases": "missing_boundary",
    "unclear_data_dependency": "missing_data",
    "unclear_interface_dependency": "missing_interface",
    "mixed_goals": "mixed_scope",
    "unclear_scope": "mixed_scope",
    "missing_error_handling": "missing_error",
    "internal_conflict": "auth_conflict",
}


def metrics(tp, fp, fn):
    precision = tp / (tp + fp) if tp + fp else 0
    recall = tp / (tp + fn) if tp + fn else 0
    return {
        "tp": tp,
        "fp": fp,
        "fn": fn,
        "precision": round(precision, 4),
        "recall": round(recall, 4),
        "f1": round(2 * precision * recall / (precision + recall), 4)
        if precision + recall
        else 0,
    }


def run(split):
    path = ROOT / "dataset" / "requirements.json"
    rows = json.loads(path.read_text(encoding="utf-8"))
    selected = [r for r in rows if r["split"] == split]
    counts = {k: [0, 0, 0] for k in [*MAPPING, "ambiguous_language"]}
    errors = []
    risks = 0
    for row in selected:
        result = evaluate_rules(EvaluateRequest(text=row["text"]))
        ids = {f.id for f in result.findings}
        predicted = {key: ident in ids for key, ident in MAPPING.items()}
        predicted["ambiguous_language"] = any(
            f.kind == "ambiguous" for f in result.findings
        )
        risks += result.risk_level == row["expected_risk_level"]
        for key, pred in predicted.items():
            gold = row["labels"][key]
            if pred and gold:
                counts[key][0] += 1
            elif pred and not gold:
                counts[key][1] += 1
                errors.append({"id": row["id"], "label": key, "type": "false_positive"})
            elif gold:
                counts[key][2] += 1
                errors.append({"id": row["id"], "label": key, "type": "false_negative"})
    totals = [sum(c[i] for c in counts.values()) for i in range(3)]
    return {
        "split": split,
        "sample_count": len(selected),
        "micro": metrics(*totals),
        "per_label": {k: metrics(*v) for k, v in counts.items()},
        "errors": errors,
        "risk_matches": risks,
        "dataset_sha256": hashlib.sha256(path.read_bytes()).hexdigest(),
    }


if __name__ == "__main__":
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "rule_version": "rules-v1",
        "annotation_status": "AI起草标签，尚未经过独立人工复核；仅供工程验证",
        "train": run("train"),
        "test": run("test"),
        "llm": "未进行人工语义评测，不报告准确率",
    }
    (ROOT / "dataset" / "results.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    print(
        json.dumps(
            {s: report[s]["micro"] for s in ("train", "test")}, ensure_ascii=False
        )
    )
