# 架构与数据责任

ReqGuard 是原创的需求质量与交付证据工作台。React → Java REST → PostgreSQL；Java → Python FastAPI → 确定性规则／可选 OpenAI 兼容接口。Python 不持久化需求。Java 是版本、评估快照、复核及交付证据唯一写入方。

Requirement 的元数据与原文在创建后保留；RequirementVersion 仅追加，版本号在事务锁内分配。Evaluation 绑定版本并保存评分、证据和规则／Prompt 版本。Feedback 绑定评估中的 suggestion_id，修改反馈保留原建议与修改文本。DevelopmentTask 和 DeliveryEvidence 绑定需求版本。Retrospective 保存生成时的证据快照和 Markdown，之后的反馈不追改旧报告。

版本链：Requirement → Version → Evaluation → Clarification/Suggestion → 新 Version → Acceptance/Test suggestions → DevelopmentTask → DeliveryEvidence → Feedback → Retrospective。

本地默认 H2 仅用于开发及集成测试，部署使用 PostgreSQL 和 Flyway；不以 H2 作为生产部署数据库。无身份认证的 MVP 只绑定本机，不适合直接公开。
