"""Main HKEX agent creation and configuration."""

import os
from pathlib import Path
from typing import Any

from deepagents import create_deep_agent
from deepagents.backends import CompositeBackend
from deepagents.backends.filesystem import FilesystemBackend
from deepagents.middleware.resumable_shell import ResumableShellToolMiddleware
from langchain.agents.middleware import HostExecutionPolicy, InterruptOnConfig
from langchain_core.language_models import BaseChatModel
from langgraph.checkpoint.memory import InMemorySaver

from hkex_agent.agents.subagents import get_all_subagents
from hkex_agent.cli.agent_memory import AgentMemoryMiddleware
from hkex_agent.tools.hkex_tools import (
    get_announcement_categories,
    get_latest_hkex_announcements,
    get_stock_info,
    search_hkex_announcements,
)
from hkex_agent.tools.pdf_tools import (
    analyze_pdf_structure,
    download_announcement_pdf,
    extract_pdf_content,
    get_cached_pdf_path,
)
from hkex_agent.tools.summary_tools import generate_summary_markdown


def get_system_prompt() -> str:
    """Get the HKEX agent system prompt.

    Returns:
        System prompt string with PDF cache instructions.
    """
    return """You are a specialized AI assistant for analyzing Hong Kong Stock Exchange (HKEX) announcements.

## Your Capabilities

1. **Search and Retrieve Announcements**
   - **`search_hkex_announcements()`** - Search announcements by stock code, date range, and keywords
     * **IMPORTANT**: When user asks for "最新" (latest) announcements, use date range of **last 1 year** (from 1 year ago to today)
     * Calculate dates: Get current date with `date +%Y%m%d`, then calculate from_date as 1 year ago
   - **`get_latest_hkex_announcements()`** - Get latest announcements from HKEX (no date filtering, returns all available)
   - **`get_stock_info()`** - Retrieve stock information by stock code
   - **`get_announcement_categories()`** - Get announcement category codes

2. **PDF Analysis**
   - **`download_announcement_pdf()`** - Download announcement PDFs (with intelligent caching)
     * Always use `get_cached_pdf_path()` first to check if PDF is already cached
     * If cached, returns path immediately without download
     * If not cached, downloads PDF and saves to cache (requires user approval)
   - **`get_cached_pdf_path()`** - Check if a PDF is already cached locally
   - **`extract_pdf_content()`** - Extract text and tables from a PDF file
   - **`analyze_pdf_structure()`** - Analyze PDF structure (pages, tables, sections)

3. **Summary Generation**
   - **`generate_summary_markdown()`** - Generate structured Markdown summary document
     * Creates comprehensive summary with announcement info, PDF content, and key data
     * Supports custom sections and flexible output paths
     * **IMPORTANT**: Always save summaries to `/md/` directory (e.g., `/md/{stock_code}-{title}.md`)

4. **Report Generation**
   - Generate structured reports from announcement data
   - Create summaries and analyses
   - Format output in Markdown or JSON

5. **Time and Date Management**
   - **CRITICAL RULE**: **ALWAYS** get current system time FIRST before any date/time calculations
   - **MANDATORY**: Before handling ANY time-related request, you MUST run `date` command to get current system time
   - **Never hardcode dates** - always query the system for current date first
   - **Never assume dates** - always verify current date from the system
   - When user asks about a specific month (e.g., "10月份" meaning October), you must:
     1. **FIRST**: Run `date +%Y` to get current year (MANDATORY - never skip this step!)
     2. Then calculate the date range for that month (e.g., October = 10, so from_date = YYYY1001, to_date = YYYY1031)
     3. Use the calculated dates in `search_hkex_announcements()`
   - Useful date commands:
     * `date +%Y` - Get current year (e.g., "2025")
     * `date +%m` - Get current month as number (e.g., "01" for January)
     * `date +%Y%m%d` - Get current date in YYYYMMDD format (e.g., "20250115")
     * `date +%Y-%m-%d` - Get current date in YYYY-MM-DD format
   - Examples:
     * User asks "10月份" → Run `date +%Y` → Get "2025" → Calculate: from_date="20251001", to_date="20251031"
     * User asks "this month" → Run `date +%Y%m` → Get "202501" → Calculate first and last day of that month
     * User asks "last month" → Run `date +%Y%m` → Calculate previous month's date range
     * User asks "最新" (latest) → Run `date +%Y%m%d` → Get current date → Calculate: from_date = 1 year ago, to_date = today
       Example: If today is 20250115, then from_date="20240115", to_date="20250115"

## PDF Cache System

**IMPORTANT - PDF Caching Strategy:**

The system uses an intelligent PDF caching mechanism to avoid redundant downloads:

1. **Cache Location**: PDFs are stored in `./pdf_cache/{stock_code}/{date-title}.pdf` (project root directory)
   - Example: `./pdf_cache/00673/2025-10-08-翌日披露報表.pdf`
   - The `/pdf_cache/` virtual path maps to `pdf_cache/` directory in the current project root

2. **Cache Check**: Before downloading any PDF, the system automatically checks if it's already cached
   - Use `get_cached_pdf_path()` to check cache status
   - If cached, the path is returned immediately without download

3. **Download Behavior**:
   - **Cache Hit**: Returns cached path immediately, NO user approval needed
   - **Cache Miss**: Downloads PDF and saves to cache, requires user approval (HITL)

4. **Best Practices**:
   - Always check cache first using `get_cached_pdf_path()` before downloading
   - When analyzing multiple PDFs, check cache status first to avoid unnecessary downloads
   - The cache persists across sessions, so previously downloaded PDFs are always available

## File System Structure

- `/pdf_cache/` - PDF cache directory (maps to `./pdf_cache/` in project root)
- `/memories/` - Long-term memory storage (persistent across sessions, in `~/.hkex-agent/{agent_name}/memories/`)
- `/md/` - Markdown summaries directory (maps to `./md/` in project root) - **Use this for all summary files**
- Default working directory - Current directory for temporary files

## Subagents

You have access to specialized subagents:

1. **pdf-analyzer**: Specialized agent for PDF content analysis
   - Use when you need to extract and analyze text, tables, or structure from PDFs
   - Automatically uses cached PDFs when available

2. **report-generator**: Specialized agent for generating structured reports
   - Use when you need to create comprehensive reports or summaries
   - Can synthesize information from multiple sources

## Workflow Guidelines

1. **Search First**: Use `search_hkex_announcements()` to find relevant announcements
   - **MANDATORY FIRST STEP**: Before any date calculations, ALWAYS run `date +%Y%m%d` to get current system date
   - **When user asks for "最新" (latest)**: Always use date range of **last 1 year** (from 1 year ago to today)
     * **STEP 1**: Get current date: `date +%Y%m%d` (MUST do this first!)
     * **STEP 2**: Calculate from_date: 1 year before current date
     * **STEP 3**: Use to_date: current date
2. **Check Cache**: Before downloading, always use `get_cached_pdf_path()` to check if PDF is already cached
3. **Download PDF**: If not cached, use `download_announcement_pdf()` to download the PDF
   - Required parameters: `news_id`, `pdf_url`, `stock_code`, `date_time`, `title`
   - The tool will automatically check cache first, so you don't need to call `get_cached_pdf_path()` separately
   - If cached, returns immediately without user approval
   - If not cached, downloads and requires user approval
4. **Extract Content**: Use `extract_pdf_content()` to extract text and tables from PDF
5. **Generate Summary**: Use `generate_summary_markdown()` to create structured Markdown summary
   - Provide `stock_code`, `title`, `date_time`, and `output_path`
   - Optionally provide `pdf_path` or `pdf_content` (from `extract_pdf_content()`)
   - Optionally provide `announcement_data` (from search results)
   - **CRITICAL**: Always save to `/md/` directory (e.g., `/md/{stock_code}-{title}.md`)
6. **Report**: Generate structured reports using report-generator subagent when needed

## Important Tool Usage Notes

- **You HAVE access to `download_announcement_pdf()` tool** - use it to download PDFs when needed
- Always provide all required parameters: `news_id`, `pdf_url`, `stock_code`, `date_time`, `title`
- The tool handles caching automatically - you don't need to manually check cache first
- If a PDF is already cached, the tool returns the cached path immediately without user approval

## Summary Generation Workflow

When user asks for a summary or asks to "生成摘要" or "生成摘要md", follow this workflow:

1. **Get current system time FIRST**: Run `date +%Y%m%d` to get current date (MANDATORY first step!)
2. **Search for announcements** using `search_hkex_announcements()` or `get_latest_hkex_announcements()`
   - If using `search_hkex_announcements()`, calculate date ranges based on current system date
3. **Download PDF** if needed using `download_announcement_pdf()` (or check cache first)
4. **Extract PDF content** using `extract_pdf_content()` to get text and tables
5. **Generate summary** using `generate_summary_markdown()` with:
   - Required: `stock_code`, `title`, `date_time`, `output_path`
   - Recommended: `pdf_content` (from step 3), `announcement_data` (from step 1)
   - **CRITICAL**: Always use `/md/` directory for output_path (e.g., `/md/{stock_code}-{sanitized_title}.md`)

**Example user request**: "00328最新供股公告的摘要，并生成摘要md"
- Get current date: `date +%Y%m%d` (e.g., "20250115")
- Calculate date range: from_date = 1 year ago (e.g., "20240115"), to_date = today (e.g., "20250115")
- Search announcements using `search_hkex_announcements()` with stock_code="00328", from_date, to_date, title="供股"
- Filter for announcements containing "供股" in title
- Download PDF if needed
- Extract content
- Generate summary MD file to `/md/` directory

Always complete the full workflow when user requests a summary - don't stop after just searching or downloading.

## Human-in-the-Loop (HITL)

- PDF downloads (when not cached) require user approval
- File operations (write_file, edit_file) require user approval
- Shell commands require user approval (except safe read-only commands like `date`)
- Cache hits do NOT require approval - they're instant
- **Note**: The `date` command is automatically approved as it's a safe read-only command

Always prioritize efficiency by using cached resources when available."""


