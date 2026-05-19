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

NotebookLM **无条件执行**。先试，结果如何后面再判断。

```bash
# 1. 创建新 Notebook
notebooklm create "标题"

# 2. 添加内容源
notebooklm source add <URL> -n <notebook_id>

# 3. 生成报告
notebooklm generate report -n <notebook_id>
# 获取 task_id

# 4. 等待生成完成
notebooklm artifact wait <task_id> -n <notebook_id>

# 5. 下载报告到 brain-vault
notebooklm download report ~/MyDoc/brain-vault/文件名_总结.md -n <notebook_id>
```

**如果 NotebookLM 成功** → ✅ 直接完成，不执行 Step 2。

### Step 2: NotebookLM 失败 → 判断是否 Fallback

当 NotebookLM 出现以下错误时触发：
- `CSRF token not found`（认证失效）
- `artifact was removed by the server`（配额/限流）
- `Generation failed`（服务异常）

**先获取视频时长，再决定是否 fallback：**

```bash
yt-dlp --dump-json "https://www.youtube.com/watch?v=VIDEO_ID" | python3 -c "import sys,json; print(json.load(sys.stdin).get('duration',0))"
```

**决策逻辑（重要——严格按此顺序）：**

```
NotebookLM 失败后：
  ├─ TOKEN_PROTECTION=true 且 视频时长 > 阈值(600s=10min) → ❌ 跳过
  │   回报: "⛔ token保护: 视频 {duration}min > 10min，跳过"
  │   不抓字幕，不保存任何文件
  │
  └─ TOKEN_PROTECTION=false 或 视频时长 ≤ 阈值(10min)
       └─ 尝试本地字幕 fallback：
            ├─ 字幕可用 → AI 总结 → 保存 ✅
            └─ 字幕不可用 → ❌ 跳过
                回报: "❌ 无可用字幕，跳过 → URL"
                绝不使用 description
```

> ⚠️ **常见错误**：不要在 NotebookLM 失败前就判断时长跳过。NotebookLM 总是先试，失败了才看保护规则。

### Step 3: 写入 Brain-Vault

```bash
VAULT="${OBSIDIAN_VAULT_PATH:-$HOME/MyDoc/brain-vault}"
cat > "$VAULT/标题.md" << 'ENDNOTE'
...Markdown 内容...
ENDNOTE
```

## 输出格式

笔记保存为 Markdown 文件，包含：
- 元数据（来源链接、日期）
- 核心框架 / 章节
- 关键观点和金句
- 个人评论（若有）

## 重要约束

### ⛔ 禁止并行
NotebookLM CLI 不支持并发操作。多个 agent 同时调用会导致：
- 上下文漂移（一个 agent 的 `use` 影响另一个）
- Google 配额快速耗尽
- 生成任务互相覆盖

**必须串行处理**，一次只处理一个视频。不要用 `delegate_task` 或其他并行机制。

### 批量处理策略：共享 notebook
处理多个视频时，**不要**每个视频新建一个 notebook。有两个风险：
1. `notebooklm create` 的 RPC 端点偶尔服务器端故障（`RPC CREATE_NOTEBOOK failed / Invalid argument`）
2. 大量残留 notebook 需要手动清理

正确做法：**创建一个共享 notebook 处理所有视频**：

```bash
# 只创建一次
notebooklm create "今日份" -n BATCH_ID

# 逐个加源 → 生成 → 下载 → 删源 → 下一个
notebooklm source add <URL1> -n BATCH_ID
notebooklm generate report -n BATCH_ID → 下载 → source remove

notebooklm source add <URL2> -n BATCH_ID
notebooklm generate report -n BATCH_ID → 下载 → source remove
```

如果 `create` 挂了（RPC 失败），用已有的 notebook ID 前缀照样能加源和生成。

### 强制覆盖模式（新启动的干掉旧的）
`flush` 和 `cron` 等长时间运行的任务，启动时自动清理之前残留的同类进程：

```python
import subprocess, os, signal

def kill_previous_flush():
    """杀掉之前启动的 flush/cron 进程"""
    my_pid = os.getpid()
    script = os.path.abspath(__file__)
    # 查找同一脚本的其他进程
    r = subprocess.run(
        ["pgrep", "-f", f"python3.*{script}.*(flush|cron)"],
        capture_output=True, text=True, timeout=10
    )
    for pid_str in r.stdout.strip().split("\n"):
        pid = pid_str.strip()
        if pid and pid != str(my_pid):
            try:
                os.kill(int(pid), signal.SIGTERM)
                print(f"  🧹 已干掉旧进程 PID={pid}")
            except (ProcessLookupError, ValueError):
                pass
```

