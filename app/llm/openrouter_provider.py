import httpx
import logging
from typing import List, Dict
from app.llm.base import LLMProvider, LLMError
from app.config import Config

logger = logging.getLogger(__name__)

class OpenRouterProvider(LLMProvider):
    def __init__(self):
        self.api_key = Config.OPENROUTER_API_KEY
        self.model = Config.OPENROUTER_MODEL_FREE
        self.url = "https://openrouter.ai/api/v1/chat/completions"

    async def chat_completion(self, messages: List[Dict[str, str]]) -> str:
        if not self.api_key:
            raise LLMError("OpenRouter API key not configured")

        async with httpx.AsyncClient(timeout=Config.TIMEOUT) as client:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/rjw/pygram",
                "X-Title": "Pygram AI Bot"
            }
            payload = {
                "model": self.model,
                "messages": messages
            }
            
            try:
                resp = await client.post(self.url, headers=headers, json=payload)
                if resp.status_code == 429:
                    raise RateLimitError("OpenRouter rate limit reached")
                
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError as e:
                logger.error(f"OpenRouter API error: {e.response.text}")
                raise LLMError(f"OpenRouter error: {e.response.status_code}")
            except Exception as e:
                logger.error(f"OpenRouter unexpected error: {e}")
                raise LLMError(f"Unexpected error: {str(e)}")
