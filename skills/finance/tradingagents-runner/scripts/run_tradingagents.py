#!/usr/bin/env python3
"""Run TradingAgents non-interactively with configurable analysis settings."""

from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import date, datetime
from pathlib import Path
from typing import Iterable


DEFAULT_PROJECT = Path("/home/bdwillwin/agents/TradingAgents")
VALID_ANALYSTS = {"market", "social", "news", "fundamentals"}
ANALYST_ALIASES = {
    "technical": "market",
    "technicals": "market",
    "tech": "market",
    "sentiment": "social",
    "social_media": "social",
    "fundamental": "fundamentals",
    "financials": "fundamentals",
}

PROVIDER_MODELS = {
    "deepseek": {"quick": "deepseek-chat", "deep": "deepseek-reasoner"},
    "openai": {"quick": "gpt-5.4-mini", "deep": "gpt-5.4"},
    "google": {"quick": "gemini-2.5-flash", "deep": "gemini-2.5-flash"},
    "anthropic": {"quick": "claude-sonnet-4-6", "deep": "claude-sonnet-4-6"},
    "xai": {"quick": "grok-4", "deep": "grok-4"},
    "qwen": {"quick": "qwen-plus", "deep": "qwen-plus"},
    "glm": {"quick": "glm-5", "deep": "glm-5"},
    "openrouter": {"quick": "openai/gpt-5.4-mini", "deep": "openai/gpt-5.4"},
    "ollama": {"quick": "llama3.1", "deep": "llama3.1"},
    "azure": {"quick": "gpt-5.4-mini", "deep": "gpt-5.4"},
}

PROVIDER_KEYS = {
    "deepseek": "DEEPSEEK_API_KEY",
    "openai": "OPENAI_API_KEY",
    "google": "GOOGLE_API_KEY",
    "anthropic": "ANTHROPIC_API_KEY",
    "xai": "XAI_API_KEY",
    "qwen": "DASHSCOPE_API_KEY",
    "glm": "ZHIPU_API_KEY",
    "openrouter": "OPENROUTER_API_KEY",
    "azure": "AZURE_OPENAI_API_KEY",
}


def parse_analysts(raw: str) -> list[str]:
    analysts: list[str] = []
    for item in raw.split(","):
        key = item.strip().lower().replace("-", "_")
        if not key:
            continue
        key = ANALYST_ALIASES.get(key, key)
        if key not in VALID_ANALYSTS:
            valid = sorted(VALID_ANALYSTS | set(ANALYST_ALIASES))
            raise argparse.ArgumentTypeError(
                f"unknown analyst {item!r}; valid: {', '.join(valid)}"
            )
        if key not in analysts:
            analysts.append(key)
    if not analysts:
        raise argparse.ArgumentTypeError("at least one analyst is required")
    return analysts


def parse_env_file(path: Path) -> dict[str, str]:
    values: dict[str, str] = {}
    if not path.exists():
        return values
    for line in path.read_text(encoding="utf-8").splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or "=" not in stripped:
            continue
        key, value = stripped.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            values[key] = value
    return values


def load_env(project_dir: Path) -> None:
    home_env = parse_env_file(Path.home() / ".env")
    if not os.getenv("DEEPSEEK_API_KEY") and home_env.get("TRADING_AGENTS_DEEPSEEK_API_KEY"):
        os.environ["DEEPSEEK_API_KEY"] = home_env["TRADING_AGENTS_DEEPSEEK_API_KEY"]

    try:
        from dotenv import load_dotenv
    except Exception:
        return
    load_dotenv(project_dir / ".env", override=False)
    load_dotenv(project_dir / ".env.enterprise", override=False)


def choose_models(provider: str, depth: str, deep_model: str | None, quick_model: str | None) -> tuple[str, str]:
    defaults = PROVIDER_MODELS.get(provider, PROVIDER_MODELS["deepseek"])
    quick = quick_model or defaults["quick"]
    if deep_model:
        deep = deep_model
    elif depth == "deep":
        deep = defaults["deep"]
    else:
        deep = quick
    return deep, quick


def compact_state(state: dict[str, object]) -> dict[str, object]:
    keep = [
        "company_of_interest",
        "trade_date",
        "market_report",
        "sentiment_report",
        "news_report",
        "fundamentals_report",
        "investment_plan",
        "trader_investment_plan",
        "final_trade_decision",
    ]
    return {key: state.get(key, "") for key in keep}


