# Cron 定时任务陷阱

## API Key 在 cron session 中不可用

当用 `/cron add` 创建定时任务时，cron 调度器启动的 agent session 可能读不到 `config.yaml` 中的 API key。  
这会导致报错：`Provider 'X' is set in config.yaml but no API key was found.`

**根因（两层）**：

**第一层** — 代码不查 `DEEPSEEK_API_KEY` env var：
`resolve_runtime_provider()` 对 `deepseek` 这类非 OpenRouter、非 custom 的 provider，查找 api_key 的候选列表是：
```
[explicit_api_key, cfg_api_key(仅当use_config_base_url时), OLLAMA_API_KEY, OPENAI_API_KEY, OPENROUTER_API_KEY]
```
里面**没有** `DEEPSEEK_API_KEY`，所以 `.env` 写了也找不到。

**修复**：在 `hermes_cli/runtime_provider.py` 的 `api_key_candidates` 列表中加入 `os.getenv("DEEPSEEK_API_KEY")`。本环境已做此修改。

**第二层** — config.yaml 的 `model.api_key` 不被读取：
`use_config_base_url` 只对 `requested_norm == "auto"` 或 `"custom"` 为 True。`"deepseek"` 不命中，config 里的 key 被跳过。

**完整修复步骤**（缺一不可）：

```bash
# 1. API key 写入 .env（标准位置）
echo 'DEEPSEEK_API_KEY=sk-xxxxx' >> ~/.hermes/.env

# 2. 修改 runtime_provider.py 源码
# 在 hermes_cli/runtime_provider.py 的 api_key_candidates 列表中加入：
#     os.getenv("DEEPSEEK_API_KEY"),

# 3. 重启 gateway
systemctl --user restart hermes-gateway
```

**验证方法**：`hermes cron list` 不再报 API key 错误即修复成功。

## 需要同时加载多个 skill

如果 cron 任务需要多个 skill 协作（如 youtubd + notebooklm-to-brainvault），用 `--skills` 指定：

```bash
--skills youtubd,notebooklm-to-brainvault
```

## 需要配置 toolsets

默认 toolset 可能不够。显式指定：

```bash
--toolsets terminal,file,web
```

## 调度器 ticker 间隔

系统每60秒 tick 一次。`cronjob(action='run')` 只是将 job 标记为待执行，实际执行要等下个 tick。
