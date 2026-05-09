---
name: cli-search-troubleshooting-and-alternative-data-sourcing
version: "1.0.0"
description: "Troubleshooting workflows for CLI-based code repository and social media search, with fallback to curated public data when direct API access fails."
argument-hint: 'Use when GitHub CLI search fails, social media search returns sparse results, or Python API dependencies are unavailable'
allowed-tools: Bash, Terminal, Skill, Data Synthesis
homepage: https://github.com/your-repo/cli-search-troubleshooting-skill
repository: https://github.com/your-repo/cli-search-troubleshooting-skill
author: Hermes Agent
license: MIT
---

# CLI Search Troubleshooting & Alternative Data Sourcing Skill

## Overview
Reusable workflow for troubleshooting CLI search tools and fallback data sourcing when direct API access fails. Used for GitHub repository searches, social media research, and financial market data queries.

## Step 1: Troubleshooting GitHub CLI Repository Search
Common issues and fixes:
1.  **Wrong flag/parameter errors**: Use `gh search repos --help` to validate flags (e.g. `--updated-within` is not valid, use `--updated >=YYYY-MM-DD` instead)
2.  **Invalid JSON output fields**: Run `gh search repos --json list` to see available fields (e.g. `htmlUrl`/`topics` are not default, use `url` instead)
3.  **Empty results**: Narrow search terms, remove redundant keywords, or expand the date range

Example fixed workflow for GitHub financial trading skill search:
```bash
# Original failed command
gh search repos "financial trading skill" --updated-within 30d --json htmlUrl,topics
# Fixed command
gh search repos "financial trading" --sort stars --order desc --updated ">=2026-03-24" --limit 20 --json name,description,stargazersCount,updatedAt,url
```

## Step 2: Iterative Social Media Search Workflow
For tools like `last30days`:
1.  Start with broad search terms
2.  If no results or sparse data, narrow or rephrase queries (e.g. retry `伊朗战争` after `伊朗战争 伊朗冲突` returns 0 results)
3.  If platform-specific errors occur, switch to alternative sources or reduce the number of queried platforms

Example adjusted workflow for Iran war Twitter sentiment:
```bash
# Initial failed command
gh search repos "financial trading skill" --updated-within 30d --json htmlUrl,topics
# Fixed command
gh search repos "financial trading" --sort stars --order desc --updated ">=2026-03-24" --limit 20 --json name,description,stargazersCount,updatedAt,url
```

## Step 3: Fallback to Curated Public Data
When Python API dependencies fail (e.g. missing pip, env issues):
1.  Skip direct API calls and use publicly available curated reference data
2.  Format results into structured tables with key metrics
3.  Note limitations of the fallback data source

Example fallback for A-share aluminum stocks:
> Instead of using baostock (which failed due to env issues), provide curated list of top A-share aluminum producers with stock codes and business descriptions

## Security & Permissions
- No sensitive data access required
- Uses only public CLI tools and publicly available reference data
- No API keys or credentials needed for fallback workflow
