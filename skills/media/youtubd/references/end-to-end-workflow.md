# youtubd 端到端工作流

## 首次使用

```bash
# 1. 订阅频道
python3 ~/.hermes/skills/media/youtubd/scripts/manage.py subscribe 读书 魏知超
python3 ~/.hermes/skills/media/youtubd/scripts/manage.py subscribe 科技 最佳拍档

# 2. 设置权重
python3 ~/.hermes/skills/media/youtubd/scripts/manage.py weight "魏知超" 4

# 3. 拉取最新视频
python3 ~/.hermes/skills/media/youtubd/scripts/manage.py fetch

# 4. 查看待处理
python3 ~/.hermes/skills/media/youtubd/scripts/manage.py new

# 5. 用 NotebookLM 逐个处理视频（由 agent 完成）
# notebooklm create → source add → generate report → download → mark
```

## 日常使用

```bash
# 拉取新视频
manage.py fetch
# 或（按 cron_task.json 配置）
manage.py cron

# 查看待处理
manage.py new

# 批量处理所有待办 → 输出JSON → 清空
manage.py flush
```

## 外部列表导入

```bash
# 从外部 txt 文件导入（每行一个URL或11位ID）
manage.py loadlist ~/youtube_todo.txt

# 同样支持默认 todolist.txt
manage.py loadlist
```

## 定时任务设置

```bash
/cron add "youtubd 每日拉取+总结" \
  --schedule "0 9 * * *" \
  --model '{"model":"deepseek-v4-flash","provider":"deepseek"}' \
  --skills youtubd,notebooklm-to-brainvault \
  --toolsets terminal,file,web \
  --prompt "1. manage.py cron 2. 读 todolist → NotebookLM 逐个处理 → 存 brain-vault 3. 清空 todolist"
```
