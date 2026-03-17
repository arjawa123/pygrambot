import httpx
import re
import logging
from datetime import datetime
from html import unescape
from typing import Optional, Dict, Any
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from app.config import Config

logger = logging.getLogger(__name__)

class WebService:
    @staticmethod
    def validate_url(url: str) -> bool:
        """Simple regex to validate HTTP/HTTPS URLs."""
        pattern = re.compile(r'^https?://[^\s/$.?#].[^\s]*$', re.IGNORECASE)
        return bool(pattern.match(url))

    @staticmethod
    def clean_text(text: str) -> str:
        """Cleans extracted text for LLM consumption."""
        # Unescape HTML entities
        text = unescape(text)
        # Remove extra whitespace/newlines
        text = re.sub(r'\s+', ' ', text)
        return text.strip()

    @staticmethod
    def extract_content(html: str) -> Dict[str, str]:
        """
        Lightweight HTML parser using regex (Stdlib only).
        Extracts title, meta description, and cleaned main text.
        """
        # Extract Title
        title_match = re.search(r'<title>(.*?)</title>', html, re.IGNORECASE | re.DOTALL)
        title = title_match.group(1).strip() if title_match else "No Title Found"

        # Extract Meta Description
        meta_match = re.search(r'<meta\s+name=["\']description["\']\s+content=["\'](.*?)["\']', html, re.IGNORECASE)
        description = meta_match.group(1).strip() if meta_match else ""

        # Remove Scripts, Styles, Nav, Footer, and other noisy tags
        cleaned_html = re.sub(r'<(script|style|nav|footer|header|aside|form|iframe).*?>.*?</\1>', '', html, flags=re.IGNORECASE | re.DOTALL)
        
        # Remove all other tags
        text_content = re.sub(r'<.*?>', ' ', cleaned_html)
        
        # Clean the text
        clean_text = WebService.clean_text(text_content)
        
        # Limit text size
        if len(clean_text) > Config.WEB_MAX_CHARS:
            clean_text = clean_text[:Config.WEB_MAX_CHARS] + "..."

        return {
            "title": unescape(title),
            "description": unescape(description),
            "text": clean_text
        }

    @classmethod
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=6),
        retry=retry_if_exception_type((httpx.RequestError, httpx.TimeoutException))
    )
    async def fetch_url(cls, url: str) -> Dict[str, Any]:
        """
        Robust async fetch with retries and safety checks.
        """
        if not cls.validate_url(url):
            raise ValueError("Invalid URL format. Must start with http:// or https://")

        headers = {"User-Agent": Config.WEB_USER_AGENT}
        
        async with httpx.AsyncClient(timeout=Config.WEB_FETCH_TIMEOUT, follow_redirects=True) as client:
            # 1. First check headers (Head request)
            response_head = await client.head(url, headers=headers)
            
            # Content-Type check
            content_type = response_head.headers.get("Content-Type", "").lower()
            if "text/html" not in content_type:
                raise ValueError(f"Unsupported content type: {content_type}. Only text/html is supported.")
            
            # Content-Length check
            content_length = int(response_head.headers.get("Content-Length", 0))
            if content_length > Config.WEB_MAX_CONTENT_LENGTH:
                raise ValueError(f"Content too large: {content_length} bytes (Max: {Config.WEB_MAX_CONTENT_LENGTH})")

            # 2. Fetch full content
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            # Final verification after GET (some servers don't report length correctly on HEAD)
            if len(response.content) > Config.WEB_MAX_CONTENT_LENGTH:
                 raise ValueError(f"Content exceeded limit after download.")

            # Extract and structure data
            html = response.text
            content_data = cls.extract_content(html)
            
            return {
                "url": url,
                "final_url": str(response.url),
                "title": content_data["title"],
                "description": content_data["description"],
                "text": content_data["text"],
                "fetched_at": datetime.now().isoformat()
            }

    @classmethod
    async def fetch_url_content(cls, url: str) -> str:
        """Compatibility helper for existing handler code."""
        try:
            data = await cls.fetch_url(url)
            return data["text"]
        except Exception as e:
            return f"Error fetching URL: {str(e)}"
