# 播放列表操作实现细节

## listplaylists（列出所有播放列表）

通过 MCP bridge 读取浏览器 `/feed/playlists` 页面，从 `ytInitialData` 提取所有 `LOCKUP_CONTENT_TYPE_PLAYLIST` 的 `lockupViewModel`。

### 数据结构

2025+ YouTube UI 使用 `richGridRenderer` + `lockupViewModel`：

```javascript
// ytInitialData 结构
ytInitialData.contents
  .twoColumnBrowseResultsRenderer.tabs[0]
  .tabRenderer.content
  .richGridRenderer.contents  // Array<richItemRenderer | continuationItemRenderer>

// 每个 playlist 卡片
content.richItemRenderer.content.lockupViewModel = {
  contentId: "PLxxx...",     // 播放列表 ID
  contentType: "LOCKUP_CONTENT_TYPE_PLAYLIST",
  metadata: {
    lockupMetadataViewModel: {
      title: { content: "名称" },
      // subtitle 可能为空
      metadata: {
        contentMetadataViewModel: {
          metadata: [{ text: "80 个视频" }]  // 视频计数
        }
      }
    }
  }
}
```

### 关键点

- 页面顶部有 **chipBarViewModel** 包含标签：最新添加 / 播放列表 / 自有 / 已保存
- 默认显示"播放列表"tab，只展示 10 个初始项目
- 可能有 continuationItemRenderer 用于加载更多（通常没有，一次性加载所有）
- 不存在的 contentId: `WL` = 稍后观看, `LL` = 赞过的视频

## importplaylist（导入播放列表视频）

两步走策略：

### Step 1: 解析名称 → ID

**方式 A — 直接提供 ID**（最快）：
- 以 `PL`、`WL`、`LL`、`FL` 开头 → 直接作为 ID 使用
- 含 `youtube.com/playlist` 或 `list=` 参数 → regex 提取

**方式 B — 名称查找**（需 MCP bridge）：
```
打开 /feed/playlists → 遍历 ytInitialData 中所有
LOCKUP_CONTENT_TYPE_PLAYLIST 的 lockupViewModel →
匹配 title.content.toLowerCase() 包含查询字符串 →
返回 contentId
```

### Step 2: yt-dlp 抓取视频

直接用 yt-dlp 抓取播放列表（**不需要认证**，公开播放列表可直接访问）：

```bash
yt-dlp --flat-playlist --dump-json \
  "https://www.youtube.com/playlist?list=PLAYLIST_ID"
```

`--flat-playlist` 只取元数据不下视频，速度快。输出 JSON Lines 格式，每行一个视频。

### 输出到文件

默认追加到 `todolist.txt`（带完整 URL）。支持 `--output` 参数指定其他文件（纯视频 ID，一行一个）：

```bash
# 默认 → todolist.txt（完整 URL 格式）
python3 manage.py importplaylist PLVt93Bo6TqvyDyaVT_pDp2wcUfALtOtuJ

# 指定路径 → 纯视频 ID
python3 manage.py importplaylist PLVt93Bo6TqvyDyaVT_pDp2wcUfALtOtuJ --output playlist.txt

# 名称查找 + 指定路径
python3 manage.py importplaylist 系统经济金融 --output playlist.txt
```

### 合并到 history.json 和 todolist.txt

- 自动去重：video_id 已存在则跳过
- 添加时标记 `category: "播放列表导入"` 和 `note: "来自播放列表 {id}"`
- 自动去重添加到 todolist（累计模式）

### 用例

```bash
# 按 ID 导入
python3 manage.py importplaylist PLVt93Bo6TqvyDyaVT_pDp2wcUfALtOtuJ

# 按名称导入（需 Chrome 运行）
python3 manage.py importplaylist 系统经济金融
```
