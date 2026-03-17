import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction
from app.db import Database
from app.llm.manager import LLMManager
from app.services.memory_service import MemoryService
from app.config import Config

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """Kamu adalah Pygram AI Assistant, asisten produktif yang cerdas.
Aturan:
1. Jawab singkat, akurat, dan praktis.
2. Gunakan KONTEKS yang diberikan (Memori, File, Web, History).
3. Memori berisi fakta penting tentang user atau preferensi chat ini. Gunakan itu agar personal.
4. Jika ada konteks Web, ringkas atau jawab berdasarkan isi web tersebut.
5. Gunakan gaya bahasa user (Bahasa Indonesia default).
6. Format jawaban dengan Markdown.
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

        # 3. Build messages with ALL contexts
        messages = [{"role": "system", "content": SYSTEM_PROMPT}]
        
        # A. Add Memory Context
        memory_ctx = await MemoryService.get_memory_context(chat_id)
        if memory_ctx:
            messages.append({"role": "system", "content": memory_ctx})

        # B. Add Web Context (Temporary for current session)
        web_data = context.chat_data.get('web_context')
        web_mode = context.chat_data.get('web_qa_mode', False)
        
        if web_data:
            if web_mode:
                # When Q&A mode is active, make the context VERY prominent
                messages.append({
                    "role": "system", 
                    "content": f"PRIORITAS UTAMA: Kamu sedang dalam mode Web Q&A. Jawablah pertanyaan user HANYA berdasarkan konten dari URL: {web_data['url']}. \n\nISI KONTEN:\n{web_data['content']}"
                })
            else:
                messages.append({
                    "role": "system", 
                    "content": f"Konteks Web Terbaru (URL: {web_data['url']}):\n{web_data['content']}"
                })

        # C. Add File Context
        recent_files = await Database.get_recent_files(chat_id, 2)
        if recent_files:
            file_ctx = "Konteks file terbaru:\n"
            for f in recent_files:
                file_ctx += f"• File: {f[0]}\nIsi: {f[2] or 'Tidak ada teks'}\n\n"
            messages.append({"role": "system", "content": file_ctx})

        # D. Add Chat History
        history = await Database.get_history(chat_id)
        messages.extend(history)

        try:
            # 4. Get AI Response
            response = await self.llm.get_response(messages)
            
            # If Web QA Mode is active, add a prefix
            if context.chat_data.get('web_qa_mode'):
                response = f"🌐 **Berdasarkan web terakhir:**\n\n{response}"

            # 5. Save assistant response
            await Database.add_message(chat_id, user_id, "assistant", response)

            # 6. Split and Send
            await self.send_long_message(update, response)

        except Exception as e:
            logger.error(f"Chat error: {e}")
            await update.message.reply_text(f"❌ **Kesalahan:**\n`{str(e)}`", parse_mode="Markdown")

    async def send_long_message(self, update: Update, text: str):
        limit = Config.MAX_REPLY_CHARS
        if len(text) <= limit:
            await update.message.reply_text(text, parse_mode="Markdown")
            return

        chunks = [text[i:i+limit] for i in range(0, len(text), limit)]
        for chunk in chunks:
            await update.message.reply_text(chunk, parse_mode="Markdown")
