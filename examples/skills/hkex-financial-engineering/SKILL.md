---
name: hkex-financial-engineering
description: Comprehensive analysis framework for Hong Kong stock financial engineering operations (財技分析)
---

# 港股財技分析技能 (HKEX Financial Engineering Analysis)

## When to Use This Skill

Use this skill when you need to:
- Analyze corporate action announcements (供股、配股、拆股、合股)
- Identify shell game operations (買賣殼、白武士重組)
- Detect manipulation patterns in CCASS data (射倉、實物存入)
- Evaluate capital restructuring strategies
- Assess risk/opportunity in financial engineering plays

## Background: What is Financial Engineering (財技)?

Financial engineering in Hong Kong stocks refers to corporate actions and market manipulation techniques used by major shareholders to:
1. **Raise capital** - through placements, rights issues
2. **Consolidate control** - through offers, capital reorganization
3. **Extract value** - through distribution patterns, shell games
4. **Reset share price** - through consolidation + split combos

### Key Market Participants (炒股生態食物鏈)

| Level | Participant | Role |
|-------|-------------|------|
| 1 | 大股東 (Major Shareholder) | Controls company decisions |
| 2 | 莊家 (Market Maker) | Coordinates price movements |
| 3 | 配售商 (Placee) | Provides capital, takes positions |
| 4 | 基金/機構 | Follows trends, adds liquidity |
| 5 | 散戶 (Retail) | Last in chain, highest risk |

---

## Part 1: Corporate Actions Analysis (股本操作)

### 1.1 Rights Issue (供股)

**Definition**: Company offers existing shareholders the right to buy new shares at a discount.

**Key Metrics to Extract:**
- 供股比例 (Subscription Ratio): e.g., "2-for-1" means 2 new shares for every 1 held
- 供股價 (Subscription Price)
- 折讓率 (Discount to Market): (Market Price - Subscription Price) / Market Price × 100%
- 包銷安排 (Underwriting): Fully underwritten vs. non-underwritten
- 不可撤回承諾 (Irrevocable Undertaking): Major shareholder commitment

**Risk Assessment:**

| Indicator | Low Risk | Medium Risk | High Risk |
|-----------|----------|-------------|-----------|
| Ratio | ≤1-for-5 | 1-for-2 | ≥1-for-1 |
| Discount | ≤10% | 10-20% | >20% |
| Underwriting | Fully underwritten | Partially | Not underwritten |
| Use of Proceeds | Specific projects | Working capital | Debt repayment |

**Decision Tree:**
```
供股公告
├── 有包銷?
│   ├── 是 → 評估包銷商信用
│   │   ├── 知名投行 → 相對安全
│   │   └── 不知名 → 注意風險
│   └── 否 → 高風險，大股東可能想逼出散戶
├── 大股東承諾認購?
│   ├── 100%承諾 → 正面信號
│   ├── 部分承諾 → 中性
│   └── 無承諾 → 負面信號
└── 折讓率?
    ├── ≤10% → 正常籌資
    ├── 10-20% → 需注意
    └── >20% → 可能是財技操作
```

### 1.2 Placement (配股/配售)

**Definition**: Company issues new shares to selected investors at a discount.

**Key Metrics to Extract:**
- 配售股份數量 (Number of Shares)
- 配售價 (Placement Price)
- 較市價折讓 (Discount to Market)
- 認購人 (Placees): Who are they?
- 所得款項用途 (Use of Proceeds)
- 禁售期 (Lock-up Period)

**Placee Analysis:**

| Placee Type | Signal | Interpretation |
|-------------|--------|----------------|
| 知名基金 | Positive | Institutional endorsement |
| 大股東關聯方 | Neutral/Negative | Possible circular arrangement |
| 獨立第三方 | Depends | Check background |
| 散戶配售商 | Negative | Often for distribution |

**Red Flags:**
- ❌ Discount >20% without clear reason
- ❌ Placees are shell companies or unknown parties
- ❌ No lock-up period
- ❌ Proceeds for "general working capital" only
- ❌ Frequent placements (3+ per year)

### 1.3 Stock Split (拆股)

**Definition**: Increase number of shares, reduce price per share proportionally.

**Common Ratios:** 1拆2, 1拆5, 1拆10

**Purpose Analysis:**
- ✅ Legitimate: Improve liquidity, lower entry barrier
- ⚠️ Suspicious: Following consolidation (合股後拆股)
- ❌ Manipulation: Combined with placement at "new" price

### 1.4 Reverse Split / Consolidation (合股)

**Definition**: Reduce number of shares, increase price per share proportionally.

