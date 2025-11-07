"""PDF processing tools for DeepAgents."""

import os
from pathlib import Path
from typing import Any

from langchain_core.tools import tool

from hkex_agent.services.hkex_api import HKEXAPIService
from hkex_agent.services.pdf_parser import (
    PDFParserService,
    format_date_for_filename,
)

# Initialize service instances
_hkex_service = HKEXAPIService()
_pdf_service = PDFParserService()


def _resolve_cache_dir(cache_dir: str) -> str:
    """Resolve virtual cache directory path to actual filesystem path.
    
    Args:
        cache_dir: Virtual path like "/pdf_cache/" or actual path like "./pdf_cache/"
        
    Returns:
        Actual filesystem path
    """
    # If it's a virtual path starting with "/pdf_cache/", resolve to project root
    if cache_dir.startswith("/pdf_cache"):
        # Remove leading slash and resolve relative to project root
        relative_path = cache_dir.lstrip("/")
        project_root = Path.cwd()
        actual_path = project_root / relative_path
        return str(actual_path)
    
    # If it's already a relative or absolute path, use as-is
    return cache_dir


@tool
def get_cached_pdf_path(
    stock_code: str,
    date_time: str,
    title: str,
    cache_dir: str,
) -> dict[str, Any]:
    """Check if a PDF is already cached locally.

    This tool checks if a PDF announcement has already been downloaded and cached.
    Use this before downloading to avoid redundant downloads.

    Args:
        stock_code: 5-digit stock code (e.g., "00673").
        date_time: Date time string in format "dd/mm/yyyy HH:MM" or "YYYY-MM-DD".
        title: Announcement title.
        cache_dir: Cache directory path (usually "/pdf_cache/").

    Returns:
        Dictionary containing:
        - cached: Boolean indicating if PDF is cached
        - path: Full path to cached PDF if exists, None otherwise
        - stock_code: Stock code
        - date: Parsed date in YYYY-MM-DD format
    """
    date = format_date_for_filename(date_time)
    # Resolve virtual path to actual filesystem path
    actual_cache_dir = _resolve_cache_dir(cache_dir)
    cached_path = _pdf_service.get_cached_pdf_path(
        stock_code=stock_code,
        date=date,
        title=title,
        cache_dir=actual_cache_dir,
    )

    return {
        "cached": cached_path is not None,
        "path": cached_path,
        "stock_code": stock_code,
        "date": date,
    }


@tool
def download_announcement_pdf(
    news_id: str,
    pdf_url: str,
    stock_code: str,
    date_time: str,
    title: str,
    cache_dir: str = "/pdf_cache/",
    force_download: bool = False,
) -> dict[str, Any]:
    """Download an announcement PDF with intelligent caching.

    This tool downloads a PDF announcement from HKEX. It automatically checks the cache
    first and only downloads if the file doesn't exist locally. This saves time and
    bandwidth.

    Args:
        news_id: News ID from announcement data.
        pdf_url: PDF URL (relative path like "/listedco/listconews/sehk/2025/1008/file.pdf").
        stock_code: 5-digit stock code (e.g., "00673").
        date_time: Date time string in format "dd/mm/yyyy HH:MM".
        title: Announcement title.
        cache_dir: Cache directory path (default: "/pdf_cache/").
        force_download: If True, download even if cached (default: False).

    Returns:
        Dictionary containing:
        - success: Boolean indicating success
        - path: Full path to PDF file (cached or newly downloaded)
        - cached: Boolean indicating if file was from cache
        - news_id: News ID
        - stock_code: Stock code
    """
    date = format_date_for_filename(date_time)

    # Resolve virtual path to actual filesystem path
    actual_cache_dir = _resolve_cache_dir(cache_dir)

    # Check cache first (unless force_download)
    if not force_download:
        cached_path = _pdf_service.get_cached_pdf_path(
            stock_code=stock_code,
            date=date,
            title=title,
            cache_dir=actual_cache_dir,
        )
        if cached_path:
            return {
                "success": True,
                "path": cached_path,
                "cached": True,
                "news_id": news_id,
                "stock_code": stock_code,
            }

    # Download PDF
    try:
        pdf_path = _pdf_service.download_pdf(
            url=pdf_url,
            stock_code=stock_code,
            date=date,
            title=title,
            cache_dir=actual_cache_dir,
        )

        return {
            "success": True,
            "path": pdf_path,
            "cached": False,
            "news_id": news_id,
            "stock_code": stock_code,
        }

    except Exception as e:
        return {
            "success": False,
            "path": None,
            "cached": False,
            "news_id": news_id,
            "stock_code": stock_code,
            "error": str(e),
        }


@tool
def extract_pdf_content(
    pdf_path: str,
    include_tables: bool = True,
) -> dict[str, Any]:
    """Extract text and tables from a PDF file.

    This tool extracts all text content and optionally tables from a PDF announcement.
    The PDF should already be downloaded (use download_announcement_pdf first).

    Args:
        pdf_path: Full path to PDF file.
        include_tables: Whether to extract tables (default: True).

    Returns:
        Dictionary containing:
        - success: Boolean indicating success
        - text: Extracted text content
        - tables: List of tables (if include_tables=True), each with:
          - page: Page number
          - table: Table data as list of rows
        - text_length: Length of extracted text
        - num_tables: Number of tables extracted
    """
    try:
        # Extract text
        text = _pdf_service.extract_text(pdf_path)

        # Extract tables if requested
        tables = []
        if include_tables:
            tables = _pdf_service.extract_tables(pdf_path)

        return {
            "success": True,
            "text": text,
            "tables": tables,
            "text_length": len(text),
            "num_tables": len(tables),
        }

    except Exception as e:
        return {
            "success": False,
            "text": "",
            "tables": [],
            "text_length": 0,
            "num_tables": 0,
            "error": str(e),
        }


@tool
def analyze_pdf_structure(pdf_path: str) -> dict[str, Any]:
    """Analyze the structure of a PDF file.

    This tool analyzes a PDF to identify its structure, including number of pages,
    presence of tables, and estimated sections/headings.

    Args:
        pdf_path: Full path to PDF file.

    Returns:
        Dictionary containing:
        - success: Boolean indicating success
        - num_pages: Number of pages in PDF
        - has_tables: Boolean indicating if PDF contains tables
        - estimated_sections: List of potential section markers with page numbers
    """
    try:
        structure = _pdf_service.analyze_structure(pdf_path)

        return {
            "success": True,
            **structure,
        }

    except Exception as e:
        return {
            "success": False,
            "num_pages": 0,
            "has_tables": False,
            "estimated_sections": [],
            "error": str(e),
        }

