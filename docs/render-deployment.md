# 公网部署：Render 在线演示

ReqGuard已部署公网在线工作台：[https://reqguard-demo.onrender.com/](https://reqguard-demo.onrender.com/)。使用者可通过浏览器直接体验，账号为`reqguard`，密码由项目作者向使用者单独提供。已实现网页登录、真实AI接入及内部服务隔离；下文说明部署方式与维护限制。

此配置用于个人作品演示：一个免费Web Service包含Nginx入口、Java业务服务、Python AI服务与H2演示数据库。不是生产部署，也不提供永久数据保存。

## 资源与入口

`render.yaml`只声明一个`plan: free`服务，不创建收费私有服务或数据库。Dockerfile为`deploy/render/Dockerfile`，构建上下文为仓库根目录。Render提供HTTPS入口；仅Nginx监听`PORT`，Java8080与Python8000只监听容器内127.0.0.1。

整个页面与`/api/*`均要求认证；匿名访问页面跳转到`/login`，API返回401。网页登录使用HttpOnly、Secure、SameSite=Strict Cookie，会话有效期8小时，退出时撤销，最多128个会话；拒绝跨站Origin。CLI继续支持Basic Auth，但不发送触发浏览器原生弹窗的WWW-Authenticate挑战。登录账号默认`reqguard`，`DEMO_PASSWORD`由Render生成随机值。认证进程仅在容器内127.0.0.1:9000监听，内存中保存密码摘要与随机会话，不向Java、AI或Nginx子进程传递登录密码；密码不会写入前端、Git或日志；未配置足够长的密码时容器拒绝启动。`/healthz`不认证，只返回Java健康状态，不返回需求数据。API入口限流，单IP60请求/分钟、突发30、并发4；平台代理下IP可能共享，因此这是保守容量限制，不是按用户计费额度。

## 创建步骤

1. 登录Render Dashboard，New → Blueprint，连接`xxu94420-commits/ReqGuard`仓库，分支main，使用根目录`render.yaml`。
2. 核对只有一个Free Web Service，没有付费数据库、磁盘或私有服务。不要升级实例或添加支付方式来完成本教程。
3. 在提示中填写`LLM_API_KEY`，使用自己的Groq完整密钥；不想启用AI时可留空，或在创建后删除该环境变量。其他模型配置已在Blueprint中声明。密钥由用户直接输入Render，不发送到聊天。
4. 创建并部署。等待服务Live，复制Render给出的`https://...onrender.com`网址。
5. 在服务Environment中查看生成的`DEMO_PASSWORD`，在`/login`网页表单中用`reqguard`账号登录网址。不要将密码发到聊天、截图或公开README。浏览器只有在HTTPS下输入账号密码。
6. 新建一条虚构需求，选择LLM-enhanced，核对实际模式、模型与延迟；无密钥时验证Rule-only。

Render已有同名服务时先检查已有资源，避免重复创建。Blueprint新增`sync: false`环境变量不会自动提示，须在服务Environment手动填写。

## 测试与运行限制

CI额外构建本容器，并在512MiB限制下验证缺少密码拒绝启动、匿名API与错误密码401、网页跳转、Cookie属性、跨站拒绝、退出撤销、登录后访问、真实Java→Python规则模式生命周期。CI不调用付费模型。真实Render平台的冷启动、出口网络与AI供应商兼容性仍须部署后验证；CI通过不表示已上线。

Render免费服务15分钟无流量后会休眠，重新访问会冷启动。H2文件在重新部署、重启与休眠时丢失，版本历史仅在当前实例生命周期保存。需要长期留存时改用持久化PostgreSQL，免费Postgres只有30天有效期，不作为本方案默认依赖。

免费实例小时数、流量及构建分钟受平台额度限制；有支付方式的账号超出部分额度可能计费，因此应在Billing检查支出限制。LLM供应商费用独立于Render免费计划。不要上传真实业务数据；此处共享登录保护不能替代多用户权限、审计与生产数据管理。

本地Docker验证（需要已安装Docker，密码仅示例）：

```bash
docker build -f deploy/render/Dockerfile -t reqguard-render .
docker run --rm -p 127.0.0.1:10000:10000 -e DEMO_USERNAME=reqguard -e DEMO_PASSWORD=local-only-change-this-password reqguard-render
```

参考：[Render免费限制](https://render.com/docs/free)、[Blueprint规范](https://render.com/docs/blueprint-spec)、[Web Service与端口](https://render.com/docs/web-services)。

## 登录排障

原生HTTP Basic Auth在部分内置/自动化浏览器中无法弹出认证框，可能出现ERR_INVALID_AUTH_CREDENTIALS，即使普通浏览器可用。网页登录表单解决这一入口兼容问题，沿用DEMO_USERNAME/DEMO_PASSWORD，不更换密码也不开放匿名API。共享账号仍是演示用途，不能替代生产用户管理。

网页登录采用JSON提交，服务器设置安全Cookie后，页面检查`/api/health`再进入工作台。Nginx关闭绝对重定向，避免TLS代理后的跳转带上容器HTTP端口。密码提交按IP限制为每分钟5次、突发5次；GET登录页面不计入此额度。显示429时停止重复提交，等待约一分钟后重试；持续失败时核对Render中的账号与密码配置，不要把凭据发到聊天。

2026-10-04已在[公网演示](https://reqguard-demo.onrender.com/)验证网页登录和真实AI调用，详情见[验证记录](verification.md)。这不改变免费实例数据可能丢失及共享账号的限制。