**Risk Assessment:**

| Ratio | Risk Level | Common Purpose |
|-------|------------|----------------|
| 2合1 | Low | Administrative |
| 5合1 | Medium | Avoid penny stock |
| 10合1 | High | Price manipulation setup |
| 20合1+ | Very High | Severe dilution incoming |

**Warning Pattern: 合股 → 配股 → 拆股**
```
Step 1: 10合1 (Price: $0.10 → $1.00)
Step 2: 配股 at $0.50 (50% discount "to $1.00")
Step 3: 拆股 1拆5 (Price: $0.50 → $0.10)
Result: Massive dilution, price back to start, capital raised
```

### 1.5 Capital Reduction (削減股本)

**Definition**: Reduce share capital, often to eliminate accumulated losses.

**Types:**
1. **股份註銷**: Cancel shares (reduces total shares)
2. **削減面值**: Reduce par value (accounting adjustment)
3. **回購註銷**: Buyback and cancel

**Purpose Analysis:**
- Positive: Enable dividend payments (clear accumulated losses)
- Neutral: Accounting cleanup
- Negative: Preparation for further financial engineering

---

## Part 2: Shell Game Operations (買賣殼操作)

### 2.1 General Offer (全購)

**Definition**: Offer to acquire all shares at a fixed price.

**Trigger Conditions (《收購守則》Rule 26):**
- Acquirer crosses 30% threshold
- Acquirer in 30-50% range and increases >2% in 12 months

**Key Analysis Points:**
- 收購價 vs 現價: Premium or discount?
- 強制性全面收購: Mandatory general offer triggered?
- 收購條件: Conditions precedent
- 最低接納水平: Minimum acceptance level

### 2.2 Partial Offer (非全購)

**Definition**: Offer to acquire a portion of shares only.

**Key Characteristics:**
- Usually for specific percentage (e.g., 20% of shares)
- Requires 執行人員裁決 (Executive ruling)
- Often signals intention for future full acquisition

**Analysis Points:**
- Why partial instead of full?
- Is this a prelude to control change?
- Fair value assessment

### 2.3 White Knight Rescue (白武士重組)

**Definition**: New investor rescues financially distressed company.

**Opportunity Recognition (百倍股搖籃模式):**

```
Distressed Company State:
├── 股價暴跌 (>80% from peak)
├── 業務困難 / 債務危機
├── 停牌 or 除牌警告
└── 大股東尋求白武士

White Knight Entry:
├── 注入新資產 (asset injection)
├── 削減股本清理帳目
├── 股本重組
└── 新管理層入主

Potential Outcome:
├── 成功重組 → 股價反彈數倍
└── 失敗 → 除牌
```

**Due Diligence Checklist:**
- [ ] 白武士背景調查
- [ ] 注入資產質量
- [ ] 重組方案可行性
- [ ] 監管機構態度
- [ ] 時間表是否合理

### 2.4 Backdoor Listing (啤殼上市)

**Definition**: Private company acquires listed company to gain listing status.

**Key Indicators:**
- 反向收購 (Reverse Takeover) announcement
- Major asset injection
- Complete change of business
- New controlling shareholder

**Regulatory Scrutiny:**
- HKEX Rule 14.06B: Very Substantial Acquisition
- Rule 14.54: Reverse takeover provisions
- Possible trading suspension

---

## Part 3: CCASS Advanced Analysis

### 3.1 數街貨 (Counting Street Float)

**Definition**: Calculate true free float by analyzing CCASS holdings.

**Calculation Method:**
```
Street Float = Total Issued Shares - Locked Shares
Where Locked Shares = Major Shareholders + Strategic Holders + CCASS Non-trading Participants
```

**Significance Thresholds:**
- Street Float <20%: Easily manipulated
- Street Float 20-40%: Tight supply
- Street Float >40%: More liquid

### 3.2 射倉 (Position Manipulation)

**Definition**: Artificial movement of shares between CCASS accounts to create appearance of activity.

**Detection Patterns:**

| Pattern | Description | Signal |
|---------|-------------|--------|
| 對倒 | Same-day opposite movements | Possible wash trading |
| 集中 | Multiple accounts → One account | Accumulation |
| 分散 | One account → Multiple accounts | Distribution setup |
| 輪轉 | Circular movements | Manipulation |

**Alert Thresholds:**
- Single participant change >5% in one day
- Top 3 participants change >10% collectively
- New participant appears with >3% immediately

### 3.3 實物存入 (Physical Deposit)

**Definition**: Transfer of physical share certificates into CCASS.

