# HKEX Agent - 港交所公告分析助手

基于 DeepAgents 的港交所公告分析助手，支持搜索、下载、分析港交所公告，并提供智能PDF缓存机制。

## 功能特性

- 🔍 **公告搜索**: 按股票代码、日期范围、关键词搜索港交所公告
- 📄 **PDF下载与分析**: 自动下载公告PDF，提取文本和表格
- 💾 **智能缓存**: PDF缓存机制，避免重复下载
- 📊 **报告生成**: 基于分析结果生成结构化报告
- 🤖 **子Agent支持**: PDF分析专家和报告生成专家
- 💬 **交互式CLI**: 友好的命令行交互界面
- 🐍 **Python API**: 提供程序化接口

## 安装

### 前置要求

- Python >= 3.11
- 至少配置一个模型供应商的API密钥

### 安装步骤

1. 克隆仓库并进入项目目录：

```bash
cd /path/to/deepagents-hk
```

2. 安装依赖：

```bash
# 使用 uv (推荐)
uv sync

# 或使用 pip
pip install -e src/hkex_agent
```

3. 配置环境变量：

创建 `.env` 文件或设置环境变量：

```bash
# 硅基流动 (推荐，优先级最高)
export SILICONFLOW_API_KEY=your_api_key_here
export SILICONFLOW_MODEL=deepseek-chat  # 可选，默认 deepseek-chat

# 或 OpenAI
export OPENAI_API_KEY=your_api_key_here
export OPENAI_MODEL=gpt-5-mini  # 可选，默认 gpt-5-mini

# 或 Anthropic
export ANTHROPIC_API_KEY=your_api_key_here
export ANTHROPIC_MODEL=claude-sonnet-4-5-20250929  # 可选
```

**注意**: 至少需要配置一个模型供应商的API密钥。优先级：硅基流动 > OpenAI > Anthropic

## 使用方法

### CLI 交互式界面

启动交互式CLI：

```bash
hkex
```

使用特定agent：

```bash
hkex --agent my-agent
```

启用自动批准（跳过HITL审批）：

```bash
hkex --auto-approve
```

#### CLI 命令

- `/help` - 显示帮助信息
- `/clear` - 清屏并重置对话
- `/tokens` - 显示Token使用统计
- `/quit` 或 `/exit` - 退出CLI

#### CLI 示例

```bash
# 搜索股票00673在2025年1月1日到10月8日的公告
搜索股票00673在2025年1月1日到10月8日的公告

# 下载并分析最新公告
下载并分析股票00673的最新公告PDF

# 生成报告
生成股票00673在2025年9月的公告摘要报告
```

### Python API

```python
from hkex_agent.api.client import HKEXAgentClient

# 创建客户端
client = HKEXAgentClient(agent_id="my-agent")

# 搜索公告
results = client.search_announcements(
    stock_code="00673",
    from_date="20250101",
    to_date="20251008"
)
print(results)

# 分析公告
response = client.analyze_announcement(
    "分析股票00673在2025年9月的所有公告，提取关键财务数据"
)
print(response)

# 生成报告
report = client.generate_report(
    "生成股票00673在2025年第三季度的公告摘要报告"
)
print(report)

# 流式响应
async for chunk in client.chat_async("搜索最新公告", stream=True):
    print(chunk, end="", flush=True)
```

## PDF缓存机制

### 缓存目录结构

```
~/.hkex-agent/{AGENT_NAME}/
├── memories/                  # 长期记忆
│   └── agent.md              # Agent自定义指令
└── pdf_cache/                # PDF缓存（持久化）
    ├── 00673/                # 按股票代码组织
    │   ├── 2025-10-08-翌日披露報表.pdf
    │   ├── 2025-09-30-中期業績公告.pdf
    │   └── ...
    ├── 00700/
    │   ├── 2025-10-15-季度報告.pdf
    │   └── ...
    └── ...
```

### 缓存特性

1. **自动缓存检查**: 下载前自动检查缓存，存在则直接返回
2. **文件命名**: `{公告日期}-{公告标题}.pdf`，日期格式为 `YYYY-MM-DD`
3. **目录组织**: 按股票代码组织，便于查找和管理
4. **跨会话持久化**: 使用FilesystemBackend，确保缓存跨会话保留
5. **HITL优化**: 缓存命中无需审批，仅首次下载需要用户批准

