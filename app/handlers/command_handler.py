import os
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from app.db import Database
from app.services.system_service import SystemService
from app.services.memory_service import MemoryService
from app.services.web_service import WebService
from app.services.log_service import LogService
from app.services.exec_service import ExecService
from app.llm.manager import LLMManager
from app.config import Config
from app.utils.command_registry import get_commands_by_category, CATEGORY_ICONS

logger = logging.getLogger(__name__)

class CommandHandler:
    @staticmethod
    async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = (
            "👋 **Halo! Saya Pygram AI Assistant.**\n\n"
            "Saya asisten serba bisa yang dilengkapi dengan memori persisten, "
            "kemampuan analisis file, dan ekstraksi web.\n\n"
            "📜 **Ketik `/` untuk melihat semua command.**"
        )
        await update.message.reply_text(text, parse_mode="Markdown")

    @staticmethod
    async def help(update: Update, context: ContextTypes.DEFAULT_TYPE):
        categories = get_commands_by_category()
        help_text = "🛠️ **Bantuan & Fitur Pygram**\n\n"
        for category, commands in categories.items():
            icon = CATEGORY_ICONS.get(category, "🔹")
            help_text += f"{icon} **{category}**\n"
            for cmd in commands:
                cmd_link = f"/{cmd.command}"
                usage_info = cmd.usage[len(cmd_link):] if cmd.usage and " " in cmd.usage else ""
                admin_tag = " (Admin Only)" if cmd.admin_only else ""
                help_text += f"{cmd_link}{usage_info} — {cmd.description}{admin_tag}\n"
            help_text += "\n"
        await update.message.reply_text(help_text, parse_mode="Markdown")

    @staticmethod
    async def web(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("❌ Gunakan: `/web <url>`")
            return
            
        url = context.args[0]
        if not WebService.validate_url(url):
            await update.message.reply_text("❌ URL tidak valid. Pastikan diawali dengan `http://` atau `https://`.")
            return

        status_msg = await update.message.reply_text(f"🔍 **Membaca {url}...**")
        
        try:
            data = await WebService.fetch_url(url)
            
            # Store in session context
            context.chat_data['web_context'] = {
                'url': data['url'],
                'title': data['title'],
                'description': data['description'],
                'content': data['text'],
                'timestamp': data['fetched_at']
            }
            
            # Build Inline Keyboard
            keyboard = [
                [
                    InlineKeyboardButton("✨ Ringkas", callback_data="web:summary"),
                    InlineKeyboardButton("💾 Simpan Memory", callback_data="web:save")
                ],
                [
                    InlineKeyboardButton("ℹ️ Detail", callback_data="web:detail"),
                    InlineKeyboardButton("🗑️ Hapus Context", callback_data="web:clear")
                ],
                [
                    InlineKeyboardButton("💬 Tanya Isi Web", callback_data="web:ask")
                ]
            ]
            reply_markup = InlineKeyboardMarkup(keyboard)

            response = (
                f"🌐 **Web Content Loaded**\n"
                f"• **URL:** `{data['url']}`\n"
                f"• **Title:** `{data['title']}`\n\n"
                f"✅ Konten berhasil dimuat ke konteks sementara.\n"
                f"Pilih aksi di bawah ini:"
            )
            
            await status_msg.edit_text(response, reply_markup=reply_markup, parse_mode="Markdown")
            
        except Exception as e:
            await status_msg.edit_text(f"❌ **Gagal membaca website:**\n`{str(e)}`", parse_mode="Markdown")

    @staticmethod
    async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handles inline button clicks for web actions."""
        query = update.callback_query
        data = query.data
        chat_id = update.effective_chat.id
        user_id = update.effective_user.id
        
        # Security: Only allow user who initiated the chat (optional, but good)
        # For now, let's focus on logic
        
        web_ctx = context.chat_data.get('web_context')
        if not web_ctx and data.startswith("web:"):
            await query.answer("⚠️ Konteks web sudah kadaluarsa atau dihapus.", show_alert=True)
            return

        await query.answer() # Acknowledge the click

        if data == "web:summary":
            status_msg = await query.message.reply_text("⏳ **Meringkas konten...**")
            llm = LLMManager()
            prompt = [
                {"role": "system", "content": "Kamu adalah asisten yang ahli meringkas. Buat ringkasan yang padat, poin-poin penting, dan informatif dari teks yang diberikan."},
                {"role": "user", "content": f"Ringkas konten dari website '{web_ctx['title']}' berikut ini:\n\n{web_ctx['content']}"}
            ]
            summary = await llm.get_response(prompt)
            await status_msg.edit_text(f"📝 **Ringkasan Web:**\n\n{summary}", parse_mode="Markdown")

        elif data == "web:save":
            await MemoryService.remember_web(chat_id, user_id, web_ctx['title'], web_ctx['url'], web_ctx['content'])
            await query.message.reply_text(f"✅ **Berhasil!** Ringkasan dari `{web_ctx['title']}` telah disimpan ke persistent memory.")

        elif data == "web:detail":
            detail = (
                f"ℹ️ **Web Metadata Detail**\n"
                f"• **Title:** `{web_ctx['title']}`\n"
                f"• **URL:** `{web_ctx['url']}`\n"
                f"• **Desc:** _{web_ctx['description'] or 'N/A'}_\n"
                f"• **Length:** `{len(web_ctx['content'])} characters`\n"
                f"• **Fetched At:** `{web_ctx['timestamp']}`"
            )
            await query.message.reply_text(detail, parse_mode="Markdown")

        elif data == "web:clear":
            context.chat_data.pop('web_context', None)
            context.chat_data.pop('web_qa_mode', None)
            await query.edit_message_text("🗑️ **Konteks web dan mode Q&A telah dihapus.**")

        elif data == "web:ask":
            # Enable the special Mode
            context.chat_data['web_qa_mode'] = True
            
            keyboard = [[InlineKeyboardButton("🚪 Keluar Mode Web", callback_data="web:exit")]]
            reply_markup = InlineKeyboardMarkup(keyboard)

            await query.message.reply_text(
                f"🧠 **Web Q&A mode aktif**\n"
                f"Saya sekarang fokus menjawab berdasarkan konten dari `{web_ctx['title']}`.\n\n"
                f"Silakan kirim pertanyaan Anda! Gunakan `/exitweb` untuk keluar.",
                reply_markup=reply_markup
            )

        elif data == "web:exit":
            context.chat_data.pop('web_qa_mode', None)
            await query.message.reply_text("🚪 **Keluar dari mode Web Q&A.** Kembali ke mode chat normal.")

    @staticmethod
    async def exitweb(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Disables the Web Q&A mode via command."""
        if context.chat_data.get('web_qa_mode'):
            context.chat_data.pop('web_qa_mode', None)
            await update.message.reply_text("🚪 **Mode Web Q&A dinonaktifkan.**")
        else:
            await update.message.reply_text("ℹ️ Kamu tidak sedang dalam mode Web Q&A.")

    @staticmethod
    async def saveweb(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Compatibility for text command /saveweb."""
        web_data = context.chat_data.get('web_context')
        if not web_data:
            await update.message.reply_text("❌ Tidak ada konten web terbaru di sesi ini.")
            return
        await MemoryService.remember_web(update.effective_chat.id, update.effective_user.id, web_data['title'], web_data['url'], web_data['content'])
        await update.message.reply_text("✅ Konten disimpan ke memori permanen.")

    @staticmethod
    async def hostinfo(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if Config.ALLOWED_USER_IDS and user_id not in Config.ALLOWED_USER_IDS:
            await update.message.reply_text("🚫 **Akses Ditolak.**")
            return
        info = SystemService.get_host_info_formatted()
        await update.message.reply_text(info, parse_mode="Markdown")

    @staticmethod
    async def logs(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if Config.ALLOWED_USER_IDS and user_id not in Config.ALLOWED_USER_IDS:
            await update.message.reply_text("🚫 **Akses Ditolak.**")
            return
        n_lines = 30
        filter_level = None
        if context.args:
            if context.args[0].isdigit(): n_lines = int(context.args[0])
            else: filter_level = context.args[0]
        logs = LogService.get_logs_summary(n_lines, filter_level)
        header = f"📋 **Recent Logs ({n_lines} lines)**\n"
        if filter_level: header = f"📋 **Filtered Logs: {filter_level.upper()}**\n"
        await update.message.reply_text(f"{header}```\n{logs}\n```", parse_mode="Markdown")

    @staticmethod
    async def exec_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if Config.ALLOWED_USER_IDS and user_id not in Config.ALLOWED_USER_IDS:
            await update.message.reply_text("🚫 **Akses Ditolak.**")
            return
        if not context.args:
            await update.message.reply_text("❌ Gunakan: `/exec <command>`")
            return
        command = " ".join(context.args)
        status_msg = await update.message.reply_text(f"⏳ **Executing:** `{command}`...")
        output = await ExecService.run_command(command)
        final_text = f"💻 **Command:**\n`{command}`\n\n**Output:**\n```bash\n{output}\n```"
        await status_msg.edit_text(final_text, parse_mode="Markdown")

    @staticmethod
    async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🏓 **Pong!** Bot aktif.")

    @staticmethod
    async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        stats = await Database.get_stats(chat_id)
        text = f"📊 **Statistik Chat**\n• Pesan: `{stats['messages']}`\n• File: `{stats['files']}`\n• Memori: `{stats['memories']}`"
        await update.message.reply_text(text, parse_mode="Markdown")

    @staticmethod
    async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        await Database.clear_history(chat_id)
        await update.message.reply_text("🧹 **Riwayat chat telah dibersihkan.**")

    @staticmethod
    async def model(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = f"🤖 **AI Model Info**\n• **Primary:** `{Config.PRIMARY_PROVIDER.upper()}` (`{Config.GROQ_MODEL}`)\n• **Fallback:** `OPENROUTER` (`{Config.OPENROUTER_MODEL_FREE}`)"
        await update.message.reply_text(text, parse_mode="Markdown")

    @staticmethod
    async def remember(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("❌ Gunakan: `/remember <fakta yang ingin diingat>`")
            return
        content = " ".join(context.args)
        await MemoryService.remember(update.effective_chat.id, update.effective_user.id, content)
        await update.message.reply_text("✅ **Memori disimpan.**")

    @staticmethod
    async def memories(update: Update, context: ContextTypes.DEFAULT_TYPE):
        mems = await MemoryService.get_all_memories(update.effective_chat.id)
        if not mems:
            await update.message.reply_text("📭 **Belum ada memori tersimpan.**")
            return
        text = "🧠 **Memori Tersimpan:**\n"
        for m in mems: text += f"`{m[0]}`. {m[1]}\n"
        text += "\n💡 Gunakan `/forget <id>` untuk menghapus."
        await update.message.reply_text(text, parse_mode="Markdown")

    @staticmethod
    async def forget(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args or not context.args[0].isdigit():
            await update.message.reply_text("❌ Gunakan: `/forget <id_memori>`")
            return
        mem_id = int(context.args[0])
        await MemoryService.forget(update.effective_chat.id, mem_id)
        await update.message.reply_text(f"🗑️ **Memori `{mem_id}` telah dihapus.**")

    @staticmethod
    async def files(update: Update, context: ContextTypes.DEFAULT_TYPE):
        files = await Database.get_all_files(update.effective_chat.id)
        if not files:
            await update.message.reply_text("📭 **Tidak ada file tersimpan.**")
            return
        text = "📁 **Daftar File:**\n"
        for f in files: text += f"`{f[0]}`. `{f[1]}`\n"
        text += "\n💡 Gunakan `/deletefile <id>` untuk menghapus."
        await update.message.reply_text(text, parse_mode="Markdown")

    @staticmethod
    async def deletefile(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args or not context.args[0].isdigit():
            await update.message.reply_text("❌ Gunakan: `/deletefile <id_file>`")
            return
        f_id = int(context.args[0])
        path = await Database.delete_file(f_id, update.effective_chat.id)
        if path and os.path.exists(path):
            os.remove(path)
            await update.message.reply_text(f"🗑️ **File `{f_id}` telah dihapus.**")
        else:
            await update.message.reply_text("❌ File tidak ditemukan.")

    @staticmethod
    async def clearfiles(update: Update, context: ContextTypes.DEFAULT_TYPE):
        paths = await Database.clear_files(update.effective_chat.id)
        count = 0
        for p in paths:
            if os.path.exists(p):
                os.remove(p)
                count += 1
        await update.message.reply_text(f"🗑️ **{count} file telah dihapus.**")
