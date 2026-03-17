import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatAction
from app.db import Database
from app.llm.manager import LLMManager
from app.services.memory_service import MemoryService
from app.services.search_service import SearchService
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

        # 3. Build Contextual System Prompt
        context_parts = []
        
        # A. Add Memory Context
        memory_ctx = await MemoryService.get_memory_context(chat_id)
        if memory_ctx:
            context_parts.append(f"### LONG-TERM MEMORY (Fakta Penting):\n{memory_ctx}")

        # B. Add Web Context
        web_data = context.chat_data.get('web_context')
        web_mode = context.chat_data.get('web_qa_mode', False)
        if web_data:
            web_header = "### WEB CONTEXT (Prioritas Tinggi):" if web_mode else "### WEB CONTEXT:"
            context_parts.append(f"{web_header}\nURL: {web_data['url']}\nTitle: {web_data['title']}\nContent: {web_data['content']}")

        # C. Add File Context (Smarter Search)
        # Search for files matching keywords from the user question
        relevant_files = await SearchService.find_relevant_files(chat_id, user_text, limit=3)
        if relevant_files:
            file_ctx = "### FILE CONTEXT (Dokumen Terkait):\n"
            for f in relevant_files:
                file_ctx += f"• File: {f[0]}\nContent Snippet: {f[2] or 'No text'}\n"
            context_parts.append(file_ctx)

        # Combine into a single System Prompt update
        final_system_prompt = SYSTEM_PROMPT
        if context_parts:
            final_system_prompt += "\n\nBERIKUT ADALAH KONTEKS SAAT INI UNTUK MEMBANTU JAWABANMU:\n" + "\n\n".join(context_parts)
            if web_mode:
                final_system_prompt += "\n\nCATATAN: Kamu sedang dalam mode Web Q&A. Utamakan informasi dari Web Context di atas."

        messages = [{"role": "system", "content": final_system_prompt}]

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
