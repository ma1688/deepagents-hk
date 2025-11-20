"""Agent management and creation for the CLI."""

import shutil
from pathlib import Path

from src.agents.main_agent import create_hkex_agent
from src.prompts.prompts import get_default_agent_md
from .config import COLORS, config, console


def list_agents():
    """List all available agents."""
    from src.config.agent_config import get_agent_dir_name
    agent_dir_name = get_agent_dir_name()
    agents_dir = Path.home() / agent_dir_name

    if not agents_dir.exists() or not any(agents_dir.iterdir()):
        console.print("[yellow]No agents found.[/yellow]")
        console.print(
            "[dim]Agents will be created in ~/.hkex-agent/ when you first use them.[/dim]",
            style=COLORS["dim"],
        )
        return

    console.print("\n[bold]Available Agents:[/bold]\n", style=COLORS["primary"])

    for agent_path in sorted(agents_dir.iterdir()):
        if agent_path.is_dir():
            agent_name = agent_path.name
            agent_md = agent_path / "memories" / "agent.md"

            if agent_md.exists():
                console.print(f"  • [bold]{agent_name}[/bold]", style=COLORS["primary"])
                console.print(f"    {agent_path}", style=COLORS["dim"])
            else:
                console.print(
                    f"  • [bold]{agent_name}[/bold] [dim](incomplete)[/dim]",
                    style=COLORS["tool"],
                )
                console.print(f"    {agent_path}", style=COLORS["dim"])

    console.print()


def reset_agent(agent_name: str, source_agent: str = None):
    """Reset an agent to default or copy from another agent."""
    from src.config.agent_config import get_agent_dir_name
    agent_dir_name = get_agent_dir_name()
    agents_dir = Path.home() / agent_dir_name
    agent_dir = agents_dir / agent_name

    if source_agent:
        source_dir = agents_dir / source_agent
        source_md = source_dir / "memories" / "agent.md"

        if not source_md.exists():
            console.print(
                f"[bold red]Error:[/bold red] Source agent '{source_agent}' not found or has no agent.md"
            )
            return

        source_content = source_md.read_text()
        action_desc = f"contents of agent '{source_agent}'"
    else:
        source_content = get_default_agent_md()
        action_desc = "default"

    if agent_dir.exists():
        shutil.rmtree(agent_dir)
        console.print(f"Removed existing agent directory: {agent_dir}", style=COLORS["tool"])

    agent_dir.mkdir(parents=True, exist_ok=True)
    (agent_dir / "memories").mkdir(exist_ok=True)
    (agent_dir / "pdf_cache").mkdir(exist_ok=True)
    agent_md = agent_dir / "memories" / "agent.md"
    agent_md.write_text(source_content)

    console.print(f"✓ Agent '{agent_name}' reset to {action_desc}", style=COLORS["primary"])
    console.print(f"Location: {agent_dir}\n", style=COLORS["dim"])


async def create_agent_with_config(model, assistant_id: str, tools: list, enable_mcp: bool = False, enable_skills: bool = True):
    """Create and configure an HKEX agent with the specified model and tools.

    Args:
        model: Language model instance.
        assistant_id: Agent identifier.
        tools: List of additional tools (optional).
        enable_mcp: Enable MCP tools integration (default: False).
        enable_skills: Enable Skills system (default: True).

    Returns:
        Configured HKEX agent.
    """
    # Prepare Skills middleware if enabled
    middlewares = []
    if enable_skills:
        from pathlib import Path
        from src.cli.skills.middleware import SkillsMiddleware
        from src.config.agent_config import get_agent_dir_name
        
        # Setup Skills directory
        agent_dir_name = get_agent_dir_name()
        agent_dir = Path.home() / agent_dir_name / assistant_id
        skills_dir = agent_dir / "skills"
        skills_dir.mkdir(parents=True, exist_ok=True)
        
        # Create Skills middleware
        skills_middleware = SkillsMiddleware(
            skills_dir=skills_dir,
            assistant_id=assistant_id,
        )
        middlewares.append(skills_middleware)
    
    agent = await create_hkex_agent(
        model=model,
        assistant_id=assistant_id,
        tools=tools,
        enable_mcp=enable_mcp,
        middlewares=middlewares if middlewares else None,
    )

    return agent.with_config(config)
