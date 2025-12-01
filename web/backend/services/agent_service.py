"""Agent service wrapping HKEXAgentClient for web API."""

import os
import sys
from collections.abc import AsyncGenerator
from pathlib import Path
from typing import TYPE_CHECKING

# Add project root to path for imports
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from langchain_core.messages import HumanMessage
from langchain_openai import ChatOpenAI

# Lazy imports to avoid circular import issues
_create_hkex_agent = None
_search_hkex_announcements = None


def _get_hkex_agent_func():
    """Lazy load create_hkex_agent to avoid circular imports."""
    global _create_hkex_agent
    if _create_hkex_agent is None:
        from src.agents.main_agent import create_hkex_agent
        _create_hkex_agent = create_hkex_agent
    return _create_hkex_agent


def _get_search_func():
    """Lazy load search_hkex_announcements to avoid circular imports."""
    global _search_hkex_announcements
    if _search_hkex_announcements is None:
        from src.tools.hkex_tools import search_hkex_announcements
        _search_hkex_announcements = search_hkex_announcements
    return _search_hkex_announcements


class AgentService:
    """Service for interacting with HKEX agent."""
    
    def __init__(
        self,
        provider: str = "siliconflow",
        model_name: str = "deepseek-chat",
        api_key: str | None = None,
        base_url: str | None = None,
        temperature: float = 0.7,
        max_tokens: int = 20000,
    ):
        """Initialize agent service with configuration.
        
        Args:
            provider: Model provider (siliconflow, openai, anthropic)
            model_name: Name of the model to use
            api_key: API key (uses env var if not provided)
            base_url: Custom base URL
            temperature: Temperature for generation
            max_tokens: Maximum tokens for response
        """
        self.provider = provider
        self.model_name = model_name
        self.temperature = temperature
        self.max_tokens = max_tokens
        
        # Set up API configuration
        if provider == "siliconflow":
            self.api_key = api_key or os.getenv("SILICONFLOW_API_KEY")
            self.base_url = base_url or "https://api.siliconflow.cn/v1"
        elif provider == "openai":
            self.api_key = api_key or os.getenv("OPENAI_API_KEY")
            self.base_url = base_url or "https://api.openai.com/v1"
        elif provider == "anthropic":
            self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
            self.base_url = base_url
        else:
            raise ValueError(f"Unknown provider: {provider}")
        
        if not self.api_key:
            raise ValueError(f"API key not found for provider: {provider}")
        
        self._model = None
        self._agent = None
    
    def _create_model(self) -> ChatOpenAI:
        """Create LangChain chat model."""
        if self.provider == "anthropic":
            from langchain_anthropic import ChatAnthropic
            return ChatAnthropic(
                model=self.model_name,
                api_key=self.api_key,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
        
        # Use OpenAI-compatible API for siliconflow and openai
        return ChatOpenAI(
            model=self.model_name,
            api_key=self.api_key,
            base_url=self.base_url,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
    
    @property
    def model(self) -> ChatOpenAI:
        """Get or create the chat model."""
        if self._model is None:
            self._model = self._create_model()
        return self._model
    
    @property
    def agent(self):
        """Get or create the HKEX agent."""
        if self._agent is None:
            create_hkex_agent = _get_hkex_agent_func()
            self._agent = create_hkex_agent(
                model=self.model,
                assistant_id="web-agent",
                tools=None,  # Use default tools
            )
        return self._agent
    
    async def chat_stream(
        self,
        message: str,
        thread_id: str = "main"
    ) -> AsyncGenerator[str, None]:
        """Stream chat response from agent.
        
        Args:
            message: User message
            thread_id: Conversation thread ID
            
        Yields:
            Response chunks as strings
        """
        config = {
            "configurable": {"thread_id": thread_id},
        }
        
        async for chunk in self.agent.astream(
            {"messages": [HumanMessage(content=message)]},
            config=config,
            stream_mode=["messages"],
        ):
            if isinstance(chunk, tuple) and len(chunk) == 3:
                namespace, stream_mode, data = chunk
                if stream_mode == "messages":
                    if isinstance(data, tuple) and len(data) == 2:
                        msg, metadata = data
                        if hasattr(msg, "content") and msg.content:
                            yield msg.content
    
    async def chat(self, message: str, thread_id: str = "main") -> str:
        """Get complete chat response from agent.
        
        Args:
            message: User message
            thread_id: Conversation thread ID
            
        Returns:
            Complete response string
        """
        parts = []
        async for chunk in self.chat_stream(message, thread_id):
            parts.append(chunk)
        return "".join(parts)
    
    def search_announcements(
        self,
        stock_code: str,
        from_date: str,
        to_date: str,
        title: str | None = None,
        market: str = "SEHK",
        row_range: int = 100,
    ) -> dict:
        """Search HKEX announcements.
        
        Args:
            stock_code: 5-digit stock code
            from_date: Start date (YYYYMMDD)
            to_date: End date (YYYYMMDD)
            title: Optional title filter
            market: Market code (SEHK or GEM)
            row_range: Number of results
            
        Returns:
            Search results dictionary
        """
        search_func = _get_search_func()
        return search_func.invoke({
            "stock_code": stock_code,
            "from_date": from_date,
            "to_date": to_date,
            "title": title,
            "market": market,
            "row_range": row_range,
        })


# Encryption helpers for API keys
def encrypt_api_key(api_key: str, secret_key: str | None = None) -> str:
    """Encrypt API key for storage.
    
    Simple Fernet encryption. In production, use proper key management.
    """
    from cryptography.fernet import Fernet
    import base64
    import hashlib
    
    # Use environment variable or derive key from secret
    key = secret_key or os.getenv("ENCRYPTION_KEY")
    if not key:
        # Derive a key from a default secret (NOT secure for production!)
        key = base64.urlsafe_b64encode(
            hashlib.sha256(b"hkex-agent-default-key").digest()
        )
    else:
        # Ensure key is proper format
        if len(key) < 32:
            key = base64.urlsafe_b64encode(
                hashlib.sha256(key.encode()).digest()
            )
        else:
            key = key.encode() if isinstance(key, str) else key
    
    f = Fernet(key)
    return f.encrypt(api_key.encode()).decode()


def decrypt_api_key(encrypted_key: str, secret_key: str | None = None) -> str:
    """Decrypt stored API key."""
    from cryptography.fernet import Fernet
    import base64
    import hashlib
    
    key = secret_key or os.getenv("ENCRYPTION_KEY")
    if not key:
        key = base64.urlsafe_b64encode(
            hashlib.sha256(b"hkex-agent-default-key").digest()
        )
    else:
        if len(key) < 32:
            key = base64.urlsafe_b64encode(
                hashlib.sha256(key.encode()).digest()
            )
        else:
            key = key.encode() if isinstance(key, str) else key
    
    f = Fernet(key)
    return f.decrypt(encrypted_key.encode()).decode()

