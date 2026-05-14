---
name: youtube-summary-to-brain-vault
description: 从YouTube视频链接抓取字幕、生成结构化摘要，并作为Markdown笔记保存到Obsidian vault（brain-vault）
---

# YouTube 视频 → Obsidian Vault 总结笔记

将 YouTube 视频的完整字幕抓取、结构化整理，并直接写入 Obsidian vault 作为笔记。

## 前置条件

1. `youtube-transcript-api`（Python 库）
   ```bash
   pip install youtube-transcript-api
   ```

2. `OBSIDIAN_VAULT_PATH` 环境变量已设置（指向你的 Obsidian vault 目录）

3. `youtube-content` 技能已安装（脚本路径：`~/.hermes/skills/media/youtube-content/scripts/fetch_transcript.py`）

## 工作流程

### Step 1: 抓取字幕

```bash
python3 ~/.hermes/skills/media/youtube-content/scripts/fetch_transcript.py \
  "https://www.youtube.com/watch?v=VIDEO_ID" --text-only --timestamps
```

备用命令（无时间戳）：
```bash
python3 ~/.hermes/skills/media/youtube-content/scripts/fetch_transcript.py \
  "https://www.youtube.com/watch?v=VIDEO_ID" --text-only
```

### Step 2: 验证字幕

- 检查输出是否为空
- 如果为空，尝试不带 `--language` 参数重试（自动检测可用语言）
- 如果仍为空 → **失败退出**，告知用户该视频无字幕，不保存任何内容

> 重要规则：字幕不可用时，**绝不 fallback** 到视频 description 或浏览器提取文本。description 没有完整内容，不值得保存。宁可跳过。

### Step 3: 生成结构化摘要（AI 总结）

基于字幕内容生成 Markdown 格式的结构化笔记，包含：

- **标题**：视频主题
- **来源信息**：YouTube 链接
- **核心框架**：视频的主要论点和结构
- **分章节摘要**：按时间戳或话题划分
- **关键数据/人物/案例**：重要事实
- **金句摘录**：视频中的名句/观点
- **个人思考/总结**：整体评价

### Step 4: 写入 Obsidian Vault

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/Documents/Obsidian Vault}"
cat > "$VAULT/笔记标题.md" << 'ENDNOTE'
...Markdown 内容...
ENDNOTE
```

## 注意事项

### 字幕不可用时
- 视频可能禁用了字幕
- 直接失败，不生成任何文件

### 长视频处理
- 字幕超过 ~50K 字符时，需要分块处理（每块 ~40K，重叠 2K）
- 分别总结每块后再合并

### NotebookLM 已恢复
NotebookLM CLI 当前可用（2026-05-11 已验证：YouTube 源可正常添加和生成报告）。如需使用 NotebookLM，优先调用 `notebooklm-to-brainvault` 技能。本技能作为字幕抓取的 fallback 路径使用。

## 返回值（Agent 链式调用用）

**成功时：**
```
✅ 已保存 → /home/bdwillwin/MyDoc/brain-vault/视频标题_总结.md
```

**失败时：**
```
❌ 无可用字幕，跳过 → https://www.youtube.com/watch?v=VIDEO_ID
```

Agent 必须检查返回值。失败时不创建任何文件，不写入 database 的 note 字段，不标记 processed。