### 缓存管理

```python
# 获取缓存目录
cache_dir = client.get_cache_dir()
print(f"Cache directory: {cache_dir}")

# 清空缓存
deleted_count = client.clear_cache()
print(f"Deleted {deleted_count} cached PDFs")
```

## 项目结构

```
src/hkex_agent/
│   ├── agents/
│   │   ├── main_agent.py      # 主Agent创建
│   │   └── subagents.py       # 子Agent定义
│   ├── services/
│   │   ├── hkex_api.py        # 港交所API封装
│   │   └── pdf_parser.py      # PDF解析服务
│   ├── tools/
│   │   ├── hkex_tools.py      # HKEX工具
│   │   └── pdf_tools.py       # PDF处理工具
│   ├── cli/
│   │   ├── main.py            # CLI入口
│   │   ├── agent.py           # Agent创建
│   │   ├── config.py          # 配置管理
│   │   ├── execution.py       # 任务执行
│   │   ├── ui.py              # UI渲染
│   │   └── ...                # 其他CLI模块
│   └── api/
│       └── client.py          # Python API客户端
├── pyproject.toml
└── README.md
```

## 配置说明

### 模型供应商配置

#### 硅基流动 (SiliconFlow) - 推荐

硅基流动提供OpenAI兼容的API，支持多种模型（如deepseek-chat、qwen等），价格实惠。

```bash
export SILICONFLOW_API_KEY=your_api_key_here
export SILICONFLOW_MODEL=deepseek-chat  # 可选
```

获取API密钥: https://siliconflow.cn

#### OpenAI

```bash
export OPENAI_API_KEY=your_api_key_here
export OPENAI_MODEL=gpt-5-mini  # 可选
```

#### Anthropic

```bash
export ANTHROPIC_API_KEY=your_api_key_here
export ANTHROPIC_MODEL=claude-sonnet-4-5-20250929  # 可选
```

### Agent配置

Agent配置存储在 `~/.hkex-agent/{AGENT_NAME}/memories/agent.md`，可以自定义Agent的行为和指令。

## 工具说明

### HKEX工具

- `search_hkex_announcements` - 搜索公告
- `get_latest_hkex_announcements` - 获取最新公告
- `get_stock_info` - 获取股票信息
- `get_announcement_categories` - 获取分类信息

### PDF工具

- `get_cached_pdf_path` - 检查PDF缓存
- `download_announcement_pdf` - 下载公告PDF（智能缓存）
- `extract_pdf_content` - 提取PDF内容（文本+表格）
- `analyze_pdf_structure` - 分析PDF结构

## 子Agent

### pdf-analyzer

PDF分析专家，专门处理PDF内容分析：
- 提取文本和表格
- 分析PDF结构
- 识别关键信息

### report-generator

报告生成专家，专门生成结构化报告：
- 基于分析结果生成报告
- 支持多种格式（Markdown、JSON等）
- 综合多源信息

## 常见问题

### Q: PDF下载失败怎么办？

A: 检查网络连接和SSL配置。如果问题持续，可以尝试：
1. 检查缓存目录权限
2. 查看错误日志
3. 手动清理缓存后重试

### Q: 如何清理旧缓存？

A: 使用Python API：

```python
client = HKEXAgentClient()
deleted = client.clear_cache()
print(f"Deleted {deleted} files")
```

### Q: 支持哪些模型？

A: 支持所有通过LangChain兼容的模型：
- 硅基流动（deepseek-chat、qwen等）
- OpenAI（gpt-5-mini、gpt-4等）
- Anthropic（claude-sonnet等）

### Q: 如何自定义Agent行为？

A: 编辑 `~/.hkex-agent/{AGENT_NAME}/memories/agent.md` 文件，添加自定义指令。

## 开发

### 运行测试

```bash
cd src/hkex_agent
pytest
```

### 代码格式化

```bash
ruff format .
ruff check .
```

## 许可证

MIT License

## 贡献

欢迎提交Issue和Pull Request！

## 相关链接

- [DeepAgents](https://github.com/your-org/deepagents) - 基础框架
- [港交所披露易](https://www.hkexnews.hk) - 数据来源

