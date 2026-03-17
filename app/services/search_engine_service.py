import logging
import httpx
from bs4 import BeautifulSoup
from typing import List, Dict

logger = logging.getLogger(__name__)

class SearchEngineService:
    @staticmethod
    async def search(query: str, max_results: int = 5) -> List[Dict[str, str]]:
        """
        Performs a free web search using DuckDuckGo HTML version.
        This version is highly stable for scraping in Termux.
        """
        # DuckDuckGo HTML endpoint (no JavaScript required)
        url = "https://html.duckduckgo.com/html/"
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Content-Type": "application/x-www-form-urlencoded",
            "Origin": "https://html.duckduckgo.com",
            "Referer": "https://html.duckduckgo.com/"
        }
        
        # Form data for DuckDuckGo search
        data = {"q": query}

        try:
            async with httpx.AsyncClient(timeout=20.0, follow_redirects=True) as client:
                # 1. Send search request
                response = await client.post(url, headers=headers, data=data)
                
                if response.status_code != 200:
                    logger.error(f"DDG Search failed with status: {response.status_code}")
                    return []

                # 2. Parse HTML
                soup = BeautifulSoup(response.text, 'html.parser')
                results = []
                
                # Each result is contained in a div with class 'result'
                for i, result in enumerate(soup.select('.result'), 1):
                    if i > max_results:
                        break
                    
                    # Extract Title and URL
                    title_tag = result.select_one('.result__a')
                    snippet_tag = result.select_one('.result__snippet')
                    
                    if title_tag:
                        title = title_tag.get_text(strip=True)
                        href = title_tag.get('href', '#')
                        # Handle internal DDG redirect links if necessary
                        if href.startswith('//duckduckgo.com/l/?kh=-1&uddg='):
                            from urllib.parse import unquote, urlparse, parse_qs
                            parsed = urlparse('https:' + href)
                            href = parse_qs(parsed.query).get('uddg', [href])[0]

                        snippet = snippet_tag.get_text(strip=True) if snippet_tag else "No description."
                        
                        results.append({
                            "title": title,
                            "href": href,
                            "body": snippet
                        })

                return results

        except Exception as e:
            logger.error(f"DuckDuckGo Search error: {e}")
            return []

    @staticmethod
    def format_results(results: List[Dict[str, str]]) -> str:
        """Formats the search results into a readable Markdown string."""
        if not results:
            return "❌ **Pencarian Gagal:** Tidak ada hasil yang ditemukan. Coba gunakan kata kunci yang lebih spesifik."
        
        formatted = "🌐 **Hasil Pencarian Web:**\n\n"
        for i, res in enumerate(results, 1):
            title = res.get('title', 'No Title')
            href = res.get('href', '#')
            body = res.get('body', 'No description.')
            
            # Format display URL for cleaner look
            from urllib.parse import urlparse
            display_url = urlparse(href).netloc
            
            formatted += f"{i}. [{title}]({href})\n"
            formatted += f"🔗 `{display_url}`\n"
            formatted += f"_{body}_\n\n"
        
        return formatted
