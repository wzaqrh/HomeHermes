---
name: small-business-internal-accounting
description: >-
  Generate professional internal accounting reports (内账) from raw Excel data for small
  businesses. Parses income (收银记录) and expense (支出明细) xlsx files, produces multi-sheet
  Excel output with P&L, revenue details, expense classification, project margin analysis,
  and consultant performance.
trigger:
  - The user provides xlsx files with business income and expense data and asks for internal accounting
  - The user says "帮我做个内账" or "做账"
  - The user needs a P&L statement, revenue analysis, or expense breakdown from Excel data
---

# Small Business Internal Accounting (内账)

Generate professional internal accounting reports from raw Excel data for small businesses.

## Workflow

### Step 1: Parse all source files

Use `openpyxl` with `data_only=True` to read xlsx files. Read ALL sheets in each file to understand structure.

```python
import openpyxl
wb = openpyxl.load_workbook(path, data_only=True)
```

### Step 2: Understand the data structure

**Income file (收银记录表) typically has:**
- Columns: 序号, 顾客姓名, 收银单日期, 已收金额, 实收金额总计, 预存款支付总计, 收银单号, 项目名称, 数量, 成本, 手续费, 利润, 所属顾问
- Row 3 often has summary totals
- Data starts from row 4

**Expense file (支出明细) typically has:**  
- Columns grouped by category: 材料支出, 工资支出, 房租水电, 设计费
- Row 1: summary totals
- Row 3: headers
- Data from row 4 onwards

### Step 3: Classify expenses properly (CRITICAL)

This is the most important step for accurate P&L. Separate expenses into:

1. **日常耗材/办公用品 (Consumables)** - period expenses, go to P&L
2. **工资社保 (Salary/Insurance)** - period expenses, go to P&L  
3. **房租水电 (Rent/Utilities)** - period expenses, go to P&L
4. **进货/货款 (Inventory purchases)** - capitalised as assets, NOT period expenses
5. **设备购置 (Equipment)** - capitalised as fixed assets, NOT period expenses
6. **手续费 (Transaction fees)** - period expenses, go to P&L

**Classification heuristic:**
```python
inventory_keywords = ['进货', '货款', '进货款']
equipment_keywords = [...]  # known device names + high-value items

for e in material_expenses:
    item = e['item']
    if any(k in item for k in inventory_keywords):
        inventory_purchases.append(e)
    elif e['amount'] > 30000 and ('设备关键词' in item):
        equipment_purchases.append(e)
    else:
        consumables.append(e)
```

> **Pitfall:** Many raw expense sheets lump inventory purchases (进货) with daily consumables. If you expense 50,000+ of inventory purchases all in one month, the P&L will show a huge artificial loss. Always separate inventory.

### Step 4: Build P&L statement

```
营业收入 (Revenue)
  减: 产品成本 (COGS from income sheet)
  减: 手续费 (Transaction fees)
= 毛利 (Gross Profit)
  减: 日常耗材 (Consumables)
  减: 工资社保 (Salary & Insurance)  
  减: 房租水电 (Rent & Utilities)
  减: 设计/其他 (Other period expenses)
= 净利润 (Net Profit/Loss)
```

Note: Equipment and inventory purchases are listed as notes/備註, not in the P&L body.

### Step 5: Generate multi-sheet Excel

Create these sheets using `openpyxl`:

| Sheet | Content |
|-------|---------|
| 利润表 | P&L with ratios and notes |
| 收入明细 | All revenue line items |
| 支出明细 | All expenses with category coloring |
| 项目毛利分析 | Product/service margin ranking |
| 顾问业绩 | Sales consultant performance |
| 收支总览 | Dashboard summary |

### Step 6: Style the output

```python
from openpyxl.styles import Font, Alignment, Border, Side, PatternFill

# Colors
header_fill = PatternFill(start_color='2F5496', end_color='2F5496', fill_type='solid')
loss_fill = PatternFill(start_color='FCE4EC', end_color='FCE4EC', fill_type='solid')
profit_fill = PatternFill(start_color='E8F5E9', end_color='E8F5E9', fill_type='solid')
inventory_fill = PatternFill(start_color='FFF3E0', end_color='FFF3E0', fill_type='solid')
equip_fill = PatternFill(start_color='E3F2FD', end_color='E3F2FD', fill_type='solid')

# Conditional margin formatting
if margin >= 80: fill = green
elif margin >= 50: fill = yellow  
elif margin >= 0: fill = red
else: fill = dark_red
```

## Verification

- Total revenue should equal sum of all individual rows
- Gross profit = Revenue - COGS (from income sheet)
- Period expenses = consumables + salary + rent + transaction fees + other
- Net profit/loss should be explained in notes (one-time items, startup phase, etc.)
- Equipment + inventory total should be listed separately as assets

## Pitfalls

- **Double-counting costs:** Income sheet already has a 成本 (COGS) column per transaction. Do NOT double-count inventory purchases on top of that.
- **First-month losses are normal:** New businesses often have heavy upfront costs (装修, 设备, 首批进货). Note this clearly in the output.
- **Missing income data:** Often the expense file has more months than the income file. Explain the data gap clearly.
- **Handwritten data:** Some entries may have typographical errors or inconsistent formatting. Handle gracefully.
- **Negative amounts in expenses:** Some rows may be refunds/reimbursements (e.g., "上瘾红活动报销" = -4200). These should be included as-is (they're valid adjustments).
