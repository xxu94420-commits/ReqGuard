# 自动化质量保障专项

## 目标与范围

验证需求创建、评估、人工复核和版本变更的正确性，重点保护原文、评估归属和追加式历史。接口测试使用真实 Java、Python 与数据库；浏览器测试通过真实 Chromium 操作页面，不拦截或伪造接口。模型供应商异常的单元验证沿用 `ai-service/tests/test_api.py`，与真实链路测试分别呈现。

这是一项测试工程实践，不宣称已经覆盖直播业务、多端兼容、生产规模性能或安全审计。

## 测试设计

| 风险 | 场景与断言 | 优先级 | 实现 |
| --- | --- | --- | --- |
| 无效数据写入 | 必填字段、长度上界加一、未知字段、非法优先级；拒绝后列表无新增 | P0 | test_contract.py |
| 版本竞争覆盖 | 两个请求使用同一 baseVersion；一成功一409，只追加一个版本 | P0 | test_contract.py |
| 原文或历史被覆盖 | 新版保存后原文和旧评估内容不变，旧评估仍绑定v1 | P0 | test_contract.py |
| 复核越界或无依据 | 跨需求评估引用、未知建议、拒绝缺理由、修改缺内容均拒绝且无反馈落库 | P0 | test_contract.py |
| 错误版本被评估 | 非法模式和版本返回400，不存在的版本返回404；均不追加评估 | P0 | test_contract.py |
| 前后端流程不一致 | 新建→规则评估→采纳→保存v2→历史→回到v1查看原评估 | P0 | test_browser.py |
| 依赖超时或错误内容 | 模型超时、认证失败、限流、Schema与证据校验；确定性结果保留 | P0 | 现有模型单元测试 |
| 基础性能退化 | 持续读取一条预置需求，校验状态码、需求ID和版本数组 | P1 | locustfile.py |

## 环境与运行

仅在可丢弃的本地实例运行，测试会创建记录，暂不做业务删除。使用新建 Compose 项目以隔离数据卷，例如 `docker compose -p reqguard-qa up --build -d --wait`，确保3000端口未被其他实例占用。模型密钥置空，测试不发送真实业务数据。独立启动时 Java 可使用 `DATABASE_URL=jdbc:h2:mem:qa;MODE=PostgreSQL;DATABASE_TO_LOWER=TRUE;DB_CLOSE_DELAY=-1`。

```bash
pip install -r qa/requirements.txt
python -m playwright install chromium
export QA_API_URL=http://127.0.0.1:3000
export QA_WEB_URL=http://127.0.0.1:3000
export NO_PROXY=localhost,127.0.0.1
python -m pytest qa/test_contract.py qa/test_browser.py -q --junitxml=artifacts/local/quality-junit.xml
```

PowerShell 中用 `$env:QA_API_URL='http://127.0.0.1:3000'` 等方式设置变量。源码独立启动的默认地址分别为8080与5173。测试地址限制为HTTP回环地址；仍须自行保证使用独立数据库，不能指向日常开发数据。

## 性能实验

在计时外创建一条固定需求。使用需求详情而不是健康检查，以包含服务和数据库读取；不调用外部模型，不在循环内写入，避免数据量不断增长干扰结果。

```bash
export QA_REQUIREMENT_ID=$(python qa/seed_performance.py)
python -m locust -f qa/locustfile.py --headless --host "$QA_API_URL" -u 5 -r 1 -t 20s --csv artifacts/local/performance --html artifacts/local/performance.html --exit-code-on-error 1
```

PowerShell：`$env:QA_REQUIREMENT_ID = python qa/seed_performance.py`。如需负载阶梯，分别运行5、10、20用户，并保持机器、数据库夹具、等待时间和时长一致。记录机器配置、操作系统、提交SHA、H2或PostgreSQL版本、数据量、用户数、升压速率和时长；从CSV报告读取请求数、错误率、吞吐量、P50/P95/P99。共享CI机器的20秒5用户检查仅验证脚本能运行且响应正确，不作为稳定性能基线或服务等级承诺。

## CI证据与故障定位

新增 `quality-suite` 在独立GitHub runner中启动Compose，运行接口与浏览器用例及小规模性能冒烟。无论成败上传 `quality-suite-evidence`，包含JUnit、Playwright trace、Locust CSV及HTML；失败时保留容器日志。可用 `python -m playwright show-trace artifacts/local/browser-trace.zip` 查看页面、请求和执行顺序。

Linux排障路径：先看JUnit失败断言和浏览器trace，再使用 `docker compose logs backend ai web` 对齐服务日志；以 `ss -lntp` 检查端口、`ps` 检查进程。压测异常先区分HTTP失败、响应内容失败与延迟增长，再检查CPU、内存、数据库和连接池。只有真实发现并复现的缺陷才写入缺陷记录，不预设修复或提效成果。

## 本次本地验证（2026-10-05）

此次更新提供的本地验证记录：Windows 本地 Java 17 → Python 服务 → 独立 H2 内存数据库：14 项真实 HTTP 接口测试通过，既有 Python 测试 17 项通过，QA 静态检查通过。5 用户、1 用户/秒升压、20 秒的只读详情接口冒烟共完成 416 次请求，0 次失败，近似 P95 为 6 ms；这是本机单条数据的小规模结果，不代表公网或生产性能。

Windows本地浏览器启动曾受沙箱限制；随后已在GitHub Actions Linux runner完成真实Chromium流程、14项接口测试及Locust性能冒烟。[此次CI](https://github.com/xxu94420-commits/ReqGuard/actions/runs/37218238691)六个任务全部成功，归档`quality-suite-evidence`包含JUnit、浏览器trace及性能报告。416次请求是前述本地实验的数据，不等同于CI请求数。

本地压测原始CSV及来源说明见[压测证据](evidence/qa-2026-10-05/README.md)。
