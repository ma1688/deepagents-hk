---
name: hkex-announcement
description: 港交所公告分析的结构化方法（配售、供股、业绩）- 可独立使用，也被 hkex-financial-engineering 技能引用
---

# 港交所公告分析技能

## 何时使用此技能

当您需要以下操作时，请使用此技能：
- 分析配售（配售）公告
- 评估供股（供股）公告
- 审阅中期/年度业绩公告
- 比较多个港交所公告
- 从公告中提取关键指标

## 公告类型和关键指标

### 1. 配售（Placement）
**需要提取的关键信息：**
- 配售股份数量
- 认购价
- 较市价折让
- 所得款项用途
- 认购人
- 先决条件

### 2. 供股（Rights Offering）
**需要提取的关键信息：**
- 供股比例，例如"1供1"
- 认购价
- 包销安排
- 不可撤回承诺
- 预期时间表
- 所得款项用途

### 3. 业绩公告（Results Announcement）
**需要提取的关键信息：**
- 收入
- 盈利/亏损
- 每股盈利（EPS）
- 股息
- 同比变化
- 管理层讨论

## 分析流程

### 步骤 1：搜索和下载

1. **使用 search_hkex_announcements 工具搜索公告**：
```
# 首先获取当前日期
date +%Y%m%d

# 然后搜索（使用 from_date/to_date，而非 start_date/end_date）
search_hkex_announcements(
    stock_code="00700",
    from_date="20251101",
    to_date="20251120"
)
# 注意：手动从结果中筛选关键词（标题字段）
```

2. **使用 download_announcement_pdf 下载 PDF**：
```
download_announcement_pdf(
    news_id="[搜索结果中的 NEWS_ID]",
    pdf_url="[搜索结果中的 PDF_URL]",
    stock_code="00700",
    date_time="[搜索结果中的 DATE_TIME]",
    title="[搜索结果中的 TITLE]"
)
```

### 步骤 2：提取内容

1. **使用 extract_pdf_content 提取文本和表格**：
```
extract_pdf_content(pdf_path="[缓存的 PDF 路径]")
```

2. **使用 analyze_pdf_structure 分析结构**：
```
analyze_pdf_structure(pdf_path="[缓存的 PDF 路径]")
```

### 步骤 3：提取关键指标

**对于配售：**
- 搜索"配售价"或"Subscription Price"
- 搜索"配售股份"或"Placement Shares"
- 搜索"折讓"或"Discount"
- 搜索"認購人"或"Placee"
- 搜索"所得款項用途"或"Use of Proceeds"

**对于供股：**
- 搜索"供股比例"或"Subscription Ratio"
- 搜索"供股價"或"Subscription Price"
- 搜索"包銷"或"Underwriting"
- 搜索"承諾"或"Undertaking"
- 搜索"時間表"或"Timetable"

**对于业绩：**
- 搜索"收入"或"Revenue"
- 搜索"利潤"或"Profit"
- 搜索"每股盈利"或"EPS"
- 搜索"股息"或"Dividend"

### 步骤 4：生成结构化摘要

**使用 generate_summary_markdown 或 write_file 写入摘要**：
```
# 使用 /md/ 目录（项目标准）
write_file(
    path="/md/[stock_code]-[event_type]-analysis.md",
    content="[包含所有关键指标的结构化摘要]"
)
```

**配售摘要模板：**
```markdown
# [股票代码] 配售公告分析

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
1. [用途 1]: HK$ [amount]
2. [用途 2]: HK$ [amount]

## 市场影响
- **摊薄效应**: [dilution]%
- **集资额**: HK$ [total amount]

## 关键条款
- [关键条款和条件]
```

### 步骤 5：比较（如有需要）

使用 task 工具生成子代理进行隔离分析：
```
task(
    description="将此次配售与过去6个月的类似配售进行比较。搜索配售、下载 PDF、提取关键指标，并返回比较表格。",
    subagent_type="general-purpose"
)
```
> 注意：子代理拥有与主代理相同的工具。用于上下文隔离。

## 最佳实践

**建议做的事：**
- ✅ 始终先下载和缓存 PDF
- ✅ 同时提取文本和表格以获取完整信息
- ✅ 交叉对比多个章节以确保准确性
- ✅ 使用结构化 Markdown 编写摘要
- ✅ 包含来源引用（页码）

**避免做的事：**
- ❌ 如果在 PDF 中找不到指标，不要猜测
- ❌ 不要跳过表格数据（通常包含关键指标）
- ❌ 不要忽视附注和条件
- ❌ 不要混淆繁体/简体中文金额

## 常见陷阱

1. **货币混淆**：检查金额是港元、人民币还是美元
2. **股份单位**：确认是股、手还是百万
3. **日期格式**：港交所使用 DD/MM/YYYY 格式
4. **繁体中文**：港交所公告使用繁体中文（繁體）

## 示例工作流程

**用户请求**："分析00700最新的配售公告"

**执行步骤：**
1. 获取当前日期：`date +%Y%m%d`（例如，"20251120"）
2. 计算日期范围：from_date = 一年前，to_date = 今天
3. 搜索公告：`search_hkex_announcements(stock_code="00700", from_date="20241120", to_date="20251120")`
4. 筛选标题中包含"配售"的结果
5. 下载 PDF：`download_announcement_pdf(news_id=..., pdf_url=..., stock_code="00700", date_time=..., title=...)`
6. 提取内容：`extract_pdf_content([PDF 路径])`
7. 从提取的文本/表格中识别关键指标
8. 写入摘要：`write_file("/md/00700-配售分析.md", [内容])`
9. 向用户展示摘要

## 辅助文件

此技能可配合可选的辅助脚本使用：
- `parse_placement.py`：提取配售特定指标
- `parse_rights_offering.py`：提取供股指标
- `parse_results.py`：提取财务业绩

将脚本放置在与此 SKILL.md 文件相同的目录中。
