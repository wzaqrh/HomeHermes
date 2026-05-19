# NotebookLM CLI 已知陷阱

## 命令格式

```
notebooklm delete -n <id> -y    ✅
notebooklm delete <id>           ❌ 报错，必须用 -n
```

`delete` 命令必须加 `-n` 参数，不支持裸 ID。

## 缓存问题

`notebooklm list` 返回的结果可能是**缓存的**：
- 删除 notebook 后，list 可能仍显示已删除的条目
- 直接 `delete -n <id> -y` 会报 "No notebook found" 证实删除成功
- 刷新页面或等待几分钟后 list 才会更新
- **不要依赖 list 判断操作是否生效**，改用 `delete -n <id> -y` 的返回码

## 多账号路由问题

部分 notebook 在 `list` 中可见但操作时报 "Not Found"：
- 可能因为多 Google 账号，CLI 会话路由到了不同账号
- 用完整 ID（非前缀）尝试操作
- 如果持续失败，`notebooklm login` 重新登录

## source add 瞬态失败

`notebooklm source add <URL> -n <id>` 偶发以下错误：
- `API returned no data for URL` — YouTube 侧临时问题，换视频即可
- 重试通常不会修复同一个视频
- 原因：YouTube 视频编码、地域限制、反爬机制

## create RPC 故障

`notebooklm create` 返回 `RPC CREATE_NOTEBOOK failed / Invalid argument`：
- Google 服务端端点故障，不是本地问题
- 已有 notebook 不受影响（`-n <existing_id>` 仍然可用）
- 策略：用一个共享 notebook 处理所有视频，而不是每视频建一个
