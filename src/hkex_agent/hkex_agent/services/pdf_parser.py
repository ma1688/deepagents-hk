"""PDF parsing service with caching support."""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
import pdfplumber
import ssl


def sanitize_filename(filename: str, max_length: int = 200) -> str:
    """Sanitize filename by removing special characters.

    Args:
        filename: Original filename.
        max_length: Maximum filename length.

    Returns:
        Sanitized filename.
    """
    # Remove or replace special characters
    filename = re.sub(r'[/\\:*?"<>|]', "-", filename)
    # Remove multiple consecutive dashes
    filename = re.sub(r"-+", "-", filename)
    # Remove leading/trailing dashes
    filename = filename.strip("-")

    # Truncate if too long
    if len(filename) > max_length:
        name, ext = os.path.splitext(filename)
        max_name_length = max_length - len(ext) - 3  # Reserve space for "..."
        filename = name[:max_name_length] + "..." + ext

    return filename


def format_date_for_filename(date_time_str: str) -> str:
    """Format date string for filename.

    Args:
        date_time_str: Date time string in format "dd/mm/yyyy HH:MM" or "YYYY-MM-DD".

    Returns:
        Date string in YYYY-MM-DD format.
    """
    try:
        # Try parsing "dd/mm/yyyy HH:MM" format
        if "/" in date_time_str:
            dt = datetime.strptime(date_time_str.split()[0], "%d/%m/%Y")
            return dt.strftime("%Y-%m-%d")
        # Try parsing "YYYY-MM-DD" format
        elif "-" in date_time_str:
            dt = datetime.strptime(date_time_str.split()[0], "%Y-%m-%d")
            return dt.strftime("%Y-%m-%d")
    except Exception:
        pass

    return ""


class PDFParserService:
    """Service for parsing PDF files with caching."""

    BASE_URL = "https://www1.hkexnews.hk"
    DEFAULT_HEADERS = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        ),
    }

    def __init__(self, timeout: int = 60):
        """Initialize PDF parser service.

        Args:
            timeout: Request timeout in seconds.
        """
        self.timeout = timeout
        # Create SSL context that doesn't verify certificates
        self.ssl_context = ssl.create_default_context()
        self.ssl_context.check_hostname = False
        self.ssl_context.verify_mode = ssl.CERT_NONE
        self.ssl_context.minimum_version = ssl.TLSVersion.TLSv1_2

    def get_cached_pdf_path(
        self, stock_code: str, date: str, title: str, cache_dir: str
    ) -> str | None:
        """Get cached PDF path if it exists.

        Args:
            stock_code: Stock code (e.g., "00673").
            date: Date string in YYYY-MM-DD format.
            title: Announcement title.
            cache_dir: Cache directory path.

        Returns:
            Full path to cached PDF if exists, None otherwise.
        """
        if not date or not title:
            return None

        # Format filename
        filename = sanitize_filename(f"{date}-{title}.pdf")
        cache_path = Path(cache_dir) / stock_code / filename

        if cache_path.exists():
            return str(cache_path)

        return None

    def download_pdf(
        self,
        url: str,
        stock_code: str,
        date: str,
        title: str,
        cache_dir: str,
    ) -> str:
        """Download PDF and save to cache.

        Args:
            url: PDF URL (relative or absolute).
            stock_code: Stock code (e.g., "00673").
            date: Date string in YYYY-MM-DD format.
            title: Announcement title.
            cache_dir: Cache directory path.

        Returns:
            Full path to downloaded PDF.
        """
        # Check cache first
        cached_path = self.get_cached_pdf_path(stock_code, date, title, cache_dir)
        if cached_path:
            return cached_path

        # Build full URL if relative
        if url.startswith("/"):
            full_url = self.BASE_URL + url
        else:
            full_url = url

        # Format filename
        filename = sanitize_filename(f"{date}-{title}.pdf")
        cache_path = Path(cache_dir) / stock_code / filename

        # Create directory if needed
        cache_path.parent.mkdir(parents=True, exist_ok=True)

        # Download PDF
        try:
            with httpx.Client(
                headers=self.DEFAULT_HEADERS,
                timeout=self.timeout,
                verify=False,
            ) as client:
                response = client.get(full_url)
                response.raise_for_status()

                # Save to cache
                with open(cache_path, "wb") as f:
                    f.write(response.content)

                return str(cache_path)

        except Exception as e:
            raise RuntimeError(f"Failed to download PDF from {full_url}: {e}") from e

    def extract_text(self, pdf_path: str) -> str:
        """Extract text from PDF.

        Args:
            pdf_path: Path to PDF file.

        Returns:
            Extracted text content.
        """
        text_parts = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page in pdf.pages:
                    text = page.extract_text()
                    if text:
                        text_parts.append(text)

            return "\n\n".join(text_parts)

        except Exception as e:
            raise RuntimeError(f"Failed to extract text from PDF: {e}") from e

    def extract_tables(self, pdf_path: str) -> list[dict[str, Any]]:
        """Extract tables from PDF.

        Args:
            pdf_path: Path to PDF file.

        Returns:
            List of tables, each as a list of rows.
        """
        tables = []

        try:
            with pdfplumber.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    page_tables = page.extract_tables()
                    for table in page_tables:
                        if table:
                            tables.append(
                                {
                                    "page": page_num,
                                    "table": table,
                                }
                            )

            return tables

        except Exception as e:
            raise RuntimeError(f"Failed to extract tables from PDF: {e}") from e

    def analyze_structure(self, pdf_path: str) -> dict[str, Any]:
        """Analyze PDF structure (sections, headings, etc.).

        Args:
            pdf_path: Path to PDF file.

        Returns:
            Dictionary with structure information.
        """
        structure = {
            "num_pages": 0,
            "has_tables": False,
            "estimated_sections": [],
        }

        try:
            with pdfplumber.open(pdf_path) as pdf:
                structure["num_pages"] = len(pdf.pages)

                # Check for tables
                for page in pdf.pages:
                    tables = page.extract_tables()
                    if tables:
                        structure["has_tables"] = True
                        break

                # Try to identify sections by font size (heuristic)
                for page_num, page in enumerate(pdf.pages, 1):
                    chars = page.chars
                    if chars:
                        # Group by font size to identify potential headings
                        font_sizes = {}
                        for char in chars:
                            size = char.get("size", 0)
                            if size > 0:
                                font_sizes[size] = font_sizes.get(size, 0) + 1

                        # Large font sizes might indicate headings
                        if font_sizes:
                            max_size = max(font_sizes.keys())
                            if max_size > 12:  # Threshold for headings
                                structure["estimated_sections"].append(
                                    {
                                        "page": page_num,
                                        "max_font_size": max_size,
                                    }
                                )

        except Exception as e:
            raise RuntimeError(f"Failed to analyze PDF structure: {e}") from e

        return structure

    def cleanup_old_pdfs(self, cache_dir: str, days: int = 30) -> int:
        """Clean up PDFs older than specified days.

        Args:
            cache_dir: Cache directory path.
            days: Number of days to keep.

        Returns:
            Number of files deleted.
        """
        cache_path = Path(cache_dir)
        if not cache_path.exists():
            return 0

        cutoff_time = datetime.now().timestamp() - (days * 24 * 60 * 60)
        deleted_count = 0

        for pdf_file in cache_path.rglob("*.pdf"):
            if pdf_file.stat().st_mtime < cutoff_time:
                try:
                    pdf_file.unlink()
                    deleted_count += 1
                except Exception:
                    pass

        return deleted_count

