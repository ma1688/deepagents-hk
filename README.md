# 🧠🤖 Deep Agents - HKEX 港股智能分析系统

本项目是基于 Deep Agents 框架开发的港股交易数据分析智能代理系统，专门用于处理港交所公告、PDF 文档解析和智能摘要生成。

## 项目概述

Deep Agents 采用 LLM 循环调用工具的架构，通过实现**规划工具**、**子代理**、**文件系统**和**详细提示词**四大核心组件，解决了传统代理在复杂任务中"浅层处理"的问题。

本项目专门针对港股市场数据分析进行了优化，主要功能包括：
- 📄 **PDF 公告解析**：智能解析港交所 PDF 公告文件（支持大型年报自动截断）
- 🔍 **内容摘要生成**：自动生成关键信息摘要
- 📊 **结构化数据提取**：从非结构化文档中提取结构化数据
- 💾 **缓存管理**：智能缓存已处理的文档和摘要
- ⚡ **智能截断**：大型 PDF（> 50k 字符）自动保存到缓存，防止 LLM token 溢出

<img src="deep_agents.png" alt="deep agent" width="600"/>

**技术致谢：本项目主要灵感来源于 Claude Code，旨在探索其通用化能力并进行专门化定制。**

## 安装

```bash
# 使用 uv (推荐)
uv sync

# 或使用 pip
pip install -r requirements.txt

# 或使用 poetry
poetry install
```

## 环境配置

创建 `.env` 文件并配置必要的环境变量：

```bash
# ========== LLM Provider API Keys ==========
# 优先级: SiliconFlow > OpenAI > Anthropic

# SiliconFlow (推荐 - 成本优化)
SILICONFLOW_API_KEY=your_siliconflow_api_key
SILICONFLOW_MODEL=deepseek-ai/DeepSeek-V3.1-Terminus  # 主Agent模型
SILICONFLOW_PDF_MODEL=Qwen/Qwen2.5-7B-Instruct       # PDF分析子Agent
SILICONFLOW_REPORT_MODEL=Qwen/Qwen2.5-72B-Instruct   # 报告生成子Agent

# OpenAI
OPENAI_API_KEY=your_openai_api_key
OPENAI_MODEL=gpt-4o  # 可选，默认gpt-5-mini

# Anthropic (Claude)
ANTHROPIC_API_KEY=your_anthropic_api_key
ANTHROPIC_MODEL=claude-sonnet-4-5-20250929  # 可选

# ========== 模型参数 ==========
SILICONFLOW_TEMPERATURE=0.7           # 温度 (0.0-1.0)
SILICONFLOW_MAX_TOKENS=20000          # 最大token数
SILICONFLOW_TOP_P=0.9                 # Top-p采样 (可选)
SILICONFLOW_FREQUENCY_PENALTY=0.0     # 频率惩罚 (可选)
SILICONFLOW_PRESENCE_PENALTY=0.0      # 存在惩罚 (可选)
SILICONFLOW_API_TIMEOUT=60            # API超时(秒)
SILICONFLOW_API_RETRY=3               # 重试次数

# 子Agent独立温度配置 (可选)
SILICONFLOW_PDF_TEMPERATURE=0.5       # PDF分析温度
SILICONFLOW_REPORT_TEMPERATURE=0.7    # 报告生成温度

# ========== UI配置 ==========
HKEX_ASCII_FONT=slant                 # ASCII横幅字体 (571种可选)
HKEX_RAINBOW=true                     # 彩虹渐变效果 (true/false)

# ========== 其他功能 ==========
TAVILY_API_KEY=your_tavily_api_key    # 网络搜索功能
```

详细配置说明请参考 `.env.example` 文件。

## 快速开始

### 港股公告分析示例

```python
import os
from hkex_agent import HKEXAnalyzer

# 初始化分析器
analyzer = HKEXAnalyzer()

# 分析 PDF 公告
result = analyzer.analyze_announcement("path/to/hkex_announcement.pdf")

print("摘要:", result.summary)
print("关键数据:", result.key_data)
print("市场影响:", result.market_impact)
```

### 基础 Deep Agents 使用

