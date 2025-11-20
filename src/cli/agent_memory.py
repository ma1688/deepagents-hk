"""Middleware for loading agent-specific long-term memory with dual-scope support.

This middleware supports both user-level and project-level agent.md files:
- User-level: ~/.hkex-agent/{agent}/memories/agent.md (personality, universal behavior)
- Project-level: [project]/.hkex-agent/agent.md (project-specific instructions)
"""

from collections.abc import Awaitable, Callable
from pathlib import Path
from typing import NotRequired, TypedDict

from langchain.agents.middleware.types import (
    AgentMiddleware,
    AgentState,
    ModelRequest,
    ModelResponse,
)
from langgraph.runtime import Runtime

from src.cli.project_utils import find_project_root


class AgentMemoryState(AgentState):
    """State for the agent memory middleware."""

    user_memory: NotRequired[str]
    """Personal preferences from ~/.hkex-agent/{agent}/memories/ (applies everywhere)."""

    project_memory: NotRequired[str]
    """Project-specific context (loaded from project root)."""


class AgentMemoryStateUpdate(TypedDict):
    """A state update for the agent memory middleware."""

    user_memory: NotRequired[str]
    """Personal preferences from ~/.hkex-agent/{agent}/memories/ (applies everywhere)."""

    project_memory: NotRequired[str]
    """Project-specific context (loaded from project root)."""


# Long-term Memory Documentation
LONGTERM_MEMORY_SYSTEM_PROMPT = """

## Long-term Memory

Your long-term memory is stored in files on the filesystem and persists across sessions.

**User Memory Location**: `{agent_dir_absolute}/memories` (displays as `{agent_dir_display}/memories`)
**Project Memory Location**: {project_memory_info}

Your system prompt is loaded from TWO sources at startup:
1. **User agent.md**: `{agent_dir_absolute}/memories/agent.md` - Your personal preferences across all projects
2. **Project agent.md**: Loaded from project root if available - Project-specific instructions

Project-specific agent.md is loaded from:
- `[project-root]/.hkex-agent/agent.md`

**When to CHECK/READ memories (CRITICAL - do this FIRST):**
- **At the start of ANY new session**: Check both user and project memories
  - User: `ls {agent_dir_absolute}/memories`
  - Project: `ls {project_hkex_dir}` (if in a project)
- **BEFORE answering questions**: If asked "what do you know about X?" or "how do I do Y?", check project memories FIRST, then user
- **When user asks you to do something**: Check if you have project-specific guides or examples
- **When user references past work**: Search project memory files for related context

**Memory-first response pattern:**
1. User asks a question → Check project directory first: `ls {project_hkex_dir}`
2. If relevant files exist → Read them with `read_file '{project_hkex_dir}/[filename]'`
3. Check user memory if needed → `ls {agent_dir_absolute}/memories`
4. Base your answer on saved knowledge supplemented by general knowledge

**When to update memories:**
- **IMMEDIATELY when the user describes your role or how you should behave**
- **IMMEDIATELY when the user gives feedback on your work** - Update memories to capture what was wrong and how to do it better
- When the user explicitly asks you to remember something
- When patterns or preferences emerge (coding styles, conventions, workflows)
- After significant work where context would help in future sessions

**Learning from feedback (CRITICAL):**
- Treat each correction as a learning opportunity - update memories immediately
- Each correction is a chance to improve permanently - don't just fix the immediate issue, update your instructions
- When user says "you should remember X" or "be careful about Y", treat this as HIGH PRIORITY - update memories IMMEDIATELY
- Look for the underlying principle behind corrections, not just the specific mistake

## Deciding Where to Store Memory

When writing or updating agent memory, decide whether each fact, configuration, or behavior belongs in:

### User Agent File: `{agent_dir_absolute}/memories/agent.md`
→ Describes the agent's **personality, style, and universal behavior** across all projects.

**Store here:**
- Your general tone and communication style
- Universal coding preferences (formatting, comment style, etc.)
- General workflows and methodologies you follow
- Tool usage patterns that apply everywhere
- Personal preferences that don't change per-project

**Examples:**
- "Be concise and direct in responses"
- "Always use type hints in Python"
- "Prefer functional programming patterns"

### Project Agent File: `{project_hkex_dir}/agent.md`
→ Describes **how this specific project works** and **how the agent should behave here only.**

**Store here:**
- Project-specific architecture and design patterns
- Coding conventions specific to this codebase
- Project structure and organization
- Testing strategies for this project
- Deployment processes and workflows
- Team conventions and guidelines

**Examples:**
- "This project uses FastAPI with SQLAlchemy"
- "Tests go in tests/ directory mirroring src/ structure"
- "All API changes require updating OpenAPI spec"

### Project Memory Files: `{project_hkex_dir}/*.md`
→ Use for **project-specific reference information** and structured notes.

**Store here:**
- API design documentation
- Architecture decisions and rationale
- Deployment procedures
- Common debugging patterns
- Onboarding information

**Examples:**
- `{project_hkex_dir}/api-design.md` - REST API patterns used
- `{project_hkex_dir}/architecture.md` - System architecture overview
- `{project_hkex_dir}/deployment.md` - How to deploy this project

### File Operations:

**User memory:**
```
ls {agent_dir_absolute}/memories                        # List user memory files
read_file '{agent_dir_absolute}/memories/agent.md'      # Read user preferences
edit_file '{agent_dir_absolute}/memories/agent.md' ...  # Update user preferences
```

**Project memory (preferred for project-specific information):**
```
ls {project_hkex_dir}                                   # List project memory files
read_file '{project_hkex_dir}/agent.md'                 # Read project instructions
edit_file '{project_hkex_dir}/agent.md' ...             # Update project instructions
write_file '{project_hkex_dir}/notes.md' ...           # Create project memory file
```

**Important**:
- Project memory files are stored in `.hkex-agent/` inside the project root
- Always use absolute paths for file operations
- Check project memories BEFORE user when answering project-specific questions"""


