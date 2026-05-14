# youtubd 命令参考

所有命令通过 `scripts/manage.py` 执行：

## 频道管理
```
subscribe 分类 频道名    订阅频道（权重默认3）
unsubscribe 频道名/ID    取消订阅
weight 频道名/ID <1-5>   设置权重
list                     列出所有订阅 + 未处理数
```

## 数据采集
```
fetch [分类]   拉取频道最新视频到 history + todolist
loadlist [路径] 从txt导入视频（每行一个URL或ID，默认 todolist.txt）
search 关键词 N 搜索YouTube视频（输出标准化JSON）
```

## 处理与标记
```
mark 视频ID     标记 history 中为 processed
new [分类]      列出未处理的视频
flush           处理 todolist 全部条目 → 输出JSON → 清空
```

## 定时任务
```
cron    按 cron_task.json 配置：fetch → 加权随机抽取 → 追加到 todolist
stats   统计总览
```
