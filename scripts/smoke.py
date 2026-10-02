"""Exercise real Java → Python → DB lifecycle. No mocks and no GitHub writes."""

import argparse
import json

import httpx

parser = argparse.ArgumentParser()
parser.add_argument("--base-url", default="http://127.0.0.1:8080")
args = parser.parse_args()


def request(client, method, path, body=None, expected=200):
    response = client.request(method, "/api" + path, json=body)
    assert response.status_code == expected, (
        path,
        response.status_code,
        response.text[:200],
    )
    return response.json()


with httpx.Client(base_url=args.base_url, timeout=40) as client:
    request(client, "GET", "/health")
    requirement = request(
        client,
        "POST",
        "/requirements",
        {
            "title": "演示：运营订单导出",
            "description": "用户：运营登录后尽快优化订单导出。",
            "type": "feature",
            "priority": "high",
            "source": "smoke",
            "owner": "演示运营",
            "project": "ReqGuard Demo",
        },
        201,
    )
    root = "/requirements/" + requirement["id"]
    evaluation = request(
        client, "POST", root + "/evaluations", {"version": 1, "mode": "rule-only"}
    )
    assert evaluation["payload"]["mode"] == "rule-only"
    assert len(evaluation["payload"]["dimension_scores"]) == 14
    suggestion = evaluation["payload"]["suggestions"][0]
    request(
        client,
        "POST",
        root + "/feedback",
        {
            "evaluationId": evaluation["id"],
            "suggestionId": suggestion["id"],
            "action": "accept",
        },
    )
    export = request(
        client,
        "GET",
        "/integrations/devflow/requirements/" + requirement["id"] + "?version=1",
    )
    assert len(export["accepted_suggestions"]) == 1
    revised = request(
        client,
        "POST",
        root + "/versions",
        {
            "baseVersion": 1,
            "text": "用户：运营在登录后导出，目标2秒内完成。功能范围：仅订单，输入日期输出CSV。边界：最大100条，超过拒绝。验收 Given授权账号 When输入日期 Then返回CSV。数据来源orders表字段脱敏。接口API v1/export超时2秒。异常失败返回错误并记录。",
            "reason": "澄清范围和验收",
        },
    )
    assert revised["number"] == 2
    request(
        client,
        "POST",
        root + "/versions",
        {"baseVersion": 1, "text": "stale", "reason": "冲突"},
        409,
    )
    request(client, "POST", root + "/evaluations", {"version": 2, "mode": "rule-only"})
    request(
        client,
        "POST",
        root + "/tasks",
        {
            "version": 2,
            "taskId": "DEMO-1",
            "plan": "日期筛选与CSV导出",
            "plannedDelivery": "2026-10-10",
        },
    )
    request(
        client,
        "POST",
        root + "/delivery",
        {
            "version": 2,
            "task_id": "DEMO-1",
            "issue_id": "demo",
            "delivery_cycle": 16,
            "ai_assisted": True,
            "test_passed": True,
            "defect_count": 1,
            "rework_count": 1,
            "delivery_timestamp": "2026-10-11T00:00:00Z",
            "commit": "demo-not-real-commit",
            "pull_request": "",
            "test_summary": "演示数据：导出、错误及边界场景",
            "defects": "演示数据：编码兼容",
            "rework_reason": "演示数据：初版未说明编码",
        },
    )
    report = request(client, "POST", root + "/retrospectives?version=2", {})
    assert "偏差：1天" in report["payload"]["markdown"]
    detail = request(client, "GET", root)
    assert detail["requirement"]["originalText"] == "用户：运营登录后尽快优化订单导出。"
    assert len(detail["versions"]) == 2
    request(client, "GET", "/benchmark")
    analysis = request(client, "GET", "/analytics")
    assert "因果" in analysis["warning"]
    print(
        json.dumps(
            {
                "status": "passed",
                "requirement_id": requirement["id"],
                "version_count": 2,
                "score_v1": evaluation["payload"]["quality_score"],
                "record_count": len(detail["records"]),
            },
            ensure_ascii=False,
        )
    )
