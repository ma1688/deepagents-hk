"""API routes module."""

from .auth import router as auth_router
from .chat import router as chat_router
from .config import router as config_router
from .history import router as history_router
from .search import router as search_router

__all__ = [
    "auth_router",
    "chat_router",
    "config_router",
    "history_router",
    "search_router",
]

