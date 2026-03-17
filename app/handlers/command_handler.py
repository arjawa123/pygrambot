import os
from telegram import Update
from telegram.ext import ContextTypes
from app.db import Database
from app.services.system_service import SystemService
from app.services.memory_service import MemoryService
from app.services.web_service import WebService
from app.services.log_service import LogService
from app.services.exec_service import ExecService
from app.config import Config
from app.utils.command_registry import get_commands_by_category, CATEGORY_ICONS

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
                # To make it clickable in Telegram, use plain /command without backticks.
                # If there's a usage, we show it like: /command <args> — description
                cmd_link = f"/{cmd.command}"
                
                # Check if command has additional usage/args to show
                usage_info = ""
                if cmd.usage and " " in cmd.usage:
                    # Get only the args part: "/remember <text>" -> " <text>"
                    usage_info = cmd.usage[len(cmd_link):]
                
                admin_tag = " (Admin Only)" if cmd.admin_only else ""
                
                # Format: /command <args> — description
                help_text += f"{cmd_link}{usage_info} — {cmd.description}{admin_tag}\n"
            help_text += "\n"
            
        await update.message.reply_text(help_text, parse_mode="Markdown")

    @staticmethod
    async def ping(update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text("🏓 **Pong!** Bot aktif.")

    @staticmethod
    async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        stats = await Database.get_stats(chat_id)
        text = (
            "📊 **Statistik Chat**\n"
            f"• Pesan: `{stats['messages']}`\n"
            f"• File: `{stats['files']}`\n"
            f"• Memori: `{stats['memories']}`"
        )
        await update.message.reply_text(text, parse_mode="Markdown")

    @staticmethod
    async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
        chat_id = update.effective_chat.id
        await Database.clear_history(chat_id)
        await update.message.reply_text("🧹 **Riwayat chat telah dibersihkan.**")

    @staticmethod
    async def model(update: Update, context: ContextTypes.DEFAULT_TYPE):
        text = (
            "🤖 **AI Model Info**\n"
            f"• **Primary:** `{Config.PRIMARY_PROVIDER.upper()}` (`{Config.GROQ_MODEL}`)\n"
            f"• **Fallback:** `OPENROUTER` (`{Config.OPENROUTER_MODEL_FREE}`)"
        )
        await update.message.reply_text(text, parse_mode="Markdown")

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
            if context.args[0].isdigit():
                n_lines = int(context.args[0])
            else:
                filter_level = context.args[0]

        logs = LogService.get_logs_summary(n_lines, filter_level)
        
        header = f"📋 **Recent Logs ({n_lines} lines)**\n"
        if filter_level:
            header = f"📋 **Filtered Logs: {filter_level.upper()}**\n"
            
        await update.message.reply_text(
            f"{header}```\n{logs}\n```", 
            parse_mode="Markdown"
        )

    @staticmethod
    async def exec_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Executes a shell command from Telegram (Admin Only)."""
        user_id = update.effective_user.id
        if Config.ALLOWED_USER_IDS and user_id not in Config.ALLOWED_USER_IDS:
            await update.message.reply_text("🚫 **Akses Ditolak.**")
            return

        if not context.args:
            await update.message.reply_text("❌ Gunakan: `/exec <command>`")
            return

        command = " ".join(context.args)
        status_msg = await update.message.reply_text(f"⏳ **Executing:** `{command}`...")

        # Run command
        output = await ExecService.run_command(command)
        
        # Format the response
        final_text = (
            f"💻 **Command:**\n`{command}`\n\n"
            f"**Output:**\n"
            f"```bash\n{output}\n```"
        )
        
        await status_msg.edit_text(final_text, parse_mode="Markdown")

    @staticmethod
    async def remember(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("❌ Gunakan: `/remember <fakta yang ingin diingat>`")
            return
        content = " ".join(context.args)
        await MemoryService.remember(update.effective_chat.id, update.effective_user.id, content)
        await update.message.reply_text("✅ **Memori disimpan.** Saya akan mengingat ini dalam percakapan kita.")

    @staticmethod
    async def memories(update: Update, context: ContextTypes.DEFAULT_TYPE):
        mems = await MemoryService.get_all_memories(update.effective_chat.id)
        if not mems:
            await update.message.reply_text("📭 **Belum ada memori tersimpan.**")
            return
        text = "🧠 **Memori Tersimpan:**\n"
        for m in mems:
            text += f"`{m[0]}`. {m[1]}\n"
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
        for f in files:
            text += f"`{f[0]}`. `{f[1]}`\n"
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

    @staticmethod
    async def web(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if not context.args:
            await update.message.reply_text("❌ Gunakan: `/web <url>`")
            return
        url = context.args[0]
        await update.message.reply_text(f"🔍 **Membaca {url}...**")
        content = await WebService.fetch_url_content(url)
        context.chat_data['web_context'] = {'url': url, 'content': content}
        await update.message.reply_text(
            f"✅ **Berhasil membaca website!**\n"
            f"Kirim pesan untuk menganalisis isi website ini.",
            parse_mode="Markdown"
        )
