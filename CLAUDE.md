# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 项目概述

**deepagents-hk** (v0.2.5) 是基于 Deep Agents 框架开发的港股智能分析系统，专门处理港交所公告、PDF 文档解析和智能摘要生成。

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

# 启动并显示Agent思考过程
hkex --show-thinking

# 自动批准工具调用（跳过确认）
hkex --auto-approve

# 使用指定Agent ID
hkex --agent my-agent

# 列出所有Agent
hkex list

# 重置Agent
hkex reset --agent hkex-agent

# 运行测试
pytest

# 运行特定测试
pytest libs/deepagents/tests/unit_tests/test_pdf_truncation.py
pytest libs/deepagents/tests/integration_tests/test_subagent_middleware.py
pytest libs/deepagents-cli/tests/tools/test_fetch_url.py

# 代码检查和格式化
ruff check src/
ruff format src/
mypy src/

# 生成覆盖率报告
pytest --cov=src tests/
```

### 交互式命令（CLI内）
| 命令 | 说明 |
|------|------|
| `/help` | 显示帮助信息 |
| `/clear` | 清除对话历史，重置上下文 |
| `/tokens` | 显示当前Token使用情况 |
| `/skills list` | 列出可用技能 |
| `/skills show <name>` | 显示技能详情 |
| `/skills search <query>` | 搜索技能 |
| `/memory` | 显示内存配置路径 |
| `/quit` 或 `/exit` | 退出程序 |
| `!<command>` | 执行Shell命令 |
| `Ctrl+T` | 切换自动批准模式 |
| `Ctrl+O` | 切换工具输出显示 |
| `Ctrl+E` | 打开外部编辑器 |
| `Alt+Enter` | 多行输入换行 |

### 环境配置
创建 `.env` 文件，优先级: SiliconFlow > OpenAI > Anthropic

```bash
# ========== SiliconFlow (推荐) ==========
SILICONFLOW_API_KEY=your_api_key
SILICONFLOW_MODEL=deepseek-chat                    # 主Agent模型
SILICONFLOW_PDF_MODEL=Qwen/Qwen2.5-7B-Instruct     # PDF分析模型（轻量）
SILICONFLOW_REPORT_MODEL=Qwen/Qwen2.5-72B-Instruct # 报告生成模型（高质量）

# 模型参数（可选）
SILICONFLOW_TEMPERATURE=0.7          # 温度 (0.0-1.0)
SILICONFLOW_MAX_TOKENS=20000         # 最大输出tokens
SILICONFLOW_TOP_P=0.9                # Top-p采样
SILICONFLOW_API_TIMEOUT=60           # API超时（秒）
SILICONFLOW_API_RETRY=3              # 重试次数

# 子Agent独立温度（可选）
SILICONFLOW_PDF_TEMPERATURE=0.3      # PDF分析更确定性
SILICONFLOW_REPORT_TEMPERATURE=0.8   # 报告生成更创造性

# ========== OpenAI ==========
OPENAI_API_KEY=your_api_key
OPENAI_MODEL=gpt-5-mini

# ========== Anthropic ==========
ANTHROPIC_API_KEY=your_api_key
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929

# ========== MCP 集成（可选） ==========
ENABLE_MCP=true
MCP_CONFIG_PATH=mcp_config.json

# ========== Agent 目录配置（可选） ==========
HKEX_AGENT_DIR=.hkex-agent           # 自定义Agent目录名称
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

### 模型上下文窗口配置
```python
# 支持的模型及其上下文限制（tokens）
MODEL_CONTEXT_LIMITS = {
    # SiliconFlow
    "deepseek-chat": 163840,
    "deepseek-ai/DeepSeek-V3.1-Terminus": 163840,
    "deepseek-reasoner": 163840,
    "Qwen/Qwen2.5-7B-Instruct": 32768,
    "Qwen/Qwen2.5-32B-Instruct": 131072,
    "Qwen/Qwen2.5-72B-Instruct": 131072,
    "MiniMaxAI/MiniMax-M2": 186000,
    
    # OpenAI
    "gpt-5-mini": 128000,
    "gpt-5": 128000,
    "gpt-4o": 128000,
    "gpt-4.1": 128000,
    
    # Anthropic
    "claude-sonnet-4-5-20250929": 200000,
    "claude-opus-4": 200000,
}
```

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
├── __init__.py
├── agents/              # 代理核心逻辑
│   ├── __init__.py
│   ├── main_agent.py    # 主代理
│   └── subagents.py     # 子代理系统
├── api/                 # Python SDK API
│   ├── __init__.py
│   └── client.py
├── cli/                 # 命令行工具
│   ├── __init__.py
│   ├── __main__.py
│   ├── main.py          # CLI入口
│   ├── agent.py         # Agent创建
│   ├── commands.py      # 斜杠命令处理
│   ├── config.py        # CLI配置
│   ├── execution.py     # 任务执行
│   ├── file_ops.py      # 文件操作
│   ├── input.py         # 输入处理
│   ├── token_utils.py   # Token计算
│   ├── tools.py         # 工具包装
│   ├── ui.py            # UI组件
│   ├── project_utils.py # 项目检测工具
│   ├── agent_memory.py  # 双范围内存
│   └── skills/          # Skills系统
│       ├── __init__.py
│       ├── load.py      # 技能加载器
│       ├── middleware.py # 技能中间件
│       └── commands.py  # 技能CLI命令
├── config/              # 配置模块
│   ├── __init__.py
│   └── agent_config.py  # 多模型配置
├── prompts/             # 提示词模板
│   ├── __init__.py
│   ├── prompts.py
│   ├── main_system_prompt.md
│   └── hkex_modules/
│       └── __init__.py
├── services/            # 业务服务
│   ├── __init__.py
│   ├── hkex_api.py      # 港交所API客户端
│   └── pdf_parser.py    # PDF解析服务
└── tools/               # 工具集合
    ├── __init__.py
    ├── hkex_tools.py    # 港交所工具
    ├── pdf_tools.py     # PDF工具
    └── summary_tools.py # 摘要工具
