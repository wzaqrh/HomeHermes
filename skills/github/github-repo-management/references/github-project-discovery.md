# GitHub Project Discovery & Cataloging Workflow

**When to use**: User asks to "find GitHub projects about X", "research what's available for Y", "look for GPU implementations of Z".

Generates a structured, categorized markdown report from GitHub search results.

---

## Workflow

### Phase 1: Broad Search with `gh search repos`

```bash
# Start with the most direct keyword
gh search repos "gpu xpbd" --limit 20 --json name,owner,description,url,stargazersCount,language,updatedAt

# Broaden if results are sparse
gh search repos "xpbd" --limit 30 --json name,owner,description,url,stargazersCount,language,updatedAt

# Then drill into specific categories
gh search repos "cloth simulation gpu" --limit 20 --json name,owner,description,url,stargazersCount,language,updatedAt
gh search repos "cloth simulation cuda" --limit 20 ...
gh search repos "cloth simulation pbd" --limit 20 ...
```

Tip: `gh search repos` is the quickest first pass. For each query, capture the full JSON output rather than the summary view — you need the URLs later.

### Phase 2: Enrich with Python + GitHub API

For detailed info (topics, license), `gh repo view` is inconsistent. Use a Python script:

```python
import urllib.request, json, sys

repos = {
    "owner/repo-name": "Category description for this repo",
    # Add all unique repos from Phase 1
}

for repo, note in repos.items():
    url = f"https://api.github.com/repos/{repo}"
    req = urllib.request.Request(url, headers={"User-Agent": "curl/1.0"})
    with urllib.request.urlopen(req, timeout=10) as resp:
        d = json.loads(resp.read())
    stars = d.get("stargazers_count", "?")
    lang = d.get("language", "?")
    updated = (d.get("updated_at") or "?")[:10]
    desc = (d.get("description") or "").strip()
    topics = d.get("topics", [])
    license_ = d.get("license", {})
    lic = license_.get("spdx_id", "") if license_ else ""
    
    print(f"{repo}  |  {stars} stars  |  {lang}")
    print(f"  Desc: {desc}")
    print(f"  Category: {note}")
    if topics: print(f"  Topics: {', '.join(topics)}")
    if lic: print(f"  License: {lic}")
    print(f"  URL: https://github.com/{repo}")
    print(f"  Updated: {updated}")
    print()
```

**Why a script file instead of inline**: Inline Python with escaped quotes (e.g. `print(f\"{d.get(\\\"key\\\")}\")`) causes shell escaping errors. Write a proper `.py` file with `skill_manage action=write_file` or `write_file` tool, then run it via `terminal`.

For multi-query search with dedup, use `/search/repositories` API:

```python
import urllib.request, urllib.parse, json

def search_gh(query, sort="stars", order="desc", per_page=20):
    q = urllib.parse.quote(query)
    url = f"https://api.github.com/search/repositories?q={q}&sort={sort}&order={order}&per_page={per_page}"
    req = urllib.request.Request(url, headers={"User-Agent": "curl/2.0"})
    with urllib.request.urlopen(req, timeout=15) as resp:
        return json.loads(resp.read())

results = {}
seen = set()

queries = [
    ("keyword1 another", "Category A"),
    ("keyword2 another", "Category B"),
]

for query, note in queries:
    data = search_gh(query)
    for item in data.get("items", []):
        fn = item["full_name"]
        if fn not in seen:
            seen.add(fn)
            results[fn] = {
                "stars": item["stargazers_count"],
                "lang": item.get("language") or "",
                "desc": (item.get("description") or "").strip(),
                "url": item["html_url"],
                "note": note
            }

sorted_results = sorted(results.items(), key=lambda x: -x[1]["stars"])
```

### Phase 3: Categorize and Report

**Organize by technology route** (not flat list):

| Route | Why this category | 
|-------|-------------------|
| CUDA / GPU Compute | For performant cross-platform |
| WebGPU | For in-browser GPU access |
| Unity Compute Shader | For game engine integration |
| Taichi Lang | For Python GPU prototyping |
| PBD / XPBD pure | For teaching and research |

**Write to a markdown file** with sections:

```
# Topic Name - GitHub Project Catalog

## Overview
Brief summary of findings, total projects found, date.

## By Technology Route

### CUDA Route (N repos)
Highest-impact GPU-accelerated projects.

### WebGPU Route (N repos)
Browser-based GPU implementations.

### ... etc

## Ranked by Stars

| Project | Stars | Language | Route | Description |
|---------|-------|----------|-------|-------------|
| owner/repo | N | Lang | CUDA | Short description |

## Key Insights
- What trends emerge
- Which areas are crowded vs underserved
- Any standout projects worth deeper look
```

### Phase 4: Save to `~/reports/`

```
~/reports/github-<topic>-projects.md
```

---

## Pitfalls

- **Shell escaping**: Never write complex Python in `-c` inline strings with escaped quotes. Always write a `.py` file first.
- **`gh repo view` fails silently**: Some repos return empty output from `gh repo view`. Use the REST API instead via Python for reliability.
- **Rate limits**: GitHub API allows 5,000 req/hr. Each `search/` endpoint call returns up to 20-30 items — batch queries to minimize calls.
- **Deduplication**: Multiple search queries (e.g. "cloth simulation gpu" + "xpbd cloth simulation") will overlap. Track `seen` set.
- **No auth needed for public data**: You can query `api.github.com` without `GITHUB_TOKEN` for public repos, but rate limit drops to 60 req/hr. Better to use the env token if available.
- **Security blocks**: `curl ... | python3 -c` pipes may trigger security warnings. Use `write_file` + `terminal` instead.
