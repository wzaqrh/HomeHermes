# Cron 定时任务陷阱

## API Key 在 cron session 中不可用

当用 `/cron add` 创建定时任务时，cron 调度器启动的 agent session 可能读不到 `config.yaml` 中的 API key。  
这会导致报错：`Provider 'X' is set in config.yaml but no API key was found.`

**根因**：`resolve_runtime_provider()` 对 `deepseek` 这类非 OpenRouter、非 custom 的 provider，不会从 config.yaml 中读取 `model.api_key`（因为 `use_config_base_url` 只对 `"auto"` 和 `"custom"` 为 True）。

**解决方法**：把 API key 写入 `~/.hermes/.env`（标准 API key 存储位置），cron 调度器启动 agent 时会读取该文件：
```bash
echo 'DEEPSEEK_API_KEY=sk-xxxxx' >> ~/.hermes/.env
# 然后重启 gateway
systemctl --user restart hermes-gateway
```

**备用方案**：创建 cron job 时显式指定 model 和 provider（仅部分场景有效，.env 方案更可靠）：
```bash
/cron add "任务名" \
  --schedule "0 9 * * *" \
  --model '{"model":"deepseek-v4-flash","provider":"deepseek"}' \
  --skills skill_a,skill_b \
  --toolsets terminal,file \
  --prompt "..."
```

`--model` 参数让调度器直接拿到正确的 provider 配置，但 key 仍需通过环境变量或 .env 提供。

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
