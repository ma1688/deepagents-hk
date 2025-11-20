"""Skills module for deepagents CLI.

Public API:
- SkillsMiddleware: Middleware for integrating skills into agent execution
- execute_skills_command: Execute skills subcommands (list/create/info)
- execute_skills_command_interactive: Execute skills commands in interactive CLI
- setup_skills_parser: Setup argparse configuration for skills commands

All other components are internal implementation details.
"""

from src.cli.skills.commands import (
    execute_skills_command,
    execute_skills_command_interactive,
    setup_skills_parser,
)
from src.cli.skills.middleware import SkillsMiddleware

__all__ = [
    "SkillsMiddleware",
    "execute_skills_command",
    "execute_skills_command_interactive",
    "setup_skills_parser",
]
