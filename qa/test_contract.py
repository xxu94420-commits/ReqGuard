"""Exercise Java → Python → database through real HTTP, including rejected writes."""

from concurrent.futures import ThreadPoolExecutor
from uuid import uuid4

import pytest


def root(requirement):
    return "/api/requirements/" + requirement["id"]


@pytest.mark.parametrize(
    "field,value",
    [
        ("title", ""),
        ("title", "x" * 201),
        ("description", ""),
        ("description", "x" * 30001),
        ("owner", ""),
        ("priority", "urgent"),
        ("unexpected", "field"),
    ],
    ids=[
        "blank-title",
        "long-title",
        "blank-description",
        "long-description",
        "blank-owner",
        "invalid-priority",
        "unknown-field",
    ],
)
def test_invalid_creation_is_rejected_without_partial_write(api, field, value):
    before = {r["id"] for r in api.get("/api/requirements").json()}
    body = dict(
        title="invalid",
        description="需求",
        type="feature",
        priority="high",
        source="qa",
        owner="qa",
        project="qa",
    )
    body[field] = value
    assert api.post("/api/requirements", json=body).status_code == 400
    assert {r["id"] for r in api.get("/api/requirements").json()} == before


def test_unknown_requirement(api):
    assert api.get("/api/requirements/" + str(uuid4())).status_code == 404


def test_evaluation_and_revision_preserve_original_and_evidence(api, requirement):
    path = root(requirement)
    first = api.post(path + "/evaluations", json={"version": 1, "mode": "rule-only"})
    assert first.status_code == 200
    record = first.json()
    assert len(record["payload"]["dimension_scores"]) == 14
    revised = api.post(
        path + "/versions",
        json={"baseVersion": 1, "text": "新版本需求", "reason": "QA"},
    )
    assert revised.status_code == 200 and revised.json()["number"] == 2
    detail = api.get(path).json()
    assert detail["requirement"]["originalText"] == requirement["originalText"]
    assert detail["versions"][0]["text"] == requirement["originalText"]
    stored = next(r for r in detail["records"] if r["id"] == record["id"])
    assert stored["versionId"] == detail["versions"][0]["id"]
    assert stored["payload"] == record["payload"]


def test_concurrent_revision_accepts_one_writer(api, requirement):
    path = root(requirement)

    def revise(text):
        return api.post(
            path + "/versions", json={"baseVersion": 1, "text": text, "reason": "race"}
        ).status_code

    with ThreadPoolExecutor(max_workers=2) as pool:
        codes = sorted(pool.map(revise, ["并发修改 A", "并发修改 B"]))
    assert codes == [200, 409]
    assert len(api.get(path).json()["versions"]) == 2


@pytest.mark.parametrize(
    "body", [{"version": 0, "mode": "rule-only"}, {"version": 1, "mode": "unknown"}]
)
def test_invalid_evaluation_does_not_append_record(api, requirement, body):
    path = root(requirement)
    assert api.post(path + "/evaluations", json=body).status_code == 400
    assert api.get(path).json()["records"] == []


def test_feedback_validation_and_cross_requirement_isolation(api, requirement):
    path = root(requirement)
    record = api.post(
        path + "/evaluations", json={"version": 1, "mode": "rule-only"}
    ).json()
    body = dict(
        evaluationId=record["id"],
        suggestionId=record["payload"]["suggestions"][0]["id"],
        action="reject",
    )
    assert api.post(path + "/feedback", json=body).status_code == 400
    body["action"] = "modify"
    assert api.post(path + "/feedback", json=body).status_code == 400
    body.update(action="accept", suggestionId="not-in-evaluation")
    assert api.post(path + "/feedback", json=body).status_code == 400
    body["suggestionId"] = record["payload"]["suggestions"][0]["id"]
    other = api.post(
        "/api/requirements",
        json=dict(
            title="Other QA",
            description="其他需求",
            type="feature",
            priority="low",
            source="qa",
            owner="qa",
            project="qa",
        ),
    ).json()
    assert api.post(root(other) + "/feedback", json=body).status_code == 404
    assert api.get(root(other)).json()["records"] == []
    assert len(api.get(path).json()["records"]) == 1
    assert api.post(path + "/feedback", json=body).status_code == 200
    exported = api.get(
        "/api/integrations/devflow/requirements/" + requirement["id"] + "?version=1"
    ).json()
    assert len(exported["accepted_suggestions"]) == 1


def test_nonexistent_version_is_not_evaluated(api, requirement):
    path = root(requirement)
    assert (
        api.post(
            path + "/evaluations", json={"version": 99, "mode": "rule-only"}
        ).status_code
        == 404
    )
    assert api.get(path).json()["records"] == []
