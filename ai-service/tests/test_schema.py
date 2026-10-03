import pytest
from pydantic import ValidationError

from app.models import Finding, SemanticResult
from app.rules import RUBRIC
from app.output_schema import strict_output_schema


def test_prompt_schema_contains_exact_original_dimension_taxonomy():
    schema = SemanticResult.model_json_schema()
    assert set(schema["$defs"]["Finding"]["properties"]["dimension"]["enum"]) == {
        r[0] for r in RUBRIC
    }


def test_invented_dimension_rejected_before_aggregation():
    with pytest.raises(ValidationError):
        Finding(
            id="fake",
            dimension="authentication",
            kind="conflict",
            message="冲突",
            evidence="登录",
            confidence=0.8,
        )


def test_provider_strict_schema_requires_all_fields_and_keeps_enums():
    schema = strict_output_schema()
    finding = schema["properties"]["findings"]["items"]
    suggestion = schema["properties"]["suggestions"]["items"]
    for obj in [schema, finding, suggestion]:
        assert set(obj["required"]) == set(obj["properties"])
        assert obj["additionalProperties"] is False
    assert len(finding["properties"]["dimension"]["enum"]) == 14
    assert "default" not in finding["properties"]["needs_confirmation"]
    assert "$ref" not in str(schema)
