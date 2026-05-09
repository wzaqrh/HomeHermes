---
name: twitter-to-notebooklm-analysis
version: "1.0.0"
description: 将Twitter搜索结果抓取并上传到NotebookLM进行深度分析，生成结构化报告的完整流程
user-invocable: true
tags: ["research", "twitter", "notebooklm", "social-media", "analysis"]
---

# Twitter内容到NotebookLM分析技能

## 技能描述
将Twitter搜索结果抓取并上传到NotebookLM进行深度分析，生成结构化报告的完整流程。适用于社交媒体舆情分析、主题趋势研究等场景。

## 前置条件
1.  已安装`last30days`和`qiaomu-anything-to-notebooklm`技能
2.  已配置NotebookLM CLI认证（运行`notebooklm login`验证）
3.  系统中已安装Python 3.12+

## 完整工作流程

### 步骤1: 执行Twitter搜索
使用`last30days`技能搜索指定关键词，限定时间范围和平台：
```bash
cd /home/bdwillwin/.hermes/skills/research/last30days && /usr/bin/python3.12 scripts/last30days.py "YOUR_KEYWORD" --search=x --emit=compact --lookback-days=30
```

### 步骤2: 保存搜索结果为Markdown文件
将搜索结果整理为结构化Markdown格式，保存到临时目录：
```bash
cat > /tmp/twitter-search-results.md << 'EOF'
# Twitter搜索结果：[关键词]
日期范围：[开始日期]至[结束日期]
共找到[数量]条结果

## 主要内容集群：
...（整理搜索到的内容集群）

## 代表性推文：
...（整理代表性推文）
EOF
```

### 步骤3: 创建NotebookLM笔记本
```bash
notebooklm create "Twitter [关键词] 搜索分析"
```

### 步骤4: 切换到新建笔记本并上传源文件
```bash
notebooklm use [笔记本ID]
notebooklm source add /tmp/twitter-search-results.md --title "Twitter [关键词] 搜索结果"
```

### 步骤5: 生成分析报告
```bash
notebooklm generate report
```

### 步骤6: 等待并下载报告
```bash
notebooklm artifact wait [任务ID]
notebooklm download report -a [任务ID] /tmp/final-report.md --force
```

## 常见问题与解决方案

### 问题1: Python版本不兼容
**症状**: `last30days v3 requires Python 3.12+`
**解决方案**: 安装Python 3.12并指定使用:
```bash
# 安装Python 3.12
sudo apt update && sudo apt install -y software-properties-common
sudo add-apt-repository -y ppa:deadsnakes/ppa
sudo apt update && sudo apt install -y python3.12

# 使用Python 3.12运行last30days
/usr/bin/python3.12 scripts/last30days.py [参数]
```

### 问题2: NotebookLM CLI命令错误
**症状**: 找不到`download`命令或参数错误
**解决方案**: 查看帮助文档:
```bash
notebooklm --help
notebooklm download report --help
```

### 问题3: 认证失败
**症状**: `NotebookLM 认证失败`
**解决方案**: 重新登录认证:
```bash
notebooklm login
notebooklm list  # 验证认证成功
```

## 示例命令
```bash
# 搜索world model主题
/usr/bin/python3.12 scripts/last30days.py "world model" --search=x --emit=compact --lookback-days=30 > /tmp/twitter-world-model-results.md

# 创建笔记本
notebooklm create "Twitter World Model 搜索结果"

# 上传并生成报告
notebooklm use 1bf265b3-31fe-43ce-9c9c-a4c97ee93d65
notebooklm source add /tmp/twitter-world-model-results.md --title "Twitter World Model 搜索结果"
notebooklm generate report

# 下载报告
notebooklm download report -a afdfdc3f-4fb6-46d6-bb76-d33a7c3f2e0b /tmp/twitter-world-model-report.md --force
```

## 输出
最终会得到结构化的舆情分析报告，包含:
- 执行摘要
- 关键主题深度分析
- 重要引用与背景脈絡
- 行動洞察与建议