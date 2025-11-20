---
name: ccass-tracking
description: Track and analyze CCASS (Central Clearing and Settlement System) participant holdings over time
---

# CCASS Tracking Skill

## When to Use This Skill

Use this skill when you need to:
- Track institutional holdings via CCASS
- Analyze broker position changes
- Identify accumulation/distribution patterns
- Monitor major shareholder movements
- Detect unusual trading activities

## Background: What is CCASS?

CCASS (中央結算系統) is the Central Clearing and Settlement System operated by HKEX. It shows holdings by:
- **Participant IDs**: Broker codes (e.g., C00001, B01234)
- **Participant Names**: Broker names (e.g., HSBC, Goldman Sachs)
- **Holdings**: Number of shares held
- **Percentage**: % of total issued shares

## Data Sources

### 1. CCASS MCP Server (Preferred)
If the CCASS MCP server is enabled, use it for live data:
```
# Check if MCP is available
ls ~/.hkex-agent/[agent]/mcp_servers/

# Use CCASS query tool (if available)
# This is automatically loaded when enable_mcp=True
```

### 2. Web Scraping (Fallback)
If MCP is not available, fetch from HKEX website:
- URL: `https://www.hkexnews.hk/sdw/search/stocklist_c.aspx`
- Manual data extraction required

### 3. Historical Data
Access cached CCASS data from project directories or user memories.

## Analysis Process

### Step 1: Fetch CCASS Data

**For a single date:**
```
# If MCP available (check with /mcp list command)
# Use the CCASS MCP tool directly

# If MCP not available, inform user:
"CCASS MCP服务器未启用。请手动访问 HKEX 网站或提供 CCASS 数据文件。"
```

**For date range tracking:**
Create a tracking task:
```
task(
    description="Track CCASS holdings for stock 00700 from 2025-10-01 to 2025-11-20. Extract top 10 participants and their holding changes.",
    subagent_type="data-analyzer"
)
```

### Step 2: Identify Key Participants

**Top Holders Analysis:**
1. List top 10 participants by shareholding percentage
2. Identify well-known brokers:
   - HSBC
   - Goldman Sachs
   - Morgan Stanley
   - UBS
   - JP Morgan
   - China brokers (CICC, Guotai Junan, etc.)

**Categorize by type:**
- Retail brokers (e.g., Futu, Tiger)
- Investment banks (Goldman, Morgan Stanley)
- Chinese brokers (CICC, Haitong)
- Custodian banks (HSBC, Standard Chartered)

### Step 3: Calculate Changes

**Key Metrics:**
- **Absolute change**: Current holdings - Previous holdings
- **Percentage change**: (Change / Previous) × 100%
- **Share of turnover**: Change / Daily volume
- **Net flow**: Sum of all positive changes - Sum of all negative changes

**Thresholds for significance:**
- Large change: >5% of holdings
- Very large change: >10% of holdings
- Massive change: >20% of holdings

### Step 4: Identify Patterns

**Accumulation signals:**
- Multiple participants increasing holdings
- Investment banks buying
- Holdings increasing over consecutive dates

**Distribution signals:**
- Top holders reducing positions
- Retail brokers showing outflows
- Holdings decreasing over consecutive dates

**Rotation signals:**
- Some participants buying, others selling
- Net flow near zero
- Broker type shifting (e.g., retail → institutional)

### Step 5: Generate Report

Create a structured CCASS analysis report:

```markdown
# CCASS 持仓分析 - [Stock Code] ([Date Range])

## 概况
- **股票代码**: [code]
- **分析期间**: [start date] 至 [end date]
- **当前总持仓**: [total shares] ([% of issued shares])

## Top 10 参与者

| 排名 | 参与者 | 持股数量 | 占比 | 变化 | 变化% |
|------|--------|---------|------|------|-------|
| 1 | [Name] | [shares] | [%] | +/- [change] | +/- [%] |
| ... | ... | ... | ... | ... | ... |

## 关键变化

### 大幅增持 (>5%)
- **[Participant Name]**: +[X]% ([reason/analysis])

### 大幅减持 (>5%)
- **[Participant Name]**: -[X]% ([reason/analysis])

### 新进入者
- **[Participant Name]**: 首次出现，持股 [X]%

### 退出者
- **[Participant Name]**: 已清仓

## 资金流向
- **净流入**: +[X] 股 (+[Y]%)
- **买方主力**: [Participant types]
- **卖方主力**: [Participant types]

## 市场影响分析
- **持仓集中度**: [Top 10 占比]
- **流通性**: [分析]
- **机构vs散户**: [占比分析]

## 风险提示
- [Any unusual patterns or risks]
```

### Step 6: Save to File

```
write_file(
    path="ccass_analysis/[stock_code]_[date_range].md",
    content="[Report content]"
)
```

## Best Practices

**Do's:**
- ✅ Track at least 5-10 consecutive dates for trend analysis
- ✅ Focus on top 20 participants (they hold 80%+ of CCASS shares)
- ✅ Cross-reference with price movements
- ✅ Note any corporate actions during the period
- ✅ Identify broker names (not just IDs)

**Don'ts:**
- ❌ Don't ignore small but consistent changes
- ❌ Don't forget to account for corporate actions (splits, dividends)
- ❌ Don't assume broker code = beneficial owner
- ❌ Don't ignore weekends/holidays (no data)

## Important Notes

### CCASS Limitations
1. **Not beneficial ownership**: CCASS shows broker holdings, not end investors
2. **Retail underrepresented**: Many retail investors hold via brokers not in CCASS
3. **Lag time**: Data is T+1 (published next day)
4. **Incomplete picture**: Only ~70-80% of shares tracked in CCASS

### Interpretation Guidelines
- **Broker accumulation**: May indicate institutional interest OR client orders
- **Custodian changes**: Often administrative, not trading
- **Retail broker flows**: Better indicator of retail sentiment
- **Investment bank positions**: May be proprietary or client-related

## Example Workflow

**User Request**: "追踪00700最近一个月的CCASS变化"

**Execution Steps:**
1. Check if CCASS MCP is available: `/mcp list`
2. If yes, use MCP tool to fetch data
3. If no, inform user and suggest alternatives
4. Analyze top 10 holders
5. Calculate changes
6. Identify patterns (accumulation/distribution)
7. Create analysis folder: `mkdir ccass_analysis`
8. Write report: `write_file("ccass_analysis/00700_ccass_report.md", [content])`
9. Present summary to user

## Supporting Scripts

Optional helper scripts (create as needed):
- `fetch_ccass.py`: Fetch CCASS data from HKEX website
- `parse_participants.py`: Parse participant names and categorize
- `calculate_flows.py`: Calculate net flows and changes
- `generate_charts.py`: Generate holding trend charts (requires matplotlib)

Place scripts in: `~/.hkex-agent/[agent]/skills/ccass-tracking/`

