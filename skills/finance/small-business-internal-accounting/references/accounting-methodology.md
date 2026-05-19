# Internal Accounting Methodology for Small Medical Aesthetics Business (医美诊所内账)

## File Structure Convention

### Income File (收银记录表)
- Sheet name: 收银记录表
- Row 1-2: Headers (merged cells common)
- Row 3: Summary totals
- Row 4+: Individual transactions

Key columns:
- 已收金额 = full invoice amount (including deposit consumption)
- 实收金额总计 = actual cash/card received
- 预存款支付总计 = deposit balance used
- 成本 = product/service cost (COGS per item)
- 手续费 = transaction fees
- 利润 = 已收金额 - 成本 - 手续费

### Expense File (支出明细)
- Each month is a separate sheet named by date (e.g., 2025.11, 2025.12)
- Single "前期装修费" sheet for pre-opening renovation costs
- Layout uses 4 column groups horizontally:
  - Col A-C: 材料支出 (Material)
  - Col D: 经手人 (Handler)
  - Col E-G: 工资支出 (Salary)
  - Col H-J: 房租水电 (Rent/Utilities)
  - Col K-M: 设计费 (Design/Other)
- Row 1 = totals, Row 3 = headers
- Empty Sheet4 often exists as a journal template

## Expense Classification Rules

Critical for accurate P&L. Use these heuristics:

### 1. Equipment (设备购置 → Fixed Assets)
- Medical devices: 科英光子, 雾光炮 (>30,000)
- Treatment machines: 热玛吉, 超声王
- Large office equipment: 苹果一体机, 电视机
- → NOT in P&L. Note as asset acquisition.

### 2. Inventory (库存进货 → Current Assets)
- Keywords: 进货, 货款, 进货款
- Products: 乔雅登, 保妥适, 嗨体, 弗曼胶原, 衡力, etc.
- Format varies: "商品名+进货" or "商品名+货款"
- → NOT in P&L. These become COGS gradually via the income system.

### 3. Consumables (日常耗材 → Period Expense)
- Small supplies: 面膜, 手套, 针头, 化妆棉
- Office: 打印纸, 笔, 文件盒
- Daily: 水, 纸巾, 清洁用品
- → In P&L as operating expense.

### 4. Salary (工资 → Period Expense)
- Employee wages, bonuses
- Social insurance (社保扣费)
- Tax withholdings (个人所得税)
- Accommodation, travel reimbursement for doctors
- → In P&L.

### 5. Rent/Utilities (房租水电 → Period Expense)
- Store rent, property fees
- Electricity, water
- Broadband/internet
- Medical waste disposal
- → In P&L.

## P&L Structure Template

```
一、营业收入                    XX,XXX   100%
  减：产品成本 (COGS)           X,XXX     X%
  减：手续费                    XXX      X%
= 毛  利                       XX,XXX    XX%

二、期间费用
  日常耗材/办公                 X,XXX     X%
  工资及社保                   XX,XXX    XX%
  房租水电                     X,XXX     X%
  期间费用合计                  XX,XXX    XX%

三、净利润                      X,XXX     X%

【备注明细】
* 设备购置（未计入）：科英光子82,000元（固定资产，分期折旧）
* 库存进货（未计入）：50,074元（存货，随消耗计入COGS）
```

## Key Accounting Decisions for This Client

1. **开业首月亏损正常** - November 2025 was the first operating month. The clinic had heavy one-time procurement costs (科英光子 82,000, first batch inventory 50,000+). The operating P&L showed a manageable loss of ~23,561.

2. **毛利率判断** - 73.6% gross margin is healthy for medical aesthetics. Most profitable items: 雾光炮 (100%), 保妥适单部位 (90%), 爱拉丝提 (92%). Low margin: 弗曼胶原 (42%), 瑞蓝唯瑅 (33%).

3. **品牌/渠道成本** - The 顾问 system (郑洁 vs 方林瑞) data is useful but the allocation was skewed (郑洁 handled most high-value customers).

## Output Quality Checklist

- [ ] P&L properly separates CAPEX from OPEX
- [ ] Notes explain any large one-time items
- [ ] Revenue detail has all individual transactions
- [ ] Expense detail color-coded by category
- [ ] Project margin analysis with color-coded profitability
- [ ] Consultant performance if available
- [ ] Dashboard summary for quick reference
