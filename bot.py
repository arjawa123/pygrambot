import asyncio
import contextlib
import csv
import io
import logging
import os
import re
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Tuple

import aiosqlite
import httpx
from dotenv import load_dotenv
from telegram import Update, Message, Document
from telegram.constants import ChatAction
from telegram.ext import (
    Application,
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

# =========================
# Config
# =========================
load_dotenv()

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
GROQ_MODEL = os.getenv("GROQ_MODEL", "openai/gpt-oss-20b").strip()
BOT_DB_PATH = os.getenv("BOT_DB_PATH", "bot.db").strip()
BOT_FILES_DIR = Path(os.getenv("BOT_FILES_DIR", "bot_files").strip())
MAX_HISTORY_MESSAGES = int(os.getenv("MAX_HISTORY_MESSAGES", "20"))
MAX_FILE_TEXT_CHARS = int(os.getenv("MAX_FILE_TEXT_CHARS", "12000"))
MAX_REPLY_CHARS = int(os.getenv("MAX_REPLY_CHARS", "3500"))
REQUEST_TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "90"))
ENABLE_CODE_EXECUTION = os.getenv("ENABLE_CODE_EXECUTION", "true").lower() == "true"
ALLOWED_USER_IDS_RAW = os.getenv("ALLOWED_USER_IDS", "").strip()

ALLOWED_USER_IDS = {
    int(x.strip()) for x in ALLOWED_USER_IDS_RAW.split(",") if x.strip().isdigit()
}

if not TELEGRAM_BOT_TOKEN:
    raise RuntimeError("TELEGRAM_BOT_TOKEN belum diisi di .env")
if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY belum diisi di .env")

BOT_FILES_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
log = logging.getLogger("telegram-groq-bot")

GLOBAL_SEMAPHORE = asyncio.Semaphore(3)

SYSTEM_PROMPT = """Kamu adalah asisten Telegram bergaya Open Interpreter.

Aturan:
1. Jawab singkat, jelas, dan praktis.
2. Gunakan konteks history chat jika relevan.
3. Gunakan konteks file terakhir jika tersedia.
4. Jangan mengarang isi file yang tidak ada.
5. Jika user meminta analisis file, pakai isi file yang tersimpan.
6. Bot hanya mengeksekusi Python saat user memakai command /py.
7. Ikuti bahasa user.
"""

TEXT_FILE_EXTS = {
    ".txt", ".md", ".py", ".json", ".csv", ".log", ".ini", ".yaml", ".yml", ".toml"
}

http_client = httpx.AsyncClient(
    base_url="https://api.groq.com/openai/v1",
    headers={
        "Authorization": f"Bearer {GROQ_API_KEY}",
        "Content-Type": "application/json",
    },
    timeout=REQUEST_TIMEOUT,
)

# =========================
# Helpers
# =========================
def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()

def split_chunks(text: str, max_len: int = MAX_REPLY_CHARS) -> List[str]:
    if len(text) <= max_len:
        return [text]

    chunks = []
    start = 0
    while start < len(text):
        end = min(start + max_len, len(text))
        if end < len(text):
            nl = text.rfind("\n", start, end)
            if nl > start + 300:
                end = nl
        chunks.append(text[start:end].strip())
        start = end

    return [c for c in chunks if c]

def sanitize_filename(name: str) -> str:
    name = re.sub(r"[^a-zA-Z0-9._-]+", "_", name)
    return name[:120] or "file"

def is_allowed_exec_user(user_id: int) -> bool:
    if not ALLOWED_USER_IDS:
        return True
    return user_id in ALLOWED_USER_IDS

def trim_text(text: str, limit: int) -> str:
    return text if len(text) <= limit else text[:limit] + "\n...[truncated]"

def extract_text_from_file(path: Path) -> Tuple[Optional[str], str]:
    ext = path.suffix.lower()

    if ext not in TEXT_FILE_EXTS:
        return None, f"File tersimpan, tapi ekstensi {ext or '(none)'} belum di-auto-parse."

    try:
        raw = path.read_text(encoding="utf-8", errors="replace")

        if ext == ".csv":
            reader = csv.reader(io.StringIO(raw))
            rows = []
            for i, row in enumerate(reader):
                rows.append(" | ".join(row))
                if i >= 30:
                    rows.append("... [rows truncated]")
                    break
            raw = "\n".join(rows)

        return trim_text(raw, MAX_FILE_TEXT_CHARS), "Teks file berhasil diekstrak."
    except Exception as e:
        return None, f"Gagal baca file: {e}"

