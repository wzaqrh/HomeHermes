# 批量处理管道：youtubd flush

当有多个视频要处理时，推荐启动 `manage.py flush` 后台进程，而非手动逐个处理。

## 触发方式
```bash
# 将未处理视频 id/url 写入 todolist.txt
python3 ~/.hermes/skills/media/youtubd/scripts/manage.py cron

# 后台启动全自动串行处理
nohup python3 ~/.hermes/skills/media/youtubd/scripts/manage.py flush &
```

## flush 会做什么
1. 逐行读取 todolist.txt 的 URL
2. 逐个串行：
   - 创建 Notebook
   - 添加 YouTube 源
   - `notebooklm generate report`（含耐心等待重试 15/30/60min）
   - 下载到 `~/MyDoc/brain-vault/`
   - 标记 history 中 processed=true
3. 全部完成后清空 todolist.txt

## 与手动处理的区别
| 维度 | manual | flush |
|------|--------|-------|
| 处理方式 | Agent 逐个调用工具 | Python 脚本全自动 |
| 并发 | 串行 | 串行 |
| 配额等待 | 需 Agent 等待 | 脚本内部 sleep |
| 超时限制 | 600s 单次工具调用 | 无限制（后台进程） |
| 进度 | 实时可见 | 完成后一次性看到 |
