import os
import logging
import html
from telegram import Update
from telegram.constants import ParseMode
from telegram.ext import ContextTypes
from app.services.termux_service import TermuxService
from app.utils.decorators import admin_only

logger = logging.getLogger(__name__)

class TermuxHandler:
    @staticmethod
    @admin_only
    async def battery_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /battery command."""
        status = await TermuxService.get_battery_status()
        if not status:
            await update.message.reply_text("❌ Failed to get battery status.")
            return

        percentage = status.get("percentage")
        status_text = status.get("status")
        temperature = status.get("temperature")
        plugged = status.get("plugged")
        
        icon = "🔋" if percentage > 20 else "🪫"
        if status_text == "CHARGING": icon = "⚡"

        message = (
            f"{icon} <b>Battery Status</b>\n"
            f"• <b>Level:</b> <code>{percentage}%</code>\n"
            f"• <b>Status:</b> <code>{status_text}</code>\n"
            f"• <b>Temp:</b> <code>{temperature}°C</code>\n"
            f"• <b>Plugged:</b> <code>{plugged}</code>"
        )
        await update.message.reply_text(message, parse_mode=ParseMode.HTML)

    @staticmethod
    @admin_only
    async def toast_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /toast command."""
        text = " ".join(context.args)
        if not text:
            await update.message.reply_text("Usage: <code>/toast &lt;text&gt;</code>", parse_mode=ParseMode.HTML)
            return
        
        await TermuxService.show_toast(text)
        safe_text = html.escape(text)
        await update.message.reply_text(f"✅ Toast sent: <code>{safe_text}</code>", parse_mode=ParseMode.HTML)

    @staticmethod
    @admin_only
    async def tts_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /tts command."""
        text = " ".join(context.args)
        if not text:
            await update.message.reply_text("Usage: <code>/tts &lt;text&gt;</code>", parse_mode=ParseMode.HTML)
            return
        
        await TermuxService.tts_speak(text)
        safe_text = html.escape(text)
        await update.message.reply_text(f"🗣️ Speaking: <code>{safe_text}</code>", parse_mode=ParseMode.HTML)

    @staticmethod
    @admin_only
    async def location_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /location command."""
        await update.message.reply_text("🛰️ Requesting location... (this may take a few seconds)")
        loc = await TermuxService.get_location()
        if not loc:
            await update.message.reply_text("❌ Failed to get location.")
            return

        lat = loc.get("latitude")
        lon = loc.get("longitude")
        acc = loc.get("accuracy")
        provider = loc.get("provider")

        message = (
            f"📍 <b>Device Location</b>\n"
            f"• <b>Lat:</b> <code>{lat}</code>\n"
            f"• <b>Lon:</b> <code>{lon}</code>\n"
            f"• <b>Accuracy:</b> <code>{acc}m</code>\n"
            f"• <b>Provider:</b> <code>{provider}</code>\n\n"
            f"<a href=\"https://www.google.com/maps/search/?api=1&query={lat},{lon}\">Google Maps</a>"
        )
        await update.message.reply_text(message, parse_mode=ParseMode.HTML, disable_web_page_preview=False)

    @staticmethod
    @admin_only
    async def torch_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /torch command."""
        arg = context.args[0].lower() if context.args else "toggle"
        
        if arg in ["on", "1", "yes"]:
            await TermuxService.torch(True)
            await update.message.reply_text("🔦 Torch ON")
        elif arg in ["off", "0", "no"]:
            await TermuxService.torch(False)
            await update.message.reply_text("🔦 Torch OFF")
        else:
            await update.message.reply_text("Usage: <code>/torch on</code> or <code>/torch off</code>", parse_mode=ParseMode.HTML)

    @staticmethod
    @admin_only
    async def vibrate_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /vibrate command."""
        duration = 500
        if context.args:
            try:
                duration = int(context.args[0])
            except ValueError:
                pass
        
        await TermuxService.vibrate(duration)
        await update.message.reply_text(f"📳 Vibrating for <code>{duration}ms</code>", parse_mode=ParseMode.HTML)

    @staticmethod
    @admin_only
    async def clipboard_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /clipboard command."""
        if not context.args:
            text = await TermuxService.get_clipboard()
            safe_text = html.escape(text)
            await update.message.reply_text(f"📋 <b>Clipboard Content:</b>\n<code>{safe_text}</code>", parse_mode=ParseMode.HTML)
        else:
            text = " ".join(context.args)
            await TermuxService.set_clipboard(text)
            safe_text = html.escape(text)
            await update.message.reply_text(f"✅ Clipboard set to: <code>{safe_text}</code>", parse_mode=ParseMode.HTML)

    @staticmethod
    @admin_only
    async def photo_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /photo command."""
        await update.message.reply_text("📸 Taking photo...")
        try:
            os.makedirs("bot_files", exist_ok=True)
            file_path = await TermuxService.take_photo()
            if os.path.exists(file_path):
                with open(file_path, 'rb') as photo:
                    await update.message.reply_photo(photo, caption="📸 Photo captured from device")
            else:
                await update.message.reply_text("❌ Photo file not found after capture.")
        except Exception as e:
            await update.message.reply_text(f"❌ Error taking photo: {html.escape(str(e))}", parse_mode=ParseMode.HTML)

    @staticmethod
    @admin_only
    async def volume_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /volume command."""
        volumes = await TermuxService.get_volume()
        if not volumes:
            await update.message.reply_text("❌ Failed to get volume info.")
            return

        lines = ["🔊 <b>Volume Status</b>"]
        for v in volumes:
            stream = v.get("stream", "Unknown")
            volume = v.get("volume", 0)
            max_vol = v.get("max_volume", 0)
            lines.append(f"• <b>{stream.capitalize()}:</b> <code>{volume}/{max_vol}</code>")
            
        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)

    @staticmethod
    @admin_only
    async def sms_send_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /sms_send command."""
        if len(context.args) < 2:
            await update.message.reply_text("Usage: <code>/sms_send &lt;number&gt; &lt;message&gt;</code>", parse_mode=ParseMode.HTML)
            return
        
        number = html.escape(context.args[0])
        message = " ".join(context.args[1:])
        await TermuxService.send_sms(number, message)
        await update.message.reply_text(f"✉️ SMS sent to <code>{number}</code>", parse_mode=ParseMode.HTML)
