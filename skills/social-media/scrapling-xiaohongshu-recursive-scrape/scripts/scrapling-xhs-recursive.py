import random
import hashlib
import os
from scrapling.fetchers import StealthyFetcher
from scrapling.parser import Selector

MAX_DEPTH = 5
BASE_URL = "https://www.xiaohongshu.com"

# 从文件中提取已有的链接
def extract_links_from_html(html):
    selector = Selector(html)
    links = []
    for a in selector.css(".note-item a.cover"):
        href = a.attrib.get('href', '')
        if href.startswith('/explore/') or href.startswith('/note/'):
            full_url = f"{BASE_URL}{href}"
            links.append(full_url)
    # 去重
    return list(set(links))

# 保存页面内容
def save_page(url, content, depth):
    url_hash = hashlib.md5(url.encode()).hexdigest()
    filename = f"xhs-depth-{depth}-{url_hash}.html"
    with open(filename, 'w', encoding='utf-8') as f:
        f.write(str(content))
    print(f"Saved: {filename} -> {url}")
    return filename

# 递归爬取函数
def recursive_scrape(url, current_depth=0, visited=None):
    if visited is None:
        visited = set()
    
    if current_depth >= MAX_DEPTH or url in visited:
        return
    
    visited.add(url)
    print(f"[{current_depth}] Scraping: {url}")
    
    try:
        # 使用scrapling获取页面
        page = StealthyFetcher.fetch(url, solve_cloudflare=True, remote_debugging_port=9222, wait_until="networkidle")
        if not page:
            print(f"Failed to fetch: {url}")
            return
        
        # 保存页面
        save_page(url, page.text, current_depth)
        print(f"Page length: {len(page.text)}")
        
        # 提取子链接
        if current_depth < MAX_DEPTH -1:
            sub_links = extract_links_from_html(page.text)
            if sub_links:
                # 随机选择一个子链接
                next_url = random.choice(sub_links)
                print(f"Found {len(sub_links)} links, choosing random: {next_url}")
                recursive_scrape(next_url, current_depth +1, visited)
            else:
                print(f"No sub links found at: {url}")
    except Exception as e:
        print(f"Error scraping {url}: {e}")

if __name__ == "__main__":
    # 先从已有的temp.html提取初始链接
    import sys
    import os
    script_dir = os.path.dirname(os.path.abspath(__file__))
    temp_html_path = os.path.join(script_dir, "temp.html")
    
    with open(temp_html_path, 'r', encoding='utf-8') as f:
        html = f.read()
    
    initial_links = extract_links_from_html(html)
    if not initial_links:
        print("No initial links found!")
        exit(1)
    
    print(f"Found {len(initial_links)} initial links")
    # 随机选择一个初始链接
    start_url = random.choice(initial_links)
    print(f"Starting with random link: {start_url}")
    
    recursive_scrape(start_url)
    print("\nRecursive scrape completed!")