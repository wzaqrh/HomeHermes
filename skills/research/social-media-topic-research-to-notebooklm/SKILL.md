---
name: social-media-topic-research-to-notebooklm
category: research
description: 从指定社交媒体平台抓取指定时间范围的话题内容，导入NotebookLM生成结构化深度分析报告的完整工作流
trigger: 需要对社交媒体话题进行批量分析、生成专业报告时使用
---

# 社交媒体话题研究与NotebookLM分析工作流

## 触发条件
当需要对Twitter/X、B站、YouTube等平台的指定话题进行批量内容抓取，并生成深度分析报告时使用。

## 前置准备
1.  确保已安装并配置`last30days-skill`（30天社交媒体话题搜索工具）
2.  已完成目标社交媒体平台的认证配置（如Twitter的AUTH_TOKEN、CT0）
3.  确保NotebookLM可访问抓取的内容或已准备好导入的文本数据

## 执行步骤
1.  使用`last30days-skill`搜索指定关键词、时间范围的社交媒体内容，保存结果为文本文件
2.  提取搜索结果中的核心内容，整理为NotebookLM可导入的格式
3.  将整理后的内容上传至NotebookLM，启动分析任务
4.  从NotebookLM导出分析报告，整理为结构化的Markdown文档
5.  可选：将报告保存至指定目录（如`/tmp/`或用户指定路径）

## 常见陷阱
1.  注意社交媒体平台的IP风控限制，需确保使用合法代理或合规网络
2.  部分平台的内容抓取可能受版权限制，仅可用于非商业性分析
3.  确保NotebookLM的导入格式符合要求（通常为纯文本或Markdown格式）

## 验证步骤
1.  运行`last30days-skill`测试搜索关键词，确认可获取有效内容
2.  导入小批量测试内容至NotebookLM，确认分析流程正常
3.  生成测试报告，检查内容完整性与准确性