```

### 测试目录结构
```
libs/
├── deepagents/
│   └── tests/
│       ├── unit_tests/
│       │   ├── test_middleware.py
│       │   ├── test_pdf_truncation.py
│       │   └── backends/
│       │       ├── test_store_backend.py
│       │       ├── test_state_backend.py
│       │       ├── test_filesystem_backend.py
│       │       └── test_composite_backend.py
│       └── integration_tests/
│           ├── test_deepagents.py
│           ├── test_hitl.py
│           ├── test_filesystem_middleware.py
│           ├── test_subagent_middleware.py
│           └── test_pdf_truncation_workflow.py
└── deepagents-cli/
    └── tests/
        ├── test_placeholder.py
        ├── test_file_ops.py
        └── tools/
            └── test_fetch_url.py
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
    main_model: str = "deepseek-chat"  # 主Agent (¥1.33/百万tokens)
    pdf_analyzer_model: str = "Qwen/Qwen2.5-7B-Instruct"  # PDF分析 (¥0.42/百万tokens)
    report_generator_model: str = "Qwen/Qwen2.5-72B-Instruct"  # 报告生成 (¥3.5/百万tokens)
    
    # 模型参数
    temperature: float = 0.7
    max_tokens: int = 20000
    api_timeout: int = 60
    api_retry_attempts: int = 3
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

## HKEX工具API

### 可用工具
| 工具 | 说明 |
|------|------|
| `search_hkex_announcements()` | 搜索公告（支持股票代码、日期范围） |
| `get_latest_hkex_announcements()` | 获取最新公告 |
| `get_stock_info()` | 获取股票信息 |
| `get_announcement_categories()` | 获取公告分类代码 |
| `get_cached_pdf_path()` | 检查PDF缓存 |
| `download_announcement_pdf()` | 下载公告PDF（智能缓存） |
| `extract_pdf_content()` | 提取PDF内容（自动截断） |
| `analyze_pdf_structure()` | 分析PDF结构 |
| `generate_summary_markdown()` | 生成Markdown摘要 |

### 日期计算规则（重要）
```bash
# 正确方式：使用date命令处理闰年
to_date=$(date +%Y%m%d)           # 当前日期
from_date=$(date -v-1y +%Y%m%d)   # macOS: 一年前
from_date=$(date -d "1 year ago" +%Y%m%d)  # Linux: 一年前

# 错误方式：手动减年份（闰年bug）
# 20240229 - 1 year = 20230229 ❌ (不存在的日期)
```

## 最佳实践

### 开发建议
- 所有模块使用 `from src.xxx` 导入
- 大型PDF处理会自动缓存，无需手动管理
- 使用子代理进行上下文隔离的专门化处理
- 利用MCP集成扩展外部功能

### 测试重点
- PDF截断功能测试: `pytest libs/deepagents/tests/unit_tests/test_pdf_truncation.py`
- 中间件测试: `pytest libs/deepagents/tests/unit_tests/test_middleware.py`
- 子代理集成测试: `pytest libs/deepagents/tests/integration_tests/test_subagent_middleware.py`
- HITL测试: `pytest libs/deepagents/tests/integration_tests/test_hitl.py`

### 故障排查
- 检查环境变量配置优先级（SiliconFlow > OpenAI > Anthropic）
- 查看PDF缓存目录权限
- 验证API密钥和模型可用性
- 监控上下文使用率避免超限
- 使用 `--show-thinking` 调试Agent推理过程
