---
name: hkex-announcement-analysis
description: Structured approach to analyzing HKEX announcements (placements, rights offerings, results)
---

# HKEX Announcement Analysis Skill

## When to Use This Skill

Use this skill when you need to:
- Analyze placement (配售) announcements
- Evaluate rights offering (供股) announcements
- Review interim/annual results announcements
- Compare multiple HKEX announcements
- Extract key metrics from announcements

## Announcement Types and Key Metrics

### 1. Placement (配售)
**Key Information to Extract:**
- Number of shares placed (配售股份数量)
- Subscription price (认购价)
- Discount to market price (较市价折让)
- Use of proceeds (所得款项用途)
- Subscribers (认购人)
- Conditions precedent (先决条件)

### 2. Rights Offering (供股)
**Key Information to Extract:**
- Subscription ratio (供股比例) e.g., "1-for-1"
- Subscription price (认购价)
- Underwriting arrangement (包销安排)
- Irrevocable undertakings (不可撤回承诺)
- Expected timetable (预期时间表)
- Use of proceeds (所得款项用途)

### 3. Results Announcement (业绩公告)
**Key Information to Extract:**
- Revenue (收入)
- Profit/Loss (盈利/亏损)
- EPS (每股盈利)
- Dividend (股息)
- Year-on-year comparison (同比变化)
- Management discussion (管理层讨论)

## Analysis Process

### Step 1: Search and Download

1. **Search for announcements** using the search_hkex_announcements tool:
```
search_hkex_announcements(
    stock_code="00700",
    start_date="2025-11-01",
    end_date="2025-11-20",
    category="配售"  # or "供股", "业绩"
)
```

2. **Download the PDF** using download_announcement_pdf:
```
download_announcement_pdf(
    announcement_url="[URL from search results]",
    stock_code="00700"
)
```

### Step 2: Extract Content

1. **Extract text and tables** using extract_pdf_content:
```
extract_pdf_content(pdf_path="[cached PDF path]")
```

2. **Analyze structure** using analyze_pdf_structure:
```
analyze_pdf_structure(pdf_path="[cached PDF path]")
```

### Step 3: Extract Key Metrics

**For Placements:**
- Search for "配售价" or "Subscription Price"
- Search for "配售股份" or "Placement Shares"
- Search for "折讓" or "Discount"
- Search for "認購人" or "Placee"
- Search for "所得款項用途" or "Use of Proceeds"

**For Rights Offerings:**
- Search for "供股比例" or "Subscription Ratio"
- Search for "供股價" or "Subscription Price"
- Search for "包銷" or "Underwriting"
- Search for "承諾" or "Undertaking"
- Search for "時間表" or "Timetable"

**For Results:**
- Search for "收入" or "Revenue"
- Search for "利潤" or "Profit"
- Search for "每股盈利" or "EPS"
- Search for "股息" or "Dividend"

### Step 4: Generate Structured Summary

1. **Create analysis folder**:
```
mkdir analysis_[stock_code]_[date]
```

2. **Write summary** using generate_summary_markdown or write_file:
```
write_file(
    path="analysis_[stock_code]_[date]/summary.md",
    content="[Structured summary with all key metrics]"
)
```

**Summary Template for Placements:**
```markdown
# [Stock Code] 配售公告分析

## 基本信息
- **股票代码**: [code]
- **公司名称**: [name]
- **公告日期**: [date]

## 配售详情
- **配售股份数量**: [number] 股
- **配售价**: HK$ [price]
- **较市价折让**: [discount]%
- **认购人**: [placee names]

## 所得款项用途
1. [Use 1]: HK$ [amount]
2. [Use 2]: HK$ [amount]

## 市场影响
- **摊薄效应**: [dilution]%
- **集资额**: HK$ [total amount]

## 关键条款
- [Key terms and conditions]
```

### Step 5: Comparison (if requested)

Use the task tool to spawn a comparison subagent:
```
task(
    description="Compare this placement with similar ones from the past 6 months",
    subagent_type="data-analyzer"
)
```

## Best Practices

**Do's:**
- ✅ Always download and cache PDFs first
- ✅ Extract both text and tables for complete information
- ✅ Cross-reference multiple sections for accuracy
- ✅ Use structured markdown for summaries
- ✅ Include source references (page numbers)

**Don'ts:**
- ❌ Don't guess metrics if not found in PDF
- ❌ Don't skip table data (often contains key metrics)
- ❌ Don't ignore footnotes and conditions
- ❌ Don't mix up traditional/simplified Chinese amounts

## Common Pitfalls

1. **Currency confusion**: Check if amounts are in HK$, RMB, or USD
2. **Share units**: Confirm if in shares, lots (手), or millions
3. **Date formats**: HKEX uses DD/MM/YYYY format
4. **Traditional Chinese**: HKEX announcements use traditional Chinese (繁體)

## Example Workflow

**User Request**: "分析00700最新的配售公告"

**Execution Steps:**
1. Search announcements: `search_hkex_announcements("00700", "2025-11-01", "2025-11-20", "配售")`
2. Download PDF: `download_announcement_pdf([URL], "00700")`
3. Extract content: `extract_pdf_content([PDF path])`
4. Identify key metrics from extracted text/tables
5. Create analysis folder: `mkdir analysis_00700_placement_2025-11-20`
6. Write summary: `write_file("analysis_00700_placement_2025-11-20/summary.md", [content])`
7. Present summary to user

## Supporting Files

This skill can work with optional helper scripts:
- `parse_placement.py`: Extract placement-specific metrics
- `parse_rights_offering.py`: Extract rights offering metrics
- `parse_results.py`: Extract financial results

Place scripts in the same directory as this SKILL.md file.

