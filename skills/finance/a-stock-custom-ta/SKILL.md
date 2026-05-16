---
name: a-stock-custom-ta
description: 为A股编写自定义Python技术分析脚本，覆盖TradingAgents不支持的分析方法（斐波那契、量价统计、波动率分析等）。使用yfinance获取数据，保存结果到~/ta_reports/。当用户要求非标的专项分析时使用。
keywords: a股, python, yfinance, technical-analysis, fibonacci, volume-analysis, backtest, 自定义分析
version: 1.0.0
---

# A股自定义技术分析 (Custom TA)

## 何时使用（触发条件）

当用户要求的分析方法**不在** TradingAgents 原生支持范围内时使用：

- 斐波那契回调/扩展分析（长期/中期/短期多周期）
- 量价模式统计（放量阳线、放量阴线、缩量突破等）
- 自定义回测（信号 → 后续 N 日收益统计）
- 波动率分析（ATR、布林带、历史波动率分位）
- 形态识别（双底、头肩、三角整理等）
- K线组合统计（吞没、十字星、三乌鸦等）

不要用这个技能替代 TradingAgents — TradingAgents 做基本面+技术面+新闻综合评判时更好。
Custom TA 适合**用户明确要求某种特定技术方法**的场景。

## 前置条件

- `pip`: yfinance, numpy, pandas, matplotlib (mplfinance 可选)
- 输出目录: `~/ta_reports/` 已存在（不存在则 mkdir -p）

## 标准工作流

### 1. 分析设计

先明确：
- **分析目标**: 用户要什么？斐波那契？量价统计？回测？
- **周期跨度**: 长期(5y) / 中期(1y) / 短期(3mo)
- **数据粒度**: 1h/1d/1wk
- **输出需求**: 终端展示 + 文件保存

### 2. 脚本模式

统一模式：

```python
#!/usr/bin/env python3
import yfinance as yf, numpy as np, pandas as pd

# fetch
df = yf.download(ticker, period="5y", auto_adjust=True)
# handle MultiIndex columns from yfinance
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)
df = df.dropna(subset=["Open","High","Low","Close","Volume"])

# compute indicators / signals
# ...

# print formatted results + stats
# ...
```

### 3. 常见陷阱

| 陷阱 | 处理方式 |
|------|---------|
| yfinance 返回 MultiIndex columns | 拍平: `df.columns = df.columns.get_level_values(0)` |
| DatetimeIndex vs Date column | 用 `.idxmax().date()` 获取日期字符串, 勿假定有 'Date' 列 |
| 未来数据泄露 | 回测时确保信号只用截止到当天的数据，roll forward |
| 小时线数据有缺口（非交易时段） | 无需填充，但统计时要意识到缺失的 bars |
| Volume 为 0 的末期数据 | 最新几天成交量可能为 0 (未收盘)，判断放量时排除 |

### 4. 输出规范

```bash
# 直接打印到终端 + 保存到文件
python /tmp/analysis_script.py 2>&1 | tee ~/ta_reports/<TICKER>-<topic>.md
```

文件命名: `<TICKER>-<分析主题>.md`
  - 002299.SZ-斐波那契分析.md
  - 002299.SZ-放量阳线统计.md

### 5. 信号统计的回测规范

做信号回测时，严格做到：

1. **信号定义清晰**: 声明参数（放量倍数、阳线条件、过滤规则）
2. **样本量标注**: 每次统计都标出有效样本数
3. **多维输出**: 均值/中位数/胜率/最大收益/最大亏损/盈亏比/夏普
4. **位置区分**: 高位信号和低位信号的后续表现通常截然不同，按均线位置分层统计
5. **免责声明**: 报告末尾标注"仅供研究参考，不构成投资建议"

## 参考文件

- `references/fibonacci-methodology.md` — 斐波那契多周期分析的方法论和代码模板
- `references/volume-signal-backtest.md` — 量价信号回测的方法论和代码模板
