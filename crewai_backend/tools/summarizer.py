# ---------------------------------------------------------
# This file defines a lightweight summarization tool.
# - It uses simple heuristic sentence selection.
# - No external models needed for this tool itself.
# - The Analysis Agent uses this tool to compress text.
# ---------------------------------------------------------
from crewai.tools import tool


def _top_sentences(text: str, n: int = 5) -> str:
    """
    Simple sentence-based summarization:
    - Split on periods
    - Take the first N non-empty sentences
    """
    sentences = [s.strip() for s in text.replace("\n", " ").split(".") if s.strip()]
    top = sentences[:n]
    if not top:
        return "No content to summarize."
    return ". ".join(top) + "."


@tool("Summarizer Tool")
def summarizer_tool(text: str) -> str:
    """
    Summarize a block of text into 4–6 concise sentences.
    Used by the Analysis Agent as part of the pipeline.
    """
    if not text or not text.strip():
        return "No content to summarize."
    return _top_sentences(text, n=5)
