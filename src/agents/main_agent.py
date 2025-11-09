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

from .subagents import get_all_subagents
from src.cli.agent_memory import AgentMemoryMiddleware
from src.tools.hkex_tools import (
    get_announcement_categories,
    get_latest_hkex_announcements,
    get_stock_info,
    search_hkex_announcements,
)
from src.tools.pdf_tools import (
    analyze_pdf_structure,
    download_announcement_pdf,
    extract_pdf_content,
    get_cached_pdf_path,
)
from src.prompts.prompts import get_main_system_prompt
from src.tools.summary_tools import generate_summary_markdown


def get_system_prompt() -> str:
    """Get the HKEX agent system prompt.

    Returns:
        System prompt string with PDF cache instructions.
    """
    return get_main_system_prompt()


async def create_hkex_agent(
    model: BaseChatModel,
    assistant_id: str = "default",
    tools: list[Any] | None = None,
    enable_mcp: bool = False,
) -> Any:
    """Create and configure the main HKEX agent.

    Args:
        model: Language model instance.
        assistant_id: Agent identifier (default: "default").
        tools: Additional tools to include (optional).
        enable_mcp: Enable MCP tools integration (default: False).

    Returns:
        Configured HKEX agent instance.
    """
    # Set up agent directory structure
    agent_dir = Path.home() / ".hkex-agent" / assistant_id
    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "memories").mkdir(exist_ok=True)
    # PDF cache is now in project root, not in agent_dir

    # Create agent.md if it doesn't exist
    from src.prompts.prompts import get_default_agent_md
    
    agent_md = agent_dir / "memories" / "agent.md"
    if not agent_md.exists():
        agent_md.write_text(get_default_agent_md())

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

    # ========== Load MCP tools if enabled ==========
    if enable_mcp:
        try:
            from langchain_mcp_adapters.client import MultiServerMCPClient
            import json
            
            # 1. Read MCP configuration
            mcp_config_path = os.getenv("MCP_CONFIG_PATH", "mcp_config.json")
            with open(mcp_config_path, "r") as f:
                mcp_config = json.load(f)
            
            # 2. Convert config to connections format
            connections = {}
            for server_name, server_config in mcp_config.get("mcpServers", {}).items():
                if not server_config.get("isActive", True):
                    continue
                
                # Map type to transport
                transport_type = server_config.get("type", "sse")
                if transport_type == "sse":
                    connections[server_name] = {
                        "url": server_config.get("url") or server_config.get("baseUrl"),
                        "transport": "sse",
                    }
                elif transport_type == "streamable_http":
                    connections[server_name] = {
                        "url": server_config.get("url") or server_config.get("baseUrl"),
                        "transport": "streamable_http",
                    }
                elif transport_type == "stdio":
                    connections[server_name] = {
                        "command": server_config.get("command"),
                        "args": server_config.get("args", []),
                        "transport": "stdio",
                    }
            
            # 3. Create MCP client
            mcp_client = MultiServerMCPClient(connections)
            
            # 4. Get MCP tools
            mcp_tools = await mcp_client.get_tools()
            
            # 5. Add to tool list
            hkex_tools.extend(mcp_tools)
            
            print(f"✅ 已加载 {len(mcp_tools)} 个 MCP 工具")
            
            # 6. Print tool list (for debugging)
            for tool in mcp_tools:
                print(f"   - {tool.name}: {tool.description}")
                
        except Exception as e:
            print(f"⚠️  MCP 工具加载失败: {e}")
            import traceback
            traceback.print_exc()
    # ================================================

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
