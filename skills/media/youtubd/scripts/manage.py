#!/usr/bin/env python3
"""
youtubd 订阅管理脚本
========================
用法:
  python3 scripts/manage.py list                          # 列出所有已关注的频道
  python3 scripts/manage.py add <分类> <频道名或URL>      # 关注频道
  python3 scripts/manage.py remove <频道ID或名称>          # 取消关注
  python3 scripts/manage.py fetch [分类]                   # 拉取指定分类/所有频道的最新视频
  python3 scripts/manage.py new [分类]                     # 只显示未处理过的新视频
  python3 scripts/manage.py mark <视频ID>                  # 标记为已处理
  python3 scripts/manage.py stats                          # 统计概览
"""

import json, subprocess, sys, os, re
from datetime import date
from pathlib import Path

SKILL_DIR = Path(__file__).resolve().parent.parent
DB_PATH = SKILL_DIR / "database.json"


def load_db():
    with open(DB_PATH) as f:
        return json.load(f)


def save_db(db):
    with open(DB_PATH, "w") as f:
        json.dump(db, f, indent=2, ensure_ascii=False)


def get_channel_id(query):
    result = subprocess.run(
        ["yt-dlp", f"ytsearch1:{query}", "--flat-playlist", "--dump-json"],
        capture_output=True, text=True, timeout=30
    )
    if not result.stdout.strip():
        return None, None
    raw = json.loads(result.stdout.strip().split("\n")[0])
    return raw.get("channel_id"), raw.get("channel", query)


def fetch_channel_videos(channel_id, limit=20):
    pid = "UU" + channel_id[2:]
    result = subprocess.run(
        ["yt-dlp", f"https://www.youtube.com/playlist?list={pid}",
         "--flat-playlist", "--dump-json"],
        capture_output=True, text=True, timeout=60
    )
    videos = []
    for line in result.stdout.strip().split("\n"):
        if not line.strip():
            continue
        raw = json.loads(line)
        v = {
            "id": raw["id"],
            "title": raw.get("title", ""),
            "url": f"https://www.youtube.com/watch?v={raw['id']}",
            "channel_name": raw.get("channel", ""),
            "channel_id": channel_id,
            "duration": raw.get("duration", 0),
            "view_count": raw.get("view_count", 0),
            "upload_date": raw.get("upload_date", ""),
        }
        videos.append(v)
        if len(videos) >= limit:
            break
    return videos


def cmd_list():
    db = load_db()
    cats = db.get("categories", {})
    if not cats:
        print("没有关注的频道。用 add 添加。")
        return
    for cat, data in cats.items():
        channels = data.get("channels", {})
        if not channels: continue
        print(f"\n📂 [{cat}] ({len(channels)} 个频道)")
        for cid, info in channels.items():
            n = sum(1 for v in db.get("history", []) if v["channel_id"] == cid and not v.get("processed"))
            print(f"  📺 {info['name']}  ─  {n} 个未处理")


def cmd_add(category, query):
    db = load_db()
    if category not in db["categories"]:
        db["categories"][category] = {"channels": {}}
    cid, cname = get_channel_id(query)
    if not cid:
        print(f"找不到频道: {query}")
        return
    cat = db["categories"][category]
    if cid in cat["channels"]:
        print(f"已在[{category}]中: {cname}")
        return
    cat["channels"][cid] = {"name": cname, "url": f"https://www.youtube.com/channel/{cid}", "added": str(date.today())}
    save_db(db)
    print(f"已关注 [{category}] {cname}")


def cmd_remove(query):
    db = load_db()
    for cat, data in db["categories"].items():
        for cid, info in list(data["channels"].items()):
            if query in cid or query.lower() in info["name"].lower():
                del data["channels"][cid]
                save_db(db)
                print(f"已取消关注 [{cat}] {info['name']}")
                return
    print(f"没找到: {query}")


def cmd_fetch(category=None):
    db = load_db()
    existing = {v["id"] for v in db["history"]}
    new_vids = []
    for cat, data in db["categories"].items():
        if category and cat != category: continue
        for cid, info in data["channels"].items():
            print(f"  拉取 {info['name']}...")
            try:
                videos = fetch_channel_videos(cid)
            except Exception as e:
                print(f"  失败: {e}")
                continue
            for v in videos:
                if v["id"] not in existing:
                    v["category"] = cat
                    v["fetched_at"] = str(date.today())
                    v["processed"] = False
                    v["note"] = ""
                    db["history"].append(v)
                    existing.add(v["id"])
                    new_vids.append(v)
            print(f"    -> {len(videos)} 条, 新增 {len(new_vids)}")
    if new_vids:
        save_db(db)
        print(f"\n新增 {len(new_vids)} 个视频")
    else:
        print("\n没有新视频")