**Analysis Points:**
- Large physical deposit = Major holder entering market
- Often precedes significant trading activity
- May indicate upcoming placement or distribution

**Workflow:**
```
Detect Physical Deposit > 2%
├── Identify participant (broker type)
├── Check recent announcements
├── Monitor subsequent trading
└── Assess: Accumulation or Distribution setup?
```

### 3.4 CCASS Anomaly Detection

**Comprehensive Checklist:**
- [ ] 單一經紀商持倉突變 (>3%)
- [ ] 頭10大參與者變動 (>10% collective)
- [ ] 新參與者大額進入 (>2%)
- [ ] 實物存入/提取 (>1%)
- [ ] 持倉集中度變化

---

## Part 4: Trading Strategy Analysis

### 4.1 向下炒 (Downward Manipulation)

**Definition**: Major shareholders profit by selling high, then buying back lower through capital reorganization.

**Pattern Recognition:**
```
Phase 1: Distribution
├── 大股東高位配售
├── 利好消息出貨
└── CCASS持倉分散

Phase 2: Price Decline
├── 股價持續下跌
├── 成交量萎縮
└── 負面消息/業績差

Phase 3: Accumulation
├── 大折讓供股/配股
├── 大股東低位增持
├── 削減股本重組
└── 資產注入

Phase 4: Recovery
├── 股價反彈
├── 大股東獲利
└── 循環重複
```

### 4.2 出貨的藝術 (Distribution Art)

**Definition**: Techniques used to sell large positions without crashing the price.

**莊家散貨模型 (Market Maker Distribution Model):**

| Stage | Action | CCASS Signal |
|-------|--------|--------------|
| 1 | 製造利好 | Holdings stable |
| 2 | 推高股價 | Slight concentration |
| 3 | 分批出貨 | Gradual dispersion |
| 4 | 最後拉高 | Rapid dispersion |
| 5 | 急跌 | Retail brokers heavy |

**Warning Signs:**
- 高位放量不漲
- 好消息不漲反跌
- CCASS轉移到散戶經紀
- 大股東減持公告

### 4.3 急跌博反彈 (Bounce Trading)

**Entry Criteria (123 法則):**
1. 急跌 >20% in ≤3 days
2. 成交量放大 (Volume spike)
3. 技術超賣 (RSI <30)

**Risk Assessment:**
- Check if fundamental reason exists
- Check if major shareholder buying
- Check CCASS for institutional accumulation
- Set strict stop-loss (-10%)

---

## Analysis Process Workflow

### Step 1: Announcement Classification

```
收到公告
├── 股本操作類
│   ├── 供股 → 1.1 Rights Issue Analysis
│   ├── 配股 → 1.2 Placement Analysis
│   ├── 拆股 → 1.3 Split Analysis
│   ├── 合股 → 1.4 Consolidation Analysis
│   └── 股本重組 → Combined Analysis
├── 收購合併類
│   ├── 全面收購 → 2.1 General Offer
│   ├── 部分收購 → 2.2 Partial Offer
│   ├── 反向收購 → 2.4 Backdoor Listing
│   └── 白武士 → 2.3 White Knight
└── 持倉異動類
    └── CCASS變動 → Part 3 Analysis
```

### Step 2: Data Extraction

**For Corporate Actions:**
```python
# Search and download announcement
search_hkex_announcements(stock_code="XXXXX", from_date="YYYYMMDD", to_date="YYYYMMDD")
download_announcement_pdf(news_id=..., pdf_url=..., stock_code=..., date_time=..., title=...)
extract_pdf_content(pdf_path="[cached PDF path]")
```

**Key Fields to Extract:**
- 股份數量 (Number of shares)
- 價格 (Price)
- 折讓/溢價 (Discount/Premium)
- 認購人/收購方 (Subscriber/Acquirer)
- 時間表 (Timetable)
- 條件 (Conditions)

### Step 3: Risk/Opportunity Assessment

**Scoring Framework:**

| Factor | Weight | Score Range |
|--------|--------|-------------|
| Discount Level | 25% | 1-5 (1=low, 5=high risk) |
| Underwriting | 20% | 1-5 |
| Placee Quality | 20% | 1-5 |
| Use of Proceeds | 15% | 1-5 |
| Major Shareholder Action | 20% | 1-5 |

**Risk Classification:**
- Total Score ≤2.0: Low Risk
- Total Score 2.0-3.5: Medium Risk
- Total Score >3.5: High Risk

### Step 4: Generate Report

**Report Template:**

