# ---------------------------------------------------------
# This file defines a web search tool using DuckDuckGo.
# - Called by the Research Agent.
# - Uses duckduckgo_search to fetch up to N results.
# - Returns title + snippet + URL strings.
# ---------------------------------------------------------
from crewai.tools import tool
from duckduckgo_search import DDGS


@tool("Web Search Tool")
def web_search_tool(query: str) -> str:
    """
    Search the web using DuckDuckGo and return up to 5 results
    with title, snippet, and URL. This tool is used by the
    Research Agent to gather raw information.
    """
    try:
        results = []
        with DDGS() as ddgs:
            for r in ddgs.text(query, max_results=5):
                title = r.get("title", "").strip()
                snippet = r.get("body", "").strip()
                href = r.get("href", "").strip()
                if not title and not snippet:
                    continue
                results.append(f"- {title}\n  {snippet}\n  {href}")
        if not results:
            return "No search results found."
        return "Search Results:\n" + "\n".join(results)
    except Exception as e:
        return f"Web search failed: {e}"
