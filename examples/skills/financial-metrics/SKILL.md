---
name: financial-metrics
description: Calculate and analyze financial metrics from HKEX announcements (results, reports)
---

# Financial Metrics Analysis Skill

## When to Use This Skill

Use this skill when you need to:
- Analyze interim/annual financial results
- Calculate valuation metrics
- Compare financial performance across periods
- Benchmark against industry peers
- Identify financial trends and anomalies

## Key Financial Metrics Categories

### 1. Valuation Metrics

**Price-to-Earnings (P/E Ratio)**
- Formula: Market Price / Earnings Per Share
- Interpretation: Lower = cheaper, Higher = growth premium
- Benchmark: Compare to industry average

**Price-to-Book (P/B Ratio)**
- Formula: Market Price / Book Value Per Share
- Interpretation: <1 = trading below book value
- Benchmark: Compare to historical P/B

**EV/EBITDA**
- Formula: (Market Cap + Debt - Cash) / EBITDA
- Interpretation: Capital structure-adjusted valuation
- Benchmark: Industry comparison

**Dividend Yield**
- Formula: Annual Dividend / Share Price × 100%
- Interpretation: Income return for investors
- Benchmark: Risk-free rate, peer comparison

### 2. Profitability Metrics

**Gross Profit Margin**
- Formula: Gross Profit / Revenue × 100%
- Interpretation: Product pricing power
- Trend: Rising = improving efficiency

**Operating Margin**
- Formula: Operating Profit / Revenue × 100%
- Interpretation: Core business profitability
- Trend: Key operational health indicator

**Net Profit Margin**
- Formula: Net Profit / Revenue × 100%
- Interpretation: Bottom-line efficiency
- Benchmark: Industry comparison

**Return on Equity (ROE)**
- Formula: Net Income / Shareholders' Equity × 100%
- Interpretation: Return generated for shareholders
- Benchmark: >15% is generally good

**Return on Assets (ROA)**
- Formula: Net Income / Total Assets × 100%
- Interpretation: Asset utilization efficiency
- Benchmark: Industry-specific

### 3. Growth Metrics

**Revenue Growth (YoY)**
- Formula: (Current Revenue - Prior Revenue) / Prior Revenue × 100%
- Interpretation: Top-line expansion
- Benchmark: GDP growth, industry growth

**Profit Growth (YoY)**
- Formula: (Current Profit - Prior Profit) / Prior Profit × 100%
- Interpretation: Bottom-line expansion
- Benchmark: Revenue growth (leverage effect)

**EPS Growth**
- Formula: (Current EPS - Prior EPS) / Prior EPS × 100%
- Interpretation: Per-share profit growth
- Benchmark: Market expectations

**Quarter-over-Quarter (QoQ) Growth**
- Compare Q1 vs Q2, Q2 vs Q3, etc.
- Seasonality-adjusted if needed

### 4. Leverage Metrics

**Debt-to-Equity Ratio**
- Formula: Total Debt / Total Equity
- Interpretation: Financial leverage
- Benchmark: <1.0 conservative, >2.0 aggressive

**Interest Coverage Ratio**
- Formula: EBIT / Interest Expense
- Interpretation: Ability to service debt
- Benchmark: >3.0 is comfortable

**Net Gearing**
- Formula: (Total Debt - Cash) / Equity × 100%
- Interpretation: Net debt position
- Benchmark: Negative = net cash

### 5. Liquidity Metrics

**Current Ratio**
- Formula: Current Assets / Current Liabilities
- Interpretation: Short-term liquidity
- Benchmark: >1.0 is healthy

**Quick Ratio**
- Formula: (Current Assets - Inventory) / Current Liabilities
- Interpretation: Immediate liquidity
- Benchmark: >1.0 is good

## Analysis Process

### Step 1: Download Financial Results

1. **Search for results announcements**:
```
search_hkex_announcements(
    stock_code="00700",
    start_date="2025-01-01",
    end_date="2025-12-31",
    category="業績"  # Results
)
```

2. **Download PDF**:
```
download_announcement_pdf(
    announcement_url="[URL]",
    stock_code="00700"
)
```

### Step 2: Extract Financial Data

