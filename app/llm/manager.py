import logging
from typing import List, Dict
from app.llm.base import LLMProvider, RateLimitError, LLMError
from app.llm.groq_provider import GroqProvider
from app.llm.openrouter_provider import OpenRouterProvider
from app.config import Config

logger = logging.getLogger(__name__)

class LLMManager:
    def __init__(self):
        self.primary = GroqProvider()
        self.fallback = OpenRouterProvider()

    async def get_response(self, messages: List[Dict[str, str]]) -> str:
        try:
            # Try primary
            logger.info(f"Using primary provider: {Config.PRIMARY_PROVIDER}")
            return await self.primary.chat_completion(messages)
        except RateLimitError:
            logger.warning("Primary provider rate limited. Falling back to OpenRouter...")
            try:
                # Fallback to OpenRouter
                return await self.fallback.chat_completion(messages)
            except Exception as e:
                logger.error(f"Fallback provider also failed: {e}")
                raise LLMError(f"Both primary and fallback providers failed. {str(e)}")
        except Exception as e:
            logger.error(f"Primary provider fatal error: {e}")
            raise e
