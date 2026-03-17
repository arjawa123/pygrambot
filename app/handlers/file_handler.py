import logging
from telegram import Update
from telegram.ext import ContextTypes
from app.db import Database
from app.services.file_service import FileService
from app.config import Config

logger = logging.getLogger(__name__)

class FileHandler:
    @staticmethod
    async def handle_document(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not update.message or not update.message.document:
            return

        doc = update.message.document
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        
        file_name = FileService.sanitize_filename(doc.file_name or "file")
        local_path = Config.FILES_DIR / f"{chat_id}" / file_name
        local_path.parent.mkdir(parents=True, exist_ok=True)

        # Download
        new_file = await context.bot.get_file(doc.file_id)
        await new_file.download_to_drive(str(local_path))

        # Extract
        text, note = FileService.extract_text(local_path)

        # Save to DB
        await Database.add_file(
            chat_id, user_id, doc.file_id, doc.file_unique_id, 
            file_name, str(local_path), doc.mime_type, text, note
        )

        await update.message.reply_text(
            f"✅ **File Berhasil Disimpan!**\n\n"
            f"📄 **Nama:** `{file_name}`\n"
            f"🔍 **Status:** `{note}`\n\n"
            "Kirim pesan untuk mulai menganalisis file ini.",
            parse_mode="Markdown"
        )
