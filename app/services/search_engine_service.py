import logging
from ddgs import DDGS
from typing import List, Dict

logger = logging.getLogger(__name__)

class SearchEngineService:
    @staticmethod
    async def search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        Performs a free web search using DuckDuckGo.
        Returns a list of dictionaries containing title, href, and body.
        """
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
                return results
        except Exception as e:
            logger.error(f"DuckDuckGo search error: {e}")
            return []

    @staticmethod
    def format_results(results: List[Dict[str, str]]) -> str:
        """Formats the search results into a readable Markdown string."""
        if not results:
            return "No results found."
        
        formatted = "🌐 **Search Results:**\n\n"
        for i, res in enumerate(results, 1):
            title = res.get('title', 'No Title')
            href = res.get('href', '#')
            body = res.get('body', 'No description.')
            formatted += f"{i}. [{title}]({href})\n_{body}_\n\n"
        
        return formatted
