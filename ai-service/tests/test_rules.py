from app.models import EvaluateRequest
from app.rules import RUBRIC, evaluate_rules


def test_weights_and_determinism():
    assert sum(row[2] for row in RUBRIC) == 100
    a = evaluate_rules(EvaluateRequest(text="尽快优化平台，所有功能都要友好"))
    b = evaluate_rules(EvaluateRequest(text="尽快优化平台，所有功能都要友好"))
    assert a.quality_score == b.quality_score
    assert len(a.dimension_scores) == 14
    assert all(0 <= d.score <= 5 for d in a.dimension_scores)
    assert {f.kind for f in a.findings} >= {"ambiguous", "scope", "missing"}


def test_conflict_and_acceptance_gate():
    result = evaluate_rules(
        EvaluateRequest(text="用户无需登录，同时必须登录才能使用。目标支持输入输出。")
    )
    assert any(f.id == "auth_conflict" for f in result.findings)
    assert result.quality_score <= 49
    assert result.risk_level == "high"


def test_quantified_and_testable_improves():
    poor = evaluate_rules(EvaluateRequest(text="优化导出"))
    good = evaluate_rules(
        EvaluateRequest(
            text="背景：目前运营人工导出耗时10分钟，统计基线。用户：管理员在登录后使用，权限仅本租户。目标：减少导出时间，成功指标至少降低50%，测试窗口1天。功能范围：输入日期，输出CSV，本期仅订单。非目标：不支持跨租户，最大100条，超过上限拒绝并测试。验收：Given授权账号 When输入日期 Then返回100条。数据来源订单表，字段脱敏校验。接口API版本v1 HTTP路径/export，超时2秒。异常失败返回错误并记录，禁止重试。风险：隐私泄露，缓解脱敏，负责人监控验证。优先级P1因为影响运营，评审排序依据。交付：2026-11-01，负责人在测试环境部署，检查通过可回滚。"
        )
    )
    assert good.quality_score > poor.quality_score
    assert good.quality_score >= 80
    assert all(s.needs_confirmation for s in good.suggestions)