`manage.py` 的 `flush` 和 `cron` 命令入口处调用此函数。laocl的进程看到新进程启动自动退出。

### -n 参数位置（重要）
`-n / --notebook` 必须放在**子命令之后**：
```
notebooklm source add <URL> -n <id>      ✅
notebooklm generate report -n <id>       ✅
notebooklm download report <path> -n <id> ✅
```

### generate 配额耗尽时的耐心等待模式（默认开启）当 `generate report` 遇到配额限制时，按步进时间间隔重试，直到成功或用满16次后改用 ask。

```
第1次失败 → 等15min → 重试
第2次失败 → 等30min → 重试
第3~16次失败 → 每次等60min → 重试
第17次失败 → 改用 notebooklm ask
```

**实现方式（用 sleep + process wait，不要 notify_on_complete）：**
```python
# Step 1: 发起 generate，时长由 sleep 控制重试间隔
# 第1次等待15分钟(900秒)
terminal(f"sleep 900 && notebooklm generate report -n {notebook_id} 2>&1",
         background=True, session_id="nb_gen_1")

# Step 2: 阻塞等待完成（process wait 非忙等）
result = process(action="wait", session_id="nb_gen_1", timeout=3600)

# Step 3: 检查结果
if "completed" in result["output"]:
    # 成功 → download report
else:
    # 失败 → 下一步：等30分钟
    terminal(f"sleep 1800 && notebooklm generate report -n {notebook_id} 2>&1",
             background=True, session_id="nb_gen_2")
    result = process(action="wait", session_id="nb_gen_2", timeout=3600)
    # 再失败 → 等60分钟...
```

**关键规则：**
- 等待期间**不要处理其他视频**，只等当前这个
- 用 sleep + process wait 实现等待，**不要 notify_on_complete**
- 等待通过 `process(action='wait')` 实现，非忙等
- 超过16次失败后改用 `notebooklm ask` 替代

### 替代路径：notebooklm ask
如果 `generate report` 用满16次耐心等待仍失败，改用 `notebooklm ask`：
```bash
notebooklm ask "请从视频内容生成结构化中文摘要" -n <notebook_id>
```

### 已知错误

全部 CLI 已知陷阱见 `references/cli-pitfalls.md`。常见问题速查：

**`Error: API returned no data for URL: ...`**
`notebooklm source add` 对某些 YouTube 视频返回此错误。这是 YouTube 侧临时性问题（视频编码/地域/反爬），不是 NotebookLM 的问题。
- 重试通常无效
- 换一个视频通常就能加上
- 不影响其他视频的处理

**`RPC CREATE_NOTEBOOK failed / Invalid argument`**
`notebooklm create` 的 Google 服务端端点偶发故障。此时已有 notebook 仍然可用（`-n <existing_id>` 能正常加源和生成）。用共享 notebook 策略绕过。

**`Unknown language code: zh-CN`**
NotebookLM 不支持 `zh-CN`，正确写法是 `zh_Hans`。

**`Generation failed - no artifact_id returned`**
`generate report` 的瞬态失败。重试即可，无需切换 notebook。

### 文件路径
Sub-agents 必须使用**绝对路径** `~/MyDoc/brain-vault/` 保存文件。不能缩写为 `~/brain-vault/`，不能自己创建子目录（如 `reports/`）。

正确：
```bash
notebooklm generate report -n <notebook_id>
notebooklm source add <URL> -n <notebook_id>
notebooklm download report <path> -n <notebook_id>
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

### 子任务路径陷阱（重要）
Delegated sub-agents 必须使用**绝对路径** `~/MyDoc/brain-vault/` 保存文件。不能缩写为 `~/brain-vault/`，不能自己创建子目录（如 `reports/`）。

正例：
```bash
notebooklm download report <path> -n <notebook_id>
# path 必须是 ~/MyDoc/brain-vault/文件名_总结.md 的展开绝对路径
```

反例：
```bash
~/brain-vault/xxx.md          # 写错目录，文件丢失
~/MyDoc/brain-vault/reports/  # 不能建子目录
```

验证方法：下载后立即 `ls -lh ~/MyDoc/brain-vault/` 确认文件存在。
