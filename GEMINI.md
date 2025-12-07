# Deep Agents - HKEX 港股智能分析系统 Context

## Project Overview
**Deep Agents - HKEX** is an intelligent agent system designed to analyze Hong Kong Stock Exchange (HKEX) data. It leverages the **Deep Agents** framework (built on **LangGraph**) to process announcements, parse PDFs (with smart truncation for large files), and generate structured insights.

### Key Features
*   **Intelligent Analysis**: Analyzes HKEX announcements and financial reports using LLMs (SiliconFlow/DeepSeek, OpenAI, Anthropic).
*   **Skills System**: Modular, reusable capabilities (e.g., CCASS tracking, financial metrics) defined in Markdown/YAML.
*   **Dual-Scope Memory**: Separates user preferences (User Memory) from project-specific rules (Project Memory).
*   **Smart PDF Handling**: Automatically caches and truncates large PDFs to avoid token limits, preserving full content on disk.
*   **Context Monitoring**: Real-time tracking of token usage with visual alerts in the CLI.
*   **MCP Integration**: Supports the Model Context Protocol to extend capabilities with external tools (e.g., CCASS analysis).

## Architecture
*   **Core Framework**: `libs/deepagents` (based on LangChain/LangGraph).
*   **Application Logic**: `src/` (Agent definitions, tools, services, CLI).
*   **Entry Point**: `src.cli.main:cli_main` (exposed as `hkex` command).
*   **Storage**:
    *   `pdf_cache/`: Local cache for downloaded PDFs and extracted text/tables.
    *   `md/`: Generated markdown summaries.
    *   `~/.hkex-agent/`: User-level configuration and memory.
    *   `.hkex-agent/` (in project): Project-level configuration and memory.

## Building and Running

### Prerequisites
*   Python 3.11+
*   `uv` (recommended) or `pip` / `poetry`

### Installation
```bash
uv sync
# OR
pip install -e .
```

### Configuration
1.  Copy `.env.example` to `.env`.
2.  Configure API keys (SiliconFlow, OpenAI, Anthropic, Tavily).
3.  (Optional) Enable MCP in `.env` and configure `mcp_config.json`.

### Running the CLI
```bash
# Start the interactive agent
hkex

# CLI Flags
hkex --show-thinking   # Show agent reasoning
hkex --auto-approve    # Disable human confirmation for tools
```

### Running Tests
```bash
# Run all tests
pytest

# Run specific tests
pytest tests/test_pdf_parser.py
```

## Development Conventions

### Code Quality
*   **Linting/Formatting**: `ruff check src/`, `ruff format src/`
*   **Type Checking**: `mypy src/`
*   **Style**: Adheres to `ruff` default configurations (Google-style docstrings).

### Directory Structure
*   `libs/deepagents/`: Core reusable agent framework.
*   `src/agents/`: Main agent and sub-agent definitions.
*   `src/tools/`: Tool implementations (HKEX search, PDF processing).
*   `src/cli/`: CLI implementation (UI, input handling).
*   `docs/`: Comprehensive documentation (Skills guide, MCP testing, etc.).
*   `examples/skills/`: Example skill definitions.

### Skills System
*   Skills are defined in directories with a `SKILL.md` file.
*   Located in `~/.hkex-agent/hkex-agent/skills/` (user) or project-specific paths.
*   Use `hkex` CLI commands `/skills list` to view available skills.

### Memory Management
*   **User Memory**: `~/.hkex-agent/hkex-agent/memories/agent.md`
*   **Project Memory**: `[project_root]/.hkex-agent/agent.md`
