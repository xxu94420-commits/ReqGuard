# DevFlow 数据交换 v1

这里实现双向数据契约与REST端点，不修改既有DevFlow仓库、不自动同步、不进行GitHub写操作。

ReqGuard → DevFlow：`GET /api/integrations/devflow/requirements/{id}?version=2`

```json
{
  "requirement_id": "uuid", "requirement_version": 2,
  "quality_score": 72.4,
  "dimension_scores": [{"id":"acceptance","name":"验收标准","score":3,"weight":12,"evidence":["验收"],"confidence":0.85}],
  "risk_level":"medium", "accepted_suggestions":["人工确认的建议"],
  "requirement_change_count":1, "evaluation_timestamp":"2026-10-03T00:00:00Z"
}
```

使用指定版本最后一次评估；未评估返回409。采纳列表只使用该评估的每条建议最新反馈；modify输出修改文本，reject不输出。

DevFlow → ReqGuard：先 `POST /api/requirements/{id}/tasks` 创建对应版本任务，再 `POST /api/requirements/{id}/delivery`。

```json
{
  "version":2,"task_id":"DF-123","issue_id":"42",
  "delivery_cycle":16.5,"ai_assisted":true,"test_passed":true,
  "defect_count":1,"rework_count":1,"delivery_timestamp":"2026-10-03T00:00:00Z",
  "commit":"sha-or-url","pull_request":"https://github.com/owner/repo/pull/1",
  "test_summary":"测试摘要","defects":"缺陷记录","rework_reason":"人工确认的原因"
}
```

周期单位小时；计数非负；UTC时间；version绑定证据，task_id必须在该版本已存在。MVP不执行签名验证、自动去重或Commit真实性验证；重复上报保留历史，分析每需求仅取最新交付与同版最后评估，避免重复权重。

`GET /api/analytics`提供四个指标的Pearson：周期、变更次数、缺陷数、返工次数。少于10个独立需求不展示系数；任一方零方差不可计算；10条只是产品显示阈值，不代表统计功效足够。返工次数不是严格返工率，缺少总开发次数分母时不能伪称返工率。所有结果需提示探索性、样本偏差、复杂度/团队混杂、相关不等于因果。当前没有真实交付研究数据。
