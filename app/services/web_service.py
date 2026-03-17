import httpx
import re
import logging
from app.config import Config

logger = logging.getLogger(__name__)

class WebService:
    @staticmethod
    async def fetch_url_content(url: str) -> str:
        if not url.startswith(("http://", "https://")):
            return "❌ URL tidak valid. Pastikan dimulai dengan http:// atau https://"

        try:
            async with httpx.AsyncClient(timeout=15, follow_redirects=True) as client:
                headers = {
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
                }
                resp = await client.get(url, headers=headers)
                resp.raise_for_status()
                
                # Simple text extraction from HTML
                text = resp.text
                # Remove scripts and styles
                text = re.sub(r"<(script|style).*?>.*?</\1>", "", text, flags=re.DOTALL | re.IGNORECASE)
                # Remove all HTML tags
                text = re.sub(r"<.*?>", " ", text)
                # Normalize whitespace
                text = re.sub(r"\s+", " ", text).strip()
                
                limit = Config.MAX_FILE_CHARS
                return text[:limit] + ("\n...[truncated]" if len(text) > limit else "")
        except Exception as e:
            logger.error(f"Web fetch error for {url}: {e}")
            return f"❌ Gagal mengambil konten: {str(e)}"
