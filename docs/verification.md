# 验证记录

日期：2026-10-03。Windows本地，Java17.0.16、Python3.12、Node24。完整测试和构建结果将在交付前更新；Docker本机未安装，由仓库CI实际验证。

本地已验证：

- Python规则/Schema及降级测试6项通过；ruff检查与格式检查通过。
- Java业务测试4项通过，H2上的Flyway v1迁移成功；Spotless格式化完成，打包生成可运行Spring Boot JAR。
- 前端ESLint、TypeScript、Prettier检查通过；Vitest 2项通过；Vite生产构建成功。
- 实际启动Java8080、Python8000、前端5173。`scripts/smoke.py`真实链路通过：创建、评分、反馈、导出、新版本、409并发前置条件、任务、交付、复盘与分析。没有mock替代服务。
- 浏览器实际检查移动及桌面断点，工作台、评分、版本对比、评测视图；截图保存于`docs/screenshots/`。
- 初始评测集test micro P=0.45、R=0.90、F1=0.60。标签独立人工复核待完成。

本机未安装Docker，Compose/PostgreSQL验证交由GitHub Actions；以工作流实际结果为准。未调用真实LLM供应商，不报告其准确率。Python TestClient有1条anyio弃用警告，不影响测试结果。
