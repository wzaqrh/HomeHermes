---
name: notebooklm-to-brainvault
description: 通过 NotebookLM 处理 YouTube 视频，自动生成总结报告并保存到 Obsidian brain-vault。提供可复用的 process_video.py 脚本独立运行，集成在 youtubd 的 flush 管道中作为后端引擎。
---

# NotebookLM → Brain-Vault 自动保存技能

接收 YouTube 链接，通过 NotebookLM 生成总结报告，保存到 `~/MyDoc/brain-vault/`。

## 前置条件

1. NotebookLM CLI 已安装并登录：`notebooklm list` 验证
2. Obsidian vault：`OBSIDIAN_VAULT_PATH` 环境变量（默认 `~/MyDoc/brain-vault`）

## 配置

配置文件：`assets/.env`

```bash
# 添加视频源后等待时间（秒），让 NotebookLM 充分处理内容再 generate
# 设为 0 则不等（不推荐 — 实测不等会导致 generate 失败）
# 推荐 1200（20 分钟），至少 300（5 分钟）
SOURCE_ADD_SLEEP=1200
```

## 使用脚本（推荐）

主入口 `scripts/process_video.py`：

```bash
# 单视频处理
python3 scripts/process_video.py "https://www.youtube.com/watch?v=xxx"

# 共享 notebook（批量处理省配额，避免 RPC 失败）
python3 scripts/process_video.py "https://www.youtube.com/watch?v=xxx" --notebook BATCH_ID
```

### process_video.py 处理流程

```
输入 URL / video_id
  ├─ 检查 brain-vault 是否已有同名文件 → 有则 ⏭ 跳过
  ├─ 检查 youtubd history.json 标记 processed → 有则 ⏭ 跳过
  └─ NotebookLM 路径：
       ├─ 创建 notebook（或复用 --notebook）
       ├─ source add
       │    ├─ 成功 → 等待 SOURCE_ADD_SLEEP 秒（配的 20 分钟）
       │    │           然后 generate report（耐心等待重试）
       │    │           成功后 download → 清理 → ✅
       │    └─ 失败 → ❌ "NotebookLM 无法处理此视频，跳过"
       │              直接跳过，不走任何 fallback，不尝试本地字幕
       └─ generate report（16 次重试：15min→30min→60min→ask）
```

### 去重

- brain-vault 已有同名总结文件 → 跳过
- `youtubd/history.json` 中 `processed=true` → 跳过

### youtubd 集成

`youtubd manage.py flush --todolist <文件>` 遍历文件逐条调用 `process_video.py`：
- 替代旧的硬编码 subprocess 调用
- 继承脚本的所有重试、去重逻辑
- 通过 `kill_previous_flush()` 保证单进程运行

## 手动操作 / 调试

```bash
# 1. 创建 notebook
notebooklm create "标题"
# 2. 添加源
notebooklm source add <URL> -n <nb_id>
# 3. ⚠️ 必须等！不等则 generate 可能失败
sleep 1200
# 4. 生成报告
notebooklm generate report -n <nb_id>
# 5. 等待完成
notebooklm artifact wait <task_id> -n <nb_id>
# 6. 下载
notebooklm download report ~/MyDoc/brain-vault/xxx.md -n <nb_id>
# 7. 批量处理时删除旧源再添加
notebooklm source delete <source_id> -n <nb_id> -y
```

## 已知错误与边缘情况

### `Error: API returned no data for URL`
`source add` 对某些 YouTube 视频返回此错误。YouTube 侧临时性问题（编码/地域/反爬），非 NotebookLM 问题。重试通常无效，换视频通常就能加上。

### `RPC CREATE_NOTEBOOK failed / Invalid argument`
Google 服务端端点偶发故障。已有 notebook 不受影响，用 `--notebook` 共享 notebook 绕过。

### `Generation failed - no artifact_id returned`
瞬态失败，重试即可，不换 notebook。脚本内置 16 次重试。

### 无字幕视频
某些频道所有视频均无字幕（如 "曲博科技教室"）。此类视频 NotebookLM source add 无条件失败，直接跳过。

### `-n` 参数位置（重要）
必须放在子命令**之后**：
- ✅ `notebooklm source add <URL> -n <id>`
- ✅ `notebooklm generate report -n <id>`
- ❌ `notebooklm -n <id> source add <URL>`

## 耐心等待模式

`generate report` 遇到配额限制时自动步进等待：

```
第1次失败 → 等 15min → 重试
第2次失败 → 等 30min → 重试
第3~16次 → 每次等 60min → 重试
第17次 → 改用 notebooklm ask
```

## 重要约束

- **禁止并行**：NotebookLM CLI 不支持并发，必须串行处理
- **source add 后必须等待**：不等则 generate 失败，至少等几分钟
- **不尝试本地字幕 fallback**：NotebookLM 失败就直接跳过

## 文件概览

| 文件 | 用途 |
|------|------|
| `assets/.env` | 配置：`SOURCE_ADD_SLEEP` |
| `scripts/process_video.py` | **主脚本**：单视频完整处理流程 |
| `references/cli-pitfalls.md` | NotebookLM CLI 已知陷阱 |
