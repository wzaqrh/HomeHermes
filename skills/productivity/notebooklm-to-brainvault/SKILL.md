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

## 配置

配置文件：`<skill_dir>/assets/.env`

```bash
# 是否开启 token 保护模式（默认开启）
TOKEN_PROTECTION=true

# 阈值（秒）：超过此时长的视频，NotebookLM 失败后不走本地字幕 fallback
TOKEN_PROTECTION_THRESHOLD=600
```

**读取配置**（Agent 执行时必须先加载）：
```python
from dotenv import dotenv_values
import os
skill_dir = os.path.dirname(os.path.dirname(__file__))
config = dotenv_values(os.path.join(skill_dir, 'assets', '.env'))
protection = config.get('TOKEN_PROTECTION', 'true').lower() == 'true'
threshold = int(config.get('TOKEN_PROTECTION_THRESHOLD', '600'))
```

如果 `python-dotenv` 未安装，直接解析文件：
```python
with open(f'{skill_dir}/assets/.env') as f:
    env = dict(line.strip().split('=', 1) for line in f if '=' in line and not line.startswith('#'))
protection = env.get('TOKEN_PROTECTION', 'true').lower() == 'true'
threshold = int(env.get('TOKEN_PROTECTION_THRESHOLD', '600'))
```

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

### Step 2: 如果 NotebookLM 不可用 → 判断是否 Fallback

当 NotebookLM 出现以下错误时自动切换：
- `CSRF token not found`（认证失效）
- `artifact was removed by the server`（配额/限流）
- `Generation failed`（服务异常）

**先获取视频时长，判断是否走 fallback：**

```bash
# 获取视频时长（秒）
yt-dlp --dump-json "https://www.youtube.com/watch?v=VIDEO_ID" | python3 -c "import sys,json; print(json.load(sys.stdin).get('duration',0))"
```

**Fallback 决策逻辑：**

```
NotebookLM 失败后：
  ├─ TOKEN_PROTECTION=true 且 视频时长 > 阈值(600s=10min) → ❌ 跳过
  │   回报: "⛔ token保护: 视频 {duration}min > 10min，跳过本地字幕 fallback"
  │
  └─ TOKEN_PROTECTION=false 或 视频时长 ≤ 阈值(10min)
       └─ 尝试本地字幕 fallback：
            ├─ 字幕可用 → AI 总结 → 保存 ✅
            └─ 字幕不可用 → ❌ 跳过（绝不使用 description）
```

Fallback 流程（YouTube 视频，仅在 **时长 ≤ 10分钟 或 保护模式关闭** 时执行）：

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

### 上下文管理（重要）
`notebooklm use <notebook_id>` 不会可靠地保持上下文。所有后续命令必须显式指定 `-n <notebook_id>` 参数，不要依赖 `use` 切换的上下文状态。

反例（会漂移）：
```bash
notebooklm use <id>
notebooklm generate report           # 可能跑到其他 notebook 上
```

正例（可靠）：
```bash
notebooklm generate report -n <notebook_id>
notebooklm wait <task_id> -n <notebook_id>
notebooklm download report <path> -n <notebook_id>
```

### 生成任务瞬态失败
`notebooklm generate report` 偶发 `Generation failed - no artifact_id returned`。这是瞬态问题，重试即可。重试前不需要 `use`，直接再次调用 `generate`。

### Fallback 依赖缺失
```bash
pip install youtube-transcript-api
```

### 文件写入问题
```bash
ls ~/MyDoc/brain-vault/
# 确认目录存在且有写入权限
```

### 子任务路径陷阱（重要）
Delegated sub-agents 必须使用**绝对路径** `~/MyDoc/brain-vault/` 保存文件。不能缩写为 `~/brain-vault/`，不能自己创建子目录（如 `reports/`）。路径错误会导致文件无法被主 agent 找到。

正例：
```bash
notebooklm download report <path> -n <notebook_id>
# path 必须是 ~/MyDoc/brain-vault/文件名_总结.md 的展开绝对路径
```

反例（sub-agent 常见错误）：
```bash
~/brain-vault/xxx.md          # 写错目录，文件丢失
~/MyDoc/brain-vault/reports/  # 不能建子目录
```

验证方法：下载后立即 `ls -lh ~/MyDoc/brain-vault/` 确认文件存在。
