# 自建集标注指南

本项目36条需求均为从零撰写的虚构业务样本，无抓取、无商业文档复制。初始文本和标签由 AI Coding 助手起草，`annotation_status=ai_authored_pending_human_review`，不是已经完成的人工标注。这个状态必须保留到真实标注者审查。

人工复核流程：先只看文本与指南，不看预测或结果；两人独立判断11个布尔问题标签和low/medium/high风险，记录标注者与日期；对不一致逐项讨论，不能达成一致则留待仲裁。完成后变更该条的status并新增reviewers、reviewed_at、disagreement_reason；不能伪填标注者。此后重新执行评测，以新SHA256区别原标签。

|标签|判定为true的条件|
|---|---|
|missing_user_scenario|没有可辨认的使用者与触发情境|
|missing_acceptance_criteria|没有可观测验收；“成功/完成/满足需要”不算|
|unmeasurable_goal|目标无业务指标；数字出现在边界不算目标可量化|
|missing_edge_cases|未说明非目标、空值、极值等至少一个实际边界|
|unclear_data_dependency|需要数据但来源、字段或口径未明确|
|unclear_interface_dependency|需要外部系统但协议、路径、版本或契约未明确|
|mixed_goals|同一需求包含多个可以分别交付的目标|
|unclear_scope|全平台、全系统或其他范围无法界定|
|ambiguous_language|出现无明确阈值的模糊词；并非每个“优化”都构成问题|
|missing_error_handling|无失败、超时、拒绝等异常处理行为|
|internal_conflict|同一前提下约束互斥；不同场景下不同权限不一定冲突|

风险：high包含冲突、关键依赖不可执行或无有效验收；medium存在局部缺口但主链明确；low包含可执行范围和验收。风险标签独立于规则分数，允许不一致，禁止从预测反推标签。

“无需数据/无需外部依赖”配合解释应算明确，而不是缺失。所有false只表示本标签的条件不满足，不等于需求完美。数据仅评估问题识别，14维评分的完整人工金标准尚未建立。
