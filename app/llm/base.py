from abc import ABC, abstractmethod
from typing import List, Dict

class LLMProvider(ABC):
    @abstractmethod
    async def chat_completion(self, messages: List[Dict[str, str]]) -> str:
        pass

class LLMError(Exception):
    pass

class RateLimitError(LLMError):
    pass
