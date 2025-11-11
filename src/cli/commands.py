"""Command handlers for slash commands and bash execution."""

import subprocess
import time
from pathlib import Path

from .config import COLORS, HKEX_AGENT_ASCII, console
from .ui import TokenTracker, show_interactive_help


def handle_command(command: str, agent, token_tracker: TokenTracker) -> str | bool:
    """Handle slash commands. Returns 'exit' to exit, True if handled, False to pass to agent."""
    cmd = command.lower().strip().lstrip("/")

    if cmd in ["quit", "exit", "q"]:
        return "exit"

    if cmd == "clear":
        # Create a new thread_id for fresh conversation
        # Historical data is preserved in database and can be viewed with /history
        new_thread_id = f"main-{int(time.time())}"
        
        # Store new thread_id for use in next conversation
        # This will be picked up by execute_task()
        import os
        os.environ["HKEX_CURRENT_THREAD_ID"] = new_thread_id

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
            "... Fresh start! New conversation started.", style=COLORS["agent"]
        )
        console.print(
            f"[dim]Context reset to baseline ({token_tracker.baseline_context:,} tokens)[/dim]"
        )
        console.print(
            "[dim]💡 Tip: Previous conversations are saved. Use /history to view them.[/dim]"
        )
        console.print()
        return True

    if cmd == "help":
        show_interactive_help()
        return True

    if cmd == "tokens":
        token_tracker.display_session()
        return True

    if cmd == "history":
        # Note: This is a simple synchronous implementation
        # Full async implementation would require refactoring the command handler
        show_conversation_history_sync(agent)
        return True

    console.print()
    console.print(f"[yellow]Unknown command: /{cmd}[/yellow]")
    console.print("[dim]Type /help for available commands.[/dim]")
    console.print()
    return True

    return False


def show_conversation_history_sync(agent):
    """Display conversation history from checkpointer (synchronous version)."""
    console.print()
    console.print("[bold cyan]📝 Conversation History[/bold cyan]")
    console.print()
    
    try:
        # Get the checkpointer
        checkpointer = agent.checkpointer
        if not checkpointer:
            console.print("[yellow]No conversation history available (checkpointer not configured)[/yellow]")
            console.print()
            return
        
        # List all threads
        import os
        from pathlib import Path
        
        # Get agent directory to find database
        assistant_id = "default"  # Default value
        agent_dir = Path.home() / ".hkex-agent" / assistant_id
        db_path = agent_dir / "checkpoints.db"
        
        if not db_path.exists():
            console.print("[yellow]No conversation history found yet.[/yellow]")
            console.print("[dim]Start a conversation to create history.[/dim]")
            console.print()
            return
        
        # For now, show a simple message
        # Full implementation would require async context and state retrieval
        console.print("[green]✓[/green] Conversation history is available")
        console.print(f"[dim]Database: {db_path}[/dim]")
        console.print()
        console.print("[yellow]Note:[/yellow] Full history viewing will be implemented in a future update.")
        console.print("[dim]Current conversation automatically continues on restart.[/dim]")
        console.print()
        
    except Exception as e:
        console.print(f"[red]Error reading history: {e}[/red]")
        console.print()


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
