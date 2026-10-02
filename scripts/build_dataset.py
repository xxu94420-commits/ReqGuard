"""Original authored fixtures. Labels below are explicit annotations, never engine predictions.
Initial annotation authored by AI coding assistant; independent human review pending.
"""

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LABELS = [
    "missing_user_scenario",
    "missing_acceptance_criteria",
    "unmeasurable_goal",
    "missing_edge_cases",
    "unclear_data_dependency",
    "unclear_interface_dependency",
    "mixed_goals",
    "unclear_scope",
    "ambiguous_language",
    "missing_error_handling",
    "internal_conflict",
]

# Each tuple is independently authored text, positive label keys, risk, annotation reason.
SAMPLES = [
    (
        "背景：目前运营人工导出耗时10分钟，统计基线。用户：管理员在登录后使用，权限仅本租户。目标：减少导出时间，成功指标至少降低50%，测试窗口1天。功能范围：输入日期，输出CSV，本期仅订单。非目标：不支持跨租户，最大100条，超过上限拒绝并测试。验收：Given授权账号 When输入日期 Then返回100条。数据来源订单表，字段脱敏校验。接口API版本v1 HTTP路径/export，超时2秒。异常失败返回错误并记录，禁止重试。风险：隐私泄露，缓解脱敏，负责人监控验证。优先级P1因为影响运营，评审排序依据。交付：2026-11-01，负责人在测试环境部署，检查通过可回滚。",
        [],
        "low",
        "包含完整主链与可观察验收",
    ),
    (
        "背景：客服每天人工核对20条工单。用户：客服在交接时按租户权限查看。目标：将核对时间降低50%，统计基线测试窗口7天。功能范围仅工单查询，输入工单号输出状态。非目标不包含修改，空输入或超过32字符返回错误。验收 Given客服账号 When输入有效工单号 Then返回唯一状态，测试断言耗时不超过2秒。数据来源tickets表，字段脱敏保留30天。接口API v1路径/tickets，超时2秒返回错误并记录。风险泄露，缓解权限审计，负责人监控。优先级P1因为阻塞交接，评审排序。交付2026-11-10，负责人测试环境部署，检查通过可回滚。",
        [],
        "low",
        "客服查询有输入输出、边界与交付",
    ),
    (
        "背景：管理员手动归档每月耗时30分钟，来源调研基线。用户：管理员在月末登录后按租户权限归档。目标：减少操作，成功指标降低50%，测试窗口1月。功能范围仅归档，输入月份输出归档编号。非目标不支持删除，最大12个月，空值拒绝。验收 Given有权限账号 When输入月份 Then返回编号，测试断言2秒内输出。数据来源archive表字段，保留1年并校验。接口API v1路径/archive超时2秒。异常重复提交返回原编号并记录错误。风险误归档，缓解回滚，负责人测试验证。优先级P2因为影响月结，评审排序。交付2026-12-01，负责人测试环境部署检查通过。",
        [],
        "low",
        "归档闭环且异常可观察",
    ),
    (
        "目标：导出CSV耗时不超过2秒。范围仅订单，输入日期输出文件。验收：Given订单表 When输入日期 Then返回CSV。最大100条，超过上限拒绝。数据来源orders字段，接口API /export v1超时2秒。异常返回错误。",
        ["missing_user_scenario"],
        "medium",
        "未指定谁在何时导出",
    ),
    (
        "目标：缓存命中率至少90%，测量窗口1天。功能输入键输出值，仅内存缓存，不支持跨机。最大1000个键，超过淘汰最旧键。验收 Given缓存 When查询键 Then返回值。数据来源本地，接口API get，失败返回错误。",
        ["missing_user_scenario"],
        "medium",
        "缓存消费者与使用场景未说明",
    ),
    (
        "功能范围仅生成月度账单，输入月份输出PDF。目标2秒内完成。验收 Given账单数据 When提交月份 Then返回PDF。最大12个月，超限拒绝。数据来源billing表字段，API /bill v1。异常失败记录错误。",
        ["missing_user_scenario"],
        "medium",
        "没有账单发起者及授权场景",
    ),
    (
        "用户：运营在登录后按日期导出。目标减少耗时至2秒。输入日期输出CSV，本期仅订单。最大100条，超过上限拒绝。数据来源orders字段，接口API v1/export超时2秒。异常返回错误并记录。",
        ["missing_acceptance_criteria"],
        "high",
        "没有具体验收或测试断言",
    ),
    (
        "用户：客服在交接时查询状态。目标返回时间不超过1秒。功能仅查询，输入工单编号输出状态。边界空值拒绝，最大32字符。数据tickets表，接口API /tickets v1。异常超时返回错误。",
        ["missing_acceptance_criteria"],
        "high",
        "交付没有Given/When/Then或等价可验证标准",
    ),
    (
        "管理员在月末归档，目标降低操作时间50%。功能输入月份输出编号，仅归档不删除。最大12个月，超过拒绝。数据archive表字段，API /archive v1。异常重复返回原编号。",
        ["missing_acceptance_criteria"],
        "high",
        "未定义验收条件",
    ),
    (
        "用户：管理员在登录后查看报告。目标提升工作体验。仅报告查询，输入月份输出列表，不支持修改。空值拒绝，最大12个月。验收 Given账号 When输入月份 Then展示列表。数据reports表，API /reports。失败返回错误。",
        ["unmeasurable_goal"],
        "medium",
        "提升体验没有目标指标，边界数字不能替代业务指标",
    ),
    (
        "客服在交接时使用工单页。目标改善工作效率。功能仅工单查询，输入编号输出状态，空编号拒绝。验收 Given客服 When查编号 Then展示状态。数据来源tickets，API /tickets。异常提示失败。",
        ["unmeasurable_goal"],
        "medium",
        "效率没有基线或目标数值",
    ),
    (
        "运营在月末查看统计。目标增强决策能力。仅统计展示，输入日期输出图表，空日期拒绝。验收 Given数据 When提交日期 Then展示图表。数据来自订单表字段，接口API v1/stats。异常超时返回错误。",
        ["unmeasurable_goal"],
        "medium",
        "决策能力不可直接测试",
    ),
    (
        "用户：管理员登录后导出，目标不超过2秒。仅订单输入日期输出CSV。验收 Given账号 When导出 Then返回CSV。数据orders表字段，API /export v1。异常超时返回错误并记录。",
        ["missing_edge_cases"],
        "medium",
        "没有空值、上限或非目标",
    ),
    (
        "客服在交接时查询工单，目标1秒内返回。输入编号输出状态。验收 Given客服 When查编号 Then展示状态。数据来源tickets字段，接口API v1/tickets，异常失败返回错误。",
        ["missing_edge_cases"],
        "medium",
        "工单不存在与编号长度边界未定义",
    ),
    (
        "运营每周提交订阅请求，目标3秒内完成。输入邮件输出订阅号。验收 Given运营 When提交邮件 Then返回订阅号。数据来源subscriptions，API /subscribe。异常超时返回错误。",
        ["missing_edge_cases"],
        "medium",
        "邮件长度和空值未定义",
    ),
    (
        "用户：运营登录后查看销量，目标2秒内展示。仅销量报表，输入日期输出图表，不包含预测，最大30天超过拒绝。验收 Given运营 When提交日期 Then展示图表。需要业务数据，但不说明来源。API /sales v1超时返回错误。",
        ["unclear_data_dependency"],
        "high",
        "明确需要数据但来源字段与口径缺失",
    ),
    (
        "管理员在登录后对账，目标1分钟完成。仅对账，输入月份输出差额，最多12个月超限拒绝。验收 Given账号 When对账 Then展示差额。从现有库取得必要信息。接口API /reconcile v1，失败返回错误。",
        ["unclear_data_dependency"],
        "high",
        "现有库未定义表字段口径",
    ),
    (
        "客服在交接时查客户等级，目标2秒内输出。仅查询不修改，空编号拒绝。验收 Given客服 When查编号 Then展示等级。等级按公司的业务资料算。API /tier v1，超时提示错误。",
        ["unclear_data_dependency"],
        "medium",
        "资料来源和等级计算输入不明",
    ),
    (
        "用户：运营登录后推送账单，目标1秒内收到回执。仅账单推送，输入账单号输出回执，不支持重复，空号拒绝。验收 Given运营 When推送 Then展示回执。数据billing表字段，连接外部平台。异常失败返回错误。",
        ["unclear_interface_dependency"],
        "high",
        "外部平台没有协议路径与版本",
    ),
    (
        "管理员月末发通知，目标2秒内提交。仅邮件通知，输入地址输出回执，不做短信，空地址拒绝。验收 Given账号 When发送 Then展示回执。数据来源users表字段，通过另一个服务处理。失败返回错误。",
        ["unclear_interface_dependency"],
        "medium",
        "另一个服务的契约未知",
    ),
    (
        "客服登录后创建退款，目标3秒内返回。仅退款申请，输入单号输出申请号，不支持自动审批，空号拒绝。验收 Given客服 When申请 Then返回申请号。数据refund表字段，与财务系统对接。异常失败记录错误。",
        ["unclear_interface_dependency"],
        "high",
        "财务系统接入契约未定义",
    ),
    (
        "用户：管理员登录后管理平台。目标减少操作时间50%。同时做导出，并且做支付，以及做聊天，同时做推荐。输入业务信息输出结果。验收 Given管理员 When使用 Then成功。数据来源业务库，接口API。失败提示错误。",
        [
            "mixed_goals",
            "unclear_scope",
            "missing_edge_cases",
            "missing_acceptance_criteria",
            "unclear_data_dependency",
            "unclear_interface_dependency",
        ],
        "high",
        "四个目标混杂，成功无法判定",
    ),
    (
        "运营在工作时要一站式平台，目标提高效率。同时报表，并且营销，以及审批，同时库存。验收 Given运营 When操作 Then满足需要。数据接入全部系统。异常失败提示。",
        [
            "mixed_goals",
            "unclear_scope",
            "missing_edge_cases",
            "missing_acceptance_criteria",
            "unmeasurable_goal",
            "unclear_data_dependency",
            "unclear_interface_dependency",
        ],
        "high",
        "多目标且没有边界或可判定输出",
    ),
    (
        "客服登录后要同时退款，并且开户，以及关户，同时发券。目标减少处理时间50%。范围是这些流程，输入客户号输出操作结果。验收 Given客服 When处理 Then完成。数据客户库，API。失败返回错误。",
        [
            "mixed_goals",
            "unclear_scope",
            "missing_edge_cases",
            "missing_acceptance_criteria",
            "unclear_data_dependency",
            "unclear_interface_dependency",
        ],
        "high",
        "不同权限和流程混在一个需求",
    ),
    (
        "管理员登录后管理所有功能，覆盖全平台全部系统。目标2秒内响应。输入请求输出响应。验收 Given管理员 When请求 Then满足业务。数据业务库，API。失败提示。",
        [
            "unclear_scope",
            "missing_edge_cases",
            "missing_acceptance_criteria",
            "unclear_data_dependency",
            "unclear_interface_dependency",
        ],
        "high",
        "全平台没有可交付范围",
    ),
    (
        "运营需要全面升级系统，一站式支持所有工作。目标缩短时间50%。输入任务输出结果。验收 Given运营 When使用 Then完成。数据现有库，对接API。失败提示。",
        [
            "unclear_scope",
            "ambiguous_language",
            "missing_edge_cases",
            "missing_acceptance_criteria",
            "unclear_data_dependency",
            "unclear_interface_dependency",
        ],
        "high",
        "全面升级范围与完成条件不可判定",
    ),
    (
        "用户：客服登录后要查询全部系统记录。目标2秒内返回。输入客户号输出所有记录。验收 Given客服 When查询 Then展示记录。数据接入全部库，API。异常失败返回错误。",
        [
            "unclear_scope",
            "missing_edge_cases",
            "unclear_data_dependency",
            "unclear_interface_dependency",
        ],
        "high",
        "全部库的边界及权限未知",
    ),
    (
        "用户：运营登录后尽快优化导出，界面要友好，速度较高。仅订单输入日期输出CSV，不包含退款，最大100条超限拒绝。验收 Given运营 When导出 Then返回CSV。数据orders表字段，API /export v1。异常失败返回错误。",
        ["ambiguous_language", "unmeasurable_goal"],
        "medium",
        "尽快友好较高均无阈值",
    ),
    (
        "管理员月末查看报告，希望适当调整样式，尽可能提高体验。仅报告输入月份输出表格，空值拒绝。验收 Given账号 When提交月份 Then展示表格。数据reports表字段，API /reports v1。异常提示错误。",
        ["ambiguous_language", "unmeasurable_goal"],
        "medium",
        "适当尽可能无法判定",
    ),
    (
        "客服登录后查询工单，目标优化效率，页面友好。仅查询输入编号输出状态，空值拒绝。验收 Given客服 When查编号 Then展示状态。数据tickets表字段，API /tickets v1。异常失败返回错误。",
        ["ambiguous_language", "unmeasurable_goal"],
        "medium",
        "效率与友好没有量化",
    ),
    (
        "用户：运营登录后导出。目标2秒内完成。功能仅订单，输入日期输出CSV，不包含退款，最大100条。验收 Given运营 When导出 Then返回CSV。数据orders表字段，接口API /export v1。",
        ["missing_error_handling"],
        "high",
        "依赖失败与超限行为未指定",
    ),
    (
        "管理员月末归档，目标1秒内返回。仅归档不删除，输入月份输出编号，最大12个月。验收 Given账号 When提交月份 Then返回编号。数据archive表字段，接口API /archive v1。",
        ["missing_error_handling"],
        "medium",
        "重复归档失败等处理未定义",
    ),
    (
        "客服登录后订阅通知，目标2秒内完成。仅邮件不含短信，输入邮件输出编号，最大32字符。验收 Given客服 When订阅 Then返回编号。数据subscriptions表字段，接口API /subscribe v1。",
        ["missing_error_handling"],
        "medium",
        "外部接口失败后行为未定义",
    ),
    (
        "用户：访客无需登录查看报表，但必须登录才能查看同一报表。目标2秒内展示。仅报告查询，输入日期输出列表，不含修改，空值拒绝。验收 Given访客 When查询 Then展示列表。数据reports表字段，API /reports v1。异常返回错误。",
        ["internal_conflict"],
        "high",
        "同一报表匿名与必须登录直接冲突",
    ),
    (
        "用户：管理员登录后导出，目标2秒内完成。仅CSV，验收 Given账号 When导出 Then文件同时必须为CSV且禁止CSV。最大100条超限拒绝。数据orders表字段，API /export v1。异常返回错误。",
        ["internal_conflict"],
        "high",
        "输出格式肯定与否定冲突，规则可能漏报",
    ),
    (
        "运营在月末归档，目标2秒内完成。功能仅归档不删除。验收 Given运营 When归档 Then保存时间必须大于30天且必须小于1天。空月份拒绝。数据archive表字段，API /archive v1。异常返回错误。",
        ["internal_conflict"],
        "high",
        "保存时长区间互斥，规则可能漏报",
    ),
]


def main():
    rows = []
    for i, (text, positives, risk, reason) in enumerate(SAMPLES, 1):
        rows.append(
            {
                "id": f"REQ-{i:03}",
                "text": text,
                "labels": {key: key in positives for key in LABELS},
                "expected_risk_level": risk,
                "annotation_reason": reason,
                "split": "test" if i % 3 == 0 else "train",
                "annotation_status": "ai_authored_pending_human_review",
            }
        )
    folder = ROOT / "dataset"
    folder.mkdir(exist_ok=True)
    (folder / "requirements.json").write_text(
        json.dumps(rows, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )


if __name__ == "__main__":
    main()
