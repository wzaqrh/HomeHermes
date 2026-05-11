---
name: youtubd
category: media
description: YouTube 数据采集技能。搜索视频、爬频道视频列表、爬播放列表。输出标准化JSON，可供其他skill链式调用（如notebooklm总结、保存到brain-vault等）。
---

# youtubd — YouTube Data Scraping

Agent-to-agent 接口。输入自然语言指令，输出**结构化 JSON**，方便链式调用下游 skill。

---

## 输出规范（统一格式）

所有操作统一输出 JSON 数组，每项结构如下：

```json
{
  "id": "s3ii48qYBxA",
  "title": "Beginner's Guide To The Linux Terminal",
  "url": "https://www.youtube.com/watch?v=s3ii48qYBxA",
  "channel": "DistroTube",
  "channel_id": "UCVls1GmFKf6WlTraIb_IaJg",
  "duration": 2547,
  "view_count": 638013,
  "upload_date": "20260315",
  "source_type": "search | channel | playlist"
}
```

`source_type` 标识数据来源，下游 skill 可以根据它做不同处理。

---

## 操作 1：搜索视频

**输入**：搜索词 + 可选数量 N（默认10，最多50）

```bash
yt-dlp "ytsearch{N}:{query}" --flat-playlist --dump-json
```

**Agent 处理规则**：
1. 执行命令，解析 stdout 为 JSON（每行一个对象）
2. 用 `python3 -c` 提取关键字段，组装成统一格式的 JSON 数组
3. 返回给用户 / 或直接衔接下游 skill

**示例实现**：
```python
import subprocess, json

result = subprocess.run(
    ["yt-dlp", "ytsearch10:linux terminal", "--flat-playlist", "--dump-json"],
    capture_output=True, text=True, timeout=30
)

videos = []
for line in result.stdout.strip().split("\n"):
    if not line: continue
    raw = json.loads(line)
    videos.append({
        "id": raw["id"],
        "title": raw["title"],
        "url": f"https://www.youtube.com/watch?v={raw['id']}",
        "channel": raw.get("channel", ""),
        "channel_id": raw.get("channel_id", ""),
        "duration": raw.get("duration", 0),
        "view_count": raw.get("view_count", 0),
        "upload_date": raw.get("upload_date", ""),
        "source_type": "search"
    })

# videos 就是标准输出的 JSON 数组
print(json.dumps(videos, indent=2, ensure_ascii=False))
```

---

## 操作 2：爬频道视频

**输入**：频道名 或 频道ID

**两步走**：

Step 1 — 解析频道名 → channel_id：

```bash
yt-dlp "ytsearch1:{channel_name}" --flat-playlist --dump-json
```

从返回的 JSON 中取 `channel_id`（格式 `UCxxxxxxxxxxxx`）。

Step 2 — 用上传播放列表爬所有视频：

```bash
yt-dlp "https://www.youtube.com/playlist?list=UU{channel_id[2:]}" --flat-playlist --dump-json
```

> 规则：channel_id 去掉 `UC` 前缀，加上 `UU`，就是该频道的上传播放列表 ID。

输出格式同统一规范，`source_type` 为 `"channel"`。

---

## 操作 3：爬播放列表

**输入**：播放列表 ID（URL 中的 `list=PLxxx`）或完整 URL

```bash
yt-dlp "https://www.youtube.com/playlist?list={PLAYLIST_ID}" --flat-playlist --dump-json
```

输出格式同统一规范，`source_type` 为 `"playlist"`。

---

## 链式调用（与其他 skill 衔接）

youtubd 的核心价值是**产出可供下游消费的 JSON**。典型链路：

```
youtubd（搜视频）
  → JSON [{id, title, url, ...}]
  → 遍历 url，调用 youtube-content 获取字幕
  → 调用 notebooklm-to-brainvault 总结并保存
```

**示例：搜视频 → 总结前3个 → 存到 brain-vault**

```python
import subprocess, json

# Step 1: youtubd 搜索
result = subprocess.run(
    ["yt-dlp", "ytsearch3:AI programming", "--flat-playlist", "--dump-json"],
    capture_output=True, text=True, timeout=30
)
videos = []
for line in result.stdout.strip().split("\n"):
    if not line: continue
    raw = json.loads(line)
    videos.append({
        "id": raw["id"],
        "title": raw["title"],
        "url": f"https://www.youtube.com/watch?v={raw['id']}",
        "channel": raw.get("channel", ""),
        "duration": raw.get("duration", 0),
        "source_type": "search"
    })

# Step 2: 对每个视频调用 youtube-content 获取字幕并总结
# 然后 notebooklm-to-brainvault 保存
# （由 agent 在后续工具调用中完成）
```

**Agent 调用链示例（自然语言→翻译成工具调用）**：

```
用户："搜一下AI编程视频，把前3个总结保存到brain-vault"
Agent 行为：
  1. youtubd 搜索 → 得到 JSON 数组（含 url）
  2. 取前3个 url，逐个调用 youtube-content skill（抓字幕）
  3. 对字幕做 AI 总结
  4. 存到 ~/MyDoc/brain-vault/ 目录
```

---

## 订阅管理系统

数据库文件：`~/.hermes/skills/media/youtubd/database.json`

```json
{
  "categories": { "分类名": { "channels": { "UCxxx": {"name":"频道名", ...} } } },
  "history": [ { "id":"视频ID", "title":"...", "processed": true/false, ... } ]
}
```

管理脚本：`python3 ~/.hermes/skills/media/youtubd/scripts/manage.py`

| 命令 | 功能 |
|------|------|
| `list` | 列出所有关注的频道，显示未处理数量 |
| `stats` | 统计总览 |
| `add 分类 频道名` | 关注频道 |
| `remove 频道名` | 取消关注 |
| `fetch [分类]` | 拉取最新视频到 history |
| `new [分类]` | 列出未处理的视频 |
| `mark 视频ID` | 标记为已处理 |
| `loadlist [文件路径]` | 从txt文件导入视频列表（每行一个ID或URL，默认读取 todolist.txt） |

**Agent 工作流示例**：
1. `manage.py fetch` — 检查所有关注的频道，发现新视频追加到 history
2. `manage.py new` — 看看哪些还没处理
3. 逐个处理完后 `mark` 标记

## 注意事项

- `--flat-playlist` 只取元数据不下载，速度快
- 如需完整字段（description、tags 等），去掉 `--flat-playlist`，但单视频多一个请求
- 频道的 `@频道名/videos` 方式有时超时，推荐用 `UU` 播放列表方式
- YouTube 限流（429）时等几秒重试
- 单次搜索建议不超过50个结果
- 订阅频道列表可持久化到 `~/.hermes/skills/media/youtubd/subscriptions.json`

## 数据库参考

- `database.json` 格式详见 `references/database-schema.md`
- 数据库文件位于：`~/.hermes/skills/media/youtubd/database.json`
- todolist.txt 默认路径：`~/.hermes/skills/media/youtubd/todolist.txt`（每行一个视频ID或完整URL，支持 `#` 注释）
