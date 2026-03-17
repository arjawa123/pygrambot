from telegram import Update
from telegram.ext import ContextTypes
from app.db import Database
from app.services.system_service import SystemService
from app.config import Config

class CommandHandler:
    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = (
            "👋 **Halo! Saya Pygram AI Assistant.**\n\n"
            "Saya siap membantu Anda menjawab pertanyaan, menganalisis file, "
            "dan banyak lagi menggunakan Groq & OpenRouter.\n\n"
            "📜 **Command Utama:**\n"
            "• /help - Daftar bantuan\n"
            "• /stats - Statistik chat\n"
            "• /reset - Hapus riwayat chat\n"
            "• /model - Info AI model\n"
            "• /ping - Tes koneksi\n"
        )
        await update.message.reply_text(text, parse_mode="Markdown")

    @staticmethod
    async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = (
            "🛠️ **Daftar Bantuan Pygram**\n\n"
            "• `/start` - Mulai bot\n"
            "• `/help` - Tampilkan pesan ini\n"
            "• `/ping` - Cek bot uptime\n"
            "• `/stats` - Lihat statistik penggunaan chat ini\n"
            "• `/reset` - Bersihkan riwayat percakapan\n"
            "• `/model` - Lihat provider & model aktif\n"
            "• `/hostinfo` - Info server (Admin only)\n\n"
            "📁 **Tips:** Kirim file teks (.txt, .md, .py, .csv) untuk saya analisis."
        )
        await update.message.reply_text(text, parse_mode="Markdown")

    @staticmethod
    async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🏓 **Pong!** Bot aktif dan responsif.")

    @staticmethod
    async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        stats = await Database.get_stats(chat_id)
        text = (
            "📊 **Statistik Chat Ini**\n"
            f"• Pesan tersimpan: `{stats['messages']}`\n"
            f"• File tersimpan: `{stats['files']}`\n"
            f"• Provider: `{Config.PRIMARY_PROVIDER.upper()}`"
        )
        await update.message.reply_text(text, parse_mode="Markdown")

    @staticmethod
    async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        await Database.clear_history(chat_id)
        await update.message.reply_text("🧹 **Riwayat chat dan file telah dibersihkan.**")

    @staticmethod
    async def model(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = (
            "🤖 **Informasi Model AI**\n\n"
            f"• **Primary Provider:** `{Config.PRIMARY_PROVIDER.upper()}`\n"
            f"• **Primary Model:** `{Config.GROQ_MODEL}`\n"
            f"• **Fallback Provider:** `OPENROUTER`\n"
            f"• **Fallback Model:** `{Config.OPENROUTER_MODEL_FREE}`"
        )
        await update.message.reply_text(text, parse_mode="Markdown")

    @staticmethod
    async def hostinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if Config.ALLOWED_USER_IDS and user_id not in Config.ALLOWED_USER_IDS:
            await update.message.reply_text("🚫 **Akses Ditolak.** Anda tidak memiliki izin.")
            return
        
        info = SystemService.get_host_info()
        await update.message.reply_text(info, parse_mode="Markdown")
