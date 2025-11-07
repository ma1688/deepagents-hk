"""Custom tools for the CLI agent."""

from hkex_agent.tools.hkex_tools import (
    get_announcement_categories,
    get_latest_hkex_announcements,
    get_stock_info,
    search_hkex_announcements,
)
from hkex_agent.tools.pdf_tools import (
    analyze_pdf_structure,
    download_announcement_pdf,
    extract_pdf_content,
    get_cached_pdf_path,
)
from hkex_agent.tools.summary_tools import generate_summary_markdown

# Export all HKEX tools
__all__ = [
    "search_hkex_announcements",
    "get_latest_hkex_announcements",
    "get_stock_info",
    "get_announcement_categories",
    "get_cached_pdf_path",
    "download_announcement_pdf",
    "extract_pdf_content",
    "analyze_pdf_structure",
    "generate_summary_markdown",
]

