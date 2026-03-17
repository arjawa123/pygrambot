import aiosqlite
from datetime import datetime, timezone
from typing import List, Tuple, Optional
from app.config import Config

CREATE_TABLES_SQL = """
PRAGMA journal_mode=WAL;

CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    role TEXT NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS files (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    telegram_file_id TEXT,
    telegram_unique_id TEXT,
    file_name TEXT NOT NULL,
    local_path TEXT NOT NULL,
    mime_type TEXT,
    extracted_text TEXT,
    note TEXT,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS memories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    content TEXT NOT NULL,
    created_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS reminders (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    chat_id INTEGER NOT NULL,
    user_id INTEGER NOT NULL,
    remind_time TEXT NOT NULL,
    message TEXT NOT NULL,
    status TEXT DEFAULT 'PENDING'
);

CREATE INDEX IF NOT EXISTS idx_messages_chat_created ON messages(chat_id, created_at);
CREATE INDEX IF NOT EXISTS idx_files_chat_created ON files(chat_id, created_at);
CREATE INDEX IF NOT EXISTS idx_memories_chat ON memories(chat_id);
"""

def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

async def init_db():
    async with aiosqlite.connect(Config.DB_PATH) as db:
        await db.executescript(CREATE_TABLES_SQL)
        await db.commit()

class Database:
    # --- Messages ---
    @staticmethod
    async def add_message(chat_id: int, user_id: int, role: str, content: str):
        async with aiosqlite.connect(Config.DB_PATH) as db:
            await db.execute(
                "INSERT INTO messages (chat_id, user_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
                (chat_id, user_id, role, content, utc_now_iso()),
            )
            await db.commit()

    @staticmethod
    async def get_history(chat_id: int, limit: int = Config.MAX_HISTORY) -> List[dict]:
        async with aiosqlite.connect(Config.DB_PATH) as db:
            cur = await db.execute(
                "SELECT role, content FROM messages WHERE chat_id = ? ORDER BY id DESC LIMIT ?",
                (chat_id, limit),
            )
            rows = await cur.fetchall()
            rows.reverse()
            return [{"role": r[0], "content": r[1]} for r in rows]

    @staticmethod
    async def clear_history(chat_id: int):
        async with aiosqlite.connect(Config.DB_PATH) as db:
            await db.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
            await db.commit()

    @staticmethod
    async def get_stats(chat_id: int) -> dict:
        async with aiosqlite.connect(Config.DB_PATH) as db:
            async with db.execute("SELECT COUNT(*) FROM messages WHERE chat_id = ?", (chat_id,)) as cur:
                msg_count = (await cur.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM files WHERE chat_id = ?", (chat_id,)) as cur:
                file_count = (await cur.fetchone())[0]
            async with db.execute("SELECT COUNT(*) FROM memories WHERE chat_id = ?", (chat_id,)) as cur:
                mem_count = (await cur.fetchone())[0]
            return {"messages": msg_count, "files": file_count, "memories": mem_count}

    # --- Files ---
    @staticmethod
    async def add_file(chat_id: int, user_id: int, file_id: str, unique_id: str, 
                       name: str, path: str, mime: Optional[str], text: Optional[str], note: str):
        async with aiosqlite.connect(Config.DB_PATH) as db:
            await db.execute(
                """INSERT INTO files (chat_id, user_id, telegram_file_id, telegram_unique_id, 
                   file_name, local_path, mime_type, extracted_text, note, created_at) 
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
                (chat_id, user_id, file_id, unique_id, name, path, mime, text, note, utc_now_iso()),
            )
            await db.commit()

    @staticmethod
    async def get_recent_files(chat_id: int, limit: int = 3) -> List[Tuple]:
        async with aiosqlite.connect(Config.DB_PATH) as db:
            cur = await db.execute(
                "SELECT file_name, local_path, extracted_text, note, created_at FROM files WHERE chat_id = ? ORDER BY id DESC LIMIT ?",
                (chat_id, limit),
            )
            return await cur.fetchall()

    @staticmethod
    async def search_files(chat_id: int, query: str, limit: int = 3) -> List[Tuple]:
        """Searches for files containing specific keywords in their extracted text."""
        async with aiosqlite.connect(Config.DB_PATH) as db:
            # Use SQLite LIKE for basic searching
            cur = await db.execute(
                """SELECT file_name, local_path, extracted_text, note, created_at 
                   FROM files 
                   WHERE chat_id = ? AND extracted_text LIKE ? 
                   ORDER BY id DESC LIMIT ?""",
                (chat_id, f"%{query}%", limit),
            )
            return await cur.fetchall()

    @staticmethod
    async def get_all_files(chat_id: int) -> List[Tuple]:
        async with aiosqlite.connect(Config.DB_PATH) as db:
            cur = await db.execute("SELECT id, file_name, created_at FROM files WHERE chat_id = ? ORDER BY id ASC", (chat_id,))
            return await cur.fetchall()

    @staticmethod
    async def delete_file(file_id: int, chat_id: int) -> Optional[str]:
        async with aiosqlite.connect(Config.DB_PATH) as db:
            cur = await db.execute("SELECT local_path FROM files WHERE id = ? AND chat_id = ?", (file_id, chat_id))
            row = await cur.fetchone()
            if row:
                path = row[0]
                await db.execute("DELETE FROM files WHERE id = ?", (file_id,))
                await db.commit()
                return path
            return None

    @staticmethod
    async def clear_files(chat_id: int) -> List[str]:
        async with aiosqlite.connect(Config.DB_PATH) as db:
            cur = await db.execute("SELECT local_path FROM files WHERE chat_id = ?", (chat_id,))
            rows = await cur.fetchall()
            paths = [r[0] for r in rows]
            await db.execute("DELETE FROM files WHERE chat_id = ?", (chat_id,))
            await db.commit()
            return paths

    # --- Memories ---
    @staticmethod
    async def add_memory(chat_id: int, user_id: int, content: str):
        async with aiosqlite.connect(Config.DB_PATH) as db:
            await db.execute(
                "INSERT INTO memories (chat_id, user_id, content, created_at) VALUES (?, ?, ?, ?)",
                (chat_id, user_id, content, utc_now_iso()),
            )
            await db.commit()

    @staticmethod
    async def get_memories(chat_id: int) -> List[Tuple]:
        async with aiosqlite.connect(Config.DB_PATH) as db:
            cur = await db.execute("SELECT id, content, created_at FROM memories WHERE chat_id = ? ORDER BY id ASC", (chat_id,))
            return await cur.fetchall()

    @staticmethod
    async def delete_memory(memory_id: int, chat_id: int):
        async with aiosqlite.connect(Config.DB_PATH) as db:
            await db.execute("DELETE FROM memories WHERE id = ? AND chat_id = ?", (memory_id, chat_id))
            await db.commit()

    # --- Settings ---
    @staticmethod
    async def set_setting(key: str, value: str):
        async with aiosqlite.connect(Config.DB_PATH) as db:
            await db.execute(
                "INSERT OR REPLACE INTO settings (key, value, updated_at) VALUES (?, ?, ?)",
                (key, value, utc_now_iso()),
            )
            await db.commit()

    @staticmethod
    async def get_setting(key: str, default: str = None) -> Optional[str]:
        async with aiosqlite.connect(Config.DB_PATH) as db:
            cur = await db.execute("SELECT value FROM settings WHERE key = ?", (key,))
            row = await cur.fetchone()
            return row[0] if row else default
