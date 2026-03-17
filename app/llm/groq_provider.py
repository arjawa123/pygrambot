import httpx
import logging
from typing import List, Dict
from app.llm.base import LLMProvider, RateLimitError, LLMError
from app.config import Config

logger = logging.getLogger(__name__)

class GroqProvider(LLMProvider):
    def __init__(self):
        self.api_key = Config.GROQ_API_KEY
        self.model = Config.GROQ_MODEL
        self.url = "https://api.groq.com/openai/v1/chat/completions"

    async def chat_completion(self, messages: List[Dict[str, str]]) -> str:
        if not self.api_key:
            raise LLMError("Groq API key not configured")

        async with httpx.AsyncClient(timeout=Config.TIMEOUT) as client:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            payload = {
                "model": self.model,
                "messages": messages
            }
            
            try:
                resp = await client.post(self.url, headers=headers, json=payload)
                if resp.status_code == 429:
                    raise RateLimitError("Groq rate limit reached")
                
                resp.raise_for_status()
                data = resp.json()
                return data["choices"][0]["message"]["content"]
            except httpx.HTTPStatusError as e:
                logger.error(f"Groq API error: {e.response.text}")
                raise LLMError(f"Groq error: {e.response.status_code}")
            except RateLimitError:
                raise
            except Exception as e:
                logger.error(f"Groq unexpected error: {e}")
                raise LLMError(f"Unexpected error: {str(e)}")
