import logging
from typing import List, Dict
from app.llm.base import LLMProvider, RateLimitError, LLMError
from app.llm.groq_provider import GroqProvider
from app.llm.openrouter_provider import OpenRouterProvider
from app.config import Config

logger = logging.getLogger(__name__)

class LLMManager:
    def __init__(self):
        self.providers = {
            "groq": GroqProvider(),
            "openrouter": OpenRouterProvider()
        }
        
        self.primary_name = Config.PRIMARY_PROVIDER
        if self.primary_name not in self.providers:
            logger.warning(f"Unknown primary provider '{self.primary_name}'. Defaulting to 'groq'.")
            self.primary_name = "groq"
            
        self.primary = self.providers[self.primary_name]
        
        # Determine fallback
        fallback_name = "openrouter" if self.primary_name == "groq" else "groq"
        self.fallback = self.providers[fallback_name]

    async def get_response(self, messages: List[Dict[str, str]]) -> str:
        try:
            # Try primary
            logger.info(f"Using primary provider: {self.primary_name}")
            return await self.primary.chat_completion(messages)
        except RateLimitError:
            fallback_name = "openrouter" if self.primary_name == "groq" else "groq"
            logger.warning(f"Primary provider '{self.primary_name}' rate limited. Falling back to '{fallback_name}'...")
            try:
                # Fallback
                return await self.fallback.chat_completion(messages)
            except Exception as e:
                logger.error(f"Fallback provider '{fallback_name}' also failed: {e}")
                raise LLMError(f"Both providers failed. Last error: {str(e)}")
        except Exception as e:
            logger.error(f"Primary provider fatal error: {e}")
            raise e
