"""Command handlers for slash commands and bash execution."""

import subprocess
from pathlib import Path

from langgraph.checkpoint.memory import InMemorySaver

from .config import COLORS, HKEX_AGENT_ASCII, console
from .ui import TokenTracker, show_interactive_help


def handle_command(command: str, agent, token_tracker: TokenTracker, assistant_id: str = "hkex-agent") -> str | bool:
    """Handle slash commands. Returns 'exit' to exit, True if handled, False to pass to agent."""
    cmd = command.lower().strip().lstrip("/")

    if cmd in ["quit", "exit", "q"]:
        return "exit"

    if cmd == "clear":
        # Reset agent conversation state
        agent.checkpointer = InMemorySaver()

        # Reset token tracking to baseline
        token_tracker.reset()

        # Clear screen and show fresh UI
        console.clear()
        # 如果是Text对象（彩虹模式），直接打印；否则应用primary颜色
        from rich.text import Text
        if isinstance(HKEX_AGENT_ASCII, Text):
            console.print(HKEX_AGENT_ASCII)
        else:
            console.print(HKEX_AGENT_ASCII, style=f"bold {COLORS['primary']}")
        console.print()
        console.print(
            "... Fresh start! Conversation reset.", style=COLORS["agent"]
        )
        console.print(
            f"[dim]Context reset to baseline ({token_tracker.baseline_context:,} tokens)[/dim]"
        )
        console.print()
        return True

    if cmd == "help":
        show_interactive_help()
        return True

    if cmd == "tokens":
        token_tracker.display_session()
        return True

    if cmd.startswith("skills"):
        # Handle skills subcommands
        from src.cli.skills import execute_skills_command_interactive
        parts = cmd.split(maxsplit=1)
        subcommand = parts[1] if len(parts) > 1 else "list"
        execute_skills_command_interactive(subcommand, assistant_id)
        return True

    if cmd == "memory":
        # Show memory paths
        from pathlib import Path
        from src.config.agent_config import get_agent_dir_name
        from src.cli.project_utils import find_project_root
        
        agent_dir_name = get_agent_dir_name()
        user_memory = Path.home() / agent_dir_name / assistant_id / "memories" / "agent.md"
        project_root = find_project_root()
        
        console.print()
        console.print("[bold]Memory Configuration[/bold]", style=COLORS["primary"])
        console.print()
        console.print(f"[bold]User Memory:[/bold] {user_memory}", style=COLORS["dim"])
        if user_memory.exists():
            console.print("  ✓ File exists", style="green")
        else:
            console.print("  ○ File not created yet", style="yellow")
        
        console.print()
        if project_root:
            project_memory = project_root / agent_dir_name / "agent.md"
            console.print(f"[bold]Project Memory:[/bold] {project_memory}", style=COLORS["dim"])
            if project_memory.exists():
                console.print("  ✓ File exists", style="green")
            else:
                console.print("  ○ File not created yet", style="yellow")
        else:
            console.print("[bold]Project Memory:[/bold] Not in a project", style=COLORS["dim"])
        console.print()
        return True

    console.print()
    console.print(f"[yellow]Unknown command: /{cmd}[/yellow]")
    console.print("[dim]Type /help for available commands.[/dim]")
    console.print()
    return True

    return False


def execute_bash_command(command: str) -> bool:
    """Execute a bash command and display output. Returns True if handled."""
    cmd = command.strip().lstrip("!")

    if not cmd:
        return True

    try:
        console.print()
        console.print(f"[dim]$ {cmd}[/dim]")

        # Execute the command
        result = subprocess.run(
            cmd, check=False, shell=True, capture_output=True, text=True, timeout=30, cwd=Path.cwd()
        )

        # Display output
        if result.stdout:
            console.print(result.stdout, style=COLORS["dim"], markup=False)
        if result.stderr:
            console.print(result.stderr, style="red", markup=False)

        # Show return code if non-zero
        if result.returncode != 0:
            console.print(f"[dim]Exit code: {result.returncode}[/dim]")

        console.print()
        return True

    except subprocess.TimeoutExpired:
        console.print("[red]Command timed out after 30 seconds[/red]")
        console.print()
        return True
    except Exception as e:
        console.print(f"[red]Error executing command: {e}[/red]")
        console.print()
        return True