1. **Extract tables** (financial statements are in tables):
```
extract_pdf_content(pdf_path="[PDF path]")
# Focus on tables - balance sheet, income statement, cash flow
```

2. **Key sections to find**:
   - Consolidated Income Statement (綜合損益表)
   - Consolidated Balance Sheet (綜合資產負債表)
   - Consolidated Cash Flow Statement (綜合現金流量表)
   - Financial Highlights (財務摘要)

### Step 3: Parse Financial Figures

**Income Statement (損益表):**
- Revenue (收入/營業額)
- Cost of Sales (銷售成本)
- Gross Profit (毛利)
- Operating Profit (營業溢利)
- Profit Before Tax (除稅前溢利)
- Income Tax (所得稅)
- Net Profit (純利/淨利潤)
- EPS (每股盈利)

**Balance Sheet (資產負債表):**
- Total Assets (總資產)
- Current Assets (流動資產)
- Total Liabilities (總負債)
- Current Liabilities (流動負債)
- Total Equity (權益總額)
- Cash and Cash Equivalents (現金及現金等價物)

**Cash Flow Statement (現金流量表):**
- Operating Cash Flow (經營活動現金流)
- Investing Cash Flow (投資活動現金流)
- Financing Cash Flow (融資活動現金流)
- Net Cash Flow (現金淨變動)

### Step 4: Calculate Metrics

Create a metrics calculation workflow:

```python
# Example calculation structure (not executable, for reference)
metrics = {
    "Profitability": {
        "Gross Margin": gross_profit / revenue * 100,
        "Operating Margin": operating_profit / revenue * 100,
        "Net Margin": net_profit / revenue * 100,
        "ROE": net_profit / equity * 100,
        "ROA": net_profit / assets * 100,
    },
    "Growth": {
        "Revenue Growth YoY": (revenue - revenue_ly) / revenue_ly * 100,
        "Profit Growth YoY": (net_profit - net_profit_ly) / net_profit_ly * 100,
        "EPS Growth YoY": (eps - eps_ly) / eps_ly * 100,
    },
    "Leverage": {
        "Debt/Equity": total_debt / equity,
        "Interest Coverage": ebit / interest_expense,
        "Net Gearing": (total_debt - cash) / equity * 100,
    },
    "Liquidity": {
        "Current Ratio": current_assets / current_liabilities,
        "Quick Ratio": (current_assets - inventory) / current_liabilities,
    }
}
```

### Step 5: Benchmark and Compare

**Compare against:**
1. **Historical performance**: Company's own past results
2. **Industry peers**: Similar companies in same sector
3. **Market averages**: Hang Seng Index or sector index
4. **Analyst expectations**: Consensus estimates (if available)

**Key questions:**
- Are margins improving or declining?
- Is growth accelerating or decelerating?
- Is leverage increasing (risk) or decreasing (deleveraging)?
- Are returns improving (efficiency gains)?

### Step 6: Generate Analysis Report

Create a comprehensive financial analysis:

