"""Python API client for HKEX agent."""

import asyncio
from pathlib import Path
from typing import Any, AsyncIterator

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import HumanMessage

from src.agents.main_agent import create_hkex_agent
from src.cli.config import create_model


class HKEXAgentClient:
    """Python API client for interacting with HKEX agent programmatically."""

    def __init__(
        self,
        agent_id: str = "default",
        model: BaseChatModel | None = None,
        auto_approve: bool = False,
    ):
        """Initialize HKEX agent client.

        Args:
            agent_id: Agent identifier for separate memory stores (default: "default").
            model: Optional language model instance. If None, creates model from environment.
            auto_approve: Whether to auto-approve tool calls (default: False).
        """
        self.agent_id = agent_id
        self.auto_approve = auto_approve

        # Create model if not provided
        if model is None:
            self.model = create_model()
        else:
            self.model = model

        # Create agent
        self.agent = create_hkex_agent(
            model=self.model,
            assistant_id=agent_id,
            tools=None,  # Use default tools
        )

        # Set up config
        self.config = {
            "configurable": {"thread_id": "main"},
            "metadata": {"assistant_id": agent_id},
        }

    def search_announcements(
        self,
        stock_code: str,
        from_date: str,
        to_date: str,
        title: str | None = None,
        market: str = "SEHK",
        row_range: int = 100,
    ) -> dict[str, Any]:
        """Search HKEX announcements synchronously.

        Args:
            stock_code: 5-digit stock code (e.g., "00673").
            from_date: Start date in YYYYMMDD format (e.g., "20250101").
            to_date: End date in YYYYMMDD format (e.g., "20251008").
            title: Optional search keyword to filter by title.
            market: Market code - "SEHK" (main board) or "GEM" (default: "SEHK").
            row_range: Number of results to return, 1-500 (default: 100).

        Returns:
            Dictionary containing search results.
        """
        from src.tools.hkex_tools import search_hkex_announcements

        return search_hkex_announcements.invoke(
            {
                "stock_code": stock_code,
                "from_date": from_date,
                "to_date": to_date,
                "title": title,
                "market": market,
                "row_range": row_range,
            }
        )

    async def search_announcements_async(
        self,
        stock_code: str,
        from_date: str,
        to_date: str,
        title: str | None = None,
        market: str = "SEHK",
        row_range: int = 100,
    ) -> dict[str, Any]:
        """Search HKEX announcements asynchronously.

        Args:
            stock_code: 5-digit stock code (e.g., "00673").
            from_date: Start date in YYYYMMDD format (e.g., "20250101").
            to_date: End date in YYYYMMDD format (e.g., "20251008").
            title: Optional search keyword to filter by title.
            market: Market code - "SEHK" (main board) or "GEM" (default: "SEHK").
            row_range: Number of results to return, 1-500 (default: 100).

        Returns:
            Dictionary containing search results.
        """
        from src.tools.hkex_tools import search_hkex_announcements

        return await search_hkex_announcements.ainvoke(
            {
                "stock_code": stock_code,
                "from_date": from_date,
                "to_date": to_date,
                "title": title,
                "market": market,
                "row_range": row_range,
            }
        )

    def analyze_announcement(
        self,
        prompt: str,
        stream: bool = False,
    ) -> str | AsyncIterator[str]:
        """Analyze an announcement using the agent.

        Args:
            prompt: User prompt describing what to analyze.
            stream: Whether to stream the response (default: False).

        Returns:
            If stream=False: Complete response string.
            If stream=True: AsyncIterator of response chunks.
        """
        if stream:
            return self._stream_response(prompt)
        else:
            return asyncio.run(self._get_response(prompt))

    async def analyze_announcement_async(
        self,
        prompt: str,
        stream: bool = False,
    ) -> str | AsyncIterator[str]:
        """Analyze an announcement using the agent (async).

        Args:
            prompt: User prompt describing what to analyze.
            stream: Whether to stream the response (default: False).

        Returns:
            If stream=False: Complete response string.
            If stream=True: AsyncIterator of response chunks.
        """
        if stream:
            return self._stream_response(prompt)
        else:
            return await self._get_response(prompt)

    async def _get_response(self, prompt: str) -> str:
        """Get a complete response from the agent."""
        response_parts = []
        async for chunk in self.agent.astream(
            {"messages": [HumanMessage(content=prompt)]},
            config=self.config,
            stream_mode=["messages"],
        ):
            if isinstance(chunk, tuple) and len(chunk) == 3:
                namespace, stream_mode, data = chunk
                if stream_mode == "messages":
                    if isinstance(data, tuple) and len(data) == 2:
                        message, metadata = data
                        if hasattr(message, "content") and message.content:
                            response_parts.append(message.content)

        return "".join(response_parts)

    async def _stream_response(self, prompt: str) -> AsyncIterator[str]:
        """Stream response from the agent."""
        async for chunk in self.agent.astream(
            {"messages": [HumanMessage(content=prompt)]},
            config=self.config,
            stream_mode=["messages"],
        ):
            if isinstance(chunk, tuple) and len(chunk) == 3:
                namespace, stream_mode, data = chunk
                if stream_mode == "messages":
                    if isinstance(data, tuple) and len(data) == 2:
                        message, metadata = data
                        if hasattr(message, "content") and message.content:
                            yield message.content

    def generate_report(
        self,
        prompt: str,
        stream: bool = False,
    ) -> str | AsyncIterator[str]:
        """Generate a report using the agent.

        Args:
            prompt: User prompt describing what report to generate.
            stream: Whether to stream the response (default: False).

        Returns:
            If stream=False: Complete response string.
            If stream=True: AsyncIterator of response chunks.
        """
        return self.analyze_announcement(prompt, stream=stream)

    async def generate_report_async(
        self,
        prompt: str,
        stream: bool = False,
    ) -> str | AsyncIterator[str]:
        """Generate a report using the agent (async).

        Args:
            prompt: User prompt describing what report to generate.
            stream: Whether to stream the response (default: False).

        Returns:
            If stream=False: Complete response string.
            If stream=True: AsyncIterator of response chunks.
        """
        return await self.analyze_announcement_async(prompt, stream=stream)

    def chat(
        self,
        message: str,
        stream: bool = False,
    ) -> str | AsyncIterator[str]:
        """Chat with the agent.

        Args:
            message: User message.
            stream: Whether to stream the response (default: False).

        Returns:
            If stream=False: Complete response string.
            If stream=True: AsyncIterator of response chunks.
        """
        return self.analyze_announcement(message, stream=stream)

    async def chat_async(
        self,
        message: str,
        stream: bool = False,
    ) -> str | AsyncIterator[str]:
        """Chat with the agent (async).

        Args:
            message: User message.
            stream: Whether to stream the response (default: False).

        Returns:
            If stream=False: Complete response string.
            If stream=True: AsyncIterator of response chunks.
        """
        return await self.analyze_announcement_async(message, stream=stream)

    def get_cache_dir(self) -> Path:
        """Get the PDF cache directory for this agent.

        Returns:
            Path to PDF cache directory.
        """
        from src.config.agent_config import get_agent_dir_name
        agent_dir_name = get_agent_dir_name()
        return Path.home() / agent_dir_name / self.agent_id / "pdf_cache"

    def clear_cache(self) -> int:
        """Clear all cached PDFs.

        Returns:
            Number of files deleted.
        """
        cache_dir = self.get_cache_dir()
        if not cache_dir.exists():
            return 0

        deleted_count = 0
        for pdf_file in cache_dir.rglob("*.pdf"):
            try:
                pdf_file.unlink()
                deleted_count += 1
            except Exception:
                pass

        return deleted_count

