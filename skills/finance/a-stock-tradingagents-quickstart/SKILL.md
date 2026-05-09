---
name: a-stock-tradingagents-quickstart
description: 国内A股股票快速分析技能（基于TradingAgents框架），适配深市/沪市股票代码，支持DeepSeek LLM，包含实时数据失败时的理论分析fallback方案
keywords: a股, tradingagents, stock-analysis, deepseek, 浅度分析
version: 1.0.0
---

# A股TradingAgents快速分析技能

## 概述
本技能针对国内A股市场（股票代码后缀.SS/.SZ）优化，基于TradingAgents框架实现快速股票分析，支持基本面、技术面、新闻面分析，默认使用DeepSeek LLM，当实时数据API缺失时自动生成基于公开资料的理论分析报告。

## 前置条件
1.  已安装TradingAgents框架到`/home/bdwillwin/agents/TradingAgents`
2.  已配置DeepSeek API密钥到环境变量`DEEPSEEK_API_KEY`或`~/.bashrc`
3.  分析结果默认保存到`~/feushu`目录，符合用户约束

## 快速使用方式

### 方式一：直接运行脚本
```bash
cd ~/feushu
python a-stock-tradingagents-quickstart.py <股票代码>
# 示例：分析恒瑞医药
python a-stock-tradingagents-quickstart.py 600276
# 示例：分析迈瑞医疗
python a-stock-tradingagents-quickstart.py 300760
```

### 方式二：Python API调用
```python
from a_stock_tradingagents_quickstart import run_a_stock_analysis
result = run_a_stock_analysis("600276")
print(result)
```

## 核心功能
1.  **A股代码适配**：自动添加.SS/.SZ后缀，支持沪市/深市股票
2.  **DeepSeek LLM配置**：显式设置llm_provider为deepseek，自动加载环境变量密钥
3.  **多维度分析**：支持基本面、技术面、新闻面分析
4.  **浅度分析优化**：默认1轮辩论，快速输出结果
5.  **实时数据fallback**：当Alpha Vantage API缺失时，自动生成基于公开资料的理论分析报告
6.  **结果规范保存**：自动将分析结果保存到`~/feushu`目录

## 分析流程
1.  加载环境变量中的DeepSeek API密钥
2.  初始化TradingAgents框架，配置为浅度分析、中文输出
3.  自动添加股票代码后缀（.SS/.SZ）
4.  尝试实时分析，若失败则生成理论分析报告
5.  保存结果到`~/feushu/<股票代码>.SZ-analysis.md`或`~/feushu/<股票代码>.SS-analysis.md`
6.  返回分析结果摘要

## 典型参数配置
```python
config = {
    "llm_provider": "deepseek",
    "deep_think_llm": "deepseek-chat",
    "quick_think_llm": "deepseek-chat",
    "max_debate_rounds": 1,  # 浅度分析
    "output_language": "Chinese",
    "data_vendors": {
        "fundamental_data": "yfinance",
        "technical_indicators": "yfinance",
        "news_data": "yfinance"
    }
}
```

## 故障排除
1.  **API密钥缺失**：检查`~/.bashrc`是否配置了`export DEEPSEEK_API_KEY=你的密钥`
2.  **实时数据失败**：自动切换为理论分析，不影响结果生成
3.  **依赖问题**：确保TradingAgents框架已正确安装

## 注意事项
- 本技能生成的分析报告仅用于学术研究，不构成投资建议
- 实时数据API需要Alpha Vantage密钥，若未配置则自动使用fallback方案
- 所有结果均保存到`~/feushu`目录，符合用户的文件写入约束