# =========================
# Database
# =========================
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

CREATE INDEX IF NOT EXISTS idx_messages_chat_created
ON messages(chat_id, created_at);

CREATE INDEX IF NOT EXISTS idx_files_chat_created
ON files(chat_id, created_at);
"""

async def init_db():
    async with aiosqlite.connect(BOT_DB_PATH) as db:
        await db.executescript(CREATE_TABLES_SQL)
        await db.commit()

async def db_add_message(chat_id: int, user_id: int, role: str, content: str):
    async with aiosqlite.connect(BOT_DB_PATH) as db:
        await db.execute(
            "INSERT INTO messages (chat_id, user_id, role, content, created_at) VALUES (?, ?, ?, ?, ?)",
            (chat_id, user_id, role, content, utc_now_iso()),
        )
        await db.commit()

async def db_get_recent_messages(chat_id: int, limit: int = MAX_HISTORY_MESSAGES) -> List[Tuple[str, str]]:
    async with aiosqlite.connect(BOT_DB_PATH) as db:
        cur = await db.execute(
            """
            SELECT role, content
            FROM messages
            WHERE chat_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (chat_id, limit),
        )
        rows = await cur.fetchall()

    rows.reverse()
    return [(r[0], r[1]) for r in rows]

async def db_clear_chat(chat_id: int):
    async with aiosqlite.connect(BOT_DB_PATH) as db:
        await db.execute("DELETE FROM messages WHERE chat_id = ?", (chat_id,))
        await db.execute("DELETE FROM files WHERE chat_id = ?", (chat_id,))
        await db.commit()

