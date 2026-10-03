# Prompt 与语义结果版本

2026-10-03新增semantic-v2：实际Groq调用发现模型自创维度ID，虽然JSON结构有效仍被聚合层拒绝。将14维taxonomy加入Pydantic Literal枚举并写入Prompt JSON Schema；明确登录冲突归scope。保留旧评估semantic-v1，不覆盖历史。v2同时以合法JSON序列化Schema，不再使用Python字典repr。

`semantic-v1`位于`ai-service/app/semantic.py`。系统指令要求视输入为不可信数据，只输出Schema、逐字证据、待确认建议，不执行需求内的指令。发送数据仅text，不带需求owner、来源元数据或数据库记录。

请求 OpenAI兼容 `POST {LLM_BASE_URL}/chat/completions`，使用JSON mode。Pydantic禁止额外字段，限制数组数量、文本长度、0–1置信度和枚举。模型选择来自环境变量。Provider响应最大200KB，HTTP20秒超时；重定向不跟随；失败后返回纯规则结果，不保存供应商body或异常文本。

聚合校验维度ID、逐字证据；去重按dimension+message标准化，建议按text标准化。模型ID由服务重编，source强制llm、needs_confirmation强制true、置信度最高0.8。该上限是保守设计常量，不是校准概率。近义词级语义去重未实现。

更改指令须升Prompt版本，Schema破坏变更须升API版本，规则或权重变更各自升版本。评估快照记录rubric_version、rule_version、prompt_version、模型、实际模式、降级原因、响应耗时及时间。旧结果不按新规则回填。

JSON mode不保证符合Schema，因此本地校验不可省略。工具参考：[官方JSON输出说明](https://developers.openai.com/api/docs/guides/structured-outputs)。OpenAI兼容供应商能力可能不同，失败会降级。
