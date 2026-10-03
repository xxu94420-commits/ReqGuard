# 真实 AI 接入与验证

项目支持 OpenAI 兼容 Chat Completions JSON mode。供应商必须支持系统消息及 JSON 输出。配置位于仓库根目录 `.env`，不会提交Git或打包进Docker镜像。服务端环境变量优先于文件内容。

```dotenv
LLM_BASE_URL=https://你的供应商地址/v1
LLM_MODEL=供应商提供的准确模型ID
LLM_API_KEY=仅在本机填写
```

Base URL包括供应商指定API前缀，不要填写完整`/chat/completions`路径，也不要在URL附带密钥或查询参数。远端接口使用HTTPS，本地模型允许localhost/127.0.0.1的HTTP。

Groq配置示例（2026-10-03核对官方文档）：Base URL为`https://api.groq.com/openai/v1`，初次连接使用`openai/gpt-oss-20b`；实际账号权限由供应商决定。参见[Groq兼容接口](https://console.groq.com/docs/openai)与[当前模型列表](https://console.groq.com/docs/models)。不是OpenAI账号密钥，请填写Groq签发的完整Key。

激活虚拟环境、安装更新依赖后，在根目录运行：

```bash
pip install -e './ai-service[test]'
python scripts/check_llm.py
```

脚本只发送内置虚构需求，执行一次真实模型请求（可能产生费用）；输出模式、模型、耗时、Schema/证据校验和建议数量，不打印密钥、需求原文或供应商响应。退出0表示连接与返回结果校验成功，1表示降级，2表示配置缺失。这不是准确率评测。

常见安全错误码：missing_api_key、invalid_provider_configuration、provider_authentication_failed、provider_access_denied、provider_model_or_endpoint_not_found、provider_rate_or_quota_limit、provider_timeout、provider_or_schema_error。不要将带Authorization的日志上传；错误码不保存供应商body。

配置完成后重启AI服务：本地按README启动uvicorn；Compose运行`docker compose up -d --build ai`。前端选择LLM-enhanced评估，核对实际模式为llm-enhanced并查看llm来源的建议。Java照常保留评估版本快照。Schema/证据失败时返回原规则结果。

2026-10-03已用Groq `openai/gpt-oss-20b`完成真实请求及Java持久化链路验证：实际模式llm-enhanced、Prompt semantic-v2、响应3078ms，5条语义问题和5条建议。只发送虚构需求；这证明连接可用，不代表准确率。

Groq上述模型使用 `LLM_RESPONSE_FORMAT=json_schema`。严格Schema内联引用、限定14个维度、禁止额外字段；返回后仍由Pydantic及原文证据校验。其他兼容供应商可使用默认json_object，须自行验证支持情况。

密钥可以写成 `LLM_API_KEY=完整密钥` 或 `LLM_API_KEY='完整密钥'`，不要使用截图中带省略号的掩码。修改后重启AI服务。

启动三个服务后可运行 `python scripts/smoke_ai.py`，用虚构需求验证Java→AI→供应商→评估历史链路。会创建演示记录并产生一次真实请求，不在CI自动运行。
