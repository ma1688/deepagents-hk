"""Summary generation tools for DeepAgents."""

import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from langchain_core.tools import tool

from hkex_agent.services.pdf_parser import format_date_for_filename


def sanitize_filename_for_md(filename: str, max_length: int = 200) -> str:
    """Sanitize filename for Markdown files.

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
        name, ext = os.path.splitext(filename) if "." in filename else (filename, "")
        max_name_length = max_length - len(ext) - 3  # Reserve space for "..."
        filename = name[:max_name_length] + "..." + ext

    return filename


@tool
def generate_summary_markdown(
    stock_code: str,
    title: str,
    date_time: str,
    output_path: str,
    pdf_path: str | None = None,
    pdf_content: dict[str, Any] | None = None,
    announcement_data: dict[str, Any] | None = None,
    summary_sections: list[str] | None = None,
) -> dict[str, Any]:
    """Generate a structured Markdown summary document for an HKEX announcement.

    This tool creates a comprehensive Markdown summary document containing:
    - Basic announcement information (stock code, title, date)
    - PDF content summary (if PDF is provided)
    - Key information extracted from the announcement
    - Structured sections for easy reading

    Args:
        stock_code: 5-digit stock code (e.g., "00328").
        title: Announcement title.
        date_time: Date time string in format "dd/mm/yyyy HH:MM" or "YYYY-MM-DD".
        output_path: Path where the Markdown file should be saved. **IMPORTANT**: Use `/md/` directory for all summaries (e.g., "/md/{stock_code}-{title}.md").
        pdf_path: Optional path to PDF file (if PDF content should be extracted).
        pdf_content: Optional dictionary with PDF content (from extract_pdf_content tool).
            Should contain 'text' and optionally 'tables' keys.
        announcement_data: Optional dictionary with announcement metadata.
            Can contain keys like: NEWS_ID, STOCK_NAME, SHORT_TEXT, LONG_TEXT, etc.
        summary_sections: Optional list of section names to include in the summary.
            Default sections: ["基本信息", "公告摘要", "主要内容", "关键数据", "相关文件"]

    Returns:
        Dictionary containing:
        - success: Boolean indicating success
        - output_path: Full path to generated Markdown file
        - file_size: Size of the generated file in bytes
        - sections_included: List of sections included in the summary
    """
    try:
        # Parse date
        date_str = format_date_for_filename(date_time)
        if not date_str:
            # Try to parse as-is
            try:
                if "/" in date_time:
                    dt = datetime.strptime(date_time.split()[0], "%d/%m/%Y")
                    date_str = dt.strftime("%Y-%m-%d")
                else:
                    date_str = date_time.split()[0]
            except Exception:
                date_str = date_time.split()[0] if date_time else ""

        # Default sections
        if summary_sections is None:
            summary_sections = ["基本信息", "公告摘要", "主要内容", "关键数据", "相关文件"]

        # Build Markdown content
        md_lines = []

        # Title
        md_lines.append(f"# {title}\n")
        md_lines.append(f"**股票代码**: {stock_code}\n")
        md_lines.append(f"**发布日期**: {date_str}\n")
        if announcement_data and announcement_data.get("STOCK_NAME"):
            md_lines.append(f"**公司名称**: {announcement_data.get('STOCK_NAME')}\n")
        md_lines.append("\n---\n\n")

        # 基本信息 (Basic Information)
        if "基本信息" in summary_sections:
            md_lines.append("## 基本信息\n\n")
            md_lines.append(f"- **股票代码**: {stock_code}\n")
            md_lines.append(f"- **公告标题**: {title}\n")
            md_lines.append(f"- **发布日期**: {date_str}\n")
            if announcement_data:
                if announcement_data.get("STOCK_NAME"):
                    md_lines.append(f"- **公司名称**: {announcement_data.get('STOCK_NAME')}\n")
                if announcement_data.get("NEWS_ID"):
                    md_lines.append(f"- **公告编号**: {announcement_data.get('NEWS_ID')}\n")
                if announcement_data.get("MARKET"):
                    md_lines.append(f"- **市场**: {announcement_data.get('MARKET')}\n")
            md_lines.append("\n")

        # 公告摘要 (Announcement Summary)
        if "公告摘要" in summary_sections:
            md_lines.append("## 公告摘要\n\n")
            if announcement_data:
                if announcement_data.get("SHORT_TEXT"):
                    md_lines.append(f"{announcement_data.get('SHORT_TEXT')}\n\n")
                elif announcement_data.get("LONG_TEXT"):
                    # Use first paragraph of LONG_TEXT as summary
                    long_text = announcement_data.get("LONG_TEXT", "")
                    first_para = long_text.split("\n")[0] if long_text else ""
                    if first_para:
                        md_lines.append(f"{first_para}\n\n")
            md_lines.append("\n")

        # 主要内容 (Main Content)
        if "主要内容" in summary_sections:
            md_lines.append("## 主要内容\n\n")
            content_added = False

            # Add PDF content if available
            if pdf_content and pdf_content.get("text"):
                text = pdf_content.get("text", "")
                # Truncate if too long (keep first 5000 characters)
                if len(text) > 5000:
                    text = text[:5000] + "\n\n... (内容已截断，完整内容请查看 PDF 文件) ..."
                md_lines.append(f"{text}\n\n")
                content_added = True

            # Add LONG_TEXT if available
            if announcement_data and announcement_data.get("LONG_TEXT"):
                long_text = announcement_data.get("LONG_TEXT", "")
                if long_text:
                    md_lines.append(f"{long_text}\n\n")
                    content_added = True

            if not content_added:
                md_lines.append("*（暂无详细内容）*\n\n")
            md_lines.append("\n")

        # 关键数据 (Key Data)
        if "关键数据" in summary_sections:
            md_lines.append("## 关键数据\n\n")
            data_added = False

            # Add tables from PDF if available
            if pdf_content and pdf_content.get("tables"):
                tables = pdf_content.get("tables", [])
                for i, table_data in enumerate(tables[:5], 1):  # Limit to first 5 tables
                    page = table_data.get("page", 0)
                    table = table_data.get("table", [])
                    if table:
                        md_lines.append(f"### 表格 {i} (第 {page} 页)\n\n")
                        # Convert table to Markdown format
                        if table:
                            # Header row
                            if len(table) > 0:
                                header = table[0]
                                md_lines.append("| " + " | ".join(str(cell) if cell else "" for cell in header) + " |\n")
                                md_lines.append("| " + " | ".join("---" for _ in header) + " |\n")
                                # Data rows
                                for row in table[1:]:
                                    md_lines.append("| " + " | ".join(str(cell) if cell else "" for cell in row) + " |\n")
                        md_lines.append("\n")
                        data_added = True

            if not data_added:
                md_lines.append("*（暂无表格数据）*\n\n")
            md_lines.append("\n")

        # 相关文件 (Related Files)
        if "相关文件" in summary_sections:
            md_lines.append("## 相关文件\n\n")
            if pdf_path:
                md_lines.append(f"- **PDF 文件**: `{pdf_path}`\n")
            if announcement_data and announcement_data.get("FILE_LINK"):
                md_lines.append(f"- **文件链接**: {announcement_data.get('FILE_LINK')}\n")
            if announcement_data and announcement_data.get("FILE_INFO"):
                md_lines.append(f"- **文件信息**: {announcement_data.get('FILE_INFO')}\n")
            md_lines.append("\n")

        # Footer
        md_lines.append("---\n\n")
        md_lines.append(f"*本文档生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*\n")

        # Write to file
        output_file = Path(output_path)
        output_file.parent.mkdir(parents=True, exist_ok=True)

        md_content = "".join(md_lines)
        output_file.write_text(md_content, encoding="utf-8")

        return {
            "success": True,
            "output_path": str(output_file.absolute()),
            "file_size": len(md_content.encode("utf-8")),
            "sections_included": summary_sections,
        }

    except Exception as e:
        return {
            "success": False,
            "output_path": None,
            "file_size": 0,
            "sections_included": [],
            "error": str(e),
        }

