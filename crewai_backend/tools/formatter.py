# ---------------------------------------------------------
# This file defines the Markdown formatter tool.
# - Used by the Writer Agent.
# - Ensures the final output is a valid Markdown document.
# ---------------------------------------------------------
from crewai.tools import tool


@tool("Formatter Tool")
def formatter_tool(text: str) -> str:
    """
    Format the final answer into Markdown.
    If the input already contains headings like 'Overview',
    it is returned mostly as-is. Otherwise, we wrap it in a
    simple Markdown template.
    """
    if not text or not text.strip():
        return "# Research Summary\n\n(No content.)"

    stripped = text.strip()
    if "Overview" in stripped or "Key Claims" in stripped:
        return stripped

    return f"# Research Summary\n\n## Overview\n\n{stripped}\n"
