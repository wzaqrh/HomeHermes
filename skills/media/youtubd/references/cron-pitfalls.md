# Cron 调度器 API Key 故障排查

## 症状
Cron 任务状态为 `error`，错误信息：
```
RuntimeError: Provider 'deepseek' is set in config.yaml but no API key was found.
```

## 根因
`resolve_runtime_provider()` 在 `hermes_cli/runtime_provider.py` 中构建 `api_key_candidates` 列表时，对于**非 OpenRouter、非 custom 的 provider**（如 `deepseek`），**不会检查 `DEEPSEEK_API_KEY` 环境变量**。它只查 `OPENAI_API_KEY` 和 `OPENROUTER_API_KEY`。

config.yaml 中 `model.api_key` 仅在 `use_config_base_url=True` 时才会被加入候选列表，而该条件只对 `requested="auto"` 或 `requested="custom"` 成立。

## 修复

### 必须的修复（代码层面）
在 `~/.hermes/hermes-agent/hermes_cli/runtime_provider.py` 的 `api_key_candidates` 列表中，加一行 `os.getenv("DEEPSEEK_API_KEY")`：

```python
api_key_candidates = [
    explicit_api_key,
    (cfg_api_key if use_config_base_url else ""),
    (os.getenv("OLLAMA_API_KEY") if _is_ollama_url else ""),
    os.getenv("DEEPSEEK_API_KEY"),          # ← 添加这一行
    os.getenv("OPENAI_API_KEY"),
    os.getenv("OPENROUTER_API_KEY"),
]
```

### 环境变量配置
CU_ON_KEY 写入 `~/.hermes/.env`（API key 的标准存放位置，cron scheduler 会读取）：
```bash
DEEPSEEK_API_KEY=sk-xxx...xxx
```

### Cron 任务配置
创建/更新 cron job 时，**必须指定 `--model` 参数**让调度器知道用哪个 provider：
```bash
/cron add "xxx" --model '{"model":"deepseek-v4-flash","provider":"deepseek"}' ...
```

## 验证
```bash
cd ~/.hermes/hermes-agent
python3 -c "
import sys; sys.path.insert(0, '.')
from hermes_cli.runtime_provider import resolve_runtime_provider
r = resolve_runtime_provider(requested='deepseek')
print('OK' if len(r.get('api_key','')) > 10 else 'FAIL')
"
```
