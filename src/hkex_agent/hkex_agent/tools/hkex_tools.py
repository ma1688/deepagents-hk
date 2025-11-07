"""HKEX tools for DeepAgents."""

from datetime import datetime
from typing import Any

from langchain_core.tools import tool

from hkex_agent.services.hkex_api import HKEXAPIService

# Initialize service instance
_hkex_service = HKEXAPIService()


@tool
def search_hkex_announcements(
    stock_code: str,
    from_date: str,
    to_date: str,
    title: str | None = None,
    market: str = "SEHK",
    row_range: int = 100,
) -> dict[str, Any]:
    """Search HKEX announcements for a specific stock.

    This tool searches for announcements published by a Hong Kong stock exchange listed company
    within a date range. It first looks up the stock ID, then searches for announcements.

    Args:
        stock_code: 5-digit stock code (e.g., "00673").
        from_date: Start date in YYYYMMDD format (e.g., "20250101").
        to_date: End date in YYYYMMDD format (e.g., "20251008").
        title: Optional search keyword to filter by title.
        market: Market code - "SEHK" (main board) or "GEM" (default: "SEHK").
        row_range: Number of results to return, 1-500 (default: 100).

    Returns:
        Dictionary containing:
        - stock_id: Internal stock ID
        - stock_code: Stock code
        - announcements: List of announcement dictionaries, each containing:
          - NEWS_ID: News ID
          - TITLE: Announcement title
          - DATE_TIME: Publication date/time (dd/mm/yyyy HH:MM format)
          - FILE_LINK: Relative path to PDF file
          - STOCK_CODE: Stock code
          - STOCK_NAME: Stock name
          - FILE_TYPE: File type (usually "PDF")
          - FILE_INFO: File size information
          - SHORT_TEXT: Short description
          - LONG_TEXT: Long description
    """
    # Get stock ID
    stock_id, stock_info = _hkex_service.get_stock_id(stock_code)

    if not stock_id:
        return {
            "stock_code": stock_code,
            "stock_id": None,
            "error": "Stock not found",
            "announcements": [],
        }

    # Search announcements
    stock_id, announcements = _hkex_service.search_announcements(
        stock_id=stock_id,
        from_date=from_date,
        to_date=to_date,
        title=title,
        market=market,
        row_range=row_range,
    )

    return {
        "stock_code": stock_code,
        "stock_id": stock_id,
        "announcements": announcements,
    }


@tool
def get_latest_hkex_announcements(
    market: str | None = None,
    stock_code: str | None = None,
    t1_code: str | None = None,
    t2_code: str | None = None,
) -> dict[str, Any]:
    """Get latest announcements from HKEX.

    This tool fetches the most recent announcements from the Hong Kong Stock Exchange.
    You can filter by market, stock code, or category codes.

    Args:
        market: Filter by market - "SEHK" (main board) or "GEM" (optional).
        stock_code: Filter by 5-digit stock code (optional).
        t1_code: Filter by tier 1 category code (optional).
        t2_code: Filter by tier 2 category code (optional).

    Returns:
        Dictionary containing:
        - announcements: List of announcement dictionaries, each containing:
          - newsId: News ID
          - title: Announcement title
          - relTime: Release time (dd/mm/yyyy HH:MM format)
          - webPath: Relative path to PDF file
          - ext: File extension (usually "PDF")
          - size: File size
          - sTxt: Short text description
          - lTxt: Long text description
          - t1Code: Tier 1 category code (may be "NaN")
          - t2Code: Tier 2 category code (may be "NaN")
          - market: Market code
          - stock: List of stock dictionaries with "sc" (stock code) and "sn" (stock name)
    """
    announcements = _hkex_service.get_latest_announcements(
        market=market,
        stock_code=stock_code,
        t1_code=t1_code,
        t2_code=t2_code,
    )

    return {
        "announcements": announcements,
        "count": len(announcements),
    }


@tool
def get_stock_info(stock_code: str) -> dict[str, Any]:
    """Get stock information from HKEX.

    This tool looks up basic information about a Hong Kong stock by its code.

    Args:
        stock_code: 5-digit stock code (e.g., "00673").

    Returns:
        Dictionary containing:
        - stock_code: Stock code
        - stock_id: Internal stock ID (if found)
        - stock_info: List of stock information dictionaries, each containing:
          - stockId: Internal stock ID
          - stockCode: Stock code
          - stockName: Stock name
          - market: Market code
    """
    stock_id, stock_info = _hkex_service.get_stock_id(stock_code)

    return {
        "stock_code": stock_code,
        "stock_id": stock_id,
        "stock_info": stock_info,
        "found": stock_id is not None,
    }


@tool
def get_announcement_categories(
    category_type: str = "tierone",
) -> dict[str, Any]:
    """Get announcement category codes from HKEX.

    This tool retrieves category codes used for filtering announcements.
    Categories help classify announcements by type (e.g., financial statements, notices).

    Args:
        category_type: Type of category to retrieve:
          - "doc": Document type categories
          - "tierone": Tier 1 categories (default)
          - "tiertwo": Tier 2 categories
          - "tiertwogrp": Tier 2 group categories

    Returns:
        Dictionary containing:
        - category_type: The requested category type
        - categories: List of category dictionaries, each containing:
          - code: Category code
          - name: Category name (Chinese)
          - nameEn: Category name (English, if available)
    """
    categories = _hkex_service.get_categories(category_type)

    return {
        "category_type": category_type,
        "categories": categories,
    }

