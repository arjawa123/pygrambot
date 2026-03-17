from app.db import Database
from typing import List, Tuple

class MemoryService:
    @staticmethod
    async def remember(chat_id: int, user_id: int, content: str):
        await Database.add_memory(chat_id, user_id, content)

    @staticmethod
    async def forget(chat_id: int, memory_id: int):
        await Database.delete_memory(memory_id, chat_id)

    @staticmethod
    async def get_all_memories(chat_id: int) -> List[Tuple]:
        return await Database.get_memories(chat_id)

    @staticmethod
    async def remember_web(chat_id: int, user_id: int, title: str, url: str, content: str):
        """Saves a summarized version of web content to persistent memory."""
        # Truncate content for memory (don't store thousands of characters in long-term memory)
        snippet = content[:500] + "..." if len(content) > 500 else content
        memory_entry = f"Website Summary: {title} ({url})\nContent: {snippet}"
        await Database.add_memory(chat_id, user_id, memory_entry)

    @staticmethod
    async def get_memory_context(chat_id: int) -> str:
        memories = await Database.get_memories(chat_id)
        if not memories:
            return ""
        
        ctx = "Memori/Fakta yang perlu diingat untuk chat ini:\n"
        for m in memories:
            ctx += f"• {m[1]}\n"
        return ctx
