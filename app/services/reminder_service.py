import logging
import asyncio
from datetime import datetime, timedelta
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.base import JobLookupError
from telegram.ext import ContextTypes
from app.db import Database
import pytz

logger = logging.getLogger(__name__)

class ReminderService:
    # Explicitly use UTC to avoid local timezone issues in Termux
    _scheduler = AsyncIOScheduler(timezone=pytz.utc)
    _is_running = False

    @classmethod
    async def start_scheduler(cls, application):
        """Starts the scheduler and loads existing reminders from DB."""
        if not cls._is_running:
            cls._scheduler.start()
            cls._is_running = True
            logger.info("⏰ Scheduler started.")
            
            # TODO: Future enhancement - load pending reminders from DB and schedule them
            # For now, it handles runtime scheduling

    @classmethod
    async def add_reminder(cls, context: ContextTypes.DEFAULT_TYPE, chat_id: int, user_id: int, 
                           seconds: int, message: str):
        """Adds a reminder to the scheduler."""
        run_at = datetime.now() + timedelta(seconds=seconds)
        
        # Save to DB first
        # async with aiosqlite.connect(...) as db: # We'd need to add Database.add_reminder
        # For simplicity, we'll schedule it in memory first
        
        job_id = f"remind_{chat_id}_{int(datetime.now().timestamp())}"
        
        cls._scheduler.add_job(
            cls._send_reminder,
            'date',
            run_date=run_at,
            args=[context, chat_id, message],
            id=job_id
        )
        
        return run_at

    @staticmethod
    async def _send_reminder(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message: str):
        """Executes the reminder notification."""
        try:
            text = f"⏰ **PENGINGAT:**\n\n{message}"
            await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Failed to send reminder to {chat_id}: {e}")
