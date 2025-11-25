# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

**deepagents-hk** 是基于 Deep Agents 框架开发的港股智能分析系统，专门处理港交所公告、PDF 文档解析和智能摘要生成。

**上游同步记录**:
- 2025-11-25: ✅ 上下文窗口分数、工具返回字符串、Windows路径修复、依赖升级 (deec90d, 0d298da, d13e341)
- 2025-11-20: ✅ Skills系统和双范围内存 (4c4a552)
- 2025-11-11: ✅ 移植子代理错误处理优化 (766c41c)
- 2025-11-11: ✅ 移植 fetch_url 网页抓取工具 (e63487e)
- ⏭️ HITL并发修复暂不需要（无并发场景）

## 核心架构

### 多层代理架构
- **主代理** (`src/agents/main_agent.py`): 协调整体工作流程，处理用户请求
- **子代理系统** (`src/agents/subagents.py`): 专门化的子代理（PDF分析、报告生成）
- **上下文隔离**: 每个代理使用独立的上下文窗口

### 主要组件
- **CLI入口** (`src/cli/main.py`): 命令行交互界面
- **工具层** (`src/tools/`): 港股API、PDF处理、摘要生成工具
- **服务层** (`src/services/`): 港交所API客户端、PDF解析服务
- **配置层** (`src/config/agent_config.py`): 多模型配置和成本优化

## 开发命令

### 安装与设置
```bash
# 安装依赖
uv sync

# 激活虚拟环境
source .venv/bin/activate  # Linux/Mac
```

### 常用开发命令
```bash
# 启动HKEX交互式命令行
hkex

# 运行测试
pytest

# 运行特定测试
pytest libs/deepagents/tests/unit_tests/test_pdf_truncation.py

# 代码检查和格式化
ruff check src/
ruff format src/
mypy src/

# 生成覆盖率报告
pytest --cov=src tests/
```

### 环境配置
创建 `.env` 文件，优先级: SiliconFlow > OpenAI > Anthropic

```bash
# SiliconFlow (推荐)
SILICONFLOW_API_KEY=your_api_key
SILICONFLOW_MODEL=deepseek-ai/DeepSeek-V3.1-Terminus
SILICONFLOW_PDF_MODEL=Qwen/Qwen2.5-7B-Instruct
SILICONFLOW_REPORT_MODEL=Qwen/Qwen2.5-72B-Instruct

# MCP 集成（可选）
ENABLE_MCP=true
MCP_CONFIG_PATH=mcp_config.json
```

## 核心特性

### 智能PDF处理
- 自动识别港交所公告格式，支持繁体中文
- 大型PDF智能截断 (>50k字符)，自动保存到 `pdf_cache/`
- 完整内容保留，预览返回前5k字符 + 前5个表格

### 多模型支持
- 支持SiliconFlow、OpenAI、Anthropic多个提供商
- 不同任务使用不同模型优化成本
- 实时上下文窗口监控，颜色预警系统

### Skills系统 (新增 2025-11-20)
- **可重用技能库**: 港股分析专用技能（公告、CCASS、财务指标）
- **渐进式披露**: Agent先看技能列表，需要时读取详情
- **用户级和项目级**: 支持全局和项目特定技能
- **YAML frontmatter**: 标准化技能元数据
- **示例技能**: `examples/skills/` 包含3个HKEX专用技能

### 双范围内存 (新增 2025-11-20)
- **用户级内存**: `~/.hkex-agent/{agent}/memories/agent.md` - 个性、风格、通用行为
- **项目级内存**: `[project]/.hkex-agent/agent.md` - 项目特定指令和约定
- **优先级**: 项目内存优先于用户内存
- **自动检测**: 根据项目根目录自动加载项目内存

### MCP集成
- 支持外部MCP服务器扩展功能
- CCASS数据分析集成示例
- 动态工具加载机制

## 项目结构

### src目录结构
```
src/
├── agents/          # 代理核心逻辑
├── cli/             # 命令行工具 (入口: main.py)
│   ├── skills/      # Skills系统 (新增)
│   │   ├── load.py       # 技能加载器
│   │   ├── middleware.py # 技能中间件
│   │   └── commands.py   # 技能CLI命令
│   ├── project_utils.py  # 项目检测工具 (新增)
│   └── agent_memory.py   # 双范围内存 (更新)
├── config/          # 配置模块
├── services/        # 业务服务
├── tools/           # 工具集合
└── prompts/         # 提示词模板
```

