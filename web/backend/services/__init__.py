"""Services module."""

# Lazy import to avoid circular import issues
def get_agent_service():
    """Get AgentService class (lazy import)."""
    from .agent_service import AgentService
    return AgentService

__all__ = ["get_agent_service"]

