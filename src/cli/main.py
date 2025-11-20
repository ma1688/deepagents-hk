"""Main entry point and CLI loop for HKEX agent."""

import argparse
import asyncio
import os
import sys
from pathlib import Path

from .agent import create_agent_with_config, list_agents, reset_agent
from .commands import execute_bash_command, handle_command
from .config import COLORS, HKEX_AGENT_ASCII, SessionState, console, create_model
from .execution import execute_task
from .input import create_prompt_session
from .tools import (
    analyze_pdf_structure,
    download_announcement_pdf,
    extract_pdf_content,
    generate_summary_markdown,
    get_announcement_categories,
    get_cached_pdf_path,
    get_latest_hkex_announcements,
    get_stock_info,
    search_hkex_announcements,
)
from .ui import TokenTracker, show_help


def check_cli_dependencies():
    """Check if CLI optional dependencies are installed."""
    missing = []

    try:
        import rich
    except ImportError:
        missing.append("rich")

    try:
        import prompt_toolkit
    except ImportError:
        missing.append("prompt-toolkit")

    if missing:
        print("\n❌ Missing required CLI dependencies!")
        print("\nThe following packages are required to use the HKEX agent CLI:")
        for pkg in missing:
            print(f"  - {pkg}")
        print("\nPlease install them with:")
        print("  pip install rich prompt-toolkit")
        sys.exit(1)


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="HKEX Agent - Hong Kong Stock Exchange Announcement Analysis Assistant",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        add_help=False,
    )

    subparsers = parser.add_subparsers(dest="command", help="Command to run")

    # List command
    subparsers.add_parser("list", help="List all available agents")

    # Help command
    subparsers.add_parser("help", help="Show help information")

    # Reset command
    reset_parser = subparsers.add_parser("reset", help="Reset an agent")
    reset_parser.add_argument("--agent", required=True, help="Name of agent to reset")
    reset_parser.add_argument(
        "--target", dest="source_agent", help="Copy prompt from another agent"
    )

    # Default interactive mode
    parser.add_argument(
        "--agent",
        default="default",
        help="Agent identifier for separate memory stores (default: default).",
    )
    parser.add_argument(
        "--auto-approve",
        action="store_true",
        help="Auto-approve tool usage without prompting (disables human-in-the-loop)",
    )
    parser.add_argument(
        "--show-thinking",
        action="store_true",
        help="Show agent's reasoning/thinking process",
    )

    return parser.parse_args()


async def simple_cli(agent, assistant_id: str | None, session_state, baseline_tokens: int = 0, model_name: str = "deepseek-chat"):
    """Main CLI loop."""
    console.clear()
    # 如果是Text对象（彩虹模式），直接打印；否则应用primary颜色
    from rich.text import Text
    if isinstance(HKEX_AGENT_ASCII, Text):
        console.print(HKEX_AGENT_ASCII)
    else:
        console.print(HKEX_AGENT_ASCII, style=f"bold {COLORS['primary']}")
    console.print()

    console.print(
        "... Ready to analyze HKEX announcements! What would you like to do?",
        style=COLORS["agent"],
    )
    console.print(f"  [dim]Working directory: {Path.cwd()}[/dim]")
    console.print()

    if session_state.auto_approve:
        console.print(
            "  [yellow]⚡ Auto-approve: ON[/yellow] [dim](tools run without confirmation)[/dim]"
        )
        console.print()

    console.print(
        "  Tips: Enter to submit, Alt+Enter for newline, Ctrl+E for editor, Ctrl+T to toggle auto-approve, Ctrl+O to toggle tool outputs, Ctrl+C to interrupt",
        style=f"dim {COLORS['dim']}",
    )
    console.print()

    # Create token tracker
    token_tracker = TokenTracker(model_name=model_name)
    token_tracker.set_baseline(baseline_tokens)
    
    # Create token tracker reference for toolbar
    token_tracker_ref = {"tracker": token_tracker}
    
    # Create prompt session with token tracker reference
    session = create_prompt_session(assistant_id, session_state, token_tracker_ref)

    while True:
        try:
            user_input = await session.prompt_async()
            if session_state.exit_hint_handle:
                session_state.exit_hint_handle.cancel()
                session_state.exit_hint_handle = None
            session_state.exit_hint_until = None
            user_input = user_input.strip()
        except EOFError:
            break
        except KeyboardInterrupt:
            console.print("\nGoodbye!", style=COLORS["primary"])
            break

        if not user_input:
            continue

        # Check for slash commands first
        if user_input.startswith("/"):
            result = handle_command(user_input, agent, token_tracker)
            if result == "exit":
                console.print("\nGoodbye!", style=COLORS["primary"])
                break
            if result:
                # Command was handled, continue to next input
                continue

        # Check for bash commands (!)
        if user_input.startswith("!"):
            execute_bash_command(user_input)
            continue

        # Handle regular quit keywords
        if user_input.lower() in ["quit", "exit", "q"]:
            console.print("\nGoodbye!", style=COLORS["primary"])
            break

        await execute_task(user_input, agent, assistant_id, session_state, token_tracker)


async def main(assistant_id: str, session_state):
    """Main entry point."""
    # Create the model (checks API keys)
    model = create_model()

    # Get model name for token tracking
    # Try to get model name from environment variables (same order as create_model())
    if os.environ.get("SILICONFLOW_API_KEY"):
        model_name = os.environ.get("SILICONFLOW_MODEL", "deepseek-chat")
    elif os.environ.get("OPENAI_API_KEY"):
        model_name = os.environ.get("OPENAI_MODEL", "gpt-5-mini")
    elif os.environ.get("ANTHROPIC_API_KEY"):
        model_name = os.environ.get("ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929")
    else:
        model_name = "deepseek-chat"  # Default

    # ========== Read MCP configuration ==========
    enable_mcp = os.getenv("ENABLE_MCP", "false").lower() == "true"
    if enable_mcp:
        console.print(f"[cyan]🔌 MCP 集成已启用[/cyan]")
    # ============================================

    # Create agent with HKEX tools
    tools = [
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

    agent = await create_agent_with_config(model, assistant_id, tools, enable_mcp=enable_mcp)

    # Calculate baseline token count for accurate token tracking
    from src.agents.main_agent import get_system_prompt
    from .token_utils import calculate_baseline_tokens
    from src.config.agent_config import get_agent_dir_name

    agent_dir_name = get_agent_dir_name()
    agent_dir = Path.home() / agent_dir_name / assistant_id
    system_prompt = get_system_prompt()
    baseline_tokens = calculate_baseline_tokens(model, agent_dir, system_prompt)

    try:
        await simple_cli(agent, assistant_id, session_state, baseline_tokens, model_name)
    except Exception as e:
        console.print(f"\n[bold red]❌ Error:[/bold red] {e}\n")


def cli_main():
    """Entry point for console script."""
    # Check dependencies first
    check_cli_dependencies()

    try:
        args = parse_args()

        if args.command == "help":
            show_help()
        elif args.command == "list":
            list_agents()
        elif args.command == "reset":
            reset_agent(args.agent, args.source_agent)
        else:
            # Create session state from args
            session_state = SessionState(
                auto_approve=args.auto_approve,
                show_thinking=args.show_thinking
            )

            # API key validation happens in create_model()
            asyncio.run(main(args.agent, session_state))
    except KeyboardInterrupt:
        # Clean exit on Ctrl+C - suppress ugly traceback
        console.print("\n\n[yellow]Interrupted[/yellow]")
        sys.exit(0)


if __name__ == "__main__":
    cli_main()

