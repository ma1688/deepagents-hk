# HKEX Skills 使用指南

**版本**: 1.0  
**更新日期**: 2025-11-20  
**适用于**: deepagents-hk with Skills system

---

## 📚 什么是Skills?

Skills是HKEX Agent的**可重用专业技能库**，类似于Agent的"操作手册"。每个Skill包含:
- 何时使用该技能
- 详细的执行步骤
- 最佳实践和常见陷阱
- 示例工作流

**核心理念**: **渐进式披露** - Agent先看技能列表，需要时才读取详情。

---

## 🚀 快速开始

### 第1步: 复制示例技能

```bash
# 复制3个HKEX专用技能到用户目录
cp -r examples/skills/hkex-announcement ~/.hkex-agent/hkex-agent/skills/
cp -r examples/skills/ccass-tracking ~/.hkex-agent/hkex-agent/skills/
cp -r examples/skills/financial-metrics ~/.hkex-agent/hkex-agent/skills/
```

### 第2步: 启动HKEX CLI

```bash
hkex
```

Agent会自动:
- 加载 `~/.hkex-agent/hkex-agent/skills/` 下的所有技能
- 在系统提示词中列出可用技能
- 根据任务自动选择合适技能

### 第3步: 使用技能

**方式1: 隐式使用** (推荐)
```
> 分析00700最新的配售公告

Agent会:
1. 检查技能列表
2. 识别到 "hkex-announcement-analysis" 相关
3. 读取 SKILL.md
4. 按照技能指导执行分析
```

**方式2: 显式请求**
```
> 使用hkex-announcement-analysis技能分析00700的配售公告

Agent会直接读取并应用该技能
```

---

## 📁 技能目录结构

### 标准结构

```
~/.hkex-agent/
└── hkex-agent/               # Agent目录
    ├── memories/
    │   └── agent.md          # 用户级内存
    ├── pdf_cache/            # PDF缓存
    └── skills/               # ✨ 技能目录
        ├── hkex-announcement/
        │   ├── SKILL.md      # 必需：技能文档
        │   ├── helper.py     # 可选：辅助脚本
        │   └── data/         # 可选：数据文件
        ├── ccass-tracking/
        │   └── SKILL.md
        └── financial-metrics/
            └── SKILL.md
```

### 项目级技能 (高级)

```
/path/to/your-project/
├── .hkex-agent/
│   ├── agent.md              # 项目级内存
│   └── skills/               # 项目专用技能（可选）
│       └── project-specific/
│           └── SKILL.md
└── ...
```

**优先级**: 项目技能 > 用户技能

---

## ✍️ 创建自定义技能

### SKILL.md 格式

```markdown
---
name: my-custom-skill
description: Short description of what this skill does
---

# My Custom Skill

## When to Use This Skill
- Situation 1
- Situation 2

## Process

### Step 1: Preparation
Do this...

### Step 2: Execution
Do that...

### Step 3: Output
Generate result...

## Best Practices
- ✅ Do this
- ❌ Don't do that

## Example Workflow
**User Request**: "..."

**Execution Steps**:
1. ...
2. ...
```

### 最小示例

```markdown
---
name: quick-summary
description: Generate quick summary of HKEX announcement
---

# Quick Summary Skill

## When to Use
User needs a fast overview without details.

## Process
1. Download PDF
2. Extract first page
3. Generate 3-bullet summary
```

---

## 🎯 内置HKEX技能

### 1. hkex-announcement-analysis

**用途**: 分析配售、供股、业绩公告  
**适用场景**:
- 用户要求分析具体公告
- 需要提取关键财务指标
- 对比多个公告

**关键特性**:
- 自动识别公告类型（配售/供股/业绩）
- 结构化摘要生成
- 表格数据提取

**示例**:
```
> 分析00700在2025年11月的配售公告

Agent使用该技能:
1. 搜索00700配售公告
2. 下载PDF
3. 提取：配售价、股数、折让率、认购人
4. 生成Markdown摘要
```

---

### 2. ccass-tracking

**用途**: 追踪CCASS券商持仓变化  
**适用场景**:
- 分析机构持仓
- 识别大户进出
- 研究资金流向

**关键特性**:
- Top 10持仓分析
- 持仓变化计算
- 买卖力量对比

**示例**:
```
> 追踪00700最近一个月的CCASS变化

Agent使用该技能:
1. 如有MCP，使用CCASS工具
2. 提取Top 10持仓
3. 计算变化量和百分比
4. 识别accumulation/distribution模式
5. 生成分析报告
```

---

### 3. financial-metrics

**用途**: 计算和分析财务指标  
**适用场景**:
- 分析财务报表
- 计算估值指标
- 对比行业基准

**关键特性**:
- 5大类指标（估值、盈利、成长、杠杆、流动性）
- 自动计算P/E、ROE、负债率等
- 同比/环比比较

**示例**:
```
> 分析00700最新业绩的财务指标

Agent使用该技能:
1. 下载业绩公告
2. 提取损益表、资产负债表
3. 计算所有关键指标
4. 与上期对比
5. 生成综合分析报告
```