def cmd_new(category=None):
    db = load_db()
    pending = [v for v in db["history"] if not v.get("processed") and (not category or v.get("category") == category)]
    if not pending:
        print("没有未处理的视频")
        return
    for v in pending:
        m = v["duration"] // 60 if v["duration"] else 0
        print(f"  [{v['id']}] {v['title'][:50]}")
        print(f"       {v['category']} | {v['channel_name']} | {m}min")
        print(f"       {v['url']}")


def cmd_mark(video_id):
    db = load_db()
    for v in db["history"]:
        if v["id"] == video_id:
            v["processed"] = True
            save_db(db)
            print(f"已标记: {v['title'][:30]}...")
            return
    print(f"未找到: {video_id}")


def extract_vid(text):
    """从视频ID或URL中提取11位ID"""
    text = text.strip()
    m = re.search(r'(?:v=|youtu\.be/|shorts/|embed/|live/|watch\?v=)([a-zA-Z0-9_-]{11})', text)
    if m: return m.group(1)
    if re.match(r'^[a-zA-Z0-9_-]{11}$', text): return text
    return None


def get_video_meta(video_id):
    """获取单个视频的元数据"""
    try:
        result = subprocess.run(
            ["yt-dlp", "--dump-json", f"https://www.youtube.com/watch?v={video_id}"],
            capture_output=True, text=True, timeout=30
        )
        raw = json.loads(result.stdout.strip())
        return {
            "id": raw["id"],
            "title": raw.get("title", ""),
            "url": f"https://www.youtube.com/watch?v={raw['id']}",
            "channel_name": raw.get("channel", ""),
            "channel_id": raw.get("channel_id", ""),
            "duration": raw.get("duration", 0),
            "view_count": raw.get("view_count", 0),
            "upload_date": raw.get("upload_date", ""),
        }
    except Exception as e:
        return None


def cmd_loadlist(filepath=None):
    """从txt文件加载视频列表（每行一个视频ID或完整URL）"""
    db = load_db()
    if not filepath:
        filepath = SKILL_DIR / "todolist.txt"

    if not os.path.exists(filepath):
        print(f"文件不存在: {filepath}")
        return

    with open(filepath) as f:
        lines = [l.strip() for l in f if l.strip() and not l.startswith(("#", "=", "📺", " ")) and l.strip() not in ("", "-")]

    existing_ids = {v["id"] for v in db["history"]}
    added, skipped, failed = 0, 0, 0

    for line in lines:
        vid = extract_vid(line)
        if not vid:
            failed += 1
            continue
        if vid in existing_ids:
            skipped += 1
            continue
        meta = get_video_meta(vid)
        if not meta:
            failed += 1
            continue
        meta["category"] = "导入"
        meta["fetched_at"] = str(date.today())
        meta["processed"] = False
        meta["note"] = f"来自: {os.path.basename(filepath)}"
        db["history"].append(meta)
        existing_ids.add(vid)
        added += 1
        print(f"  + [{vid}] {meta['title'][:50]}")

    if added:
        save_db(db)
    print(f"\n新增 {added} | 跳过 {skipped} (已存在) | 失败 {failed}")


def cmd_stats():
    db = load_db()
    total = len(db["history"])
    done = sum(1 for v in db["history"] if v.get("processed"))
    ch = sum(len(c["channels"]) for c in db["categories"].values())
    print(f"频道: {ch}")
    print(f"累计视频: {total}")
    print(f"已处理: {done}")
    print(f"未处理: {total - done}")
    for cat, data in db["categories"].items():
        print(f"  [{cat}] {len(data['channels'])} 频道")


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)
    cmd = sys.argv[1]
    h = {
        "list": lambda: cmd_list(),
        "add": lambda: cmd_add(sys.argv[2], " ".join(sys.argv[3:])),
        "remove": lambda: cmd_remove(" ".join(sys.argv[2:])),
        "fetch": lambda: cmd_fetch(sys.argv[2] if len(sys.argv) > 2 else None),
        "new": lambda: cmd_new(sys.argv[2] if len(sys.argv) > 2 else None),
        "mark": lambda: cmd_mark(sys.argv[2]),
        "loadlist": lambda: cmd_loadlist(" ".join(sys.argv[2:]) or None),
        "stats": lambda: cmd_stats(),
    }
    if cmd in h:
        if cmd in ("add",) and len(sys.argv) < 4:
            print("用法: add <分类> <频道名>")
            sys.exit(1)
        h[cmd]()
    else:
        print(f"未知: {cmd}")
        print(__doc__)
