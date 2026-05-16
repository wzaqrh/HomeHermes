# 量价信号回测 — 方法论文档

## 适用场景

用户要求统计某种量价模式（如"放量阳线"、"放量突破"、"缩量回调"）的历史表现，包括胜率、平均收益、最佳/最糟情景。

## 核心思路

1. 定义信号规则（量+K线形态条件）
2. 遍历历史数据，标记每个信号日
3. 对每个信号日，计算后续 N 个交易日的收益
4. 汇总统计

## 信号定义参数

### 量条件

```
放量 threshold = 1.5× MA20_volume   # 常规放量
巨量 threshold = 2.5× MA20_volume   # 极端放量
缩量 threshold = 0.7× MA20_volume   # 缩量
```

### K线形态条件

```
阳线: close > open
阴线: close < open
十字星: |close - open| / (high - low) < 0.3
实体阳线: close > open AND body/range >= 0.3  # 过滤十字线
```

### 组合信号举例

| 信号 | 条件 |
|------|------|
| 放量阳线 | close > open AND vol ≥ 1.5×MA20vol AND body/range ≥ 0.3 |
| 放量突破 | close > 前N日高点 AND vol ≥ 2×MA20vol |
| 缩量回调 | close < open AND vol ≤ 0.7×MA20vol |
| 放量阴线 | close < open AND vol ≥ 1.5×MA20vol |

## 统计指标

对每个观察窗口 (1/3/5/10/20/60个交易日)，计算：

| 指标 | 含义 |
|------|------|
| 样本数 | 有效信号数量（排除数据不足的尾部） |
| 平均收益 | 所有样本收益的算术平均 |
| 中位数收益 | 抗异常值的中心趋势 |
| 胜率 | 收益 > 0 的样本占比 |
| 最大收益 | 最好的一次 |
| 最大亏损 | 最差的一次 |
| 夏普(日) | 均值 / 标准差，衡量风险调整后收益 |
| 盈亏比 | 平均盈利 / 平均亏损绝对值 |
| >+5% 次数 | 大赚交易数 |
| >+10% 次数 | 暴赚交易数 |
| <-5% 次数 | 大亏交易数 |

## 位置分层

信号在不同位置的表现通常天差地别。必须按以下维度分层：

### 均线位置

```
above_ma20 = close > MA20   # 短期趋势向上
above_ma50 = close > MA50   # 中期趋势向上
above_ma200 = close > MA200  # 长期趋势向上
```

### 价格区间

```
低位: price < 历史20%分位   # 低估区
中位: 价格在20%-80%分位    # 合理区
高位: price > 历史80%分位   # 高估区
```

### 经典现象

- **低位放量阳线**: 常见于底部启动，后续60日胜率>70%，平均收益>+10%
- **高位放量阳线**: 常是拉高出货，后续1个月内下跌概率大
- **均线多头排列+放量阳线**: 趋势强化信号
- **均线空头排列+放量阳线**: 可能是反弹诱多，谨慎

## 代码模板关键片段

```python
import yfinance as yf
import numpy as np
import pandas as pd

df = yf.download(ticker, period="5y", auto_adjust=True)
if isinstance(df.columns, pd.MultiIndex):
    df.columns = df.columns.get_level_values(0)

# 均量
df["MA20_vol"] = df["Volume"].rolling(20).mean()

# 信号
candle_range = df["High"] - df["Low"]
body_ratio = (df["Close"] - df["Open"]).abs() / candle_range.replace(0, np.nan)

signal = (
    (df["Close"] > df["Open"])                    # 阳线
    & (df["Volume"] >= 1.5 * df["MA20_vol"])      # 放量
    & (body_ratio >= 0.3)                          # 实体有意义
)

# 遍历信号
for d in df.index[signal]:
    idx = df.index.get_loc(d)
    entry = float(df.iloc[idx]["Close"])
    for n in lookahead_days:
        if idx + n < len(df):
            ret = (df.iloc[idx + n]["Close"] - entry) / entry * 100
            # record ret
```

## 输出格式

1. 总览: 总交易日数, 信号数, 信号频率
2. 每次信号详情表: 日期 | 价格 | 当日涨幅 | 量比 | +1d | +3d | +5d | +10d | +20d | +60d
3. 汇总统计表: 每个N日窗口的均值/胜率/盈亏比/最大收益/最大亏损
4. 分层统计: 高位 vs 低位信号的分组统计
5. 最近N次信号的表现
