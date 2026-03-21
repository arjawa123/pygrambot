import asyncio
import logging
import html
import json
import traceback
from telegram import Update
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler as TelegramCommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)
from telegram.request import HTTPXRequest
from telegram.constants import ParseMode
from app.config import Config
from app.db import init_db
from app.handlers.command_handler import CommandHandler
from app.handlers.chat_handler import ChatHandler
from app.handlers.file_handler import FileHandler
from app.handlers.termux_handler import TermuxHandler
from app.utils.logging_setup import setup_logging, get_logger
from app.services.telegram_command_service import setup_bot_commands
from app.services.reminder_service import ReminderService

# 0. Initialize Logging
setup_logging()
logger = get_logger("pygram")

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and notify the user if possible."""
    logger.error("Exception while handling an update:", exc_info=context.error)

    # traceback.format_exception returns a list of strings
    tb_list = traceback.format_exception(None, context.error, context.error.__traceback__)
    tb_string = "".join(tb_list)

    # Build the message with some details and traceback
    update_str = update.to_dict() if isinstance(update, Update) else str(update)
    
    # Notify user if update has an effective message
    if update and hasattr(update, 'effective_message') and update.effective_message:
        try:
            # Escape error message for HTML
            error_msg = html.escape(str(context.error))
            await update.effective_message.reply_text(
                f"❌ <b>Internal Error:</b>\n<code>{error_msg}</code>",
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            logger.error(f"Failed to send error message to user: {e}")

def main():
    # 1. Validate Config
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"Config error: {e}")
        return

    # 2. Build Application with increased timeouts
    request = HTTPXRequest(connect_timeout=30.0, read_timeout=30.0)
    app = ApplicationBuilder().token(Config.BOT_TOKEN).request(request).build()
    
    # Add error handler
    app.add_error_handler(error_handler)
    
    # 3. Post-init Hook for Async Tasks
    async def post_init(application):
        await init_db()
        logger.info("Database initialized successfully.")
        
        # Start Scheduler for Reminders
        await ReminderService.start_scheduler(application)
        
        # Register Telegram Slash Commands
        await setup_bot_commands(application)

    app.post_init = post_init
    
    # Handlers
    chat_handler = ChatHandler()
    
    # 4. Add Command Handlers
    app.add_handler(TelegramCommandHandler("start", CommandHandler.start))
    app.add_handler(TelegramCommandHandler("help", CommandHandler.help))
    app.add_handler(TelegramCommandHandler("ping", CommandHandler.ping))
    app.add_handler(TelegramCommandHandler("search", CommandHandler.search))
    app.add_handler(TelegramCommandHandler("remindme", CommandHandler.remindme))
    app.add_handler(TelegramCommandHandler("reminders", CommandHandler.reminders))
    app.add_handler(TelegramCommandHandler("py", CommandHandler.py_eval))
    app.add_handler(TelegramCommandHandler("stats", CommandHandler.stats))
    app.add_handler(TelegramCommandHandler("reset", CommandHandler.reset))
    app.add_handler(TelegramCommandHandler("model", CommandHandler.model))
    app.add_handler(TelegramCommandHandler("setmodel", CommandHandler.setmodel))
    app.add_handler(TelegramCommandHandler("hostinfo", CommandHandler.hostinfo))
    app.add_handler(TelegramCommandHandler("logs", CommandHandler.logs))
    app.add_handler(TelegramCommandHandler("exec", CommandHandler.exec_cmd))
    
    # Memory Commands
    app.add_handler(TelegramCommandHandler("remember", CommandHandler.remember))
    app.add_handler(TelegramCommandHandler("memories", CommandHandler.memories))
    app.add_handler(TelegramCommandHandler("forget", CommandHandler.forget))
    
    # File Management Commands
    app.add_handler(TelegramCommandHandler("files", CommandHandler.files))
    app.add_handler(TelegramCommandHandler("deletefile", CommandHandler.deletefile))
    app.add_handler(TelegramCommandHandler("clearfiles", CommandHandler.clearfiles))
    
    # Web Commands
    app.add_handler(TelegramCommandHandler("web", CommandHandler.web))
    app.add_handler(TelegramCommandHandler("saveweb", CommandHandler.saveweb))
    app.add_handler(TelegramCommandHandler("exitweb", CommandHandler.exitweb))

    # Device Commands (Termux API)
    app.add_handler(TelegramCommandHandler("battery", TermuxHandler.battery_command))
    app.add_handler(TelegramCommandHandler("toast", TermuxHandler.toast_command))
    app.add_handler(TelegramCommandHandler("tts", TermuxHandler.tts_command))
    app.add_handler(TelegramCommandHandler("location", TermuxHandler.location_command))
    app.add_handler(TelegramCommandHandler("torch", TermuxHandler.torch_command))
    app.add_handler(TelegramCommandHandler("vibrate", TermuxHandler.vibrate_command))
    app.add_handler(TelegramCommandHandler("clipboard", TermuxHandler.clipboard_command))
    app.add_handler(TelegramCommandHandler("photo", TermuxHandler.photo_command))
    app.add_handler(TelegramCommandHandler("record", TermuxHandler.record_command))
    app.add_handler(TelegramCommandHandler("volume", TermuxHandler.volume_command))
    app.add_handler(TelegramCommandHandler("wifi", TermuxHandler.wifi_command))
    app.add_handler(TelegramCommandHandler("notify", TermuxHandler.notify_command))
    app.add_handler(TelegramCommandHandler("telephony", TermuxHandler.telephony_command))
    app.add_handler(TelegramCommandHandler("sensor", TermuxHandler.sensor_command))
    app.add_handler(TelegramCommandHandler("sms_send", TermuxHandler.sms_send_command))
    app.add_handler(TelegramCommandHandler("play", TermuxHandler.play_command))
    app.add_handler(TelegramCommandHandler("stopplay", TermuxHandler.stop_play_command))

    # Callback Handlers
    app.add_handler(CallbackQueryHandler(CommandHandler.handle_callback))
    
    # 5. Add Message Handlers
    user_filter = filters.ALL
    if Config.ALLOWED_USER_IDS:
        user_filter = filters.User(user_id=Config.ALLOWED_USER_IDS)

    app.add_handler(MessageHandler(
        filters.TEXT & ~filters.COMMAND & user_filter, 
        chat_handler.handle_message
    ))
    
    # 6. Add File Handlers
    app.add_handler(MessageHandler(
        filters.Document.ALL & user_filter, 
        FileHandler.handle_document
    ))

    logger.info("🚀 Pygram AI Bot is running...")
    # run_polling is a blocking call that manages its own loop
    app.run_polling()

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("Bot stopped manually.")
