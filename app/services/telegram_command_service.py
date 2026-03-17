import logging
from telegram import BotCommand
from telegram.ext import Application
from app.utils.command_registry import COMMAND_REGISTRY

logger = logging.getLogger(__name__)

async def setup_bot_commands(application: Application):
    """
    Registers the bot commands with Telegram so they appear in the 
    slash menu suggestion list.
    """
    try:
        # Build the list of BotCommand objects for Telegram
        # We register all commands so they're visible to everyone, 
        # but execution will still be blocked by admin_only check.
        telegram_commands = [
            BotCommand(cmd.command, cmd.description)
            for cmd in COMMAND_REGISTRY
        ]
        
        # Call the Telegram API
        await application.bot.set_my_commands(telegram_commands)
        logger.info(f"Successfully registered {len(telegram_commands)} commands to Telegram slash menu.")
    except Exception as e:
        logger.error(f"Failed to set bot commands: {str(e)}")
