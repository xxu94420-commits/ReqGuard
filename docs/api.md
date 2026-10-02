# REST API v1

同源前缀`/api`，JSON请求，错误返回4xx/5xx。没有删除或覆盖原文端点。开发环境Java8080，Docker由Web3000反向代理。

|方法|路径|用途|
|---|---|---|
|GET|/health|Java健康状态；数据库及AI健康在Compose分别检查|
|GET/POST|/requirements|列表或创建原始需求|
|GET|/requirements/{id}|需求、所有版本、所有记录快照|
|POST|/requirements/{id}/versions|追加版本，baseVersion并发前置条件|
|POST|/requirements/{id}/evaluations|评估指定版本并保存快照|
|POST|/requirements/{id}/feedback|接受/拒绝/修改某评估中的建议|
|POST|/requirements/{id}/tasks|创建版本开发计划|
|POST|/requirements/{id}/delivery|追加任务实际交付证据|
|POST|/requirements/{id}/retrospectives?version=2|冻结证据，生成Markdown|
|POST|/github/import|固定公开GitHub API读取Issue并创建需求|
|GET|/integrations/devflow/requirements/{id}?version=2|质量特征与最新采纳建议|
|GET|/analytics|探索性独立需求配对分析|
|GET|/benchmark|读取真实离线规则评测结果|

创建请求必填title、description、type、priority(low/medium/high/critical)、source、owner、project；可选issueUrl、issueId。返回201及需求ID，同时创建v1。描述最多30000字符。

版本请求：`{"text":"人工确认后的正文","reason":"明确验收","baseVersion":1}`。baseVersion必须等于当前最新版本，否则409。原文不改变。

评估请求：`{"version":1,"mode":"rule-only"}`。增强模式填写llm-enhanced；返回record.id及payload。多次评估均保留，同版页面展示最后一次。AI服务不可用返回502（区别于模型供应商失败由Python降级）。

反馈请求：`{"evaluationId":"uuid","suggestionId":"q_missing_goal","action":"reject","reason":"该目标已在关联文档说明"}`。modify要求modifiedText；reject要求reason。建议必须属于该需求指定评估；反馈追加，采纳率以每个evaluationId+suggestionId的最新决定统计。

任务请求：`{"version":2,"taskId":"DF-123","plan":"日期筛选与测试","plannedDelivery":"2026-10-10"}`。交付请求见DevFlow契约，版本及任务必须一致。复盘返回`payload.markdown`与生成时`evidence_record_ids`，旧报告不会由后续记录覆盖。

GitHub导入请求：`{"owner":"example","repo":"example","number":1}`。仅GET读取公开Issue，不支持PR、私有仓库或写回。

Python独立端点`POST /evaluate`、`GET /benchmark`、`GET /health`，完整Schema见运行中的`/docs`。UI不直接调用Python；版本数据只经Java写入。
