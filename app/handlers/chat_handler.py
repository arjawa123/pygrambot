import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction
from app.db import Database
from app.llm.manager import LLMManager
from app.config import Config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Kamu adalah Pygram AI Assistant, asisten produktif, cerdas, dan membantu.
Aturan:
1. Jawab singkat, akurat, dan praktis.
2. Gunakan konteks history chat dan file terbaru yang diberikan.
3. Hindari halusinasi. Jika tidak yakin, katakan terus terang.
4. Gunakan gaya bahasa user (Bahasa Indonesia secara default).
5. Format jawaban dengan Markdown agar rapi di Telegram.
"""

class ChatHandler:
    def __init__(self):
        self.llm = LLMManager()

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.message.text:
            return

        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        user_text = update.message.text

        # 1. Save user message
        await Database.add_message(chat_id, user_id, "user", user_text)

        # 2. Show typing
        await context.bot.send_chat_action(chat_id=chat_id, action=ChatAction.TYPING)

        # 3. Build messages with context
        history = await Database.get_history(chat_id)
        recent_files = await Database.get_recent_files(chat_id, 2)

        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        # Add file context
        if recent_files:
            file_context = "Konteks file terbaru:\n"
            for f in recent_files:
                file_context += f"• File: {f[0]}\nIsi: {f[2] or 'Tidak ada teks'}\n\n"
            messages.append({"role": "system", "content": file_context})

        # Add chat history
        messages.extend(history)

        try:
            # 4. Get AI Response
            response = await self.llm.get_response(messages)
            
            # 5. Save assistant response
            await Database.add_message(chat_id, user_id, "assistant", response)

            # 6. Split and Send
            await self.send_long_message(update, response)

        except Exception as e:
            logger.error(f"Chat error: {e}")
            await update.message.reply_text(f"❌ **Maaf, terjadi kesalahan:**\n`{str(e)}`", parse_mode="Markdown")

    async def send_long_message(self, update: Update, text: str):
        limit = Config.MAX_REPLY_CHARS
        if len(text) <= limit:
            await update.message.reply_text(text, parse_mode="Markdown")
            return

        chunks = [text[i:i+limit] for i in range(0, len(text), limit)]
        for chunk in chunks:
            await update.message.reply_text(chunk, parse_mode="Markdown")
