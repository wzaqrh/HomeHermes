---
name: notebooklm-youtube-summary-classification
description: 使用NotebookLM CLI总结YouTube视频并按分类文件夹保存的完整流程，支持新闻总结和阅读笔记分类存储
user-invocable: true
---

# YouTube视频总结与分类保存技能

## 适用场景
需要将YouTube视频内容总结为报告，并按「新闻总结」或「阅读笔记」分类保存到NotebookLM笔记本中。

## 前置条件
1. 已安装并配置NotebookLM CLI
2. 已创建分类笔记本文件夹（默认已创建两个标准文件夹）

## 标准分类文件夹
| 文件夹名称 | 笔记本ID | 适用场景 |
|-----------|---------|----------|
| 新闻总结文件夹 | f316c9e8-481b-48e5-a4c2-596f32434c08 | 新闻资讯、时事分析类视频总结 |
| 阅读笔记文件夹 | b6c961a4-e32d-4641-9a8b-33e137865d8e | 深度阅读、学术研究、技术分析类视频总结 |

## 完整执行流程

### 步骤1：切换到目标分类文件夹
根据总结内容类型，切换到对应的笔记本文件夹：
```bash
# 切换到新闻总结文件夹
notebooklm use f316c9e8-481b-48e5-a4c2-596f32434c08

# 切换到阅读笔记文件夹
notebooklm use b6c961a4-e32d-4641-9a8b-33e137865d8e
```

### 步骤2：添加YouTube视频源
将YouTube视频添加到当前笔记本：
```bash
notebooklm source add https://www.youtube.com/watch?v=VIDEO_ID
```

### 步骤3：生成总结报告
启动NotebookLM生成报告任务：
```bash
notebooklm generate report
```

### 步骤4：等待任务完成
获取任务ID并等待报告生成完成：
```bash
# 查看任务列表，获取任务ID
notebooklm artifact list

# 等待任务完成
notebooklm artifact wait <task_id>
```

### 步骤5：下载报告到本地
将生成的报告下载到指定路径，按分类命名：
```bash
# 新闻总结类命名格式
notebooklm download report --artifact <task_id> /tmp/news_summary_视频标题.md

# 阅读笔记类命名格式
notebooklm download report --artifact <task_id> /tmp/reading_note_视频标题.md
```

### 步骤6（可选）：归档本地报告到笔记本
将本地生成的报告文件添加到笔记本进行永久归档：
```bash
notebooklm source add /tmp/本地报告路径 --title "报告标题"
```

## 快速命令模板

### 新闻总结快速流程
```bash
notebooklm use f316c9e8-481b-48e5-a4c2-596f32434c08
notebooklm source add https://www.youtube.com/watch?v=8p_Pdho_cq4
notebooklm generate report
notebooklm artifact wait $(notebooklm artifact list | grep -A1 "completed" | tail -n1 | awk '{print $1}')
notebooklm download report --artifact $(notebooklm artifact list | grep -A1 "completed" | tail -n1 | awk '{print $1}') /tmp/news_summary_youtube.md
```

### 阅读笔记快速流程
```bash
notebooklm use b6c961a4-e32d-4641-9a8b-33e137865d8e
notebooklm source add https://www.youtube.com/watch?v=P2c9g75O2rs
notebooklm generate report
notebooklm artifact wait $(notebooklm artifact list | grep -A1 "completed" | tail -n1 | awk '{print $1}')
notebooklm download report --artifact $(notebooklm artifact list | grep -A1 "completed" | tail -n1 | awk '{print $1}') /tmp/reading_note_youtube.md
```

## 常见问题与解决方案
1.  **任务卡住**：使用`notebooklm artifact list`查看任务状态，超时可重新提交生成任务
2.  **无法识别YouTube链接**：确认链接格式正确，或使用`notebooklm source add --help`查看参数
3.  **分类文件夹切换失败**：使用`notebooklm list`确认笔记本ID是否正确
