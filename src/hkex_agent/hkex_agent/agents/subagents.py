"""Sub-agent definitions for HKEX announcement analysis."""

from typing import Any

from hkex_agent.tools.hkex_tools import (
    get_announcement_categories,
    get_latest_hkex_announcements,
    get_stock_info,
    search_hkex_announcements,
)
from hkex_agent.tools.pdf_tools import (
    analyze_pdf_structure,
    extract_pdf_content,
    get_cached_pdf_path,
)

# PDF analyzer subagent tools
PDF_ANALYZER_TOOLS = [
    get_cached_pdf_path,
    extract_pdf_content,
    analyze_pdf_structure,
]

# Report generator subagent tools (has access to all tools)
REPORT_GENERATOR_TOOLS = [
    search_hkex_announcements,
    get_latest_hkex_announcements,
    get_stock_info,
    get_announcement_categories,
    get_cached_pdf_path,
    extract_pdf_content,
    analyze_pdf_structure,
]


def get_pdf_analyzer_subagent() -> dict[str, Any]:
    """Get PDF analyzer subagent configuration.

    This subagent specializes in analyzing PDF announcement content.
    It extracts text, tables, and structure from PDFs.

    Returns:
        Subagent configuration dictionary.
    """
    return {
        "name": "pdf-analyzer",
        "description": (
            "Specialized agent for analyzing PDF announcement content. "
            "Use this when you need to extract and analyze text, tables, "
            "or structure from PDF files."
        ),
        "system_prompt": """You are a PDF analysis expert specializing in Hong Kong Stock Exchange announcements.

Your primary responsibilities:
1. Extract and analyze text content from PDF announcements
2. Extract and structure tabular data (financial tables, etc.)
3. Analyze PDF structure to identify sections and headings
4. Generate summaries of PDF content
5. Identify key information such as financial figures, dates, and important notices

When analyzing PDFs:
- Always check the cache first using get_cached_pdf_path before downloading
- Extract both text and tables for comprehensive analysis
- Pay attention to financial data in tables
- Identify key sections and their purposes
- Provide clear, structured summaries

You have access to PDF analysis tools. Use them efficiently to provide thorough analysis.""",
        "tools": PDF_ANALYZER_TOOLS,
    }


def get_report_generator_subagent() -> dict[str, Any]:
    """Get report generator subagent configuration.

    This subagent specializes in generating structured reports based on
    announcement analysis results.

    Returns:
        Subagent configuration dictionary.
    """
    return {
        "name": "report-generator",
        "description": (
            "Specialized agent for generating structured reports from announcement analysis. "
            "Use this when you need to create comprehensive reports, summaries, or "
            "structured output based on announcement data and analysis."
        ),
        "system_prompt": """You are a report generation expert specializing in Hong Kong Stock Exchange announcements.

Your primary responsibilities:
1. Generate structured reports from announcement search results
2. Create summaries and analyses of multiple announcements
3. Format reports in Markdown, JSON, or other structured formats
4. Synthesize information from multiple sources into coherent reports
5. Highlight key findings and trends

When generating reports:
- Use data from announcement searches and PDF analyses
- Structure reports clearly with sections and subsections
- Include relevant metadata (dates, stock codes, etc.)
- Provide actionable insights when possible
- Format output appropriately (Markdown for readability, JSON for structured data)

You have access to all HKEX tools. Use them to gather comprehensive data before generating reports.""",
        "tools": REPORT_GENERATOR_TOOLS,
    }


def get_all_subagents() -> list[dict[str, Any]]:
    """Get all subagent configurations.

    Returns:
        List of subagent configuration dictionaries.
    """
    return [
        get_pdf_analyzer_subagent(),
        get_report_generator_subagent(),
    ]

