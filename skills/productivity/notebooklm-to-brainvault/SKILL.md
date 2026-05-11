---
name: notebooklm-to-brainvault
description: 通过 NotebookLM 处理 YouTube/网页/文档等内容源，自动生成总结报告并保存到 Obsidian brain-vault。NotebookLM 生成失败时自动 fallback 到本地转录+AI总结方案。
---

# NotebookLM → Brain-Vault 自动保存技能

接收 YouTube 链接、网页链接或本地文件，通过 NotebookLM 处理并生成总结报告，自动写入 Obsidian brain-vault（`~/MyDoc/brain-vault/`）。

## 前置条件

1. NotebookLM CLI 已安装并登录：`notebooklm list` 验证
2. Obsidian vault 路径：`OBSIDIAN_VAULT_PATH` 环境变量（默认 `~/MyDoc/brain-vault`）
3. Python 依赖：`youtube-transcript-api`（fallback 路径用）

## 工作流程

### Step 1: 尝试 NotebookLM 路径（主路径）

```bash
# 1. 创建新 Notebook
notebooklm create "标题"

# 2. 添加内容源（支持 YouTube URL / 网页URL / 本地文件）
notebooklm source add <URL或文件路径> --notebook <notebook_id>

# 3. 生成报告
notebooklm generate report --notebook <notebook_id>
# 获取 task_id

# 4. 等待生成完成
notebooklm artifact wait <task_id>

# 5. 下载报告
notebooklm download report <输出路径>
```

### Step 2: 如果 NotebookLM 不可用 → Fallback（本地路径）

当 NotebookLM 出现以下错误时自动切换：
- `CSRF token not found`（认证失效）
- `artifact was removed by the server`（配额/限流）
- `Generation failed`（服务异常）

Fallback 流程（YouTube 视频）：

```bash
# 1. 通过 youtube-transcript-api 抓取字幕
python3 <skill_dir>/scripts/fetch_transcript.py <YouTube_URL> --text-only --timestamps

# 2. 如果字幕抓取成功 → AI 基于完整字幕生成结构化的 Markdown 总结
# 3. 如果字幕不可用 → **失败退出**，不保存任何文件
```

> 重要规则：字幕抓取失败时，**绝不 fallback** 到视频 description 或浏览器提取文本。description 没有完整内容，不值得保存。宁可跳过。

### Step 3: 写入 Brain-Vault

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/MyDoc/brain-vault}"
cat > "$VAULT/标题.md" << 'ENDNOTE'
...
ENDNOTE
```

## 输出格式

笔记保存为 Markdown 文件，包含：
- 元数据（来源链接、日期）
- 核心框架 / 章节
- 关键观点和金句
- 个人评论（若有）

## 故障排查

### NotebookLM 认证失败
```bash
notebooklm login
notebooklm list  # 验证
```

### Fallback 依赖缺失
```bash
pip install youtube-transcript-api
```

### 文件写入问题
```bash
ls ~/MyDoc/brain-vault/
# 确认目录存在且有写入权限
```
