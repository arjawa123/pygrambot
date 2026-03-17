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
        # Fetch current active provider from database or fallback to Config
        from app.db import Database
        active_provider = await Database.get_setting("active_provider", Config.PRIMARY_PROVIDER)
        
        if active_provider not in self.providers:
            active_provider = "groq"
            
        primary = self.providers[active_provider]
        fallback_name = "openrouter" if active_provider == "groq" else "groq"
        fallback = self.providers[fallback_name]

        try:
            # Try primary
            logger.info(f"Using active provider: {active_provider}")
            return await primary.chat_completion(messages)
        except RateLimitError:
            logger.warning(f"Provider '{active_provider}' rate limited. Falling back to '{fallback_name}'...")
            try:
                # Fallback
                return await fallback.chat_completion(messages)
            except Exception as e:
                logger.error(f"Fallback provider '{fallback_name}' also failed: {e}")
                raise LLMError(f"Both providers failed. Last error: {str(e)}")
        except Exception as e:
            logger.error(f"Provider fatal error: {e}")
            raise e
