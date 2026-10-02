"""Original evidence-tier rubric. Presence alone never earns a perfect score."""

import re
from datetime import datetime, timezone

from .models import DimensionScore, EvaluateRequest, Evaluation, Finding, Suggestion

# id, Chinese name, weight, anchors, observable detail markers, verification markers
RUBRIC = [
    (
        "background",
        "背景完整度",
        5,
        r"背景|现状|痛点|因为|目前",
        r"成本|耗时|投诉|人工|分钟",
        r"基线|调研|统计|来源",
    ),
    (
        "user",
        "用户与使用场景",
        8,
        r"用户|管理员|运营|客服|访客|角色",
        r"当|在|场景|登录|使用",
        r"权限|租户|角色|账号",
    ),
    (
        "goal",
        "目标明确度",
        9,
        r"目标|为了|旨在|实现",
        r"减少|增加|完成|降低|提升",
        r"成功|指标|达到|验收",
    ),
    (
        "measurability",
        "目标可衡量性",
        9,
        r"\d+\s*(?:%|秒|分钟|条|个|小时|天|ms|MB)",
        r"不超过|至少|小于|大于|以内|≤|>=",
        r"统计|测量|基线|测试|窗口",
    ),
    (
        "scope",
        "功能范围",
        8,
        r"功能|范围|支持|提供|输入|输出",
        r"输入|输出|步骤|流程",
        r"仅|限定|本期|边界",
    ),
    (
        "boundary",
        "非目标和边界",
        7,
        r"不包含|不支持|非目标|不做|边界|仅限",
        r"超过|最大|最小|空|上限|下限",
        r"拒绝|提示|测试|返回",
    ),
    (
        "acceptance",
        "验收标准",
        12,
        r"验收|Given|给定",
        r"When|当|Then|则|应",
        r"\d+|返回|展示|拒绝|断言",
    ),
    (
        "testability",
        "可测试性",
        10,
        r"测试|验收|Given|断言",
        r"输入|给定|When|当",
        r"输出|Then|则|返回|展示",
    ),
    (
        "data",
        "数据依赖",
        5,
        r"数据|数据库|字段|来源|无需数据",
        r"来源|字段|表|格式|无需",
        r"保留|脱敏|权限|同步|校验|不适用",
    ),
    (
        "interface",
        "接口及系统依赖",
        5,
        r"接口|API|系统依赖|无需外部",
        r"协议|路径|版本|无需|HTTP",
        r"超时|契约|限流|兼容|不适用",
    ),
    (
        "error",
        "异常与错误处理",
        7,
        r"异常|失败|错误|超时|不可用",
        r"返回|重试|提示|降级|拒绝",
        r"\d+|记录|测试|禁止",
    ),
    (
        "risk",
        "风险说明",
        5,
        r"风险|隐私|安全|泄露",
        r"缓解|控制|审计|脱敏|回滚",
        r"负责人|监控|验证|测试",
    ),
    (
        "priority",
        "优先级",
        4,
        r"优先级|P[0-3]|高优先|低优先",
        r"因为|影响|阻塞|成本",
        r"排序|依据|评审|确认",
    ),
    (
        "delivery",
        "交付条件",
        6,
        r"交付|上线|截止|期限|\d{4}-\d{2}-\d{2}",
        r"负责人|环境|部署|回滚",
        r"测试|检查|通过|审批",
    ),
]

AMBIGUOUS = r"尽快|适当|友好|优化|较高|尽可能|等等|所有功能|全面升级"


def excerpts(text: str, pattern: str) -> list[str]:
    return [
        text[max(0, m.start() - 18) : m.end() + 30]
        for m in list(re.finditer(pattern, text, re.I))[:3]
    ]


