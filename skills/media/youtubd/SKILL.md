---
name: youtubd
category: media
description: YouTube 数据采集技能。搜索视频、爬频道视频列表、爬播放列表。输出标准化JSON，可供其他skill链式调用（如notebooklm总结、保存到brain-vault等）。
---

# youtubd — YouTube Data Scraping

Agent-to-agent 接口。输入自然语言指令，输出**结构化 JSON**，方便链式调用下游 skill。

> **cron 依赖**：DEEPSEEK_API_KEY 必须写入 `~/.hermes/.env`，参见 `references/cron-pitfalls.md`

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

---

## 操作 3：爬播放列表

**输入**：播放列表 ID（URL 中的 `list=PLxxx`）或完整 URL

```bash
yt-dlp "https://www.youtube.com/playlist?list={PLAYLIST_ID}" --flat-playlist --dump-json
```

---

## 数据文件

### subscribe.json — 本地订阅频道

**本地订阅**是 youtubd 内部维护的频道订阅列表（与 YouTube 账号的订阅无关），按分类组织，每个频道有权重 1-5（默认 3）和 fetch_limit（默认 100）：

```json
{
  "读书": {
    "UCFTZu3WRjMYI7euMZ5R9BbA": {
      "name": "魏知超啥书都读",
      "url": "https://www.youtube.com/@weizhichao",
      "added": "2026-05-11",
      "weight": 3,
      "fetch_limit": 100
    }
  }
}
```

> `fetch_limit` 控制 `manage.py fetch` 和 `manage.py cron` 每次拉取该频道最新多少个视频。值越大候选池越广，但也越慢（每个视频需发一个 yt-dlp 请求）。

### history.json — 历史拉取记录

以 video_id 为 key 的 map：

```json
{
  "CGFdA1WlJIQ": {
    "title": "《非对称风险》...",
    "url": "https://www.youtube.com/watch?v=CGFdA1WlJIQ",
    "channel_name": "魏知超啥书都读",
    "channel_id": "UCFTZu3WRjMYI7euMZ5R9BbA",
    "category": "读书",
    "duration": 1992,
    "view_count": 30000,
    "upload_date": "20260315",
    "fetched_at": "2026-05-11",
    "processed": true,
    "note": "已总结 → brain-vault"
  }
}
```

> 注意：history.json 的值**不包含 `id` 字段**——id 就是 key 本身。遍历时用 `hist.items()` 而不是 `hist.values()`，否则拿不到 id。

### todolist.txt — 待处理队列（累计模式）

- `fetch` / `loadlist` / `cron` 新增的视频 **追加**到末尾，不覆盖
- `mark <视频ID>` 只标记 history 中的 processed，**不操作 todolist**
- `flush` 一次性串行处理所有条目（NotebookLM → brain-vault），完成后清空
- 自动去重

---

## 定时任务（cron）

配置文件：`~/.hermes/skills/media/youtubd/cron_task.json`

```json
{
  "up_list": [
    {"name": "魏知超啥书都读", "weight": 3},
    {"name": "LT視界", "weight": 1}
  ],
  "fetch_count": 5,
  "schedule": "0 10 * * *"
}
```

| 字段 | 说明 |
|------|------|
| `up_list` | 频道列表，每项含 `name`（订阅名称）和 `weight`（权重1-5） |
| `fetch_count` | 每次加权随机抽取几个视频到 todolist |
| `schedule` | 参考 cron 表达式，实际调度由 `/cron add` 设置 |

> `fetch_limit`（每频道拉取数）在 **subscribe.json 每个频道的 `fetch_limit` 字段**中配置，不在 cron_task.json 里。

**工作原理：**
1. 拉取所有目标频道的最新视频（每个频道 fetch_limit 条）
2. 按权重加权随机抽取 fetch_count 个
3. 追加写入 todolist.txt

**设置定时任务（配合 /cron add）：**

⚠️ **必须指定 `--model` 和 `--skills`**，否则 cron 调度器读不到 API key。参考 `references/cron-pitfalls.md`。

```bash
/cron add "youtubd 每日拉取" \
  --schedule "0 10 * * *" \
  --model '{"model":"deepseek-v4-flash","provider":"deepseek"}' \
  --skills youtubd,notebooklm-to-brainvault \
  --toolsets terminal,file,web \
  --prompt "..."
```

**手动触发：**
```bash
python3 ~/.hermes/skills/media/youtubd/scripts/manage.py cron
```

---

## 管理脚本

命令：`python3 ~/.hermes/skills/media/youtubd/scripts/manage.py`

| 命令 | 功能 |
|------|------|
| `list` | 列出所有**本地**订阅频道（含权重、未处理数） |
| `stats` | 统计总览 |
| `subscribe 分类 频道名` | 添加**本地**订阅频道（权重默认 3） |
| `weight 频道名/ID 1-5` | 设置频道权重 |
| `unsubscribe 频道名/ID` | 取消**本地**订阅 |
| `fetch [分类]` | 拉取最新视频到 history + 追加到 todolist |
| `new [分类]` | 列出未处理的视频 |
| `mark <视频ID>` | 标记 history 中 processed=true（不操作 todolist） |
| `loadlist [文件路径]` | 从 txt 导入视频列表（默认 todolist.txt） |
| `cron` | fetch + 加权随机抽 N 个 → 追加到 todolist |
| `flush` | **全自动串行处理** todolist 所有视频：逐个 NotebookLM 生成报告（含耐心等待重试），下载到 brain-vault，标记 processed，清空 todolist。可后台运行。 |
| `gethistory [数量]` | **拉取 YouTube 观看历史**（需 Chrome 运行 + MCP bridge），将视频追加到 todolist。默认 100 个。 |
| `listplaylists` | **列出所有播放列表**（需 Chrome 运行 + MCP bridge） |
| `importplaylist <ID/名称>` | **将播放列表内容全部导入 todolist.txt**（自动去重，支持 ID 或名称） |

