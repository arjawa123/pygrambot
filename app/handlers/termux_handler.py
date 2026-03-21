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
            # Clean up the response from ExecService
            if not text or "Command finished with no output" in text:
                await update.message.reply_text("📋 <b>Clipboard Kosong</b> atau akses diblokir oleh Android (Cek izin <i>Display over other apps</i> pada Termux:API).", parse_mode=ParseMode.HTML)
                return
                
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
        """Handler for /photo command. /photo [id]"""
        camera_id = 0
        if context.args:
            try:
                camera_id = int(context.args[0])
            except ValueError:
                pass
        
        await update.message.reply_text(f"📸 Taking photo from camera <code>{camera_id}</code>...", parse_mode=ParseMode.HTML)
        try:
            os.makedirs("bot_files", exist_ok=True)
            # Service uses the camera_id provided
            file_path = await TermuxService.take_photo(camera_id=camera_id)
            if os.path.exists(file_path) and os.path.getsize(file_path) > 100:
                with open(file_path, 'rb') as photo:
                    await update.message.reply_photo(photo, caption=f"📸 Photo captured from camera {camera_id}")
                os.remove(file_path)
            else:
                await update.message.reply_text("❌ Photo file not found or failed to capture. Check if camera ID is correct.")
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

    @staticmethod
    @admin_only
    async def wifi_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /wifi command."""
        await update.message.reply_text("📡 Scanning WiFi...")
        wifi_list = await TermuxService.get_wifi_info()
        if not wifi_list:
            await update.message.reply_text("❌ Failed to scan WiFi or no networks found.")
            return

        lines = ["📡 <b>WiFi Scan Results</b>"]
        for w in wifi_list[:10]: # Limit to 10 results
            ssid = w.get("ssid", "Unknown")
            bssid = w.get("bssid", "N/A")
            signal = w.get("rssi", 0)
            lines.append(f"• <b>{ssid}</b> (<code>{signal} dBm</code>)")
        
        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)

    @staticmethod
    @admin_only
    async def record_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /record command."""
        duration = 5
        if context.args:
            try:
                duration = int(context.args[0])
            except ValueError:
                pass
        
        await update.message.reply_text(f"🎤 Recording <code>{duration}s</code> audio...", parse_mode=ParseMode.HTML)
        try:
            # Service will now return the absolute path
            file_path = await TermuxService.record_microphone(duration)
            if os.path.exists(file_path) and os.path.getsize(file_path) > 100:
                with open(file_path, 'rb') as audio:
                    await update.message.reply_audio(audio, title=f"Record {duration}s")
                os.remove(file_path)
            else:
                await update.message.reply_text("❌ Audio file not found or empty after recording. Check logs.")
        except Exception as e:
            await update.message.reply_text(f"❌ Error recording audio: {html.escape(str(e))}", parse_mode=ParseMode.HTML)

    @staticmethod
    @admin_only
    async def notify_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /notify command."""
        full_text = " ".join(context.args)
        if "|" in full_text:
            title, content = full_text.split("|", 1)
        else:
            title = "Pygram Bot"
            content = full_text or "No message content."
        
        await TermuxService.show_notification(title.strip(), content.strip())
        await update.message.reply_text("🔔 Notification sent to device.")

    @staticmethod
    @admin_only
    async def telephony_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /telephony command."""
        info = await TermuxService.get_telephony_info()
        if not info:
            await update.message.reply_text("❌ Failed to get telephony info.")
            return

        lines = ["📱 <b>Telephony Info</b>"]
        for key, value in info.items():
            lines.append(f"• <b>{key}:</b> <code>{value}</code>")
        
        await update.message.reply_text("\n".join(lines), parse_mode=ParseMode.HTML)

    @staticmethod
    @admin_only
    async def sensor_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Handler for /sensor command."""
        sensors = await TermuxService.get_sensors()
        if not sensors:
            await update.message.reply_text("❌ Failed to get sensor list.")
            return

        lines = ["🌡️ <b>Available Sensors</b>"]
        
        # Handle different output formats of termux-sensor -l
        if isinstance(sensors, list):
            sensor_list = sensors
        elif isinstance(sensors, dict):
            sensor_list = sensors.get("sensors", [])
        else:
            sensor_list = []

        if not sensor_list:
            await update.message.reply_text("❌ No sensors detected.")
            return

        for s in sensor_list:
            # If item is dict, get name. If string (common in -l), use as is.
            name = s.get("name") if isinstance(s, dict) else str(s)
            lines.append(f"• <code>{html.escape(name)}</code>")
        
        # Limit output to prevent Telegram message length limits
        await update.message.reply_text("\n".join(lines[:30]), parse_mode=ParseMode.HTML)
