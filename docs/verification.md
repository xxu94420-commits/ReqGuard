# 验证记录

日期：2026-10-03。Windows本地，Java17.0.16、Python3.12、Node24。完整测试和构建结果将在交付前更新；Docker本机未安装，由仓库CI实际验证。

本地已验证：

- Python规则/Schema及降级测试7项通过，含供应商超时；ruff检查与格式检查通过。
- Java业务测试5项通过，含两个同时修改请求仅一个成功的真实并发测试；H2上的Flyway v1迁移成功；Spotless格式化完成，打包生成可运行Spring Boot JAR。
- 前端ESLint、TypeScript、Prettier检查通过；Vitest 2项通过；Vite生产构建成功。
- 实际启动Java8080、Python8000、前端5173。`scripts/smoke.py`真实链路通过：创建、评分、反馈、导出、新版本、409并发前置条件、任务、交付、复盘与分析。没有mock替代服务。
- 浏览器实际检查移动及桌面断点，工作台、评分、版本对比、评测视图；截图保存于`docs/screenshots/`。
- GitHub只读导入实际验证：读取本人公开DevFlow仓库Issue #1，保留URL、编号与来源；不执行GitHub写操作。
- 初始评测集test micro P=0.45、R=0.90、F1=0.60。标签独立人工复核待完成。

本机未安装Docker。首次[GitHub Actions四条流水线](https://github.com/xxu94420-commits/ReqGuard/actions/runs/37035158247)全部成功：Python、Java、前端、Docker。Docker实际构建并启动四服务，PostgreSQL上的Flyway迁移及smoke链路通过；不是仅检查配置文件。最后追加两项回归测试与跨平台换行一致性修复，再由最终提交CI验证。

未调用真实LLM供应商，不报告其准确率。Python TestClient有1条anyio弃用警告，不影响测试结果。评测文件固定LF换行，数据SHA256在Windows与Linux可比较。

## 真实AI接入回归（2026-10-03）

Python13项测试通过，ruff格式与检查通过。真实Groq模型openai/gpt-oss-20b返回结果经Schema与原文证据验证，Java保存评估历史；前端显示llm-enhanced、semantic-v2及3078ms。真实检查仅使用内置虚构需求，不将连接成功等同准确率。