(运行以下示例需要 `pip install tavily-python`)

确保在环境变量中设置了 `TAVILY_API_KEY`。你可以 [在这里](https://www.tavily.com/) 生成一个。

```python
import os
from typing import Literal
from tavily import TavilyClient
from deepagents import create_deep_agent

tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

# Web search tool
def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """Run a web search"""
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )


# System prompt to steer the agent to be an expert researcher
research_instructions = """You are an expert researcher. Your job is to conduct thorough research, and then write a polished report.

You have access to an internet search tool as your primary means of gathering information.

## `internet_search`

Use this to run an internet search for a given query. You can specify the max number of results to return, the topic, and whether raw content should be included.
"""

# Create the deep agent
agent = create_deep_agent(
    tools=[internet_search],
    system_prompt=research_instructions,
)

# Invoke the agent
result = agent.invoke({"messages": [{"role": "user", "content": "What is langgraph?"}]})
```

See [examples/research/research_agent.py](examples/research/research_agent.py) for a more complex example.

The agent created with `create_deep_agent` is just a LangGraph graph - so you can interact with it (streaming, human-in-the-loop, memory, studio)
in the same way you would any LangGraph agent.

## 核心功能

**📋 规划与任务分解**

Deep Agents 内置 `write_todos` 工具，使代理能够将复杂任务分解为离散步骤，跟踪进度，并根据新信息调整计划。

**🗂️ 上下文管理**

文件系统工具（`ls`、`read_file`、`write_file`、`edit_file`、`glob`、`grep`）允许代理将大型上下文卸载到内存，防止上下文窗口溢出，并能够处理可变长度的工具结果。

**🔄 子代理生成**

内置 `task` 工具使代理能够生成专门的子代理进行上下文隔离。这保持了主代理上下文的清洁，同时仍能深入处理特定子任务。

**💾 长期记忆**

使用 LangGraph 的 Store 扩展跨线程的持久记忆。代理可以保存和检索之前对话中的信息。

## 港股专用功能

**📄 PDF 解析引擎**
- 智能识别港交所公告格式
- 提取财务数据、交易信息等关键内容
- 支持繁体中文和英文文档

**🔍 智能摘要生成**
- 自动识别公告类型和重要性
- 生成结构化摘要和市场影响分析
- 支持自定义摘要模板

**📊 数据提取与结构化**
- 财务指标自动提取
- 公司行动信息识别
- 市场事件分类标注

**⚡ 缓存优化**
- PDF 文档缓存机制
- 摘要结果持久化存储
- 增量更新支持

**🌈 用户体验优化**
- ASCII艺术字横幅 (571种字体可选)
- 彩虹渐变效果 (7色循环显示)
- 居中对齐的启动日志
- 自定义主题颜色支持

## 项目结构

```
deepagents-hk/
├── libs/
│   ├── deepagents/          # DeepAgents框架核心
│   │   ├── graph.py         # Agent图构建
│   │   ├── backends/        # 存储后端
│   │   └── middleware/      # 中间件
│   └── deepagents-cli/      # DeepAgents CLI工具
├── src/                     # HKEX应用代码 (作为src包)
│   ├── agents/              # 代理核心逻辑
│   │   ├── main_agent.py    # 主代理
│   │   └── subagents.py     # 子代理定义
│   ├── api/                 # API 接口
│   │   └── client.py        # 客户端
│   ├── cli/                 # 命令行工具 (src.cli包)
│   │   ├── config.py        # 配置和模型创建
│   │   ├── main.py          # 主入口
│   │   └── ...
│   ├── config/              # 配置模块
│   │   └── agent_config.py  # Agent模型配置
│   ├── services/            # 业务服务
│   │   ├── hkex_api.py      # 港交所 API
│   │   └── pdf_parser.py    # PDF 解析服务
│   ├── tools/               # 工具集合
│   │   ├── hkex_tools.py    # 港股专用工具
│   │   ├── pdf_tools.py     # PDF 处理工具
│   │   └── summary_tools.py # 摘要工具
│   └── prompts/             # 提示词模板
│       ├── main_system_prompt.md
│       └── pdf_analyzer_prompt.md
├── pdf_cache/               # PDF 缓存目录 (已 gitignore)
│   └── {stock_code}/        # 按股票代码分类
│       ├── {date}-{title}.pdf      # PDF 文件
│       ├── {date}-{title}.txt      # 文本缓存 (大型 PDF)
│       └── {date}-{title}_tables.json  # 表格缓存 (大型 PDF)
├── md/                      # 摘要存储目录 (已 gitignore)
├── docs/                    # 项目文档
├── .env                     # 环境变量配置
├── pyproject.toml           # 统一项目配置
└── README.md                # 项目说明
```

**重要说明**：
- 项目已统一到单一 `pyproject.toml` 配置
- `src` 目录作为完整的Python包，所有模块使用 `from src.xxx` 导入
- `hkex` 命令entry point: `src.cli.main:cli_main`
- 支持通过环境变量配置不同LLM模型和参数

## 开发指南

### 环境设置

```bash
# 克隆项目
git clone <repository-url>
cd deepagents-hk

# 安装依赖
uv sync

# 激活虚拟环境
source .venv/bin/activate  # Linux/Mac
# 或
.venv\Scripts\activate     # Windows
```

### 运行测试

```bash
# 运行所有测试
pytest

# 运行特定测试
pytest tests/test_pdf_parser.py

# 生成覆盖率报告
pytest --cov=src tests/
```

### 代码规范

本项目使用以下工具确保代码质量：

- **Ruff**: 代码检查和格式化
- **MyPy**: 类型检查
- **Black**: 代码格式化

```bash
# 运行代码检查
ruff check src/
mypy src/

# 格式化代码
ruff format src/
black src/
```

## 自定义 Deep Agents

### `model`

By default, `deepagents` uses `"claude-sonnet-4-5-20250929"`. You can customize this by passing any [LangChain model object](https://python.langchain.com/docs/integrations/chat/).

```python
from langchain.chat_models import init_chat_model
from deepagents import create_deep_agent

model = init_chat_model("openai:gpt-4o")
agent = create_deep_agent(
    model=model,
)
```

### `system_prompt`
Deep Agents come with a built-in system prompt. This is relatively detailed prompt that is heavily based on and inspired by [attempts](https://github.com/kn1026/cc/blob/main/claudecode.md) to [replicate](https://github.com/asgeirtj/system_prompts_leaks/blob/main/Anthropic/claude-code.md)
Claude Code's system prompt. It was made more general purpose than Claude Code's system prompt. The default prompt contains detailed instructions for how to use the built-in planning tool, file system tools, and sub agents.

Each deep agent tailored to a use case should include a custom system prompt specific to that use case as well. The importance of prompting for creating a successful deep agent cannot be overstated.

```python
from deepagents import create_deep_agent

research_instructions = """You are an expert researcher. Your job is to conduct thorough research, and then write a polished report.
"""

agent = create_deep_agent(
    system_prompt=research_instructions,
)
```

### `tools`

Just like with tool-calling agents, you can provide a deep agent with a set of tools that it has access to.

```python
import os
from typing import Literal
from tavily import TavilyClient
from deepagents import create_deep_agent

tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """Run a web search"""
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )

agent = create_deep_agent(
    tools=[internet_search]
)
```

### `middleware`
`create_deep_agent` is implemented with middleware that can be customized. You can provide additional middleware to extend functionality, add tools, or implement custom hooks. 

```python
from langchain_core.tools import tool
from deepagents import create_deep_agent
from langchain.agents.middleware import AgentMiddleware

@tool
def get_weather(city: str) -> str:
    """Get the weather in a city."""
    return f"The weather in {city} is sunny."

@tool
def get_temperature(city: str) -> str:
    """Get the temperature in a city."""
    return f"The temperature in {city} is 70 degrees Fahrenheit."

class WeatherMiddleware(AgentMiddleware):
  tools = [get_weather, get_temperature]

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-20250514",
    middleware=[WeatherMiddleware()]
)
```

### `subagents`

A main feature of Deep Agents is their ability to spawn subagents. You can specify custom subagents that your agent can hand off work to in the subagents parameter. Sub agents are useful for context quarantine (to help not pollute the overall context of the main agent) as well as custom instructions.

`subagents` should be a list of dictionaries, where each dictionary follow this schema:

```python
class SubAgent(TypedDict):
    name: str
    description: str
    prompt: str
    tools: Sequence[BaseTool | Callable | dict[str, Any]]
    model: NotRequired[str | BaseChatModel]
    middleware: NotRequired[list[AgentMiddleware]]
    interrupt_on: NotRequired[dict[str, bool | InterruptOnConfig]]

class CompiledSubAgent(TypedDict):
    name: str
    description: str
    runnable: Runnable
```

**SubAgent fields:**
- **name**: This is the name of the subagent, and how the main agent will call the subagent
- **description**: This is the description of the subagent that is shown to the main agent
- **prompt**: This is the prompt used for the subagent
- **tools**: This is the list of tools that the subagent has access to.
- **model**: Optional model name or model instance.
- **middleware** Additional middleware to attach to the subagent. See [here](https://docs.langchain.com/oss/python/langchain/middleware) for an introduction into middleware and how it works with create_agent.
- **interrupt_on** A custom interrupt config that specifies human-in-the-loop interactions for your tools.

**CompiledSubAgent fields:**
- **name**: This is the name of the subagent, and how the main agent will call the subagent
- **description**: This is the description of the subagent that is shown to the main agent  
- **runnable**: A pre-built LangGraph graph/agent that will be used as the subagent

#### Using SubAgent

```python
import os
from typing import Literal
from tavily import TavilyClient
from deepagents import create_deep_agent

tavily_client = TavilyClient(api_key=os.environ["TAVILY_API_KEY"])

def internet_search(
    query: str,
    max_results: int = 5,
    topic: Literal["general", "news", "finance"] = "general",
    include_raw_content: bool = False,
):
    """Run a web search"""
    return tavily_client.search(
        query,
        max_results=max_results,
        include_raw_content=include_raw_content,
        topic=topic,
    )

research_subagent = {
    "name": "research-agent",
    "description": "Used to research more in depth questions",
    "system_prompt": "You are a great researcher",
    "tools": [internet_search],
    "model": "openai:gpt-4o",  # Optional override, defaults to main agent model
}
subagents = [research_subagent]

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-20250514",
    subagents=subagents
)
```

#### Using CustomSubAgent

For more complex use cases, you can provide your own pre-built LangGraph graph as a subagent:

```python
# Create a custom agent graph
custom_graph = create_agent(
    model=your_model,
    tools=specialized_tools,
    prompt="You are a specialized agent for data analysis..."
)

# Use it as a custom subagent
custom_subagent = CompiledSubAgent(
    name="data-analyzer",
    description="Specialized agent for complex data analysis tasks",
    runnable=custom_graph
)

subagents = [custom_subagent]

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-20250514",
    tools=[internet_search],
    system_prompt=research_instructions,
    subagents=subagents
)
```

### `interrupt_on`
A common reality for agents is that some tool operations may be sensitive and require human approval before execution. Deep Agents supports human-in-the-loop workflows through LangGraph’s interrupt capabilities. You can configure which tools require approval using a checkpointer.

These tool configs are passed to our prebuilt [HITL middleware](https://docs.langchain.com/oss/python/langchain/middleware#human-in-the-loop) so that the agent pauses execution and waits for feedback from the user before executing configured tools.

```python
from langchain_core.tools import tool
from deepagents import create_deep_agent

@tool
def get_weather(city: str) -> str:
    """Get the weather in a city."""
    return f"The weather in {city} is sunny."

agent = create_deep_agent(
    model="anthropic:claude-sonnet-4-20250514",
    tools=[get_weather],
    interrupt_on={
        "get_weather": {
            "allowed_decisions": ["approve", "edit", "reject"]
        },
    }
)

```

## Deep Agents Middleware

Deep Agents are built with a modular middleware architecture. As a reminder, Deep Agents have access to:
- A planning tool
- A filesystem for storing context and long-term memories
- The ability to spawn subagents

Each of these features is implemented as separate middleware. When you create a deep agent with `create_deep_agent`, we automatically attach **TodoListMiddleware**, **FilesystemMiddleware** and **SubAgentMiddleware** to your agent.

Middleware is a composable concept, and you can choose to add as many or as few middleware to an agent depending on your use case. That means that you can also use any of the aforementioned middleware independently!

### TodoListMiddleware

Planning is integral to solving complex problems. If you’ve used claude code recently, you’ll notice how it writes out a To-Do list before tackling complex, multi-part tasks. You’ll also notice how it can adapt and update this To-Do list on the fly as more information comes in.

**TodoListMiddleware** provides your agent with a tool specifically for updating this To-Do list. Before, and while it executes a multi-part task, the agent is prompted to use the write_todos tool to keep track of what its doing, and what still needs to be done.

```python
from langchain.agents import create_agent
from langchain.agents.middleware import TodoListMiddleware

# TodoListMiddleware is included by default in create_deep_agent
# You can customize it if building a custom agent
agent = create_agent(
    model="anthropic:claude-sonnet-4-20250514",
    # Custom planning instructions can be added via middleware
    middleware=[
        TodoListMiddleware(
            system_prompt="Use the write_todos tool to..."  # Optional: Custom addition to the system prompt
        ),
    ],
)
```

### FilesystemMiddleware

Context engineering is one of the main challenges in building effective agents. This can be particularly hard when using tools that can return variable length results (ex. web_search, rag), as long ToolResults can quickly fill up your context window.
**FilesystemMiddleware** provides four tools to your agent to interact with both short-term and long-term memory.
- **ls**: List the files in your filesystem
- **read_file**: Read an entire file, or a certain number of lines from a file
- **write_file**: Write a new file to your filesystem
- **edit_file**: Edit an existing file in your filesystem

```python
from langchain.agents import create_agent
from deepagents.middleware.filesystem import FilesystemMiddleware


# FilesystemMiddleware is included by default in create_deep_agent
# You can customize it if building a custom agent
agent = create_agent(
    model="anthropic:claude-sonnet-4-20250514",
    middleware=[
        FilesystemMiddleware(
            backend=..., # Optional: customize storage backend
            system_prompt="Write to the filesystem when...",  # Optional custom system prompt override
            custom_tool_descriptions={
                "ls": "Use the ls tool when...",
                "read_file": "Use the read_file tool to..."
            }  # Optional: Custom descriptions for filesystem tools
        ),
    ],
)
```

### SubAgentMiddleware

Handing off tasks to subagents is a great way to isolate context, keeping the context window of the main (supervisor) agent clean while still going deep on a task. The subagents middleware allows you supply subagents through a task tool.

A subagent is defined with a name, description, system prompt, and tools. You can also provide a subagent with a custom model, or with additional middleware. This can be particularly useful when you want to give the subagent an additional state key to share with the main agent.

```python
from langchain_core.tools import tool
from langchain.agents import create_agent
from deepagents.middleware.subagents import SubAgentMiddleware


@tool
def get_weather(city: str) -> str:
    """Get the weather in a city."""
    return f"The weather in {city} is sunny."

agent = create_agent(
    model="claude-sonnet-4-20250514",
    middleware=[
        SubAgentMiddleware(
            default_model="claude-sonnet-4-20250514",
            default_tools=[],
            subagents=[
                {
                    "name": "weather",
                    "description": "This subagent can get weather in cities.",
                    "system_prompt": "Use the get_weather tool to get the weather in a city.",
                    "tools": [get_weather],
                    "model": "gpt-4.1",
                    "middleware": [],
                }
            ],
        )
    ],
)
```

For more complex use cases, you can also provide your own pre-built LangGraph graph as a subagent.

```python
# Create a custom LangGraph graph
def create_weather_graph():
    workflow = StateGraph(...)
    # Build your custom graph
    return workflow.compile()

weather_graph = create_weather_graph()

# Wrap it in a CompiledSubAgent
weather_subagent = CompiledSubAgent(
    name="weather",
    description="This subagent can get weather in cities.",
    runnable=weather_graph
)

agent = create_agent(
    model="anthropic:claude-sonnet-4-20250514",
    middleware=[
        SubAgentMiddleware(
            default_model="claude-sonnet-4-20250514",
            default_tools=[],
            subagents=[weather_subagent],
        )
    ],
)
```

## Sync vs Async

Prior versions of deepagents separated sync and async agent factories. 

`async_create_deep_agent` has been folded in to `create_deep_agent`.

**You should use `create_deep_agent` as the factory for both sync and async agents**


## MCP

The `deepagents` library can be ran with MCP tools. This can be achieved by using the [Langchain MCP Adapter library](https://github.com/langchain-ai/langchain-mcp-adapters).

**NOTE:** You will want to use `from deepagents import async_create_deep_agent` to use the async version of `deepagents`, since MCP tools are async

(To run the example below, will need to `pip install langchain-mcp-adapters`)

```python
import asyncio
from langchain_mcp_adapters.client import MultiServerMCPClient
from deepagents import create_deep_agent

async def main():
    # Collect MCP tools
    mcp_client = MultiServerMCPClient(...)
    mcp_tools = await mcp_client.get_tools()

    # Create agent
    agent = create_deep_agent(tools=mcp_tools, ....)

    # Stream the agent
    async for chunk in agent.astream(
        {"messages": [{"role": "user", "content": "what is langgraph?"}]},
        stream_mode="values"
    ):
        if "messages" in chunk:
            chunk["messages"][-1].pretty_print()

asyncio.run(main())
```

## 📄 PDF 智能截断功能

### 功能概述

为了防止大型 PDF（如年报）导致 LLM token 溢出，系统实现了智能截断机制：

- **自动检测**：对于文本 > 50k 字符或表格 > 200 行的 PDF，自动触发截断
- **完整保留**：全部内容保存到缓存文件（`.txt` 和 `_tables.json`）
- **预览返回**：工具返回前 5k 字符文本预览 + 前 5 个表格
- **清晰指引**：预览中包含完整路径和 `read_file()` 使用说明

### 工作原理

```python
# 1. 提取 PDF 内容（自动截断）
pdf_content = extract_pdf_content("path/to/large_annual_report.pdf")

# 2. 检查是否被截断
if pdf_content["truncated"]:
    print(f"预览文本: {pdf_content['text'][:100]}...")
    print(f"完整文本路径: {pdf_content['text_path']}")
    print(f"完整表格路径: {pdf_content['tables_path']}")
    
    # 3. 按需读取完整内容
    full_text = read_file(pdf_content["text_path"])
    full_tables = json.loads(read_file(pdf_content["tables_path"]))
else:
    # 小文档：直接使用全文
    full_text = pdf_content["text"]
    full_tables = pdf_content["tables"]
```

### 阈值配置

默认阈值（可在 `src/tools/pdf_tools.py` 中调整）：

```python
MAX_INLINE_TEXT_CHARS = 50_000  # 50k 字符 ≈ 12.5k tokens
MAX_INLINE_TABLE_ROWS = 200     # 表格总行数限制
TEXT_PREVIEW_CHARS = 5_000      # 预览长度
TABLE_PREVIEW_COUNT = 5         # 预览表格数量
```

### 缓存文件结构

```
pdf_cache/
└── 03800/
    ├── 2025-04-29-2024年报.pdf           # 原始 PDF
    ├── 2025-04-29-2024年报.txt           # 文本缓存（大型 PDF）
    └── 2025-04-29-2024年报_tables.json   # 表格缓存（JSON 格式）
```

### 向后兼容性

- **小型 PDF**（< 50k 字符）：行为完全不变，返回结构与现有一致
- **大型 PDF**：新增 `truncated`、`text_path`、`tables_path` 字段，不影响现有代码

### 性能优化

- **延迟写入**：仅截断时才写缓存，小文档零开销
- **原子写入**：临时文件 + 重命名，防止并发读取不完整数据
- **自动清理**：`cleanup_old_pdfs()` 同时清理 PDF 和缓存文件

### 测试验证

```bash
# 运行 PDF 截断功能测试
pytest libs/deepagents/tests/unit_tests/test_pdf_truncation.py -v
pytest libs/deepagents/tests/integration_tests/test_pdf_truncation_workflow.py -v
```
