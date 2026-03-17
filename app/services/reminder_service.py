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
                           seconds_or_date: str, message: str):
        """
        Adds a reminder to the scheduler.
        seconds_or_date: Can be "10" (minutes), or "2026-03-18 10:00"
        """
        # Use system local time for detection
        now_local = datetime.now()
        now_utc = datetime.now(pytz.utc)
        run_at = None

        # Try parsing as minutes first (numeric)
        if seconds_or_date.isdigit():
            run_at = now_utc + timedelta(minutes=int(seconds_or_date))
        else:
            # Try parsing as full datetime (YYYY-MM-DD HH:MM)
            try:
                # Parse as naive local time
                local_dt = datetime.strptime(seconds_or_date, "%Y-%m-%d %H:%M")
                # Convert to UTC based on system local timezone
                run_at = local_dt.astimezone(pytz.utc)
            except ValueError:
                # Try parsing as just time (HH:MM) - assumes today
                try:
                    t = datetime.strptime(seconds_or_date, "%H:%M").time()
                    # Combine with today's date in local time
                    local_dt = datetime.combine(now_local.date(), t)
                    # Convert to UTC
                    run_at = local_dt.astimezone(pytz.utc)
                    # If time has passed today, assume tomorrow
                    if run_at < now_utc:
                        run_at += timedelta(days=1)
                except ValueError:
                    raise ValueError("Format waktu tidak valid. Gunakan menit (angka), 'HH:MM', atau 'YYYY-MM-DD HH:MM'.")

        if run_at < now_utc:
            raise ValueError("Waktu pengingat sudah terlewat.")

        job_id = f"remind_{chat_id}_{int(run_at.timestamp())}"
        
        cls._scheduler.add_job(
            cls._send_reminder,
            'date',
            run_date=run_at,
            args=[context, chat_id, message],
            id=job_id
        )
        
        return run_at

    @classmethod
    def get_all_reminders(cls, chat_id: int):
        """Returns all scheduled reminders for a specific chat."""
        jobs = cls._scheduler.get_jobs()
        reminders = []
        prefix = f"remind_{chat_id}_"
        for job in jobs:
            if job.id.startswith(prefix):
                reminders.append({
                    "id": job.id,
                    "run_at": job.next_run_time,
                    "message": job.args[2]
                })
        return sorted(reminders, key=lambda x: x['run_at'])

    @classmethod
    def delete_reminder(cls, job_id: str):
        """Deletes a specific reminder by its job ID."""
        try:
            cls._scheduler.remove_job(job_id)
            return True
        except JobLookupError:
            return False

    @staticmethod
    async def _send_reminder(context: ContextTypes.DEFAULT_TYPE, chat_id: int, message: str):
        """Executes the reminder notification."""
        try:
            text = f"⏰ **PENGINGAT:**\n\n{message}"
            await context.bot.send_message(chat_id=chat_id, text=text, parse_mode="Markdown")
        except Exception as e:
            logger.error(f"Failed to send reminder to {chat_id}: {e}")
