---
name: scrapling-xiaohongshu-scraping
description: Xiaohongshu (小红书) scraping using Scrapling with anti-bot bypass and login session support.
version: "1.0.0"
license: MIT
metadata:
  homepage: "https://github.com/D4Vinci/Scrapling"
  tags: ["xiaohongshu", "scraping", "scrapling", "china-social"]
---

# Scrapling Xiaohongshu Scraping Skill

This skill provides proven workflows for scraping Xiaohongshu (小红书) using the Scrapling framework, including fixes for common anti-bot restrictions and login requirements.

## Common Issues & Fixes

1.  **IP Restriction Blocks**
   Xiaohongshu quickly flags non-residential IPs with "安全限制 IP存在风险" errors.
   - Fix: Use residential proxies or attach to a pre-authenticated Chrome session via remote debugging.

2.  **Login Wall**
   Even with stealthy-fetch, you must be logged in to view full post content.
   - Fix: Launch Chrome with remote debugging enabled first:
     ```bash
     google-chrome --remote-debugging-port=9222 --user-data-dir="~/.chrome/xhs-session"
     ```
   - Then log into Xiaohongshu manually in the browser window that opens.

3.  **Correct CSS Selectors**
   Use these selectors to extract common content:
   - Post cover links: `.note-item a.cover`
   - Post title links: `.note-item .title a`
   - Author profiles: `.note-item .author-wrapper .author`
   - Post likes counts: `.note-item .like-wrapper .count`

4.  **Wait for Dynamic Content**
   Always wait for network idle or specific elements to load before scraping:
   - CLI: Add `--network-idle` or `--wait-selector ".note-item"`
   - Python API: Use `wait_until="networkidle"` or `wait_selector=".note-item"`

5.  **Avoid Headless Mode**
   Headless Chrome triggers stricter bot detection. Use visible browser mode or remote debugging instead.

## Quick Start Examples

### CLI Scraping
```bash
# Attach to pre-authenticated Chrome session and scrape Xiaohongshu explore page
scrapling extract stealthy-fetch "https://www.xiaohongshu.com/explore" xhs-explore.html \
  --remote-debugging-port=9222 \
  --network-idle \
  --ai-targeted

# Extract only post titles and links
scrapling extract stealthy-fetch "https://www.xiaohongshu.com/explore" xhs-titles.txt \
  --remote-debugging-port=9222 \
  --network-idle \
  --css-selector ".note-item .title a"
```

### Python Code Scraping
```python
from scrapling.fetchers import StealthyFetcher
from scrapling.parser import Selector

def scrape_xiaohongshu_explore():
    # Attach to pre-authenticated Chrome session
    page = StealthyFetcher.fetch(
        "https://www.xiaohongshu.com/explore",
        remote_debugging_port=9222,
        wait_until="networkidle",
        solve_cloudflare=True
    )
    
    # Extract post data
    selector = Selector(page.text)
    posts = []
    for item in selector.css(".note-item"):
        title = item.css(".title a::text").get()
        link = f"https://www.xiaohongshu.com{item.css(".title a::attr(href)").get()}"
        author = item.css(".author .name::text").get()
        likes = item.css(".like-wrapper .count::text").get()
        
        posts.append({
            "title": title,
            "link": link,
            "author": author,
            "likes": likes
        })
    
    return posts
```

## Important Notes
- Respect Xiaohongshu's Terms of Service and robots.txt
- Add delays between requests for large crawls to avoid IP bans
- Use residential proxies for large-scale scraping operations
- Always clean up temporary files after scraping
