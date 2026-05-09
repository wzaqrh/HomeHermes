---
name: arxiv-search-tips
description: 针对arXiv搜索的实用技巧和注意事项
version: 1.0.0
author: Hermes Agent
license: MIT
metadata:
  hermes:
    tags: [Research, Arxiv, Tips, Tricks]
    related_skills: [arxiv]
---

# arXiv搜索实用技巧

## 常见问题与解决方案
1.  **编码问题**：arXiv API对非英文关键词（如中文）可能存在编码解析问题，建议使用英文关键词进行搜索以获得最佳结果。
2.  **主题覆盖限制**：arXiv以物理学、数学、计算机科学等学科为主，经济学、金融等社会科学领域的预印本数量相对较少。如果搜索高油价溢出效应这类经济学主题，结果可能不够全面，建议结合Google Scholar、Web of Science、SSRN等专业学术数据库使用。
3.  **精准搜索建议**：
    - 高油价溢出效应相关的精准英文关键词：`oil price spillover effects`, `macroeconomic impact of high oil prices`, `volatility transmission from oil markets`, `oil price shocks and international spillover`
4.  **命令调试**：如果单行shell命令出现引号或语法解析错误，建议先将代码写入Python文件再执行，避免shell的特殊字符解析问题。