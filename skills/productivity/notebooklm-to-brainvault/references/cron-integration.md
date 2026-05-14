# Cron 集成说明

## 与 youtubd 的 flush 配合

NotebookLM 可以通过 youtubd 的 `flush` 命令批量处理 todolist：

```bash
# cron 任务中：
python3 ~/.hermes/skills/media/youtubd/scripts/manage.py cron        # fetch + 加权随机抽 N 条
# 读取 ~/.hermes/skills/media/youtubd/todolist.txt
# 对每个 URL 逐个走 NotebookLM 流程
# 处理完后清空 todolist.txt
```

## /cron add 配置

```bash
/cron add "youtubd 每日拉取+总结" \
  --schedule "0 9 * * *" \
  --model '{"model":"deepseek-v4-flash","provider":"deepseek"}' \
  --skills youtubd,notebooklm-to-brainvault \
  --toolsets terminal,file,web \
  --prompt "1. manage.py cron 2. 读 todolist → NotebookLM 逐个处理 → 存 brain-vault 3. 清空 todolist"
```

## 关键注意事项

1. **必须指定 `--model`** — 否则 cron 调度器读不到 API key
2. **必须指定 `--skills`** — 否则 agent 没有对应 skill 的上下文
3. **必须指定 `--toolsets`** — 需要 terminal + file 才能执行命令和写文件
4. **子任务路径陷阱** — 所有文件必须保存到 `~/MyDoc/brain-vault/`，不能写成 `~/brain-vault/` 或加子目录
