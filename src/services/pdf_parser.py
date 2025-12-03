"""PDF parsing service with caching support."""

import logging
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import httpx
import pdfplumber
import ssl

# Suppress pdfminer warnings about color spaces
# These warnings are common in HKEX PDFs but don't affect text/table extraction
logging.getLogger("pdfminer").setLevel(logging.ERROR)


def sanitize_filename(filename: str, max_bytes: int = 200) -> str:
    """Sanitize filename by removing special characters and limiting byte length.

    File systems typically limit filename length by bytes (255 for most),
    not characters. Chinese characters are 3-4 bytes each in UTF-8.

    Args:
        filename: Original filename.
        max_bytes: Maximum filename length in bytes (default 200, safe for all filesystems).

    Returns:
        Sanitized filename within byte limit.
    """
    # Remove or replace special characters
    filename = re.sub(r'[/\\:*?"<>|]', "-", filename)
    # Remove multiple consecutive dashes
    filename = re.sub(r"-+", "-", filename)
    # Remove leading/trailing dashes
    filename = filename.strip("-")

    # Truncate by byte length (filesystem limit is typically 255 bytes)
    encoded = filename.encode("utf-8")
    if len(encoded) <= max_bytes:
        return filename

    # Need to truncate - split into name and extension
    name, ext = os.path.splitext(filename)
    ext_bytes = ext.encode("utf-8")
    # Use Unicode ellipsis (U+2026) instead of "..." to avoid triggering
    # path traversal checks that look for ".." in paths
    suffix = "…"
    suffix_bytes = suffix.encode("utf-8")
    
    # Calculate max bytes for name part
    max_name_bytes = max_bytes - len(ext_bytes) - len(suffix_bytes)
    
    if max_name_bytes <= 0:
        # Extension too long, just truncate everything
        max_name_bytes = max_bytes - len(suffix_bytes)
        ext = ""
    
    # Truncate name by bytes while preserving valid UTF-8
    name_encoded = name.encode("utf-8")
    if len(name_encoded) > max_name_bytes:
        # Truncate and ensure we don't split a multi-byte character
        truncated = name_encoded[:max_name_bytes]
        # Decode with errors='ignore' to drop incomplete multi-byte sequences
        name = truncated.decode("utf-8", errors="ignore")
    
    return name + suffix + ext


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
        if not date:
            return None

        stock_dir = Path(cache_dir) / stock_code
        if not stock_dir.exists():
            return None

        # First try exact match with generated filename
        if title:
            filename = sanitize_filename(f"{date}-{title}.pdf")
            cache_path = stock_dir / filename
            if cache_path.exists():
                return str(cache_path)

        # If exact match fails, check all PDFs in the directory
        # Find all PDFs that start with the same date
        date_prefix = f"{date}-"
        matching_files = [f for f in stock_dir.glob("*.pdf") if f.name.startswith(date_prefix)]

        if not matching_files:
            return None

        # If only one file matches the date, return it
        if len(matching_files) == 1:
            return str(matching_files[0])

        # If multiple files match the date and we have a title, try to match by title
        if title:
            # Normalize title for comparison
            normalized_title = re.sub(r'\s+', ' ', title.strip().lower())
            best_match = None
            best_score = 0

            for cached_file in matching_files:
                # Extract title from filename
                cached_title = cached_file.stem[len(date_prefix):]
                normalized_cached_title = re.sub(r'\s+', ' ', cached_title.strip().lower())

                # Simple substring match - if normalized title is contained in cached title or vice versa
                if normalized_title in normalized_cached_title or normalized_cached_title in normalized_title:
                    # Calculate word overlap for better matching
                    title_words = set(normalized_title.split())
                    cached_words = set(normalized_cached_title.split())
                    if title_words and cached_words:
                        overlap = len(title_words & cached_words) / len(title_words | cached_words)
                        if overlap > best_score:
                            best_score = overlap
                            best_match = cached_file

            if best_match and best_score > 0:
                return str(best_match)

        # Fallback: return the first matching file (better than downloading again)
        return str(matching_files[0])

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

        # Double-check cache after directory creation (prevent race condition)
        # Another process might have created the file between the first check and now
        # Use fuzzy matching here too in case title formatting differs
        cached_path_retry = self.get_cached_pdf_path(stock_code, date, title, cache_dir)
        if cached_path_retry:
            return cached_path_retry

        # Download PDF using temporary file, then atomically rename
        # This prevents partial writes if another process reads the file during download
        temp_file = None
        try:
            # Create temporary file in the same directory for atomic rename
            temp_file = cache_path.parent / f".{filename}.tmp"
            
            with httpx.Client(
                headers=self.DEFAULT_HEADERS,
                timeout=self.timeout,
                verify=False,
            ) as client:
                response = client.get(full_url)
                response.raise_for_status()

                # Write to temporary file first
                with open(temp_file, "wb") as f:
                    f.write(response.content)

            # Double-check cache one more time before atomic rename
            # Another process might have completed the download while we were downloading
            if cache_path.exists():
                # Another process beat us to it, clean up temp file and return cached path
                try:
                    temp_file.unlink()
                except Exception:
                    pass  # Ignore cleanup errors
                return str(cache_path)

            # Atomically rename temp file to final location
            temp_file.rename(cache_path)

            return str(cache_path)

        except Exception as e:
            # Clean up temp file on error
            if temp_file and temp_file.exists():
                try:
                    temp_file.unlink()
                except Exception:
                    pass  # Ignore cleanup errors
            
            # If file was created by another process during our download, return it
            if cache_path.exists():
                return str(cache_path)
            
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

    def _get_cache_text_path(self, pdf_path: str) -> Path:
        """Get text cache path for a PDF file.
        
        Args:
            pdf_path: Path to PDF file.
        
        Returns:
            Path to text cache file (.txt).
        """
        return Path(pdf_path).with_suffix(".txt")
    
    def _get_cache_tables_path(self, pdf_path: str) -> Path:
        """Get tables cache path for a PDF file.
        
        Args:
            pdf_path: Path to PDF file.
        
        Returns:
            Path to tables cache file (_tables.json).
        """
        pdf_stem = Path(pdf_path).stem
        return Path(pdf_path).parent / f"{pdf_stem}_tables.json"
    
    def save_extracted_content(
        self,
        pdf_path: str,
        text: str,
        tables: list[dict[str, Any]],
        force: bool = False,
    ) -> tuple[str, str]:
        """Save extracted PDF content to cache files.
        
        Uses atomic write (temp file + rename) to prevent concurrent reads
        from accessing incomplete data.
        
        Args:
            pdf_path: Path to PDF file.
            text: Extracted text content.
            tables: Extracted tables list.
            force: Force overwrite existing cache files.
        
        Returns:
            Tuple of (text_cache_path, tables_cache_path).
        """
        import json
        
        text_path = self._get_cache_text_path(pdf_path)
        tables_path = self._get_cache_tables_path(pdf_path)
        
        # Write text cache with atomic rename
        if force or not text_path.exists():
            tmp_text = text_path.with_suffix(".txt.tmp")
            tmp_text.write_text(text, encoding="utf-8")
            tmp_text.rename(text_path)
        
        # Write tables cache with atomic rename
        if force or not tables_path.exists():
            tmp_tables = tables_path.with_suffix(".json.tmp")
            tmp_tables.write_text(
                json.dumps(tables, ensure_ascii=False, indent=2),
                encoding="utf-8"
            )
            tmp_tables.rename(tables_path)
        
        return str(text_path), str(tables_path)

    def cleanup_old_pdfs(self, cache_dir: str, days: int = 30) -> int:
        """Clean up PDFs and related cache files older than specified days.

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

        # Clean up PDFs and their cache files
        for pdf_file in cache_path.rglob("*.pdf"):
            if pdf_file.stat().st_mtime < cutoff_time:
                try:
                    # Delete PDF
                    pdf_file.unlink()
                    deleted_count += 1
                    
                    # Delete associated cache files
                    text_cache = self._get_cache_text_path(str(pdf_file))
                    if text_cache.exists():
                        text_cache.unlink()
                        deleted_count += 1
                    
                    tables_cache = self._get_cache_tables_path(str(pdf_file))
                    if tables_cache.exists():
                        tables_cache.unlink()
                        deleted_count += 1
                except Exception:
                    pass

        return deleted_count

