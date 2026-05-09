---
name: tradingagents-runner
description: Run local TradingAgents stock analysis from Codex with DeepSeek as the default LLM, reading DEEPSEEK_API_KEY from the environment or TRADING_AGENTS_DEEPSEEK_API_KEY from ~/.env as fallback, and supporting configurable depth, selected analysts such as fundamentals, technical/market, news, and social sentiment, dates, output language, checkpoints, and report export. Use when a user asks to test TradingAgents, analyze a ticker with TradingAgents, run a DeepSeek-backed TradingAgents report, or generate TradingAgents reports from the local source tree.
---

# TradingAgents Runner

## Purpose

Use this skill to run the local TradingAgents project reliably without re-discovering its CLI and Python wiring each time. Prefer the bundled script when the user wants a repeatable command, parameterized analysis, saved reports, or a non-interactive run.

Default project path: `/home/bdwillwin/agents/TradingAgents`.

## API Key Rule

Default to DeepSeek. The script reads API keys in this order:

1. Existing environment variable `DEEPSEEK_API_KEY`.
2. `TRADING_AGENTS_DEEPSEEK_API_KEY` from `~/.env`, then maps it to `DEEPSEEK_API_KEY`.
3. TradingAgents project `.env` as a secondary fallback.

Do not print API key values. Only report whether a key is present.

## Quick Start

Run a simple DeepSeek fundamentals-only report:

```bash
cd /home/bdwillwin/agents/TradingAgents
uv run python /home/bdwillwin/.codex/skills/tradingagents-runner/scripts/run_tradingagents.py --ticker INTC --analysts fundamentals --depth shallow --language Chinese
```

Run a broader analysis with fundamentals, technical/market, and news:

```bash
cd /home/bdwillwin/agents/TradingAgents
uv run python /home/bdwillwin/.codex/skills/tradingagents-runner/scripts/run_tradingagents.py --ticker NVDA --analysts fundamentals,market,news --depth deep --language Chinese
```

Use `bash -ic` only when the user explicitly wants to reload interactive shell exports from `~/.bashrc`.

## Parameters

- `--ticker`: Required ticker, e.g. `INTC`, `AAPL`, `601600.SS`.
- `--date`: Trade date. Defaults to today.
- `--provider`: LLM provider. Defaults to `deepseek`.
- `--depth`: `shallow`, `standard`, or `deep`.
- `--analysts`: Comma-separated analyst set. Valid values: `fundamentals`, `market`, `news`, `social`. `technical` is accepted as an alias for `market`.
- `--deep-model`: Override deep thinker model.
- `--quick-model`: Override quick thinker model.
- `--language`: Output language passed to TradingAgents, e.g. `Chinese` or `English`.
- `--results-dir`: Directory for TradingAgents JSON state logs. Defaults to project `reports`.
- `--summary-file`: Markdown file path for a compact extracted report. Defaults to a timestamped file under `reports/skill_runs/`.
- `--checkpoint`: Enable LangGraph checkpoint/resume.
- `--debug`: Print LangGraph intermediate messages.
- `--json`: Print compact JSON to stdout.
- `--check-env`: Check API key loading and exit without running analysis.

Depth behavior:

- `shallow`: one debate round and one risk round; uses `deepseek-chat` for both quick and deep models unless overridden.
- `standard`: one debate round and one risk round; same as shallow unless models are overridden.
- `deep`: two debate rounds and two risk rounds; uses `deepseek-reasoner` for deep and `deepseek-chat` for quick unless overridden.

## Workflow

1. Confirm the TradingAgents project path exists.
2. Confirm a DeepSeek key is available without printing its value.
3. Use the bundled script for non-interactive runs.
4. Summarize `final_trade_decision`, `signal`, and the selected analyst reports from the generated Markdown summary.
5. Mention that output is research only, not financial advice, when giving trading conclusions.

## Troubleshooting

- If `DEEPSEEK_API_KEY` is missing, check whether `~/.env` contains `TRADING_AGENTS_DEEPSEEK_API_KEY=***
- If `uv run` downloads dependencies on first use, let it finish.
- If a full graph is slow, reduce analysts to `fundamentals` or use `--depth shallow`.
- If the user only wants CLI exploration, use `uv run tradingagents --help` or `uv run python -m cli.main --help`.