```markdown
# [Stock Code] 財技分析報告

## 基本信息
- **股票代碼**: [code]
- **公司名稱**: [name]
- **公告日期**: [date]
- **操作類型**: [type]

## 操作詳情
[Extracted details in table format]

## 風險評估
| 因素 | 評分 | 說明 |
|------|------|------|
| 折讓水平 | X/5 | ... |
| 包銷安排 | X/5 | ... |
| 認購人質量 | X/5 | ... |
| 資金用途 | X/5 | ... |
| 大股東行動 | X/5 | ... |
| **總評分** | **X.X/5** | **[Risk Level]** |

## 財技模式識別
- [Pattern identified, if any]
- [Historical comparison]

## 市場影響分析
- 股本攤薄: [X]%
- 預期股價影響: [analysis]
- 類似案例參考: [examples]

## 投資建議
- **短期**: [1-2 weeks outlook]
- **中期**: [1-3 months outlook]
- **風險提示**: [Key risks]

## 附註
- 數據來源: HKEX 公告
- 分析日期: [date]
```

### Step 5: Save Report

```python
# Use /md/ directory (project standard)
write_file(
    path="/md/[stock_code]-財技分析-[date].md",
    content="[Report content]"
)
```

---

## Best Practices

**Do's:**
- ✅ Always cross-reference multiple announcements
- ✅ Check historical pattern for the company
- ✅ Analyze major shareholder track record
- ✅ Monitor CCASS changes before and after announcements
- ✅ Compare with industry peers
- ✅ Consider regulatory environment

**Don'ts:**
- ❌ Don't ignore small print conditions
- ❌ Don't assume all placements are negative
- ❌ Don't overlook related party transactions
- ❌ Don't trade before understanding the full picture
- ❌ Don't ignore historical financial engineering patterns

## Common Pitfalls

1. **Confirmation Bias**: Looking for evidence to support preconceived notion
2. **Ignoring Context**: Not considering broader market conditions
3. **Over-reliance on Single Indicator**: Missing the full picture
4. **Timing Errors**: Acting before announcement is fully digested
5. **Currency/Unit Confusion**: HK$ vs RMB vs USD, shares vs lots

## Example Workflows

### Example 1: Rights Issue Analysis

**User Request**: "分析00XXX最新的供股公告"

**Execution:**
1. `date +%Y%m%d` to get current date
2. `search_hkex_announcements(stock_code="00XXX", from_date=..., to_date=...)`
3. Filter for "供股" in title
4. `download_announcement_pdf(...)`
5. `extract_pdf_content(...)`
6. Extract: ratio, price, discount, underwriting, use of proceeds
7. Apply risk assessment framework
8. Check CCASS for recent changes
9. Generate report using template
10. `write_file("/md/00XXX-供股分析.md", ...)`

### Example 2: Shell Game Detection

**User Request**: "這間公司是否在進行買殼操作?"

**Execution:**
1. Search for recent announcements (3-6 months)
2. Look for patterns:
   - Major shareholder change
   - Asset injection/disposal
   - Business change
   - Capital reorganization
3. Check CCASS for unusual movements
4. Compare with known shell game patterns
5. Generate assessment report

### Example 3: CCASS Anomaly Investigation

**User Request**: "00XXX的CCASS今天有大變動，是什麼情況?"

**Execution:**
1. Fetch CCASS data (if MCP available)
2. Identify top movers
3. Check participant types
4. Cross-reference with announcements
5. Check for physical deposits/withdrawals
6. Apply anomaly detection patterns
7. Generate analysis report

---

## Reference: Key Terms Glossary

| Chinese | English | Description |
|---------|---------|-------------|
| 供股 | Rights Issue | Offer to existing shareholders |
| 配股 | Placement | Issue to selected investors |
| 拆股 | Stock Split | Increase shares, reduce price |
| 合股 | Consolidation | Reduce shares, increase price |
| 削減股本 | Capital Reduction | Reduce share capital |
| 買殼 | Shell Acquisition | Buy listed company for status |
| 賣殼 | Shell Sale | Sell listed company |
| 白武士 | White Knight | Rescuing investor |
| 啤殼 | Backdoor Listing | RTO for listing |
| 全購 | General Offer | Offer for all shares |
| 數街貨 | Street Float | Count free float |
| 射倉 | Position Manipulation | Artificial CCASS movement |
| 實物存入 | Physical Deposit | Certificate to CCASS |
| 向下炒 | Downward Manipulation | Profit from decline |
| 出貨 | Distribution | Selling large positions |

---

## Related Skills

- **hkex-announcement**: For basic announcement extraction and analysis
- **ccass-tracking**: For detailed CCASS monitoring over time
- **financial-metrics**: For fundamental analysis to support financial engineering assessment