### 重要配置
- **统一配置**: `pyproject.toml` 管理所有依赖
- **入口点**: `hkex = "src.cli.main:cli_main"`
- **包结构**: `src` 作为完整Python包，使用 `from src.xxx` 导入

## Skills系统使用

### 技能目录结构
```
~/.hkex-agent/{agent}/
├── memories/
│   └── agent.md              # 用户级内存
├── pdf_cache/                # PDF缓存（保持现有）
└── skills/                   # ✨ 技能目录 (新增)
    ├── hkex-announcement/
    │   ├── SKILL.md          # 技能文档
    │   └── helpers.py        # 辅助脚本（可选）
    ├── ccass-tracking/
    │   └── SKILL.md
    └── financial-metrics/
        └── SKILL.md

[project]/.hkex-agent/
└── agent.md                  # ✨ 项目级内存 (新增)
```

### 创建自定义技能

**1. 复制示例技能**:
```bash
# 从examples复制到用户目录
cp -r examples/skills/hkex-announcement ~/.hkex-agent/hkex-agent/skills/
cp -r examples/skills/ccass-tracking ~/.hkex-agent/hkex-agent/skills/
cp -r examples/skills/financial-metrics ~/.hkex-agent/hkex-agent/skills/
```

**2. 创建新技能**:
```bash
mkdir -p ~/.hkex-agent/hkex-agent/skills/my-skill
cat > ~/.hkex-agent/hkex-agent/skills/my-skill/SKILL.md << 'EOF'
---
name: my-skill
description: Brief description of what this skill does
---

# My Skill

## When to Use
...

## Process
...
EOF
```

**3. Agent自动识别**:
- Agent启动时自动加载技能列表
- 系统提示词包含所有可用技能
- Agent根据任务选择合适技能

### 双范围内存使用

**用户级内存** (`~/.hkex-agent/{agent}/memories/agent.md`):
```markdown
你是港股分析专家。

## 风格
- 简洁直接，避免冗长
- 优先使用表格展示数据
- 始终使用繁体中文处理港交所文档

## 偏好
- 配售分析重点关注折让率和认购人
- CCASS变化>5%视为重大变动
- 财务指标对比至少3个季度
```

**项目级内存** (`[project]/.hkex-agent/agent.md`):
```markdown
# 本项目: 港股配售追踪系统

## 项目约定
- 所有分析保存到 `analysis/` 目录
- 使用 Markdown 格式输出
- 图表使用 Mermaid 语法

## 优先使用技能
- hkex-announcement-analysis（配售公告）

## 数据源
- 优先使用本地PDF缓存
- CCASS数据使用MCP服务器
```

## 缓存机制

### PDF缓存 (`pdf_cache/`)
```
pdf_cache/
└── {stock_code}/
    ├── {date}-{title}.pdf           # 原始PDF
    ├── {date}-{title}.txt           # 文本缓存（大型PDF）
    └── {date}-{title}_tables.json   # 表格缓存
```

### 自动清理
使用 `cleanup_old_pdfs()` 同时清理PDF和缓存文件

## 子代理配置

子代理模型配置在 `src/config/agent_config.py`:

```python
@dataclass
class SubAgentModelConfig:
    main_model: str = "deepseek-chat"  # 主Agent
    pdf_analyzer_model: str = "Qwen/Qwen2.5-7B-Instruct"  # PDF分析
    report_generator_model: str = "Qwen/Qwen2.5-72B-Instruct"  # 报告生成
```

## 上下文管理

### 实时监控
- 底部工具栏显示上下文使用情况
- 智能颜色预警：绿色(<50%) / 橙色(50-80%) / 红色(>80%)
- `/tokens` 命令查看详细token使用

### 自动摘要机制
- 对话历史达到170k tokens时触发自动摘要
- 保留最近6条消息，压缩历史对话
- 建议在85%时主动使用 `/clear` 清理

## 最佳实践

### 开发建议
- 所有模块使用 `from src.xxx` 导入
- 大型PDF处理会自动缓存，无需手动管理
- 使用子代理进行上下文隔离的专门化处理
- 利用MCP集成扩展外部功能

### 测试重点
- PDF截断功能测试
- 多模型配置验证
- 上下文管理系统测试
- MCP集成功能测试

### 故障排查
- 检查环境变量配置优先级
- 查看PDF缓存目录权限
- 验证API密钥和模型可用性
- 监控上下文使用率避免超限