"""Configuration, constants, and model creation for the CLI."""

import os
import sys
from pathlib import Path

import dotenv
from rich.console import Console

dotenv.load_dotenv()

# Color scheme
COLORS = {
    "primary": "#10b981",
    "dim": "#6b7280",
    "user": "#ffffff",
    "agent": "#10b981",
    "thinking": "#34d399",
    "tool": "#fbbf24",
}

# ASCII art banner
HKEX_AGENT_ASCII = """
██╗  ██╗██╗  ██╗███████╗██╗  ██╗
██║  ██║██║  ██║██╔════╝╚██╗██╔╝
███████║███████║█████╗   ╚███╔╝
██╔══██║██╔══██║██╔══╝   ██╔██╗
██║  ██║██║  ██║███████╗██╔╝ ██╗
╚═╝  ╚═╝╚═╝  ╚═╝╚══════╝╚═╝  ╚═╝

 █████╗  ██████╗ ███████╗███╗   ██╗████████╗
██╔══██╗██╔════╝ ██╔════╝████╗  ██║╚══██╔══╝
███████║██║  ███╗█████╗  ██╔██╗ ██║   ██║
██╔══██║██║   ██║██╔══╝  ██║╚██╗██║   ██║
██║  ██║╚██████╔╝███████╗██║ ╚████║   ██║
╚═╝  ╚═╝ ╚═════╝ ╚══════╝╚═╝  ╚═══╝   ╚═╝
"""

# Interactive commands
COMMANDS = {
    "clear": "Clear screen and reset conversation",
    "help": "Show help information",
    "tokens": "Show token usage for current session",
    "quit": "Exit the CLI",
    "exit": "Exit the CLI",
}

# Maximum argument length for display
MAX_ARG_LENGTH = 150

# Agent configuration
config = {"recursion_limit": 1000}

# Rich console instance
console = Console(highlight=False)


class SessionState:
    """Holds mutable session state (auto-approve mode, etc)."""

    def __init__(self, auto_approve: bool = False):
        self.auto_approve = auto_approve
        self.exit_hint_until: float | None = None
        self.exit_hint_handle = None

    def toggle_auto_approve(self) -> bool:
        """Toggle auto-approve and return new state."""
        self.auto_approve = not self.auto_approve
        return self.auto_approve


def create_model():
    """Create the appropriate model based on available API keys.

    Priority: SiliconFlow > OpenAI > Anthropic

    Returns:
        ChatModel instance (SiliconFlow, OpenAI, or Anthropic)

    Raises:
        SystemExit if no API key is configured
    """
    # Check SiliconFlow first (highest priority)
    siliconflow_key = os.environ.get("SILICONFLOW_API_KEY")
    if siliconflow_key:
        from langchain_openai import ChatOpenAI

        model_name = os.environ.get("SILICONFLOW_MODEL", "deepseek-chat")
        console.print(f"[dim]Using SiliconFlow model: {model_name}[/dim]")
        return ChatOpenAI(
            model=model_name,
            base_url="https://api.siliconflow.cn/v1",
            api_key=siliconflow_key,
            temperature=0.7,
        )

    # Check OpenAI
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        from langchain_openai import ChatOpenAI

        model_name = os.environ.get("OPENAI_MODEL", "gpt-5-mini")
        console.print(f"[dim]Using OpenAI model: {model_name}[/dim]")
        return ChatOpenAI(
            model=model_name,
            temperature=0.7,
        )

    # Check Anthropic
    anthropic_key = os.environ.get("ANTHROPIC_API_KEY")
    if anthropic_key:
        from langchain_anthropic import ChatAnthropic

        model_name = os.environ.get(
            "ANTHROPIC_MODEL", "claude-sonnet-4-5-20250929"
        )
        console.print(f"[dim]Using Anthropic model: {model_name}[/dim]")
        return ChatAnthropic(
            model_name=model_name,
            max_tokens=20000,
        )

    # No API key found
    console.print("[bold red]Error:[/bold red] No API key configured.")
    console.print("\nPlease set one of the following environment variables:")
    console.print("  - SILICONFLOW_API_KEY  (for SiliconFlow models like deepseek-chat)")
    console.print("  - OPENAI_API_KEY       (for OpenAI models like gpt-5-mini)")
    console.print("  - ANTHROPIC_API_KEY    (for Claude models)")
    console.print("\nExample:")
    console.print("  export SILICONFLOW_API_KEY=your_api_key_here")
    console.print("  export SILICONFLOW_MODEL=deepseek-chat  # optional")
    console.print("\nOr add it to your .env file.")
    sys.exit(1)

