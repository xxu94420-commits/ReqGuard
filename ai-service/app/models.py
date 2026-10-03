from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class EvaluateRequest(StrictModel):
    text: str = Field(min_length=1, max_length=30000)
    priority: Literal["low", "medium", "high", "critical"] = "medium"
    mode: Literal["rule-only", "llm-enhanced"] = "rule-only"


class Finding(StrictModel):
    id: str
    dimension: Literal[
        "background",
        "user",
        "goal",
        "measurability",
        "scope",
        "boundary",
        "acceptance",
        "testability",
        "data",
        "interface",
        "error",
        "risk",
        "priority",
        "delivery",
    ]
    kind: Literal["missing", "ambiguous", "conflict", "risk", "scope"]
    message: str = Field(min_length=1, max_length=1000)
    evidence: str = Field(max_length=1000)
    confidence: float = Field(ge=0, le=1)
    needs_confirmation: bool = True
    source: Literal["rule", "llm"] = "rule"


class Suggestion(StrictModel):
    id: str
    kind: Literal["clarification", "revision", "acceptance", "test"]
    text: str = Field(min_length=1, max_length=30000)
    source: Literal["rule", "llm"] = "rule"
    needs_confirmation: bool = True


class DimensionScore(StrictModel):
    id: str
    name: str
    score: int = Field(ge=0, le=5)
    weight: int
    evidence: list[str]
    confidence: float


class SemanticResult(StrictModel):
    findings: list[Finding] = Field(max_length=40)
    suggestions: list[Suggestion] = Field(max_length=40)


class Evaluation(StrictModel):
    rubric_version: str = "rubric-v1"
    rule_version: str = "rules-v1"
    prompt_version: str = "semantic-v2"
    mode: str
    model: str | None = None
    latency_ms: int = 0
    fallback_reason: str | None = None
    quality_score: float
    risk_level: Literal["low", "medium", "high"]
    dimension_scores: list[DimensionScore]
    findings: list[Finding]
    suggestions: list[Suggestion]
    evaluation_timestamp: str