def evaluate_rules(request: EvaluateRequest) -> Evaluation:
    text = request.text.strip()
    dimensions = []
    findings = []
    for key, name, weight, anchor, detail, verification in RUBRIC:
        evidence = excerpts(text, anchor)
        # 0 absent, 1 heading only, 2 basic statement, 3 detail, 4 verifiable, 5 multiple evidence
        score = 0
        if evidence:
            score = 1 if len(text) < 20 else 2
            score += bool(re.search(detail, text, re.I))
            score += bool(re.search(verification, text, re.I))
            score += len(evidence) >= 2 and len(text) >= 120
        if key == "priority" and not evidence:
            score = 2  # structured priority is known, rationale is not
            evidence = [f"结构化优先级: {request.priority}；缺少排序依据"]
        dimensions.append(
            DimensionScore(
                id=key,
                name=name,
                score=min(score, 5),
                weight=weight,
                evidence=evidence,
                confidence=0.85 if evidence else 0.7,
            )
        )
        if score < 3:
            findings.append(
                Finding(
                    id=f"missing_{key}",
                    dimension=key,
                    kind="missing",
                    message=f"{name}缺失或不足，请补充可验证描述。",
                    evidence=evidence[0]
                    if evidence
                    else "全文未命中该维度线索（不等同于事实缺失）",
                    confidence=0.75,
                )
            )
    for i, match in enumerate(re.finditer(AMBIGUOUS, text)):
        findings.append(
            Finding(
                id=f"ambiguous_{i}",
                dimension="measurability",
                kind="ambiguous",
                message=f"“{match.group()}”缺少可判断的条件。",
                evidence=match.group(),
                confidence=0.95,
            )
        )
    scope_hits = excerpts(text, r"所有|全平台|全部系统|全面|一站式")
    if scope_hits or len(re.findall(r"同时|并且|以及", text)) >= 3:
        findings.append(
            Finding(
                id="mixed_scope",
                dimension="scope",
                kind="scope",
                message="范围可能过大或多目标混杂，建议拆分。",
                evidence="；".join(scope_hits) or "存在至少三个并列连接词",
                confidence=0.65,
            )
        )
    if re.search(r"无需登录|匿名", text) and re.search(r"必须登录|仅登录", text):
        findings.append(
            Finding(
                id="auth_conflict",
                dimension="scope",
                kind="conflict",
                message="匿名访问与必须登录可能冲突，请确认适用场景。",
                evidence="；".join(excerpts(text, r"无需登录|匿名|必须登录|仅登录")),
                confidence=0.85,
            )
        )
    score = round(sum(d.score * d.weight for d in dimensions) / 5, 1)
    # Release gate: weak acceptance/testability cannot be hidden by other dimensions.
    if any(d.score <= 1 for d in dimensions if d.id in {"acceptance", "testability"}):
        score = min(score, 59.0)
    if any(f.kind == "conflict" for f in findings):
        score = min(score, 49.0)
    risk = "high" if score < 50 else "medium" if score < 80 else "low"
    suggestions = [
        Suggestion(id=f"q_{f.id}", kind="clarification", text=f"请澄清：{f.message}")
        for f in findings
    ]
    suggestions.extend(
        [
            Suggestion(
                id="revision_template",
                kind="revision",
                text=text
                + "\n\n待人工补充：\n用户与场景：[角色、触发条件]\n目标：[指标、测量窗口]\n输入与输出：[契约]\n非目标与边界：[限制]\n异常：[处理方式]\n验收：[可验证结果]\n交付：[期限、负责人、环境]",
            ),
            Suggestion(
                id="ac_template",
                kind="acceptance",
                text="Given [明确角色、初始数据及权限] / When [输入和操作] / Then [可观测输出及量化阈值]。占位符确认后才可作为验收标准。",
            ),
            Suggestion(
                id="test_positive",
                kind="test",
                text="正向：有效输入与授权角色执行主流程，断言约定输出。待补充具体数据和阈值。",
            ),
            Suggestion(
                id="test_error",
                kind="test",
                text="异常：依赖超时或无权限，断言错误码、重试上限与数据不被修改。待人工确认。",
            ),
            Suggestion(
                id="test_boundary",
                kind="test",
                text="边界：空值、最大值、最大值+1，断言拒绝或允许条件。待人工确认。",
            ),
        ]
    )
    return Evaluation(
        mode="rule-only",
        quality_score=score,
        risk_level=risk,
        dimension_scores=dimensions,
        findings=findings,
        suggestions=suggestions,
        evaluation_timestamp=datetime.now(timezone.utc).isoformat(),
    )
