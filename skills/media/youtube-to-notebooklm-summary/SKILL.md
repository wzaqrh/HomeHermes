---
name: youtube-to-notebooklm-summary
description: 直接通过NotebookLM CLI生成YouTube视频总结报告的简化流程，解决qiaomu-anything-to-notebooklm主脚本的输入解析问题
user-invocable: true
---

# YouTube视频 → NotebookLM 总结报告简化流程

当`qiaomu-anything-to-notebooklm`主脚本无法处理YouTube视频链接时，可以使用以下直接命令流程完成总结：

## 前置条件
1. 已安装并登录NotebookLM CLI：`notebooklm login`
2. 已验证认证状态：`notebooklm list`

## 执行步骤

### 1. 添加YouTube视频源到NotebookLM
```bash
notebooklm source add https://www.youtube.com/watch?v=8p_Pdho_cq4
```

### 2. 生成总结报告
选择需要的输出格式，例如生成详细报告：
```bash
notebooklm generate report
```

支持的其他格式：
- `audio`: 生成播客音频
- `slide-deck`: 生成PPT幻灯片
- `mind-map`: 生成思维导图
- `quiz`: 生成测试题目

### 3. 等待生成任务完成
获取任务ID并等待：
```bash
notebooklm artifact wait <task_id>
```

### 4. 下载生成的文件
将报告下载到指定路径：
```bash
notebooklm download report /tmp/youtube_summary.md
```

## 示例
```bash
# 1. 添加视频源
notebooklm source add https://www.youtube.com/watch?v=8p_Pdho_cq4

# 2. 生成报告
notebooklm generate report

# 3. 等待任务完成
notebooklm artifact wait 05ea5440-832e-45d6-9c97-16e0b57c525c

# 4. 下载报告
notebooklm download report /tmp/youtube_news_summary.md
```

## 故障排查
1. **认证失败**：运行`notebooklm login`重新登录
2. **任务卡住**：使用`notebooklm artifact list`查看任务状态
3. **文件权限问题**：确保临时目录可写：`chmod 755 /tmp`
