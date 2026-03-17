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
    async def get_memory_context(chat_id: int) -> str:
        memories = await Database.get_memories(chat_id)
        if not memories:
            return ""
        
        ctx = "Memori/Fakta yang perlu diingat untuk chat ini:\n"
        for m in memories:
            ctx += f"• {m[1]}\n"
        return ctx
