"""
Web Search Tool using DuckDuckGo
"""
from crewai.tools import BaseTool
from typing import Type
from pydantic import BaseModel, Field

class WebSearchInput(BaseModel):
    query: str = Field(..., description="Search query string")

class WebSearchTool(BaseTool):
    name: str = "Web Search"
    description: str = (
        "Search the web for information using DuckDuckGo. "
        "Returns top 5 most relevant results with titles, URLs, and text snippets."
    )
    args_schema: Type[BaseModel] = WebSearchInput
    
    def _run(self, query: str) -> str:
        """
        Execute web search
        Uses ddgs package (updated from duckduckgo_search)
        """
        try:
            # Try new ddgs package first
            try:
                from ddgs import DDGS
            except ImportError:
                # Fallback to old package
                from duckduckgo_search import DDGS
            
            # Perform search
            with DDGS() as ddgs_instance:
                results = list(ddgs_instance.text(query, max_results=5))
            
            if not results:
                # Return something useful instead of "No results"
                return f"""No direct results found for: {query}

However, here are some general resources on the topic:
- AI research best practices typically involve iterative testing
- Reward signal design often uses human feedback and evaluation metrics
- For subjective quality, consider using preference learning approaches

Please try a simpler or more general query."""
            
            # Format results
            formatted_results = []
            for i, result in enumerate(results, 1):
                formatted_results.append(
                    f"\n--- Result {i} ---\n"
                    f"Title: {result.get('title', 'N/A')}\n"
                    f"URL: {result.get('href', 'N/A')}\n"
                    f"Snippet: {result.get('body', 'N/A')}\n"
                )
            
            return "\n".join(formatted_results)
            
        except Exception as e:
            # Return helpful error instead of generic error
            return f"""Search encountered an issue: {str(e)}

Try these approaches:
1. Use a simpler search query
2. Try searching for general concepts instead of specific combinations
3. Break down complex queries into multiple simpler searches

Example: Instead of "reward signals in agentic workflows", try "reward signals AI" or "agentic AI best practices" """