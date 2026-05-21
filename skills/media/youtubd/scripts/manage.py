#!/usr/bin/env python3
"""
youtubd 订阅管理脚本（新结构）
==============================
数据文件：
  subscribe.json  — 分类 → channel_id → {name, url, added, weight}
  history.json    — video_id → {title, url, ...}
  todolist.txt    — 未处理视频URL列表（一行一个）

命令：
  list                         列出所有本地订阅频道
  subscribe <分类> <频道名>    添加本地订阅（权重默认3）
  weight <频道名/ID> <1-5>     设置权重
  unsubscribe <频道名/ID>      取消本地订阅
  fetch [分类]                 拉取频道最新视频
  new [分类]                   列出未处理的视频
  mark <视频ID>                标记为已处理
  stats                        统计概览
  loadlist [文件路径]          从txt文件导入
  gethistory [数量]            拉取 YouTube 观看历史（需 Chrome）
"""

import json, subprocess, sys, os, re, urllib.request, urllib.error
from datetime import date, datetime, timedelta
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SUB_PATH = SKILL_DIR / "subscribe.json"
HIST_PATH = SKILL_DIR / "history.json"
TODO_PATH = SKILL_DIR / "todolist.txt"
MCP_URL = "http://127.0.0.1:12306/mcp"
YOUTUBE_HISTORY_URL = "https://www.youtube.com/feed/history"


def load_sub():
    return json.load(open(SUB_PATH)) if SUB_PATH.exists() else {}


def save_sub(sub):
    json.dump(sub, open(SUB_PATH, "w"), indent=2, ensure_ascii=False)


def load_hist():
    return json.load(open(HIST_PATH)) if HIST_PATH.exists() else {}


def save_hist(hist):
    json.dump(hist, open(HIST_PATH, "w"), indent=2, ensure_ascii=False)


def todo_append(new_lines):
    """追加新行到 todolist（去重）"""
    existing = set()
    if TODO_PATH.exists():
        with open(TODO_PATH) as f:
            old = [l.strip() for l in f if l.strip()]
            for l in old:
                vid = extract_vid(l)
                if vid: existing.add(vid)
        keep = [l for l in old if extract_vid(l) not in {extract_vid(nl) for nl in new_lines if extract_vid(nl)}]
        keep.extend(new_lines)
    else:
        keep = new_lines
    open(TODO_PATH, "w").write("\n".join(keep) + ("\n" if keep else ""))


def todo_remove(video_id):
    """从 todolist 中删除指定 video_id 的整行"""
    if not TODO_PATH.exists(): return
    with open(TODO_PATH) as f:
        lines = [l for l in f if extract_vid(l.strip()) != video_id]
    open(TODO_PATH, "w").write("".join(lines))


# ─── 工具函数 ─────────────────────────────────

def get_channel_id(query):
    r = subprocess.run(
        ["yt-dlp", f"ytsearch1:{query}", "--flat-playlist", "--dump-json"],
        capture_output=True, text=True, timeout=30)
    if not r.stdout.strip():
        return None, None
    raw = json.loads(r.stdout.strip().split("\n")[0])
    return raw.get("channel_id"), raw.get("channel", query)


def fetch_channel_videos(channel_id, limit=20):
    pid = "UU" + channel_id[2:]
    r = subprocess.run(
        ["yt-dlp", f"https://www.youtube.com/playlist?list={pid}",
         "--flat-playlist", "--dump-json"],
        capture_output=True, text=True, timeout=60)
    videos = []
    for line in r.stdout.strip().split("\n"):
        if not line.strip(): continue
        raw = json.loads(line)
        v = {"id": raw["id"], "title": raw.get("title", ""),
             "url": f"https://www.youtube.com/watch?v={raw['id']}",
             "channel_name": raw.get("channel", ""), "channel_id": channel_id,
             "duration": raw.get("duration", 0), "view_count": raw.get("view_count", 0),
             "upload_date": raw.get("upload_date", "")}
        videos.append(v)
        if len(videos) >= limit: break
    return videos


def extract_vid(text):
    text = text.strip()
    m = re.search(r'(?:v=|youtu\.be/|shorts/|embed/|live/|watch\?v=)([a-zA-Z0-9_-]{11})', text)
    if m: return m.group(1)
    if re.match(r'^[a-zA-Z0-9_-]{11}$', text): return text
    return None


def get_video_meta(video_id):
    try:
        r = subprocess.run(
            ["yt-dlp", "--dump-json", f"https://www.youtube.com/watch?v={video_id}"],
            capture_output=True, text=True, timeout=30)
        raw = json.loads(r.stdout.strip())
        return {"id": raw["id"], "title": raw.get("title", ""),
                "url": f"https://www.youtube.com/watch?v={raw['id']}",
                "channel_name": raw.get("channel", ""),
                "channel_id": raw.get("channel_id", ""),
                "duration": raw.get("duration", 0),
                "view_count": raw.get("view_count", 0),
                "upload_date": raw.get("upload_date", "")}
    except: return None


