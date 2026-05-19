# manage.py 全自动管道参考

## flush 命令

全自动串行处理 todolist。推荐后台运行。

```bash
nohup python3 ~/.hermes/skills/media/youtubd/scripts/manage.py flush > ~/flush.log 2>&1 &
```

### 行为流程

1. 读取 todolist.txt 所有视频（每行一个 URL）
2. **串行**逐个处理（禁止并行，禁止 delegate_task）
3. 每个视频：
   a. `notebooklm create "flush-{vid}"` → 记 notebook_id
   b. `notebooklm source add <URL> -n <id>` → 添加 YouTube 源
   c. `notebooklm generate report -n <id>` → 生成报告
   d. 成功 → 提取 artifact_id → `artifact wait` → `download report` 到 brain-vault
   e. 失败（配额限制）→ **耐心等待模式**
4. 标记 processed → 清理 Notebook → 下一个

### 耐心等待模式

`generate report` 遇到 Google 配额限制时的重试策略：

| 尝试次数 | 等待时间 | 策略 |
|----------|----------|------|
| 第1次 | 15min (900s) | `time.sleep(900)` |
| 第2次 | 30min (1800s) | `time.sleep(1800)` |
| 第3~16次 | 60min (3600s) | `time.sleep(3600)` |
| 第17次 | - | 改用 `notebooklm ask` |

其他非配额错误（如网络瞬断）：等 10 秒后重试。

### 强制覆盖模式

`flush` 和 `cron` 启动时自动调用 `kill_previous_flush()`：
- 查找所有 `python3.*manage.py.*(flush|cron)` 进程
- 干掉除自己以外的同类进程
- 保证同一时间只有一个在跑

### 文件路径

所有报告保存到 `~/MyDoc/brain-vault/`，文件名格式：
`{channel}_{title前30字}_总结.md`

## cron 命令

加权随机抽取，只拉取最新视频写入 todolist，**不处理 NotebookLM**（那是 flush 的事）。

```bash
python3 ~/.hermes/skills/media/youtubd/scripts/manage.py cron
```