def write_summary(path: Path, payload: dict[str, object]) -> None:
    state = payload["state"]
    assert isinstance(state, dict)
    sections: list[tuple[str, str]] = [
        ("Run", json.dumps(payload["run"], indent=2, ensure_ascii=False)),
        ("Signal", str(payload["signal"])),
    ]
    for key, title in [
        ("fundamentals_report", "Fundamentals Report"),
        ("market_report", "Market / Technical Report"),
        ("news_report", "News Report"),
        ("sentiment_report", "Social Sentiment Report"),
        ("investment_plan", "Research Manager Plan"),
        ("trader_investment_plan", "Trader Plan"),
        ("final_trade_decision", "Final Trade Decision"),
    ]:
        value = state.get(key)
        if value:
            sections.append((title, str(value)))

    body = ["# TradingAgents Skill Run\n"]
    for title, content in sections:
        body.append(f"## {title}\n\n{content.strip()}\n")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("\n".join(body), encoding="utf-8")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-dir", default=str(DEFAULT_PROJECT), help="TradingAgents source directory")
    parser.add_argument("--ticker", required=True, help="Ticker to analyze, e.g. INTC")
    parser.add_argument("--date", default=date.today().isoformat(), help="Trade date, YYYY-MM-DD")
    parser.add_argument("--provider", default="deepseek", help="LLM provider; defaults to deepseek")
    parser.add_argument("--depth", choices=["shallow", "standard", "deep"], default="shallow")
    parser.add_argument("--analysts", type=parse_analysts, default=parse_analysts("fundamentals"))
    parser.add_argument("--deep-model", default=None)
    parser.add_argument("--quick-model", default=None)
    parser.add_argument("--language", default="Chinese")
    parser.add_argument("--results-dir", default="reports")
    parser.add_argument("--summary-file", default=None)
    parser.add_argument("--checkpoint", action="store_true")
    parser.add_argument("--debug", action="store_true")
    parser.add_argument("--json", action="store_true", help="Print compact JSON to stdout")
    parser.add_argument("--check-env", action="store_true", help="Check provider API key loading and exit")
    return parser


def main(argv: Iterable[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    project_dir = Path(args.project_dir).expanduser().resolve()
    if not project_dir.exists():
        raise SystemExit(f"TradingAgents project directory not found: {project_dir}")

    sys.path.insert(0, str(project_dir))
    os.chdir(project_dir)
    load_env(project_dir)

    provider = args.provider.lower()
    env_key = PROVIDER_KEYS.get(provider)
    if env_key and not os.getenv(env_key):
        print(f"warning: {env_key} is not set; provider authentication may fail", file=sys.stderr)
    elif env_key:
        print(f"{env_key} is set", file=sys.stderr)

    if args.check_env:
        return 0 if not env_key or os.getenv(env_key) else 1

    from tradingagents.default_config import DEFAULT_CONFIG
    from tradingagents.graph.trading_graph import TradingAgentsGraph

    deep_model, quick_model = choose_models(provider, args.depth, args.deep_model, args.quick_model)
    rounds = 2 if args.depth == "deep" else 1

    config = DEFAULT_CONFIG.copy()
    config["llm_provider"] = provider
    config["deep_think_llm"] = deep_model
    config["quick_think_llm"] = quick_model
    config["max_debate_rounds"] = rounds
    config["max_risk_discuss_rounds"] = rounds
    config["output_language"] = args.language
    config["checkpoint_enabled"] = bool(args.checkpoint)
    config["results_dir"] = str((project_dir / args.results_dir).resolve())

    print(
        f"Running TradingAgents: ticker={args.ticker}, date={args.date}, provider={provider}, "
        f"depth={args.depth}, analysts={','.join(args.analysts)}, deep={deep_model}, quick={quick_model}",
        file=sys.stderr,
    )

    graph = TradingAgentsGraph(debug=args.debug, config=config, selected_analysts=args.analysts)
    state, signal = graph.propagate(args.ticker, args.date)
    payload = {
        "run": {
            "ticker": args.ticker,
            "date": args.date,
            "provider": provider,
            "depth": args.depth,
            "analysts": args.analysts,
            "deep_model": deep_model,
            "quick_model": quick_model,
            "language": args.language,
            "generated_at": datetime.now().isoformat(timespec="seconds"),
        },
        "signal": signal,
        "state": compact_state(state),
    }

    if args.summary_file:
        summary_path = Path(args.summary_file).expanduser()
    else:
        stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        summary_path = project_dir / "reports" / "skill_runs" / f"{args.ticker}_{args.date}_{stamp}.md"
    write_summary(summary_path, payload)

    if args.json:
        print(json.dumps({**payload, "summary_file": str(summary_path)}, indent=2, ensure_ascii=False))
    else:
        print(f"Summary file: {summary_path}")
        print(f"Signal: {signal}")
        final_decision = payload["state"].get("final_trade_decision", "")
        if final_decision:
            print("\n=== Final Trade Decision ===\n")
            print(final_decision)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())