import asyncio
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler as TelegramCommandHandler,
    MessageHandler,
    filters,
)
from app.config import Config
from app.db import init_db
from app.handlers.command_handler import CommandHandler
from app.handlers.chat_handler import ChatHandler
from app.handlers.file_handler import FileHandler
from app.utils.logging_setup import setup_logging, get_logger
from app.services.telegram_command_service import setup_bot_commands

# 0. Initialize Logging
setup_logging()
logger = get_logger("pygram")

def main():
    # 1. Validate Config
    try:
        Config.validate()
    except ValueError as e:
        logger.error(f"Config error: {e}")
        return

    # 2. Build Application
    app = ApplicationBuilder().token(Config.BOT_TOKEN).build()
    
    # 3. Post-init Hook for Async Tasks
    async def post_init(application):
        await init_db()
        logger.info("Database initialized successfully.")
        
        # Register Telegram Slash Commands
        await setup_bot_commands(application)

    app.post_init = post_init
    
    # Handlers
    chat_handler = ChatHandler()
    
    # 4. Add Command Handlers
    app.add_handler(TelegramCommandHandler("start", CommandHandler.start))
    app.add_handler(TelegramCommandHandler("help", CommandHandler.help))
    app.add_handler(TelegramCommandHandler("ping", CommandHandler.ping))
    app.add_handler(TelegramCommandHandler("stats", CommandHandler.stats))
    app.add_handler(TelegramCommandHandler("reset", CommandHandler.reset))
    app.add_handler(TelegramCommandHandler("model", CommandHandler.model))
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