async def db_add_file(
    chat_id: int,
    user_id: int,
    telegram_file_id: str,
    telegram_unique_id: str,
    file_name: str,
    local_path: str,
    mime_type: Optional[str],
    extracted_text: Optional[str],
    note: str,
):
    async with aiosqlite.connect(BOT_DB_PATH) as db:
        await db.execute(
            """
            INSERT INTO files
            (chat_id, user_id, telegram_file_id, telegram_unique_id, file_name, local_path, mime_type, extracted_text, note, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                chat_id,
                user_id,
                telegram_file_id,
                telegram_unique_id,
                file_name,
                local_path,
                mime_type,
                extracted_text,
                note,
                utc_now_iso(),
            ),
        )
        await db.commit()

async def db_get_recent_files(chat_id: int, limit: int = 3):
    async with aiosqlite.connect(BOT_DB_PATH) as db:
        cur = await db.execute(
            """
            SELECT file_name, local_path, extracted_text, note, created_at
            FROM files
            WHERE chat_id = ?
            ORDER BY id DESC
            LIMIT ?
            """,
            (chat_id, limit),
        )
        rows = await cur.fetchall()

    return rows

# =========================
# LLM request
# =========================
@retry(
    reraise=True,
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=8),
    retry=retry_if_exception_type(Exception),
)
async def ask_llm(chat_id: int, user_id: int, user_text: str) -> str:
    history = await db_get_recent_messages(chat_id, MAX_HISTORY_MESSAGES)
    recent_files = await db_get_recent_files(chat_id, 3)

    messages = [{"role": "system", "content": SYSTEM_PROMPT}]

    if recent_files:
        file_context_parts = []
        for idx, (file_name, local_path, extracted_text, note, created_at) in enumerate(recent_files, start=1):
            desc = f"[File {idx}] {file_name} | saved={created_at}\n"
            if extracted_text:
                desc += f"Isi terdeteksi:\n{trim_text(extracted_text, 4000)}"
            else:
                desc += f"Tidak ada teks terdeteksi. Catatan: {note}"
            file_context_parts.append(desc)

        file_context = "\n\n".join(file_context_parts)
        messages.append({
            "role": "system",
            "content": f"Konteks file terbaru untuk chat ini:\n{file_context}"
        })

    for role, content in history:
        if role in ("user", "assistant"):
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_text})

    payload = {
        "model": GROQ_MODEL,
        "messages": messages,
        "temperature": 0.2,
    }

    resp = await http_client.post("/chat/completions", json=payload)
    resp.raise_for_status()
    data = resp.json()

    return (
        data.get("choices", [{}])[0]
        .get("message", {})
        .get("content", "")
        .strip()
        or "(tidak ada jawaban)"
    )

# =========================
# Python execution
# =========================
@dataclass
class ExecResult:
    stdout: str
    stderr: str
    returncode: int
    timed_out: bool

async def run_python_code(code: str, timeout_sec: int = 15) -> ExecResult:
    with tempfile.TemporaryDirectory(prefix="tg_py_") as tmp:
        workdir = Path(tmp)
        script_path = workdir / "main.py"
        script_path.write_text(code, encoding="utf-8")

        proc = await asyncio.create_subprocess_exec(
            sys.executable,
            "-I",
            str(script_path),
            cwd=str(workdir),
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
        )

        try:
            stdout_b, stderr_b = await asyncio.wait_for(proc.communicate(), timeout=timeout_sec)
            return ExecResult(
                stdout=stdout_b.decode("utf-8", errors="replace"),
                stderr=stderr_b.decode("utf-8", errors="replace"),
                returncode=proc.returncode,
                timed_out=False,
            )
        except asyncio.TimeoutError:
            with contextlib.suppress(ProcessLookupError):
                proc.kill()
            with contextlib.suppress(Exception):
                await proc.communicate()

            return ExecResult(
                stdout="",
                stderr=f"Timeout: eksekusi melewati {timeout_sec} detik.",
                returncode=124,
                timed_out=True,
            )

# =========================
# Telegram helpers
# =========================
async def send_long_message(message: Message, text: str):
    for chunk in split_chunks(text):
        await message.reply_text(chunk)

# =========================
# Commands
# =========================
async def start_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (
        "Bot siap.\n\n"
        "Perintah:\n"
        "/ask <pesan> - chat dengan AI\n"
        "/py <kode python> - eksekusi Python\n"
        "/files - lihat file terakhir\n"
        "/reset - hapus history chat & file context chat ini\n"
        "/status - cek status bot\n\n"
        "Kamu juga bisa kirim pesan biasa tanpa /ask."
    )
    await update.message.reply_text(text)

async def status_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    txt = (
        f"Model: {GROQ_MODEL}\n"
        f"Code execution: {'ON' if ENABLE_CODE_EXECUTION else 'OFF'}\n"
        f"History limit: {MAX_HISTORY_MESSAGES}\n"
        f"Files dir: {BOT_FILES_DIR}\n"
        f"Allowed exec users: {'all' if not ALLOWED_USER_IDS else len(ALLOWED_USER_IDS)}"
    )
    await update.message.reply_text(txt)

async def reset_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    await db_clear_chat(chat_id)
    await update.message.reply_text("History dan file context chat ini sudah dihapus.")

async def files_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    rows = await db_get_recent_files(chat_id, 10)

    if not rows:
        await update.message.reply_text("Belum ada file di chat ini.")
        return

    lines = ["File terbaru:"]
    for i, (file_name, local_path, extracted_text, note, created_at) in enumerate(rows, start=1):
        lines.append(
            f"{i}. {file_name}\n"
            f"   saved: {created_at}\n"
            f"   parsed: {'ya' if extracted_text else 'tidak'}\n"
            f"   note: {note}"
        )

    await update.message.reply_text("\n".join(lines))

async def ask_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_text = " ".join(context.args).strip()
    if not user_text:
        await update.message.reply_text("Pakai: /ask pertanyaanmu")
        return
    await process_user_prompt(update, user_text)

async def py_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not ENABLE_CODE_EXECUTION:
        await update.message.reply_text("Code execution sedang dimatikan.")
        return

    user_id = update.effective_user.id
    if not is_allowed_exec_user(user_id):
        await update.message.reply_text("User ini tidak diizinkan menjalankan kode.")
        return

    code = update.message.text.partition(" ")[2].strip()
    if not code:
        await update.message.reply_text("Pakai: /py <kode python>")
        return

    fenced = re.search(r"```(?:python)?\n(.*?)```", code, flags=re.S | re.I)
    if fenced:
        code = fenced.group(1).strip()

    await update.message.chat.send_action(ChatAction.TYPING)
    result = await run_python_code(code)

    response = (
        f"Return code: {result.returncode}\n\n"
        f"STDOUT:\n{trim_text(result.stdout or '(kosong)', 6000)}\n\n"
        f"STDERR:\n{trim_text(result.stderr or '(kosong)', 4000)}"
    )
    await send_long_message(update.message, response)

# =========================
# Handlers
# =========================
async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    doc: Document = message.document
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id

    await message.chat.send_action(ChatAction.UPLOAD_DOCUMENT)

    tg_file = await doc.get_file()
    safe_name = sanitize_filename(doc.file_name or f"{doc.file_unique_id}.bin")

    chat_dir = BOT_FILES_DIR / str(chat_id)
    chat_dir.mkdir(parents=True, exist_ok=True)

    local_path = chat_dir / safe_name
    await tg_file.download_to_drive(custom_path=str(local_path))

    extracted_text, note = extract_text_from_file(local_path)

    await db_add_file(
        chat_id=chat_id,
        user_id=user_id,
        telegram_file_id=doc.file_id,
        telegram_unique_id=doc.file_unique_id,
        file_name=safe_name,
        local_path=str(local_path),
        mime_type=doc.mime_type,
        extracted_text=extracted_text,
        note=note,
    )

    await message.reply_text(
        f"File tersimpan: {safe_name}\n{note}\n"
        "Sekarang kamu bisa tanya, misalnya: ringkas file terakhir."
    )

async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = (update.message.text or "").strip()
    if not text:
        return
    await process_user_prompt(update, text)

async def process_user_prompt(update: Update, user_text: str):
    chat_id = update.effective_chat.id
    user_id = update.effective_user.id
    message = update.message

    async with GLOBAL_SEMAPHORE:
        try:
            await message.chat.send_action(ChatAction.TYPING)
            await db_add_message(chat_id, user_id, "user", user_text)

            answer = await ask_llm(chat_id, user_id, user_text)

            await db_add_message(chat_id, user_id, "assistant", answer)
            await send_long_message(message, answer)

        except httpx.HTTPStatusError as e:
            detail = e.response.text if e.response is not None else str(e)
            log.exception("HTTP error")
            await message.reply_text(f"API error:\n{trim_text(detail, 3000)}")
        except Exception as e:
            log.exception("Unhandled processing error")
            await message.reply_text(
                "Terjadi error saat memproses pesan.\n"
                f"{type(e).__name__}: {e}"
            )

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE):
    log.exception("Unhandled exception", exc_info=context.error)
    if isinstance(update, Update) and update.effective_message:
        with contextlib.suppress(Exception):
            await update.effective_message.reply_text(
                "Terjadi error tak terduga, tapi bot tetap hidup. Coba kirim ulang."
            )

# =========================
# Lifecycle
# =========================
async def post_init(app: Application):
    await init_db()
    log.info("DB siap.")

async def post_shutdown(app: Application):
    await http_client.aclose()
    log.info("HTTP client ditutup.")

def build_app() -> Application:
    app = (
        ApplicationBuilder()
        .token(TELEGRAM_BOT_TOKEN)
        .post_init(post_init)
        .post_shutdown(post_shutdown)
        .concurrent_updates(True)
        .build()
    )

    app.add_handler(CommandHandler("start", start_cmd))
    app.add_handler(CommandHandler("status", status_cmd))
    app.add_handler(CommandHandler("reset", reset_cmd))
    app.add_handler(CommandHandler("files", files_cmd))
    app.add_handler(CommandHandler("ask", ask_cmd))
    app.add_handler(CommandHandler("py", py_cmd))

    app.add_handler(MessageHandler(filters.Document.ALL, handle_document))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_text))

    app.add_error_handler(error_handler)
    return app

# =========================
# Main
# =========================
if __name__ == "__main__":
    app = build_app()
    log.info("Bot starting...")
    app.run_polling(drop_pending_updates=False)
