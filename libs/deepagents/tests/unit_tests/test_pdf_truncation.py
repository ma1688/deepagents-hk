"""Unit tests for PDF content truncation functionality."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from src.services.pdf_parser import PDFParserService
from src.tools.pdf_tools import (
    MAX_INLINE_TEXT_CHARS,
    TABLE_PREVIEW_COUNT,
    extract_pdf_content,
)


class TestPDFParserCacheMethods:
    """Test PDF parser cache path methods."""

    def test_get_cache_text_path(self):
        """Test text cache path generation."""
        parser = PDFParserService()
        pdf_path = "/path/to/document.pdf"
        text_path = parser._get_cache_text_path(pdf_path)
        assert text_path == Path("/path/to/document.txt")

    def test_get_cache_tables_path(self):
        """Test tables cache path generation."""
        parser = PDFParserService()
        pdf_path = "/path/to/document.pdf"
        tables_path = parser._get_cache_tables_path(pdf_path)
        assert tables_path == Path("/path/to/document_tables.json")

    @patch("pathlib.Path.write_text")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.rename")
    def test_save_extracted_content(self, mock_rename, mock_exists, mock_write_text):
        """Test saving extracted content to cache."""
        mock_exists.return_value = False
        parser = PDFParserService()

        text = "Sample text content"
        tables = [{"page": 1, "table": [["A", "B"], ["1", "2"]]}]

        text_path, tables_path = parser.save_extracted_content(
            "/path/to/document.pdf", text, tables
        )

        assert text_path == "/path/to/document.txt"
        assert tables_path == "/path/to/document_tables.json"
        assert mock_write_text.call_count == 2  # Text + tables

    @patch("pathlib.Path.exists")
    def test_save_extracted_content_skip_existing(self, mock_exists):
        """Test that existing cache files are not overwritten by default."""
        mock_exists.return_value = True
        parser = PDFParserService()

        text = "Sample text"
        tables = []

        text_path, tables_path = parser.save_extracted_content(
            "/path/to/document.pdf", text, tables, force=False
        )

        # Should return paths but not write
        assert text_path == "/path/to/document.txt"
        assert tables_path == "/path/to/document_tables.json"


class TestExtractPDFContentTruncation:
    """Test extract_pdf_content truncation logic."""

    @patch("src.tools.pdf_tools._pdf_service")
    def test_small_pdf_no_truncation(self, mock_service):
        """Test that small PDFs are not truncated."""
        # Mock small PDF content
        small_text = "A" * 1000  # 1k characters
        small_tables = [{"page": 1, "table": [["A", "B"], ["1", "2"]]}]

        mock_service.extract_text.return_value = small_text
        mock_service.extract_tables.return_value = small_tables

        result = extract_pdf_content("/path/to/small.pdf")

        assert result["success"] is True
        assert result["truncated"] is False
        assert result["text"] == small_text
        assert result["tables"] == small_tables
        assert "text_path" not in result
        assert "tables_path" not in result

    @patch("src.tools.pdf_tools._pdf_service")
    def test_large_pdf_text_truncation(self, mock_service):
        """Test that large PDFs trigger text truncation."""
        # Mock large PDF content
        large_text = "A" * 100_000  # 100k characters
        small_tables = []

        mock_service.extract_text.return_value = large_text
        mock_service.extract_tables.return_value = small_tables
        mock_service.save_extracted_content.return_value = (
            "/path/to/large.txt",
            "/path/to/large_tables.json",
        )

        result = extract_pdf_content("/path/to/large.pdf")

        assert result["success"] is True
        assert result["truncated"] is True
        assert len(result["text"]) < len(large_text)
        assert result["text_length"] == 100_000
        assert result["text_path"] == "/path/to/large.txt"
        assert "完整内容已保存至" in result["text"]

    @patch("src.tools.pdf_tools._pdf_service")
    def test_large_pdf_tables_truncation(self, mock_service):
        """Test that PDFs with many tables trigger truncation."""
        # Mock PDF with many large tables
        small_text = "Short text"
        large_tables = [
            {"page": i, "table": [["A", "B"]] * 50}  # 50 rows per table
            for i in range(10)  # 10 tables = 500 rows total
        ]

        mock_service.extract_text.return_value = small_text
        mock_service.extract_tables.return_value = large_tables
        mock_service.save_extracted_content.return_value = (
            "/path/to/doc.txt",
            "/path/to/doc_tables.json",
        )

        result = extract_pdf_content("/path/to/doc.pdf")

        assert result["success"] is True
        assert result["truncated"] is True
        assert len(result["tables"]) == TABLE_PREVIEW_COUNT
        assert result["num_tables"] == 10
        assert result["tables_path"] == "/path/to/doc_tables.json"

    @patch("src.tools.pdf_tools._pdf_service")
    def test_boundary_case_exact_threshold(self, mock_service):
        """Test behavior at exact truncation threshold."""
        # Exactly at threshold
        text_at_threshold = "A" * MAX_INLINE_TEXT_CHARS

        mock_service.extract_text.return_value = text_at_threshold
        mock_service.extract_tables.return_value = []

        result = extract_pdf_content("/path/to/boundary.pdf")

        # At threshold should NOT truncate (only > threshold)
        assert result["truncated"] is False
        assert result["text"] == text_at_threshold

    @patch("src.tools.pdf_tools._pdf_service")
    def test_error_handling(self, mock_service):
        """Test error handling in extract_pdf_content."""
        mock_service.extract_text.side_effect = RuntimeError("PDF parsing failed")

        result = extract_pdf_content("/path/to/broken.pdf")

        assert result["success"] is False
        assert "error" in result
        assert result["truncated"] is False


class TestCleanupExtension:
    """Test cleanup_old_pdfs extension for cache files."""

    @patch("pathlib.Path.rglob")
    @patch("pathlib.Path.exists")
    @patch("pathlib.Path.unlink")
    @patch("pathlib.Path.stat")
    def test_cleanup_removes_cache_files(
        self, mock_stat, mock_unlink, mock_exists, mock_rglob
    ):
        """Test that cleanup removes associated .txt and _tables.json files."""
        parser = PDFParserService()

        # Mock old PDF file
        old_pdf = MagicMock()
        old_pdf.stat.return_value.st_mtime = 0  # Very old
        old_pdf.__str__.return_value = "/cache/doc.pdf"

        mock_rglob.return_value = [old_pdf]
        mock_exists.return_value = True

        deleted = parser.cleanup_old_pdfs("/cache", days=30)

        # Should delete PDF + text cache + tables cache = 3 files
        assert deleted == 3
        assert mock_unlink.call_count == 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

