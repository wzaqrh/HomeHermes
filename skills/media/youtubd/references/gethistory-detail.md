# gethistory 实现细节

## 技术难点

### 1. YouTube API 认证

YouTube Internal API（`/youtubei/v1/browse`）需要三重认证：

- **Cookie**：`SAPISID`, `__Secure-1PSID`, `__Secure-3PSID` 等
- **Header**：`Authorization: SAPISIDHASH {timestamp}_{sha1(timestamp + " " + SAPISID)}`
- **Origin**：`https://www.youtube.com`

外部 Python 调用始终失败（返回 "Sign in"），即使 Cookie 和 SAPISID hash 计算正确。原因可能是 Chrome 加密存储的 cookie 被 `browser-cookie3` 读取时已损坏。

**唯一可行方案**：通过浏览器 JS 环境（`chrome_javascript`）执行 `fetch()` 或直接读 `ytInitialData`。

### 2. Chrome cookie 加密（Linux）

Linux 上 Chrome 使用 AES-CBC + system keyring 加密 cookie。`browser-cookie3` 需要 D-Bus session keyring 解密：

```python
import browser_cookie3 as bc
cookies = bc.chrome(domain_name='.youtube.com')  # 需要 DBUS_SESSION_BUS_ADDRESS
```

在 sandbox/execute_code 环境缺少 D-Bus 连接，解密失败。`yt-dlp --cookies-from-browser chrome` 同样只能解密约 32/49 个 cookie（SAPISID 等重要 cookie 被加密）。

### 3. MCP bridge async 限制

| 通道 | 支持 async | 来源 |
|------|-----------|------|
| Hermes 原生工具 `mcp_chrome_chrome_javascript` | ✅ 是 | Agent 内置 |
| HTTP API `curl http://127.0.0.1:12306/mcp` | ❌ 否 | 外部脚本 |

manage.py 作为独立 CLI 脚本只能走 HTTP API → 只能用同步 JS。

### 4. YouTube UI 版本差异

2025+ YouTube 使用新 UI 组件：

| 组件 | 页面类型 | 内容渲染 |
|------|---------|---------|
| `sectionListRenderer` | 旧版 | `videoRenderer`, `playlistRenderer`, `shelfRenderer` |
| `richGridRenderer` | 新版 `/feed/playlists` | `lockupViewModel` |
| `sectionListRenderer` + `targetId: "browse-feedFEhistory"` | 新版 `/feed/history` | `lockupViewModel` |

### 5. 播放列表页面结构

`/feed/playlists` 使用 `richGridRenderer` + `lockupViewModel`。每个 playlist 卡片结构：

```javascript
item.lockupViewModel = {
  contentId: "PLxxx...",     // 播放列表 ID
  contentType: "LOCKUP_CONTENT_TYPE_PLAYLIST",
  metadata: {
    lockupMetadataViewModel: {
      title: { content: "播放列表名称" },
      subtitle: { content: "子标题" },
      metadata: {
        contentMetadataViewModel: {
          metadata: [{ text: "80 个视频" }]
        }
      }
    }
  },
  rendererContext: {
    accessibilityContext: { label: "..." }
  }
}
```

## 测试过的方案（均失败）

| 方案 | 结果 | 原因 |
|------|------|------|
| `yt-dlp "https://www.youtube.com/feed/history" --flat-playlist --dump-json --cookies-from-browser chrome` | 超时 | yt-dlp 不支持 history 页面作为 playlist |
| `yt-dlp --cookies-from-browser chrome --cookies /tmp/cookies.txt --skip-download` | cookie 不全 | 加密 cookie 无法解密 |
| `POST /youtubei/v1/browse?key=...` with `browser-cookie3` cookies | 403 Sign in | cookie 值损坏或缺少关键 auth header |
| `POST /youtubei/v1/browse?key=...` with `requests.Session` | 403 Sign in | 同上 |
| `browser-cookie3.chrome()` from `execute_code` sandbox | D-Bus KeyError | 无 `DBUS_SESSION_BUS_ADDRESS` |

## 通过的方案

| 方案 | 说明 |
|------|------|
| `chrome_javascript` (MCP HTTP API) 读 `ytInitialData` | 同步 JS，`return` 必须显式 |
| `chrome_javascript` (Hermes 原生工具) | 支持 async/await 和 fetch() |