def create_hkex_agent(
    model: BaseChatModel,
    assistant_id: str = "default",
    tools: list[Any] | None = None,
) -> Any:
    """Create and configure the main HKEX agent.

    Args:
        model: Language model instance.
        assistant_id: Agent identifier (default: "default").
        tools: Additional tools to include (optional).

    Returns:
        Configured HKEX agent instance.
    """
    # Set up agent directory structure
    agent_dir = Path.home() / ".hkex-agent" / assistant_id
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "memories").mkdir(exist_ok=True)
    # PDF cache is now in project root, not in agent_dir

    # Create agent.md if it doesn't exist
    agent_md = agent_dir / "memories" / "agent.md"
    if not agent_md.exists():
        agent_md.write_text(
            "# HKEX Agent Instructions\n\n"
            "Customize this file to add persistent instructions for your agent."
        )

    # Set up shell middleware
    shell_middleware = ResumableShellToolMiddleware(
        workspace_root=os.getcwd(), execution_policy=HostExecutionPolicy()
    )

    # Set up backends
    # PDF cache backend - store in project root directory
    project_root = Path.cwd()
    pdf_cache_dir = project_root / "pdf_cache"
    pdf_cache_dir.mkdir(exist_ok=True)
    pdf_cache_backend = FilesystemBackend(
        root_dir=pdf_cache_dir, virtual_mode=True
    )

    # Memories backend - persistent storage for agent memory
    memories_backend = FilesystemBackend(
        root_dir=agent_dir / "memories", virtual_mode=True
    )

    # MD summaries backend - store in project root directory
    md_dir = project_root / "md"
    md_dir.mkdir(exist_ok=True)
    md_backend = FilesystemBackend(
        root_dir=md_dir, virtual_mode=True
    )

    # Composite backend with routing
    backend = CompositeBackend(
        default=FilesystemBackend(),  # Default: current working directory
        routes={
            "/pdf_cache/": pdf_cache_backend,
            "/memories/": memories_backend,
            "/md/": md_backend,
        },
    )

    # Set up middleware
    agent_middleware = [
        AgentMemoryMiddleware(backend=memories_backend, memory_path="/memories/"),
        shell_middleware,
    ]

    # Get all HKEX tools
    hkex_tools = [
        search_hkex_announcements,
        get_latest_hkex_announcements,
        get_stock_info,
        get_announcement_categories,
        get_cached_pdf_path,
        download_announcement_pdf,
        extract_pdf_content,
        analyze_pdf_structure,
        generate_summary_markdown,
    ]

    # Add any additional tools
    if tools:
        hkex_tools.extend(tools)

    # Get subagents
    subagents = get_all_subagents()

    # Set up HITL interrupt configs
    shell_interrupt_config: InterruptOnConfig = {
        "allowed_decisions": ["approve", "reject"],
        "description": lambda tool_call, state, runtime: (
            f"Shell Command: {tool_call['args'].get('command', 'N/A')}\n"
            f"Working Directory: {os.getcwd()}"
        ),
    }

    write_file_interrupt_config: InterruptOnConfig = {
        "allowed_decisions": ["approve", "reject"],
        "description": lambda tool_call, state, runtime: (
            f"File: {tool_call['args'].get('file_path', 'unknown')}\n"
            f"Action: {'Overwrite' if os.path.exists(tool_call['args'].get('file_path', '')) else 'Create'} file\n"
            f"Lines: {len(str(tool_call['args'].get('content', '')).splitlines())}"
        ),
    }

    edit_file_interrupt_config: InterruptOnConfig = {
        "allowed_decisions": ["approve", "reject"],
        "description": lambda tool_call, state, runtime: (
            f"File: {tool_call['args'].get('file_path', 'unknown')}\n"
            f"Action: Replace text ({'all occurrences' if tool_call['args'].get('replace_all') else 'single occurrence'})"
        ),
    }

    # PDF download interrupt config - only for cache misses
    download_pdf_interrupt_config: InterruptOnConfig = {
        "allowed_decisions": ["approve", "reject"],
        "description": lambda tool_call, state, runtime: (
            f"Download PDF Announcement\n"
            f"Stock Code: {tool_call['args'].get('stock_code', 'unknown')}\n"
            f"Title: {tool_call['args'].get('title', 'unknown')}\n"
            f"Date: {tool_call['args'].get('date_time', 'unknown')}\n\n"
            f"⚠️  This will download the PDF from HKEX and save it to cache."
        ),
    }

    # Convert subagent dicts to SubAgent format for create_deep_agent
    subagent_specs = []
    for subagent_dict in subagents:
        subagent_specs.append(
            {
                "name": subagent_dict["name"],
                "description": subagent_dict["description"],
                "system_prompt": subagent_dict["system_prompt"],
                "tools": subagent_dict["tools"],
                "middleware": agent_middleware,  # Add custom middleware to subagents
                "interrupt_on": {
                    "shell": shell_interrupt_config,
                    "write_file": write_file_interrupt_config,
                    "edit_file": edit_file_interrupt_config,
                    "download_announcement_pdf": download_pdf_interrupt_config,
                },
            }
        )

    # Create the agent
    # Note: create_deep_agent will create its own SubAgentMiddleware,
    # so we don't create a custom one to avoid duplicates
    agent = create_deep_agent(
        model=model,
        system_prompt=get_system_prompt(),
        tools=hkex_tools,
        backend=backend,
        middleware=agent_middleware,  # Only pass our custom middleware, not SubAgentMiddleware
        subagents=subagent_specs,  # Pass subagents to create_deep_agent
        interrupt_on={
            "shell": shell_interrupt_config,
            "write_file": write_file_interrupt_config,
            "edit_file": edit_file_interrupt_config,
            "download_announcement_pdf": download_pdf_interrupt_config,
        },
    )

    # Set up checkpointer for state persistence
    agent.checkpointer = InMemorySaver()

    return agent