# ─── 强制覆盖模式 ─────────────────────────

def kill_previous_flush():
    """杀掉之前启动的 flush/cron 进程（新启动的覆盖旧的）"""
    import signal as _sig
    my_pid = str(os.getpid())
    script = os.path.abspath(__file__)
    r = subprocess.run(
        ["pgrep", "-f", rf"python3.*{script}.*(flush|cron|gethistory)"],
        capture_output=True, text=True, timeout=10
    )
    for pid_str in r.stdout.strip().split("\n"):
        pid = pid_str.strip()
        if pid and pid != my_pid:
            try:
                os.kill(int(pid), _sig.SIGTERM)
                print(f"  🧹 已干掉旧进程 PID={pid}")
            except (ProcessLookupError, ValueError):
                pass


# ─── MCP bridge 通信 ─────────────────────────

def _mcp_connect():
    """连接 MCP bridge，返回 session ID"""
    body = json.dumps({
        "jsonrpc": "2.0", "id": 1, "method": "initialize",
        "params": {
            "protocolVersion": "2024-11-05",
            "capabilities": {},
            "clientInfo": {"name": "youtubd", "version": "1.0"}
        }
    }).encode()
    req = urllib.request.Request(
        MCP_URL, data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        sid = dict(resp.getheaders()).get('mcp-session-id', '')
        resp.read()
    return sid


def _mcp_call(sid, method, params):
    """调用 MCP tool，返回结果"""
    body = json.dumps({
        "jsonrpc": "2.0", "id": 2, "method": "tools/call",
        "params": {"name": method, "arguments": params}
    }).encode()
    req = urllib.request.Request(
        MCP_URL, data=body,
        headers={
            "Content-Type": "application/json",
            "Accept": "application/json, text/event-stream",
            "mcp-session-id": sid
        }
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        raw = resp.read().decode()
    # 解析 SSE 格式响应
    for line in raw.split("\n"):
        line = line.strip()
        if line.startswith("data: "):
            return json.loads(line[6:])
    return None


def _mcp_find_history_tab(sid):
    """在 Chrome 中查找或打开 YouTube 历史页面"""
    # 先查现有标签
    result = _mcp_call(sid, "chrome_get_windows_and_tabs", {})
    if result:
        try:
            text = result.get("result", {}).get("content", [{}])[0].get("text", "{}")
            data = json.loads(text)
            # MCP bridge 返回嵌套的 result
            inner = data.get("result", data)
            windows = inner.get("windows", [inner] if "tabs" in inner else [])
            for win in windows:
                for tab in win.get("tabs", []):
                    url = tab.get("url", "")
                    if "youtube.com/feed/history" in url:
                        print(f"  📺 找到历史页面标签")
                        return tab.get("tabId")
        except: pass
    
    # 新建标签
    print("  📺 新建标签打开历史页面...")
    result = _mcp_call(sid, "chrome_navigate", {"url": YOUTUBE_HISTORY_URL})
    if result:
        try:
            text = result.get("result", {}).get("content", [{}])[0].get("text", "{}")
            data = json.loads(text)
            inner = data.get("result", data)
            return inner.get("tabId")
        except: pass
    return None


def _mcp_run_js(sid, tab_id, js_code):
    """在浏览器标签中执行 JavaScript"""
    result = _mcp_call(sid, "chrome_javascript", {
        "tabId": tab_id, "code": js_code, "timeoutMs": 60000
    })
    if not result:
        return None
    try:
        text = result.get("result", {}).get("content", [{}])[0].get("text", "{}")
        data = json.loads(text)
        inner = json.loads(data.get("result", "{}"))
        return inner
    except:
        return None


def _fetch_videos_via_browser(sid, tab_id, limit=100):
    """通过浏览器端 JavaScript 同步提取观看记录"""
    
    # 同步 JS — 只读 ytInitialData + 不用 async/await
    js_code = (
        "var allVideos=[];"
        "var token=null;"
        "var ytid=window.ytInitialData;"
        "if(ytid){"
        "  var sections=ytid.contents?.twoColumnBrowseResultsRenderer?.tabs?.[0]?.tabRenderer?.content?.sectionListRenderer?.contents||[];"
        "  for(var i=0;i<sections.length;i++){"
        "    var sec=sections[i];"
        "    if(sec.itemSectionRenderer){"
        "      for(var j=0;j<sec.itemSectionRenderer.contents.length;j++){"
        "        var item=sec.itemSectionRenderer.contents[j];"
        "        if(item.videoRenderer){"
        "          var v=item.videoRenderer;"
        "          allVideos.push({id:v.videoId, title:(v.title?.runs?.[0]?.text||''), channel:(v.longBylineText?.runs?.[0]?.text||''), channelId:(v.longBylineText?.runs?.[0]?.navigationEndpoint?.browseEndpoint?.browseId||'')});"
        "        }else if(item.messageRenderer){"
        "          return JSON.stringify({error:'not_logged_in', message:(item.messageRenderer.text?.runs?.[0]?.text||'')});"
        "        }"
        "      }"
        "    }else if(sec.continuationItemRenderer){"
        "      token=sec.continuationItemRenderer.continuationEndpoint?.continuationCommand?.token;"
        "    }"
        "  }"
        "}"
        "return JSON.stringify({total:allVideos.length, videos:allVideos.slice(0," + str(limit) + "), hasToken:!!token});"
    )
    
    return _mcp_run_js(sid, tab_id, js_code)


# ─── 命令实现 ─────────────────────────────────

def cmd_list():
    sub = load_sub()
    hist = load_hist()
    if not sub:
        print("没有订阅。用 subscribe 添加。")
        return
    for cat, chs in sub.items():
        if not chs: continue
        print(f"\n📂 [{cat}]")
        for cid, info in chs.items():
            n = sum(1 for v in hist.values() if v.get("channel_id") == cid and not v.get("processed"))
            w = info.get("weight", 3)
            print(f"  ({w}) {info['name']}  ─  {n} 个未处理")


def cmd_subscribe(category, query):
    sub = load_sub()
    if category not in sub: sub[category] = {}
    cid, cname = get_channel_id(query)
    if not cid:
        print(f"找不到频道: {query}")
        return
    if cid in sub[category]:
        print(f"已在[{category}]中: {cname}")
        return
    sub[category][cid] = {"name": cname, "url": f"https://www.youtube.com/channel/{cid}", "added": str(date.today()), "weight": 3}
    save_sub(sub)
    print(f"已订阅 [{category}] {cname}  (权重=3)")


def cmd_weight(query, w):
    sub = load_sub()
    for cat, chs in sub.items():
        for cid, info in chs.items():
            if query in cid or query.lower() in info["name"].lower():
                info["weight"] = max(1, min(5, w))
                save_sub(sub)
                print(f"已设置 {info['name']} 权重={info['weight']}")
                return
    print(f"没找到: {query}")


def cmd_unsubscribe(query):
    sub = load_sub()
    for cat, chs in list(sub.items()):
        for cid, info in list(chs.items()):
            if query in cid or query.lower() in info["name"].lower():
                del chs[cid]
                if not chs: del sub[cat]
                save_sub(sub)
                print(f"已取消订阅 [{cat}] {info['name']}")
                return
    print(f"没找到: {query}")


def cmd_fetch(category=None):
    sub = load_sub()
    hist = load_hist()
    added = 0
    new_vids = []
    for cat, chs in sub.items():
        if category and cat != category: continue
        for cid, info in chs.items():
            ch_limit = info.get("fetch_limit", 100)
            print(f"  拉取 {info['name']}...")
            try:
                videos = fetch_channel_videos(cid, ch_limit)
            except Exception as e:
                print(f"  失败: {e}")
                continue
            for v in videos:
                if v["id"] not in hist:
                    v["category"] = cat
                    v["fetched_at"] = str(date.today())
                    v["processed"] = False
                    v["note"] = ""
                    hist[v["id"]] = v
                    new_vids.append(v)
                    added += 1
            print(f"    -> {len(videos)} 条, 新增 {added}")
    if added:
        save_hist(hist)
        new_urls = [f"https://www.youtube.com/watch?v={v['id']}" for v in new_vids]
        todo_append(new_urls)
        print(f"\n新增 {added} 个")
    else:
        print("\n没有新视频")


def cmd_new(category=None):
    hist = load_hist()
    pending = [(vid, v) for vid, v in hist.items() if not v.get("processed") and (not category or v.get("category") == category)]
    if not pending:
        print("没有未处理的视频")
        return
    for vid, v in pending:
        m = v["duration"] // 60 if v["duration"] else 0
        print(f"  [{vid}] {v['title'][:50]}")
        print(f"       {v.get('category','?')} | {v['channel_name']} | {m}min")
        print(f"       https://www.youtube.com/watch?v={vid}")


def cmd_mark(video_id):
    hist = load_hist()
    if video_id in hist:
        hist[video_id]["processed"] = True
        save_hist(hist)
        print(f"已标记: {hist[video_id]['title'][:30]}...")
    else:
        print(f"未找到: {video_id}")


def cmd_loadlist(filepath=None):
    hist = load_hist()
    if not filepath: filepath = TODO_PATH
    if not os.path.exists(filepath):
        print(f"文件不存在: {filepath}")
        return
    with open(filepath) as f:
        lines = [l.strip() for l in f if l.strip() and not l.startswith(("#", "="))]

    added_ids = []
    added = skipped = failed = 0
    for line in lines:
        vid = extract_vid(line)
        if not vid: failed += 1; continue
        if vid in hist: skipped += 1; continue
        meta = get_video_meta(vid)
        if not meta: failed += 1; continue
        meta["category"] = "导入"
        meta["fetched_at"] = str(date.today())
        meta["processed"] = False
        meta["note"] = f"来自: {os.path.basename(filepath)}"
        hist[vid] = meta
        added_ids.append(vid)
        added += 1
        print(f"  + [{vid}] {meta['title'][:50]}")
    if added:
        save_hist(hist)
        todo_append([f"https://www.youtube.com/watch?v={vid}" for vid in added_ids])
    print(f"\n新增 {added} | 跳过 {skipped} | 失败 {failed}")


def cmd_cron():
    """定时任务入口：fetch + 按权重随机挑选 N 个写入 todolist"""
    kill_previous_flush()
    import random
    cron = json.load(open(SKILL_DIR / "cron_task.json"))
    sub = load_sub()
    hist = load_hist()
    fetch_count = cron.get("fetch_count", 5)
    up_list = cron.get("up_list", [])

    targets = []
    if up_list:
        for entry in up_list:
            name = entry["name"] if isinstance(entry, dict) else entry
            w = entry.get("weight", 3) if isinstance(entry, dict) else 3
            found = False
            for cat, chs in sub.items():
                for cid, info in chs.items():
                    if name.lower() in info["name"].lower() or name == cid:
                        targets.append((cid, {**info, "weight": w}))
                        found = True
                        break
                if found: break
            if not found:
                print(f"  ⚠️  未订阅: {name}，尝试搜索...")
                cid, cname = get_channel_id(name)
                if cid:
                    targets.append((cid, {"name": cname, "weight": w}))
    else:
        for cat, chs in sub.items():
            for cid, info in chs.items():
                targets.append((cid, info))

    if not targets:
        print("❌ 没有目标频道。先在 subscribe.json 添加订阅，或填写 cron_task.json 的 up_list。")
        return

    new_vids = []
    for cid, info in targets:
        ch_limit = info.get("fetch_limit", 100)
        print(f"  📡 拉取 {info['name']}...")
        try:
            videos = fetch_channel_videos(cid, ch_limit)
        except Exception as e:
            print(f"  ⚠️  失败: {e}")
            continue
        for cat, chs in sub.items():
            if cid in chs:
                for v in videos:
                    if v["id"] not in hist:
                        v["category"] = cat
                        v["fetched_at"] = str(date.today())
                        v["processed"] = False
                        v["note"] = ""
                        hist[v["id"]] = v
                        new_vids.append(v)
                break
        else:
            for v in videos:
                if v["id"] not in hist:
                    v["category"] = "cron"
                    v["fetched_at"] = str(date.today())
                    v["processed"] = False
                    v["note"] = ""
                    hist[v["id"]] = v
                    new_vids.append(v)

    if new_vids:
        save_hist(hist)
        print(f"\n  新增 {len(new_vids)} 个视频")

    pending_items = [(vid, v) for vid, v in hist.items() if not v.get("processed")]
    if not pending_items:
        print("📭 没有未处理的视频")
        open(TODO_PATH, "w").write("")
        return

    pending_vids = [item[0] for item in pending_items]
    pending_data = [item[1] for item in pending_items]
    weights = []
    for vid, v in pending_items:
        w = 3
        cid = v.get("channel_id", "")
        for cat, chs in sub.items():
            if cid in chs:
                w = chs[cid].get("weight", 3)
                break
        override = cron.get("weight_override", {})
        if cid in override:
            w = override[cid]
        weights.append(max(1, min(5, w)))

    pick_n = min(fetch_count, len(pending_items))
    picked_indices = random.choices(range(len(pending_items)), weights=weights, k=pick_n)
    picked = [(pending_vids[i], pending_data[i]) for i in picked_indices]

    lines = [f"https://www.youtube.com/watch?v={vid}" for vid, _ in picked]
    todo_append(lines)
    save_hist(hist)

    print(f"\n🎯 定时任务完成")
    print(f"   抽取 {pick_n}/{len(pending_items)} 个 → todolist.txt")
    for vid, v in picked:
        w = weights[pending_vids.index(vid)]
        m = v["duration"] // 60 if v["duration"] else 0
        print(f"   ({w}) [{vid}] {v['title'][:45]}")
        print(f"         {v.get('category','?')} | {v['channel_name']} | {m}min")


def cmd_flush():
    """全自动串行处理 todolist 所有视频（NotebookLM → brain-vault）

    用法: flush
           flush --todolist playlist1.txt
    """
    kill_previous_flush()
    import subprocess as _sp, time as _time, os as _os

    # 解析 --todolist 参数
    todo_path = TODO_PATH
    args = sys.argv[2:]
    for i, a in enumerate(args):
        if a == '--todolist' and i + 1 < len(args):
            todo_path = Path(os.path.abspath(args[i + 1]))
            break

    if not todo_path.exists() or not todo_path.stat().st_size:
        print(f"📭 {todo_path.name} 为空或不存在")
        return

    with open(todo_path) as f:
        lines = [l.strip() for l in f if l.strip()]

    print(f"📋 待处理: {len(lines)} 个视频")
    print(f"🔧 使用 process_video.py 处理...")
    print()

    script_path = SKILL_DIR.parent / "productivity" / "notebooklm-to-brainvault" / "scripts" / "process_video.py"
    if not script_path.exists():
        script_path = Path.home() / ".hermes" / "skills" / "productivity" / "notebooklm-to-brainvault" / "scripts" / "process_video.py"

    ok = fail = skip = 0

    for i, line in enumerate(lines):
        vid = extract_vid(line)
        if not vid:
            skip += 1
            continue

        url = f"https://www.youtube.com/watch?v={vid}"
        print(f"\n[{i+1}/{len(lines)}] {url}")

        r = _sp.run(
            ["python3", str(script_path), url],
            capture_output=True, text=True, timeout=1800
        )
        print(r.stdout)
        if r.stderr:
            print(f"  ⚠️  stderr: {r.stderr[:200]}")

        if r.returncode == 0:
            ok += 1
            # 标记 history 中已处理
            hist = load_hist()
            if vid in hist:
                hist[vid]["processed"] = True
                hist[vid]["note"] = "已总结 → brain-vault"
                save_hist(hist)
        else:
            fail += 1

    # 清空 todolist
    open(todo_path, "w").write("")
    print(f"\n📊 flush 完成:  ✅ {ok}  |  ❌ {fail}  |  ⏭ {skip}")
    if ok > 0:
        print(f"  文件已清空: {todo_path}")


def cmd_gethistory(limit=100):
    """从 YouTube 拉取观看历史（需 Chrome 运行 + MCP bridge）

    通过 Chrome MCP bridge 连接已登录的浏览器，获取 YouTube 观看记录，
    将新视频加入 history.json 和 todolist.txt。

    用法: gethistory [数量]
           gethistory 50
    默认: 最近 100 个
    """
    # 解析参数
    args = sys.argv[2:]
    if args and args[0].isdigit():
        limit = int(args[0])

    kill_previous_flush()

    print("🔌 正在连接 MCP bridge...")

    # 连接 MCP bridge
    try:
        sid = _mcp_connect()
        if not sid:
            print("❌ MCP bridge 连接失败（无 session ID）")
            return
        print(f"  ✅ 已连接 (session: {sid[:8]}...)")
    except urllib.error.URLError:
        print("❌ 无法连接 MCP bridge (127.0.0.1:12306)")
        print("   请确保 Chrome 正在运行且 MCP bridge 已启动")
        print("   或在 Chrome 中点击扩展的 Connect 按钮")
        return
    except Exception as e:
        print(f"❌ 连接失败: {e}")
        return

    # 查找历史页面 tab
    tab_id = _mcp_find_history_tab(sid)
    if not tab_id:
        print("❌ 无法打开或找到 YouTube 历史页面")
        return
    print(f"  📺 使用标签 ID: {tab_id}")

    # 通过浏览器提取视频
    result = _fetch_videos_via_browser(sid, tab_id, limit)

    if not result:
        print("❌ 未能从浏览器获取数据")
        return

    if "error" in result:
        if result["error"] == "not_logged_in":
            print("❌ YouTube 未登录，请在浏览器中登录 YouTube")
        else:
            print(f"❌ 浏览器返回错误: {result.get('error')}")
            print(f"   {result.get('message', '')}")
        return

    videos = result.get("videos", [])
    total = result.get("total", 0)
    print(f"  🎬 获取到 {total} 个视频")

    if not videos:
        print("📭 没有找到历史记录")
        return

    for v in videos[:5]:
        print(f"    [{v['id']}] {v['title'][:45]}")
    if len(videos) > 5:
        print(f"    ... 还有 {len(videos)-5} 个")

    # 保存到 history.json 和 todolist.txt
    hist = load_hist()
    new_ids = []
    for v in videos:
        vid = v["id"]
        if vid in hist:
            if not hist[vid].get("processed"):
                new_ids.append(vid)
            continue

        meta = get_video_meta(vid)
        if meta:
            meta["category"] = "历史记录"
            meta["fetched_at"] = str(date.today())
            meta["processed"] = False
            meta["note"] = "来自 gethistory"
            hist[vid] = meta
            new_ids.append(vid)
        else:
            hist[vid] = {
                "id": vid,
                "title": v.get("title", ""),
                "url": f"https://www.youtube.com/watch?v={vid}",
                "channel_name": v.get("channel", ""),
                "channel_id": v.get("channelId", ""),
                "category": "历史记录",
                "fetched_at": str(date.today()),
                "processed": False,
                "note": "来自 gethistory（无元数据）"
            }
            new_ids.append(vid)

    if new_ids:
        save_hist(hist)
        lines = [f"https://www.youtube.com/watch?v={vid}" for vid in new_ids]
        todo_append(lines)
        print(f"\n✅ 添加 {len(new_ids)} 个视频到 todolist.txt")
    else:
        print("\n📭 没有新视频（均已存在或已处理）")


def cmd_listplaylists():
    """列出 YouTube 所有播放列表（需 Chrome 运行 + MCP bridge）"""
    print("🔌 正在连接 MCP bridge...")
    try:
        sid = _mcp_connect()
        print(f"  ✅ 已连接 (session: {sid[:8]}...)")
    except Exception as e:
        print(f"❌ MCP bridge 连接失败: {e}")
        return

    # 查找或打开播放列表页面
    tab_id = None
    result = _mcp_call(sid, "chrome_get_windows_and_tabs", {})
    if result:
        try:
            text = result.get("result", {}).get("content", [{}])[0].get("text", "{}")
            data = json.loads(text)
            inner = data.get("result", data)
            windows = inner.get("windows", [inner] if "tabs" in inner else [])
            for win in windows:
                for tab in win.get("tabs", []):
                    if "youtube.com/feed/playlists" in tab.get("url", ""):
                        tab_id = tab.get("tabId")
                        print(f"  📺 找到播放列表页面标签")
                        break
        except: pass

    if not tab_id:
        print("  📺 新建标签打开播放列表页面...")
        result = _mcp_call(sid, "chrome_navigate", {"url": "https://www.youtube.com/feed/playlists"})
        if result:
            try:
                text = result.get("result", {}).get("content", [{}])[0].get("text", "{}")
                data = json.loads(text)
                tab_id = data.get("result", data).get("tabId")
            except: pass

    if not tab_id:
        print("❌ 无法打开播放列表页面")
        return

    import time
    time.sleep(2)

    # 通过 JS 提取播放列表
    js_code = (
        "var ytid=window.ytInitialData;"
        "if(!ytid)return JSON.stringify({error:'no ytInitialData'});"
        "var grid=ytid.contents?.twoColumnBrowseResultsRenderer?.tabs?.[0]?.tabRenderer?.content?.richGridRenderer;"
        "if(!grid)return JSON.stringify({error:'no grid'});"
        "var contents=grid.contents||[];"
        "var items=[];"
        "for(var i=0;i<contents.length;i++){"
        "  var c=contents[i];"
        "  if(!c.richItemRenderer)continue;"
        "  var lvm=c.richItemRenderer.content?.lockupViewModel;"
        "  if(!lvm)continue;"
        "  if(lvm.contentType==='LOCKUP_CONTENT_TYPE_PLAYLIST'){"
        "    var meta=lvm.metadata?.lockupMetadataViewModel||{};"
        "    items.push({id:lvm.contentId, title:(meta.title?.content||''), contentType:lvm.contentType});"
        "  }"
        "}"
        "return JSON.stringify({total:items.length, playlists:items});"
    )

    result = _mcp_call(sid, "chrome_javascript", {
        "tabId": tab_id, "code": js_code, "timeoutMs": 15000
    })
    if not result:
        print("❌ 未能获取播放列表")
        return

    try:
        text = result.get("result", {}).get("content", [{}])[0].get("text", "{}")
        data = json.loads(text)
        inner = json.loads(data.get("result", "{}"))
    except Exception as e:
        print(f"❌ 解析数据失败: {e}")
        return

    if "error" in inner:
        print(f"❌ {inner['error']}")
        return

    playlists = inner.get("playlists", [])
    if not playlists:
        print("📭 没有找到播放列表")
        return

    print(f"\n📋 共 {len(playlists)} 个播放列表:\n")
    for i, pl in enumerate(playlists, 1):
        pid = pl["id"]
        name = pl["title"] or "(未命名)"
        print(f"  {i:2d}. {name}")
        print(f"      ID: {pid}")
        print(f"      链接: https://www.youtube.com/playlist?list={pid}")
        print()


def cmd_importplaylist():
    """将播放列表内所有视频导入 todolist.txt 或指定文件

    用法: importplaylist <播放列表ID 或 播放列表名>
           importplaylist PLVt93Bo6TqvyDyaVT_pDp2wcUfALtOtuJ
           importplaylist 系统经济金融
           importplaylist PLVt93Bo6TqvyDyaVT_pDp2wcUfALtOtuJ --output playlist.txt
    """
    if len(sys.argv) < 3:
        print("用法: importplaylist <播放列表ID 或 名称> [--output <路径>]")
        print("示例: importplaylist PLVt93Bo6TqvyDyaVT_pDp2wcUfALtOtuJ")
        print("      importplaylist 系统经济金融 --output playlist.txt")
        return

    # 解析参数：提取 --output
    args = sys.argv[2:]
    query_parts = []
    output_path = str(TODO_PATH)  # 默认 todolist.txt
    i = 0
    while i < len(args):
        if args[i] == '--output' and i + 1 < len(args):
            output_path = os.path.abspath(args[i + 1])
            i += 2
        else:
            query_parts.append(args[i])
            i += 1

    query = " ".join(query_parts)
    print(f"🔍 正在查找播放列表: {query}")

    # 尝试 yt-dlp 直接爬播放列表
    playlist_id = None
    remote_done = False

    # 如果输入的是完整 URL 或 PL/WL/LL ID，直接使用
    url_match = re.search(r'(?:list=)?([a-zA-Z0-9_-]+)', query)
    if query.startswith("PL") or query.startswith("WL") or query.startswith("LL") or query.startswith("FL"):
        playlist_id = query
    elif "youtube.com/playlist" in query or "youtu.be" in query:
        m = re.search(r'[?&]list=([a-zA-Z0-9_-]+)', query)
        if m: playlist_id = m.group(1)

    # 如果没找到 ID，尝试通过 MCP bridge 查找播放列表名称
    if not playlist_id:
        try:
            sid = _mcp_connect()
            tab_id = _mcp_find_history_tab(sid)  # reuse to find playlists tab
            # Instead, open playlists page
            result = _mcp_call(sid, "chrome_navigate", {"url": "https://www.youtube.com/feed/playlists"})
            if result:
                import time
                time.sleep(2)
                js = (
                    "var ytid=window.ytInitialData;"
                    "if(!ytid)return JSON.stringify({error:'no data'});"
                    "var grid=ytid.contents?.twoColumnBrowseResultsRenderer?.tabs?.[0]?.tabRenderer?.content?.richGridRenderer;"
                    "if(!grid)return JSON.stringify({error:'no grid'});"
                    "var contents=grid.contents||[];"
                    "for(var i=0;i<contents.length;i++){"
                    "  var c=contents[i];"
                    "  if(!c.richItemRenderer)continue;"
                    "  var lvm=c.richItemRenderer.content?.lockupViewModel;"
                    "  if(!lvm||lvm.contentType!=='LOCKUP_CONTENT_TYPE_PLAYLIST')continue;"
                    "  var meta=lvm.metadata?.lockupMetadataViewModel||{};"
                    "  var name=(meta.title?.content||'').toLowerCase();"
                    "  if(name.indexOf('" + query.lower() + "')>=0){"
                    "    return JSON.stringify({id:lvm.contentId, name:meta.title?.content||''});"
                    "  }"
                    "}"
                    "return JSON.stringify({error:'not found'});"
                )
                result = _mcp_call(sid, "chrome_javascript", {"tabId": tab_id, "code": js, "timeoutMs": 10000})
                if result:
                    text = result.get("result", {}).get("content", [{}])[0].get("text", "{}")
                    data = json.loads(text)
                    inner = json.loads(data.get("result", "{}"))
                    if "id" in inner:
                        playlist_id = inner["id"]
                        print(f"  ✅ 找到播放列表: {inner.get('name', '')} (ID: {playlist_id})")
        except:
            pass

    if not playlist_id:
        print(f"❌ 找不到播放列表: {query}")
        return

    # 用 yt-dlp 爬取播放列表所有视频
    url = f"https://www.youtube.com/playlist?list={playlist_id}"
    print(f"  📡 正在爬取播放列表视频...")
    
    try:
        r = subprocess.run(
            ["yt-dlp", "--flat-playlist", "--dump-json", url],
            capture_output=True, text=True, timeout=120
        )
    except subprocess.TimeoutExpired:
        print("❌ 请求超时（播放列表太大？）")
        return
    except Exception as e:
        print(f"❌ yt-dlp 失败: {e}")
        return

    if r.returncode != 0:
        print(f"❌ yt-dlp 错误: {r.stderr[:300]}")
        return

    # 解析视频列表
    videos = []
    for line in r.stdout.strip().split("\n"):
        if not line.strip(): continue
        try:
            raw = json.loads(line)
            videos.append({
                "id": raw["id"],
                "title": raw.get("title", ""),
                "url": f"https://www.youtube.com/watch?v={raw['id']}",
                "channel": raw.get("channel", ""),
                "channel_id": raw.get("channel_id", ""),
                "duration": raw.get("duration", 0),
                "upload_date": raw.get("upload_date", ""),
            })
        except:
            continue

    if not videos:
        print("📭 播放列表为空或无法读取")
        return

    print(f"  🎬 找到 {len(videos)} 个视频")

    # 保存到 history.json
    hist = load_hist()
    new_ids = []
    for v in videos:
        vid = v["id"]
        if vid in hist:
            if not hist[vid].get("processed"):
                new_ids.append(vid)
            continue

        hist[vid] = {
            "id": vid,
            "title": v.get("title", ""),
            "url": v["url"],
            "channel_name": v.get("channel", ""),
            "channel_id": v.get("channel_id", ""),
            "duration": v.get("duration", 0),
            "upload_date": v.get("upload_date", ""),
            "category": "播放列表导入",
            "fetched_at": str(date.today()),
            "processed": False,
            "note": f"来自播放列表 {playlist_id}"
        }
        new_ids.append(vid)

    if new_ids:
        save_hist(hist)
        if output_path == str(TODO_PATH):
            # 默认：追加到 todolist.txt（带 URL）
            lines = [f"https://www.youtube.com/watch?v={vid}" for vid in new_ids]
            todo_append(lines)
            print(f"\n✅ 添加 {len(new_ids)} 个视频到 todolist.txt")
        else:
            # 指定路径：写入纯视频 ID 列表
            output_dir = os.path.dirname(output_path)
            if output_dir:
                os.makedirs(output_dir, exist_ok=True)
            with open(output_path, "w") as f:
                for vid in new_ids:
                    f.write(f"{vid}\n")
            print(f"\n✅ 导出 {len(new_ids)} 个视频到 {output_path}")
        for v in videos[:5]:
            print(f"  + [{v['id']}] {v['title'][:45]}")
        if len(videos) > 5:
            print(f"  ... 还有 {len(videos)-5} 个")
    else:
        print("\n📭 没有新视频（均已存在或已处理）")


def cmd_stats():
    sub = load_sub()
    hist = load_hist()
    total = len(hist)
    done = sum(1 for v in hist.values() if v.get("processed"))
    ch = sum(len(c) for c in sub.values())
    print(f"订阅频道: {ch}")
    print(f"累计视频: {total}")
    print(f"已处理:   {done}")
    print(f"未处理:   {total - done}")
    for cat, chs in sub.items():
        print(f"  [{cat}] {len(chs)} 频道")


# ─── 入口 ────────────────────────────────────

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(__doc__); sys.exit(0)
    cmd = sys.argv[1]
    h = {
        "list": lambda: cmd_list(),
        "subscribe": lambda: cmd_subscribe(sys.argv[2], " ".join(sys.argv[3:])),
        "weight": lambda: cmd_weight(" ".join(sys.argv[2:-1]), int(sys.argv[-1])),
        "unsubscribe": lambda: cmd_unsubscribe(" ".join(sys.argv[2:])),
        "fetch": lambda: cmd_fetch(sys.argv[2] if len(sys.argv) > 2 else None),
        "new": lambda: cmd_new(sys.argv[2] if len(sys.argv) > 2 else None),
        "mark": lambda: cmd_mark(sys.argv[2]),
        "loadlist": lambda: cmd_loadlist(" ".join(sys.argv[2:]) or None),
        "cron": lambda: cmd_cron(),
        "flush": lambda: cmd_flush(),
        "stats": lambda: cmd_stats(),
        "gethistory": lambda: cmd_gethistory(),
        "listplaylists": lambda: cmd_listplaylists(),
        "importplaylist": lambda: cmd_importplaylist(),
    }
    if cmd in h:
        if cmd in ("subscribe",) and len(sys.argv) < 4:
            print("用法: subscribe <分类> <频道名>"); sys.exit(1)
        if cmd == "weight" and len(sys.argv) < 4:
            print("用法: weight <频道名/ID> <1-5>"); sys.exit(1)
        h[cmd]()
    else:
        print(f"未知: {cmd}")
        print(__doc__)
