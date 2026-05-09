---
name: youtube-summary-save-to-home
category: media
description: 从YouTube视频链接生成Markdown总结并保存到用户的home目录
---

# YouTube视频总结保存到Home目录技能

## 触发条件
当用户需要将YouTube视频内容精化为Markdown格式并保存到home目录时使用。

## 操作步骤
1. 提取YouTube视频ID：从链接中提取`youtu.be/`后的部分或`v=`参数值
2. 调用`media/youtube-content`技能获取视频的详细总结（包含元数据、核心内容、关键观点等）
3. 将总结内容整理为标准Markdown格式
4. 将内容写入以`youtube_<视频ID>_summary.md`命名的文件
5. 将文件保存到用户的home目录（`~/`路径）
6. 向用户反馈文件保存路径和简要内容说明

## 示例流程
输入：`https://youtu.be/yOTP8utTOBU?si=wO1EgBp3CmosLX6R`
1. 提取视频ID：`yOTP8utTOBU`
2. 调用`media/youtube-content`获取总结
3. 生成文件：`~/youtube_yOTP8utTOBU_summary.md`

## 注意事项
- 需确保`media/youtube-content`技能已正确安装并配置
- 需确认用户对home目录有写入权限
- 若视频无法访问，需提前处理平台访问限制（如代理、换网络）