DEFAULT_MEMORY_SNIPPET = """<user_memory>
{user_memory}
</user_memory>

<project_memory>
{project_memory}
</project_memory>"""


class AgentMemoryMiddleware(AgentMiddleware):
    """Middleware for loading agent-specific long-term memory with dual-scope support.

    This middleware loads both user-level and project-level agent.md files:
    - User: ~/.hkex-agent/{agent}/memories/agent.md
    - Project: [project-root]/.hkex-agent/agent.md

    Args:
        assistant_id: The agent identifier.
        system_prompt_template: Optional custom template for injecting memory.
    """

    state_schema = AgentMemoryState

    def __init__(
        self,
        *,
        assistant_id: str,
        system_prompt_template: str | None = None,
    ) -> None:
        """Initialize the agent memory middleware.

        Args:
            assistant_id: The agent identifier.
            system_prompt_template: Optional custom template for injecting
                agent memory into system prompt.
        """
        self.assistant_id = assistant_id

        # User paths
        from src.config.agent_config import get_agent_dir_name
        agent_dir_name = get_agent_dir_name()
        self.agent_dir = Path.home() / agent_dir_name / assistant_id
        # Store both display path (with ~) and absolute path for file operations
        self.agent_dir_display = f"~/{agent_dir_name}/{assistant_id}"
        self.agent_dir_absolute = str(self.agent_dir)
        self.user_memory_file = self.agent_dir / "memories" / "agent.md"

        # Project paths (detected dynamically)
        self.project_root = find_project_root()
        self.project_agent_dir_name = agent_dir_name  # Store for later use

        self.system_prompt_template = system_prompt_template or DEFAULT_MEMORY_SNIPPET

    def before_agent(
        self,
        state: AgentMemoryState,
        runtime: Runtime,
    ) -> AgentMemoryStateUpdate:
        """Load agent memory from files before agent execution.

        Loads both user agent.md and project-specific agent.md if available.
        Only loads if not already present in state.

        Dynamically checks for file existence on every call to catch user updates.

        Args:
            state: Current agent state.
            runtime: Runtime context.

        Returns:
            Updated state with user_memory and project_memory populated.
        """
        # Load user memory
        user_memory = ""
        if self.user_memory_file.exists():
            try:
                user_memory = self.user_memory_file.read_text(encoding="utf-8")
            except Exception:
                pass

        # Load project memory
        project_memory = ""
        if self.project_root:
            project_hkex_dir = self.project_root / self.project_agent_dir_name
            project_agent_file = project_hkex_dir / "agent.md"
            if project_agent_file.exists():
                try:
                    project_memory = project_agent_file.read_text(encoding="utf-8")
                except Exception:
                    pass

        return AgentMemoryStateUpdate(
            user_memory=user_memory,
            project_memory=project_memory,
        )

    async def abefore_agent(
        self,
        state: AgentMemoryState,
        runtime: Runtime,
    ) -> AgentMemoryStateUpdate:
        """(async) Load agent memory from files before agent execution."""
        return self.before_agent(state, runtime)

    def wrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], ModelResponse],
    ) -> ModelResponse:
        """Inject long-term memory documentation and content into the system prompt.

        Args:
            request: The model request being processed.
            handler: The handler function to call with the modified request.

        Returns:
            The model response from the handler.
        """
        # Get memory content from state
        user_memory = request.state.get("user_memory", "")
        project_memory = request.state.get("project_memory", "")

        # Format project memory info for docs
        project_memory_info = "Not in a project (no project-level memory)"
        project_hkex_dir = "N/A"
        if self.project_root:
            project_hkex_dir = str(self.project_root / ".hkex-agent")
            project_memory_info = f"`{project_hkex_dir}`"

        # Format the longterm memory documentation
        memory_docs = LONGTERM_MEMORY_SYSTEM_PROMPT.format(
            agent_dir_absolute=self.agent_dir_absolute,
            agent_dir_display=self.agent_dir_display,
            project_memory_info=project_memory_info,
            project_hkex_dir=project_hkex_dir,
        )

        # Format the memory content snippet
        memory_snippet = self.system_prompt_template.format(
            user_memory=user_memory,
            project_memory=project_memory,
        )

        # Combine: docs first, then actual memory content
        full_memory_prompt = memory_docs + "\n\n" + memory_snippet

        # Append to system prompt
        system_prompt = request.system_prompt or ""
        updated_prompt = system_prompt + "\n\n" + full_memory_prompt

        # Use request.override for compatibility
        return handler(request.override(system_prompt=updated_prompt))

    async def awrap_model_call(
        self,
        request: ModelRequest,
        handler: Callable[[ModelRequest], Awaitable[ModelResponse]],
    ) -> ModelResponse:
        """(async) Inject long-term memory documentation and content into the system prompt."""
        # Get memory content from state
        user_memory = request.state.get("user_memory", "")
        project_memory = request.state.get("project_memory", "")

        # Format project memory info for docs
        project_memory_info = "Not in a project (no project-level memory)"
        project_hkex_dir = "N/A"
        if self.project_root:
            project_hkex_dir = str(self.project_root / ".hkex-agent")
            project_memory_info = f"`{project_hkex_dir}`"

        # Format the longterm memory documentation
        memory_docs = LONGTERM_MEMORY_SYSTEM_PROMPT.format(
            agent_dir_absolute=self.agent_dir_absolute,
            agent_dir_display=self.agent_dir_display,
            project_memory_info=project_memory_info,
            project_hkex_dir=project_hkex_dir,
        )

        # Format the memory content snippet
        memory_snippet = self.system_prompt_template.format(
            user_memory=user_memory,
            project_memory=project_memory,
        )

        # Combine: docs first, then actual memory content
        full_memory_prompt = memory_docs + "\n\n" + memory_snippet

        # Append to system prompt
        system_prompt = request.system_prompt or ""
        updated_prompt = system_prompt + "\n\n" + full_memory_prompt

        # Use request.override for compatibility
        return await handler(request.override(system_prompt=updated_prompt))