```markdown
# 财务指标分析 - [Company Name] ([Stock Code])

## 报告期: [Period]

---

## 📊 关键财务数据

### 损益表
| 指标 | 本期 | 上期 | 变化 | 变化% |
|------|------|------|------|-------|
| 收入 | [X] | [Y] | [Z] | [%] |
| 毛利 | [X] | [Y] | [Z] | [%] |
| 营业利润 | [X] | [Y] | [Z] | [%] |
| 净利润 | [X] | [Y] | [Z] | [%] |
| EPS | [X] | [Y] | [Z] | [%] |

### 资产负债表
| 指标 | 期末 | 期初 | 变化 |
|------|------|------|------|
| 总资产 | [X] | [Y] | [Z] |
| 总负债 | [X] | [Y] | [Z] |
| 权益总额 | [X] | [Y] | [Z] |
| 现金 | [X] | [Y] | [Z] |

---

## 💰 估值指标

| 指标 | 数值 | 行业平均 | 评价 |
|------|------|----------|------|
| P/E Ratio | [X] | [Y] | [高/低/合理] |
| P/B Ratio | [X] | [Y] | [高/低/合理] |
| EV/EBITDA | [X] | [Y] | [高/低/合理] |
| Dividend Yield | [X]% | [Y]% | [高/低/合理] |

---

## 📈 盈利能力

| 指标 | 本期 | 上期 | 趋势 |
|------|------|------|------|
| 毛利率 | [X]% | [Y]% | ↑/↓/→ |
| 营业利润率 | [X]% | [Y]% | ↑/↓/→ |
| 净利率 | [X]% | [Y]% | ↑/↓/→ |
| ROE | [X]% | [Y]% | ↑/↓/→ |
| ROA | [X]% | [Y]% | ↑/↓/→ |

**分析**:
- [盈利能力分析]

---

## 🚀 成长性

| 指标 | 同比增长 | 环比增长 |
|------|----------|----------|
| 收入增长 | [X]% | [Y]% |
| 利润增长 | [X]% | [Y]% |
| EPS增长 | [X]% | [Y]% |

**分析**:
- [成长性分析]

---

## ⚖️ 杠杆与偿债能力

| 指标 | 数值 | 基准 | 评价 |
|------|------|------|------|
| 资产负债率 | [X]% | <60% | [安全/偏高] |
| 负债权益比 | [X] | <1.0 | [保守/激进] |
| 利息保障倍数 | [X] | >3.0 | [充足/紧张] |
| 净负债率 | [X]% | - | [高/低/净现金] |

**分析**:
- [杠杆分析]

---

## 💧 流动性

| 指标 | 数值 | 基准 | 评价 |
|------|------|------|------|
| 流动比率 | [X] | >1.0 | [良好/不足] |
| 速动比率 | [X] | >1.0 | [良好/不足] |
| 现金比率 | [X] | - | [充裕/紧张] |

**分析**:
- [流动性分析]

---

## 🎯 综合评价

### 优势
1. [Strength 1]
2. [Strength 2]

### 风险
1. [Risk 1]
2. [Risk 2]

### 投资建议
[Investment recommendation based on analysis]

---

## 📎 数据来源
- 公告日期: [Date]
- 报告链接: [URL]
```

### Step 7: Save Analysis

```
write_file(
    path="financial_analysis/[stock_code]_[period].md",
    content="[Report content]"
)
```

## Best Practices

**Do's:**
- ✅ Always compare with prior period
- ✅ Calculate both absolute and percentage changes
- ✅ Consider seasonality (Q4 vs Q1 may differ naturally)
- ✅ Read management discussion for context
- ✅ Note any one-off items or extraordinary items
- ✅ Check accounting policies for changes

**Don'ts:**
- ❌ Don't ignore footnotes (they contain critical info)
- ❌ Don't compare different currency figures directly
- ❌ Don't forget about share dilution effects
- ❌ Don't overlook non-recurring items
- ❌ Don't use outdated market prices for valuations

## Common Pitfalls

1. **Currency mix-up**: Some companies report in RMB, others in HK$
2. **Unit confusion**: Millions (百萬) vs Thousands (千) vs Actual
3. **Adjusted vs Reported**: Some metrics are adjusted (non-GAAP)
4. **Discontinued operations**: May distort comparisons
5. **Share splits**: Adjust historical EPS accordingly

## Example Workflow

**User Request**: "分析00700最新业绩公告的财务指标"

**Execution Steps:**
1. Search for latest results: `search_hkex_announcements("00700", ..., "業績")`
2. Download PDF: `download_announcement_pdf([URL], "00700")`
3. Extract financial statements: `extract_pdf_content([PDF])`
4. Parse key figures from tables
5. Calculate all metrics (profitability, growth, leverage, liquidity)
6. Compare with prior period
7. Benchmark against industry
8. Create analysis folder: `mkdir financial_analysis`
9. Write comprehensive report: `write_file("financial_analysis/00700_analysis.md", [content])`
10. Present key findings to user

## Supporting Scripts

Optional helper scripts:
- `extract_financials.py`: Parse financial statements from PDF
- `calculate_metrics.py`: Automated metric calculation
- `benchmark.py`: Compare against industry/peers
- `visualize.py`: Generate charts (requires matplotlib)

Place scripts in: `~/.hkex-agent/[agent]/skills/financial-metrics/`

