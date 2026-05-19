#!/usr/bin/env python3
"""
youtubd 订阅管理脚本（新结构）
==============================
数据文件：
  subscribe.json  — 分类 → channel_id → {name, url, added, weight}
  history.json    — video_id → {title, url, ...}
  todolist.txt    — 未处理视频URL列表（一行一个）

命令：
  list                         列出订阅
  subscribe <分类> <频道名>    添加订阅（权重默认3）
  weight <channel_id> <1-5>   设置权重
  unsubscribe <频道名/ID>      取消订阅
  fetch [分类]                 拉取频道最新视频
  new [分类]                   列出未处理的视频
  mark <视频ID>                标记为已处理
  stats                        统计概览
  loadlist [文件路径]          从txt文件导入
"""

import json, subprocess, sys, os, re
from datetime import date
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
SUB_PATH = SKILL_DIR / "subscribe.json"
HIST_PATH = SKILL_DIR / "history.json"
TODO_PATH = SKILL_DIR / "todolist.txt"


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
        # 只保留不与新行重复的行
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
        ["pgrep", "-f", rf"python3.*{script}.*(flush|cron)"],
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
                    added += 1
            print(f"    -> {len(videos)} 条, 新增 {added}")
    if added:
        save_hist(hist)
        # 新fetch的视频追加到 todolist
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

    # cron_task.json 结构：up_list = [{name, weight}, ...]
    # 或向后兼容：up_list 为空则用全部订阅
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

    # fetch 所有目标频道
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
            # 未分类的（up_list 里的新频道）
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

    # 按权重随机挑选未处理的
    pending_items = [(vid, v) for vid, v in hist.items() if not v.get("processed")]
    if not pending_items:
        print("📭 没有未处理的视频")
        open(TODO_PATH, "w").write("")
        return

    # 加权随机：权重越高，被挑中的概率越大
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

    # 追加写入 todolist.txt（累计模式，不覆盖）
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
    """
    全自动串行处理 todolist 所有视频。
    逐个 NotebookLM 生成报告（含耐心等待重试），下载到 brain-vault，标记 processed，清空 todolist。
    """
    kill_previous_flush()
    import subprocess as _sp, json as _json, time as _time, os as _os

    if not TODO_PATH.exists() or not TODO_PATH.stat().st_size:
        print("📭 todolist 为空或不存在")
        return

    with open(TODO_PATH) as f:
        lines = [l.strip() for l in f if l.strip()]

    hist = load_hist()
    VAULT = _os.path.expanduser("~/MyDoc/brain-vault")
    _os.makedirs(VAULT, exist_ok=True)

    ok = fail = skip = 0

    for vid_url in lines:
        vid = extract_vid(vid_url)
        if not vid:
            skip += 1
            continue

        info = hist.get(vid, {})
        title = info.get("title", vid)
        channel = info.get("channel_name", "unknown")
        duration = info.get("duration", 0)
        mins = duration // 60 if duration else 0

        safe_t = re.sub(r'[\\/*?:"<>|]', "", title)[:30]
        filename = f"{channel}_{safe_t}_总结.md".replace(" ", "_")
        filepath = _os.path.join(VAULT, filename)

        print(f"\n▶ [{vid}] {title[:40]}  |  {channel}  |  {mins}min")

        # A: 创建 Notebook
        r = _sp.run(["notebooklm", "create", f"flush-{vid}"],
                    capture_output=True, text=True, timeout=30)
        nb_id = ""
        for ln in r.stdout.split("\n"):
            if "Created notebook:" in ln:
                nb_id = ln.split(":")[1].strip().split()[0]
                break
        if not nb_id:
            print("   ❌ 创建 notebook 失败")
            fail += 1
            continue

        # B: 添加源
        r = _sp.run(["notebooklm", "source add", vid_url, "-n", nb_id],
                    capture_output=True, text=True, timeout=30)
        if "Added source" not in r.stdout:
            print("   ❌ 添加源失败")
            _sp.run(["notebooklm", "delete", nb_id], capture_output=True, timeout=15)
            fail += 1
            continue

        # C: 生成报告（耐心等待模式）
        generated = False
        for attempt in range(1, 17):
            print(f"   🏗️  生成 (第{attempt}次)...")
            r = _sp.run(["notebooklm", "generate", "report", "-n", nb_id],
                        capture_output=True, text=True, timeout=300)
            out = r.stdout + r.stderr

            if "completed" in out.lower() or "briefing document" in out.lower():
                # 获取 artifact_id 并下载
                aid = ""
                for ln in r.stdout.split("\n"):
                    if "artifact wait" in ln or "completed" in ln:
                        for p in ln.strip().split():
                            if "-" in p and len(p) > 20:
                                aid = p; break
                if not aid:
                    r2 = _sp.run(["notebooklm", "artifact", "list", "-n", nb_id],
                                 capture_output=True, text=True, timeout=30)
                    for ln in r2.stdout.split("\n"):
                        if "briefing-doc" in ln or "report" in ln.lower():
                            aid = ln.strip().split()[0]; break
                if aid:
                    _sp.run(["notebooklm", "artifact", "wait", aid, "-n", nb_id],
                            capture_output=True, text=True, timeout=300)
                    _sp.run(["notebooklm", "download", "report", filepath, "-n", nb_id],
                            capture_output=True, text=True, timeout=30)
                    if _os.path.exists(filepath) and _os.path.getsize(filepath) > 100:
                        print(f"   ✅ {filename}")
                        generated = True
                        ok += 1
                        if vid in hist:
                            hist[vid]["processed"] = True
                            hist[vid]["note"] = "已总结 → brain-vault"
                            save_hist(hist)
                        break

            if "quota" in out.lower() or "rate limited" in out.lower() or "daily quota" in out:
                w = [900, 1800][attempt - 1] if attempt <= 2 else 3600
                print(f"   ⏳ 配额限制，等{w//60}min...")
                _time.sleep(w)
            else:
                print(f"   ⚠️  失败，10秒后重试...")
                _time.sleep(10)

        if not generated:
            # 改用 notebooklm ask
            print(f"   🔄 改用 ask...")
            r = _sp.run(["notebooklm", "ask",
                        "请从视频内容生成结构化中文摘要，含核心观点、关键论述和金句摘录。",
                        "-n", nb_id], capture_output=True, text=True, timeout=120)
            if r.stdout.strip():
                with open(filepath, "w") as f:
                    f.write(r.stdout)
                print(f"   ✅ ask → {filename}")
                ok += 1
                if vid in hist:
                    hist[vid]["processed"] = True
                    hist[vid]["note"] = "已总结 → brain-vault (ask)"
                    save_hist(hist)
            else:
                print("   ❌ ask 也失败")
                fail += 1

        _sp.run(["notebooklm", "delete", nb_id], capture_output=True, timeout=15)

    open(TODO_PATH, "w").write("")
    print(f"\n📊 flush 完成:  ✅ {ok}  |  ❌ {fail}  |  ⏭ {skip}")

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