**强制覆盖模式**：`flush` 和 `cron` 启动时自动调用 `kill_previous_flush()`，干掉同类旧进程。保证同一时间只有一个在跑。

---

## 链式调用

```youtubd（爬视频）→ JSON [{url,...}] → notebooklm-to-brainvault（总结 → brain-vault）```

`flush` 命令已将 notebooklm-to-brainvault 的完整流程内嵌，无需手动串接。对单条视频也可直接调用 notebooklm-to-brainvault 手动处理。

---

## 注意事项

- `--flat-playlist` 只取元数据不下载，速度快
- 如需完整字段（description、tags 等），去掉 `--flat-playlist`
- 频道的 `@频道名/videos` 方式有时超时，推荐用 `UU` 播放列表方式
- YouTube 限流（429）时等几秒重试
- 单次搜索建议不超过50个结果
- 外部待处理列表可以用 `~/youtube_todo.txt`，然后 `loadlist` 导入
- loadlist 导入的视频自动归类为 `"导入"`
- `mark` 只标记 history，**不操作 todolist**。要清空 todolist 用 `flush`
- `flush` 全自动串行处理（NotebookLM → brain-vault），完成后自动清空 todolist
- 后台运行 flush：`python3 scripts/manage.py flush &`（强制覆盖模式会自动干掉旧的）

### 文件概览

| 文件 | 用途 |
|------|------|
| `subscribe.json` | **本地**订阅频道（分类 → channel_id → {name, weight, fetch_limit}） |
| `history.json` | 历史拉取记录（video_id → info 的 map） |
| `todolist.txt` | 未处理视频的 URL 列表，累计追加，flush 后清空 |
| `cron_task.json` | 定时任务配置（拉取范围、每次数量） |
| `scripts/manage.py` | 管理脚本（订阅、拉取、处理全流程） |
| `references/flush-autopilot.md` | flush 全自动管道详情（耐心等待、强制覆盖） |
| `references/cron-pitfalls.md` | cron API key 故障排查 |
| `references/gethistory-detail.md` | gethistory 实现细节、技术难点与 YouTube API 认证说明 |
| `references/playlist-operations.md` | listplaylists / importplaylist 实现细节：YouTube 新 UI 的 lockupViewModel 结构、名称→ID 解析、yt-dlp 抓取 |

---

## gethistory 详解

**命令：** `python3 scripts/manage.py gethistory [数量]`

拉取当前已登录 Chrome 浏览器中的 YouTube 观看记录，自动加入 todolist.txt。

### 工作原理

1. 连接本地 Chrome MCP bridge (`http://127.0.0.1:12306/mcp`)
2. 在 Chrome 中找到或打开 YouTube `/feed/history` 页面
3. 通过 `chrome_javascript` 同步执行 JS，读取 `window.ytInitialData`
4. 提取 ytInitialData 中的 `videoRenderer` → 获取 ID、标题、频道
5. 对新视频调用 `yt-dlp --dump-json` 获取完整元数据
6. 写入 `history.json` 并追加到 `todolist.txt`

### 依赖

- Chrome 浏览器正在运行（已登录 YouTube）
- MCP bridge 正常运行（端口 12306 可访问）
- Python 内置库：`json`, `urllib`, `re`, `datetime`

### 已知限制

| 限制 | 原因 | 变通 |
|------|------|------|
| 只读取初始加载的 1-20 条 | YouTube 页面使用无限滚动，MCP bridge HTTP API 不支持 async/await | 多次运行 `gethistory` |
| 无法获取 watch 时间戳 | ytInitialData 只包含视频元数据，不含观看时间 | — |
| 需要 Chrome 运行中 | 使用浏览器身份认证（cookie）获取数据 | 先启动 Chrome + MCP bridge |

### 为什么不由 CLI 直接调 YouTube API

YouTube API 需要 `SAPISID` cookie 的 hash 认证。浏览器 cookie 在 Linux 上用 Chrome 加密存储（AES-CBC + keyring），`browser-cookie3` 和 `yt-dlp --cookies-from-browser` 均无法完整解密（17/49 cookies 解密失败）。即使拿到 SAPISID 值，Python `requests` 调 API 仍返回 "Sign in" 页面。**唯一可靠方式：通过浏览器环境执行 fetch() 或读取 ytInitialData。**

### YouTube UI 注意

YouTube 2025+ 新 UI 使用 `lockupViewModel` 替代旧的 `videoRenderer` / `playlistRenderer`。新卡片结构：

```javascript
// 旧格式（playlistRenderer）
item.playlistRenderer.playlistId

// 新格式（lockupViewModel）
item.lockupViewModel.contentId  // 内容 ID
item.lockupViewModel.contentType // "LOCKUP_CONTENT_TYPE_PLAYLIST" / "_VIDEO"
item.lockupViewModel.metadata.lockupMetadataViewModel.title.content
```

页面类型也改为 `richGridRenderer` 替代 `sectionListRenderer`，搜索结果等需适配两种结构。具体见 `scripts/manage.py` 中的 `_fetch_videos_via_browser` 实现。
