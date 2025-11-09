"""PDF processing tools for DeepAgents."""

import os
from pathlib import Path
from typing import Any

from langchain_core.tools import tool

from src.services.hkex_api import HKEXAPIService
from src.services.pdf_parser import (
    PDFParserService,
    format_date_for_filename,
)

# Initialize service instances
_hkex_service = HKEXAPIService()
_pdf_service = PDFParserService()

# Truncation thresholds for large PDFs
MAX_INLINE_TEXT_CHARS = 50_000  # 50k chars ≈ 12.5k tokens (4:1 ratio)
MAX_INLINE_TABLE_ROWS = 200     # Limit total table rows
TEXT_PREVIEW_CHARS = 5_000      # Preview length for truncated text
TABLE_PREVIEW_COUNT = 5         # Number of tables to include in preview


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
    max_inline_chars: int = MAX_INLINE_TEXT_CHARS,
    max_table_rows: int = MAX_INLINE_TABLE_ROWS,
) -> dict[str, Any]:
    """Extract text and tables from a PDF file with intelligent truncation.

    **IMPORTANT**: For large PDFs (text > 50k chars or tables > 200 rows),
    the full content is automatically saved to cache files, and only a preview
    is returned to avoid exceeding LLM token limits.

    This tool extracts all text content and optionally tables from a PDF announcement.
    The PDF should already be downloaded (use download_announcement_pdf first).

    Args:
        pdf_path: Full path to PDF file.
        include_tables: Whether to extract tables (default: True).
        max_inline_chars: Maximum inline text characters (default: 50k).
        max_table_rows: Maximum inline table rows (default: 200).

    Returns:
        Dictionary containing:
        - success: Boolean indicating success
        - text: Text content (full for small PDFs, preview for large PDFs)
        - text_path: Full text cache path (only if truncated)
        - tables: List of tables (full for small PDFs, preview for large PDFs)
        - tables_path: Full tables cache path (only if truncated)
        - truncated: Boolean indicating if content was truncated
        - text_length: Total text length (characters)
        - num_tables: Total number of tables
        - preview_info: Preview information (only if truncated)
    """
    try:
        # 1. Extract full content
        full_text = _pdf_service.extract_text(pdf_path)
        full_tables = []
        if include_tables:
            full_tables = _pdf_service.extract_tables(pdf_path)

        # 2. Determine if truncation is needed
        text_truncated = len(full_text) > max_inline_chars

        # Calculate total table rows
        total_table_rows = sum(
            len(tbl.get("table", []))
            for tbl in full_tables
        )
        tables_truncated = total_table_rows > max_table_rows

        truncated = text_truncated or tables_truncated

        # 3. Save to cache if truncation is needed
        text_path = None
        tables_path = None
        if truncated:
            text_path, tables_path = _pdf_service.save_extracted_content(
                pdf_path, full_text, full_tables
            )

        # 4. Prepare return content
        if text_truncated:
            # Return preview text with instructions
            preview_text = full_text[:TEXT_PREVIEW_CHARS]
            preview_text += f"\n\n... (已截断，完整文本共 {len(full_text):,} 字符)\n"
            preview_text += f"💾 完整内容已保存至: {text_path}\n"
            preview_text += f"📖 使用 read_file('{text_path}') 获取完整文本"
        else:
            preview_text = full_text

        if tables_truncated:
            # Return preview tables with instructions
            preview_tables = full_tables[:TABLE_PREVIEW_COUNT]
            preview_info_tables = (
                f"⚠️  仅显示前 {TABLE_PREVIEW_COUNT} 个表格（共 {len(full_tables)} 个）\n"
                f"💾 完整表格已保存至: {tables_path}\n"
                f"📖 使用 read_file('{tables_path}') 获取完整表格数据"
            )
        else:
            preview_tables = full_tables
            preview_info_tables = None

        # 5. Build return structure
        result = {
            "success": True,
            "text": preview_text,
            "tables": preview_tables,
            "text_length": len(full_text),
            "num_tables": len(full_tables),
            "truncated": truncated,
        }

        # Add cache paths (only when truncated)
        if truncated:
            result["text_path"] = text_path
            result["tables_path"] = tables_path
            result["preview_info"] = {
                "text": "已截断，查看 text_path" if text_truncated else None,
                "tables": preview_info_tables if tables_truncated else None,
            }

        return result

    except Exception as e:
        return {
            "success": False,
            "text": "",
            "tables": [],
            "text_length": 0,
            "num_tables": 0,
            "truncated": False,
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

