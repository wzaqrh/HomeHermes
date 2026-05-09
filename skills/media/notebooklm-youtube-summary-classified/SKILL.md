---
name: notebooklm-youtube-summary-classified
description: 基于NotebookLM CLI的YouTube视频分类总结技能，支持将总结内容自动分类保存到不同文件夹
user-invocable: true
homepage: https://github.com/your-repo/notebooklm-youtube-summary-classified
---

# YouTube视频分类总结工作流

## 概述
本技能提供了一套完整的基于NotebookLM CLI的YouTube视频总结流程，支持将不同类型的总结内容自动分类保存到指定文件夹。

## 前置条件
1. 已安装并配置NotebookLM CLI
2. 已完成NotebookLM账号登录（`notebooklm login`）
3. 系统可正常访问YouTube并提取字幕

## 标准工作流程

### 1. 创建分类文件夹
```bash
# 创建新闻总结文件夹
notebooklm create "新闻总结文件夹"

# 创建阅读笔记文件夹
notebooklm create "阅读笔记文件夹"
```

### 2. 切换到目标分类文件夹
```bash
# 切换到阅读笔记文件夹
notebooklm use <阅读笔记文件夹ID>
```

### 3. 添加YouTube视频源
```bash
notebooklm source add https://www.youtube.com/watch?v=VIDEO_ID
```

### 4. 生成总结报告
```bash
# 生成通用总结报告
notebooklm generate report
```

### 5. 等待任务完成
```bash
notebooklm artifact wait <任务ID>
```

### 6. 下载并保存报告
```bash
# 下载到指定路径
notebooklm download report --artifact <任务ID> /path/to/save/filename.md
```

## 分类管理规则
- 📁 **新闻总结文件夹**：用于存放时事新闻、事件分析类视频总结
- 📁 **阅读笔记文件夹**：用于存放深度解读、学术分析、专业知识类视频总结

## 快速使用示例

### 快速创建新闻总结
```bash
# 切换到新闻文件夹
notebooklm use f316c9e8-481b-48e5-a4c2-596f32434c08

# 添加视频源
notebooklm source add https://www.youtube.com/watch?v=8p_Pdho_cq4

# 生成并保存报告
notebooklm generate report
notebooklm artifact wait <task-id>
notebooklm download report --artifact <task-id> /tmp/news_summary_$(date +%Y%m%d).md
```

### 快速创建阅读笔记
```bash
# 切换到阅读笔记文件夹
notebooklm use b6c961a4-e32d-4641-9a8b-33e137865d8e

# 添加视频源
notebooklm source add https://www.youtube.com/watch?v=P2c9g75O2rs

# 生成并保存报告
notebooklm generate report
notebooklm artifact wait <task-id>
notebooklm download report --artifact <task-id> /tmp/reading_note_$(date +%Y%m%d).md
```

## 故障排查
1. **视频无法添加**：检查网络连接和YouTube链接格式
2. **生成任务失败**：使用`notebooklm artifact list`查看任务状态
3. **下载失败**：检查目标路径是否存在且有写入权限

## 版本历史
- v1.0.0 (2026-04-22): 初始版本，包含完整分类总结流程
