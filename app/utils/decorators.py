import functools
import logging
from telegram import Update
from telegram.ext import ContextTypes
from app.config import Config

logger = logging.getLogger(__name__)

def admin_only(func):
    """
    Decorator to restrict access to command handlers to only ALLOWED_USER_IDS.
    If ALLOWED_USER_IDS is empty, all users are allowed.
    """
    @functools.wraps(func)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user_id = update.effective_user.id
        
        # If ALLOWED_USER_IDS is set, check if the user is in it
        if Config.ALLOWED_USER_IDS and user_id not in Config.ALLOWED_USER_IDS:
            logger.warning(f"Unauthorized access attempt by user {user_id} on command {func.__name__}")
            await update.message.reply_text("🚫 **Akses Ditolak.** Command ini hanya untuk admin.")
            return

        return await func(update, context, *args, **kwargs)
    
    return wrapper