---

## 🎨 高级用法

### 组合多个技能

```
> 分析00700：
> 1. 最新配售公告
> 2. CCASS最近变化
> 3. 最新业绩指标

Agent会:
1. 使用hkex-announcement-analysis处理配售
2. 使用ccass-tracking处理CCASS
3. 使用financial-metrics处理业绩
4. 综合三部分生成完整报告
```

### 技能链 (Skill Chaining)

某些技能可以调用其他技能:

```markdown
# In SKILL.md:

## Step 5: Deep Dive (if needed)
If user wants more details:
```
task(
    description="Use financial-metrics skill to analyze the results",
    subagent_type="financial-analyst"
)
```
```

---

## 💡 最佳实践

### 技能设计

1. **单一职责**: 每个技能专注一个任务
2. **详细步骤**: 提供明确的执行步骤
3. **错误处理**: 说明常见问题和解决方案
4. **示例导向**: 包含实际使用示例

### 技能使用

1. **先浏览**: 启动后用 `/skills list` 查看可用技能
2. **按需读取**: 不要一次性读取所有技能详情
3. **灵活调整**: 技能是指导而非硬性规则
4. **持续优化**: 根据实际使用完善技能文档

### 技能维护

1. **版本控制**: 将skills目录加入git（推荐）
2. **团队共享**: 项目级技能可以团队共享
3. **定期更新**: 随着最佳实践演进更新技能
4. **文档先行**: 修改技能前先更新文档

---

## 🔧 故障排查

### 问题1: Agent不使用技能

**症状**: Agent不按技能指导执行  
**原因**: 
- 技能描述不够清晰
- 技能名称与任务不匹配

**解决**:
```markdown
# Bad:
description: Helps with analysis

# Good:
description: Analyze HKEX placement announcements - extract price, discount, subscribers
```

### 问题2: 技能未加载

**症状**: Skills列表为空  
**检查**:
```bash
# 验证目录存在
ls -la ~/.hkex-agent/hkex-agent/skills/

# 验证SKILL.md格式
cat ~/.hkex-agent/hkex-agent/skills/hkex-announcement/SKILL.md | head -10
```

**要求**:
- SKILL.md必须有YAML frontmatter（`---`包围）
- 必须包含 `name` 和 `description` 字段

### 问题3: 技能路径错误

**症状**: Agent找不到辅助脚本  
**解决**: 使用绝对路径
```markdown
# Bad:
python helper.py

# Good:
python ~/.hkex-agent/hkex-agent/skills/my-skill/helper.py
```

---

## 📊 技能效果监控

### 检查技能使用情况

启动CLI后:
```
> /memory read

检查agent.md中是否有技能使用记录
```

### 评估技能效果

**好的指标**:
- Agent主动提及技能名称
- 执行步骤与技能文档一致
- 输出质量提升

**需要改进**:
- Agent跳过某些步骤
- 输出格式不符合预期
- 经常需要用户纠正

**优化方法**:
1. 在技能文档中加强被跳过的步骤
2. 提供更多示例
3. 添加"常见错误"章节

---

## 🌟 技能库扩展

### 推荐新技能方向

**港股分析**:
- `insider-trading`: 董事交易分析
- `dividend-history`: 股息历史追踪
- `peer-comparison`: 同行对比分析

**自动化**:
- `daily-scan`: 每日公告扫描
- `alert-setup`: 价格/公告提醒设置
- `batch-analysis`: 批量分析多只股票

**报告生成**:
- `quarterly-summary`: 季度总结报告
- `investment-thesis`: 投资论文生成
- `risk-assessment`: 风险评估报告

### 贡献技能

如果你创建了有价值的技能:
1. 整理技能文档
2. 添加使用示例
3. 提交PR到项目
4. 帮助其他用户

---

## 📚 延伸阅读

- **合并方案**: `docs/SKILLS_SYSTEM_MERGE_PLAN.md` - 详细的系统设计
- **测试报告**: `docs/SKILLS_INTEGRATION_TEST_REPORT.md` - 功能验证
- **示例技能**: `examples/skills/` - 三个完整的HKEX技能
- **CLAUDE.md**: 开发者文档，包含技术细节

---

## ❓ 常见问题

**Q: Skills和工具(Tools)有什么区别?**  
A: 工具是代码函数(如`search_hkex_announcements`)，Skills是使用指南。Skills告诉Agent如何组合多个工具完成复杂任务。

**Q: 必须使用Skills吗?**  
A: 不必须。但Skills能显著提升Agent的工作质量和一致性。

**Q: 可以禁用某个技能吗?**  
A: 可以，删除或重命名SKILL.md文件（如改为SKILL.md.disabled）。

**Q: Skills会影响性能吗?**  
A: 影响很小。Agent只在需要时读取技能详情，不会占用大量token。

**Q: 如何更新技能?**  
A: 直接编辑SKILL.md文件，Agent重启后自动生效（或使用`/memory reload`）。

---

**祝你使用愉快！如有问题，请查看项目文档或提issue。**

