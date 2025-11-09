"""Integration tests for PDF truncation workflow.

These tests verify the end-to-end behavior of PDF extraction with truncation.
"""

from pathlib import Path
from unittest.mock import patch

import pytest

from src.tools.pdf_tools import extract_pdf_content
from src.tools.summary_tools import generate_summary_markdown


class TestPDFTruncationWorkflow:
    """Test complete workflow with PDF truncation."""

    @patch("src.tools.pdf_tools._pdf_service")
    def test_large_pdf_extraction_and_summary(self, mock_service, tmp_path):
        """Test extracting large PDF and generating summary."""
        # Setup: Mock large PDF
        large_text = "Large document content. " * 10_000  # ~250k chars
        tables = [{"page": i, "table": [["Col1", "Col2"], ["A", "B"]]} for i in range(20)]

        # Mock cache paths in tmp directory
        text_cache = tmp_path / "large.txt"
        tables_cache = tmp_path / "large_tables.json"

        mock_service.extract_text.return_value = large_text
        mock_service.extract_tables.return_value = tables
        mock_service.save_extracted_content.return_value = (
            str(text_cache),
            str(tables_cache),
        )

        # Step 1: Extract PDF content
        pdf_content = extract_pdf_content(str(tmp_path / "large.pdf"))

        # Verify truncation occurred
        assert pdf_content["success"] is True
        assert pdf_content["truncated"] is True
        assert pdf_content["text_length"] > 200_000
        assert len(pdf_content["text"]) < 10_000  # Preview only
        assert "完整内容已保存至" in pdf_content["text"]

        # Step 2: Generate summary with truncated content
        output_path = tmp_path / "summary.md"
        summary = generate_summary_markdown(
            stock_code="03800",
            title="2024年报",
            date_time="2025-04-29",
            output_path=str(output_path),
            pdf_content=pdf_content,
        )

        assert summary["success"] is True

        # Verify summary contains cache path reference
        summary_content = Path(summary["output_path"]).read_text()
        assert "完整文档" in summary_content
        assert str(text_cache) in summary_content

    @patch("src.tools.pdf_tools._pdf_service")
    def test_small_pdf_backward_compatibility(self, mock_service, tmp_path):
        """Test that small PDFs work exactly as before (backward compatibility)."""
        # Setup: Mock small PDF
        small_text = "Short announcement content."
        tables = [{"page": 1, "table": [["Header"], ["Data"]]}]

        mock_service.extract_text.return_value = small_text
        mock_service.extract_tables.return_value = tables

        # Extract PDF content
        pdf_content = extract_pdf_content(str(tmp_path / "small.pdf"))

        # Verify NO truncation
        assert pdf_content["success"] is True
        assert pdf_content["truncated"] is False
        assert pdf_content["text"] == small_text
        assert pdf_content["tables"] == tables
        assert "text_path" not in pdf_content
        assert "tables_path" not in pdf_content

        # Generate summary
        output_path = tmp_path / "summary.md"
        summary = generate_summary_markdown(
            stock_code="00328",
            title="简短公告",
            date_time="2025-11-08",
            output_path=str(output_path),
            pdf_content=pdf_content,
        )

        assert summary["success"] is True

        # Verify summary contains full text (no cache reference)
        summary_content = Path(summary["output_path"]).read_text()
        assert small_text in summary_content
        assert "完整文档" not in summary_content  # No truncation message


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

