import json
import logging
import shlex
import os
import asyncio
from typing import Dict, Any, Optional, List
from app.services.exec_service import ExecService

logger = logging.getLogger(__name__)

class TermuxService:
    @staticmethod
    async def get_battery_status() -> Optional[Dict[str, Any]]:
        """Get battery status from termux-battery-status."""
        output = await ExecService.run_command("termux-battery-status")
        try:
            return json.loads(output)
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Error parsing battery status: {e}")
            return None

    @staticmethod
    async def show_toast(text: str, short: bool = True):
        """Show a toast notification on the device."""
        duration = "short" if short else "long"
        safe_text = shlex.quote(text)
        await ExecService.run_command(f"termux-toast -d {duration} {safe_text}")

    @staticmethod
    async def tts_speak(text: str):
        """Speak text using Text-to-Speech."""
        safe_text = shlex.quote(text)
        await ExecService.run_command(f"termux-tts-speak {safe_text}")

    @staticmethod
    async def get_location() -> Optional[Dict[str, Any]]:
        """Get device location using termux-location."""
        output = await ExecService.run_command("termux-location -p network -r last")
        try:
            return json.loads(output)
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Error parsing location: {e}")
            return None

    @staticmethod
    async def torch(on: bool = True):
        """Turn the flashlight on or off."""
        state = "on" if on else "off"
        await ExecService.run_command(f"termux-torch {state}")

    @staticmethod
    async def vibrate(duration_ms: int = 500):
        """Vibrate the device for a specified duration."""
        await ExecService.run_command(f"termux-vibrate -f -d {duration_ms}")

    @staticmethod
    async def get_clipboard() -> str:
        """Get the current clipboard content."""
        return await ExecService.run_command("termux-clipboard-get")

    @staticmethod
    async def set_clipboard(text: str):
        """Set the clipboard content."""
        safe_text = shlex.quote(text)
        await ExecService.run_command(f"termux-clipboard-set {safe_text}")

    @staticmethod
    async def take_photo(camera_id: int = 0, file_path: str = "bot_files/camera_photo.jpg") -> str:
        """Capture photo using detached execution to prevent shell hangs."""
        abs_path = os.path.abspath(file_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        if os.path.exists(abs_path): os.remove(abs_path)
        
        safe_path = shlex.quote(abs_path)
        # Trigger detached camera process - No output waiting
        cmd = f"termux-camera-photo -c {camera_id} {safe_path}"
        logger.info(f"Triggering camera detached: {cmd}")
        await ExecService.run_detached(cmd)
        
        # Polling: Wait up to 20 seconds
        for i in range(20):
            await asyncio.sleep(1)
            if os.path.exists(abs_path) and os.path.getsize(abs_path) > 1000:
                logger.info(f"Photo ready after {i+1}s")
                return abs_path
        
        # Fallback for camera 0
        if camera_id == 0:
            logger.warning("Retrying default camera...")
            await ExecService.run_detached(f"termux-camera-photo {safe_path}")
            for i in range(10):
                await asyncio.sleep(1)
                if os.path.exists(abs_path) and os.path.getsize(abs_path) > 1000:
                    return abs_path

        return abs_path

    @staticmethod
    async def get_volume() -> Optional[List[Dict[str, Any]]]:
        """Get volume status for all streams."""
        output = await ExecService.run_command("termux-volume")
        try:
            if not output.strip().startswith("["):
                output = "[" + output.replace("}", "},").rstrip(",") + "]"
            return json.loads(output)
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Error parsing volume info: {e}")
            return None

    @staticmethod
    async def send_sms(number: str, message: str):
        """Send an SMS to a specified number."""
        safe_num = shlex.quote(number)
        safe_msg = shlex.quote(message)
        await ExecService.run_command(f"termux-sms-send -n {safe_num} {safe_msg}")

    @staticmethod
    async def record_microphone(duration_sec: int = 5, file_path: str = "bot_files/record.m4a") -> str:
        """Record audio using detached execution and manual stop."""
        abs_path = os.path.abspath(file_path)
        os.makedirs(os.path.dirname(abs_path), exist_ok=True)
        if os.path.exists(abs_path): os.remove(abs_path)
        
        safe_path = shlex.quote(abs_path)
        
        # 1. Detached stop any previous session
        await ExecService.run_detached("termux-microphone-record -q")
        await asyncio.sleep(0.5)
        
        # 2. Detached start recording
        await ExecService.run_detached(f"termux-microphone-record -f {safe_path} -e aac")
        
        # 3. Wait duration
        await asyncio.sleep(duration_sec)
        
        # 4. Detached stop
        await ExecService.run_detached("termux-microphone-record -q")
        
        # 5. Sync wait
        await asyncio.sleep(2)
        
        return abs_path

    @staticmethod
    async def get_wifi_info() -> Optional[List[Dict[str, Any]]]:
        """Get WiFi scan info."""
        output = await ExecService.run_command("termux-wifi-scaninfo", max_chars=100000)
        try:
            return json.loads(output, strict=False)
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Error parsing WiFi info: {e}")
            return None

    @staticmethod
    async def show_notification(title: str, content: str, id: str = "bot_notif"):
        """Show a persistent Android notification."""
        safe_title = shlex.quote(title)
        safe_content = shlex.quote(content)
        await ExecService.run_command(f"termux-notification -t {safe_title} -c {safe_content} -i {id}")

    @staticmethod
    async def get_telephony_info() -> Optional[Dict[str, Any]]:
        """Get device telephony info."""
        output = await ExecService.run_command("termux-telephony-deviceinfo")
        try:
            return json.loads(output)
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Error parsing telephony info: {e}")
            return None

    @staticmethod
    async def get_sensors() -> Optional[Any]:
        """Get a list of available sensors."""
        output = await ExecService.run_command("termux-sensor -l", max_chars=100000)
        try:
            return json.loads(output)
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Error parsing sensor info: {e}")
            return None

    @staticmethod
    async def play_audio(url: str) -> str:
        """Download and play audio using termux-media-player."""
        file_path = os.path.abspath("bot_files/play_cache.mp3")
        os.makedirs(os.path.dirname(file_path), exist_ok=True)
        
        # Stop any existing playback first
        await ExecService.run_command("termux-media-player stop")
        
        # Download using curl
        safe_url = shlex.quote(url)
        safe_path = shlex.quote(file_path)
        
        # -L to follow redirects
        logger.info(f"Downloading audio from {url}")
        download_cmd = f"curl -L -o {safe_path} {safe_url}"
        await ExecService.run_command(download_cmd, timeout=60)
        
        if os.path.exists(file_path) and os.path.getsize(file_path) > 0:
            logger.info(f"Playing audio: {file_path}")
            await ExecService.run_detached(f"termux-media-player play {safe_path}")
            return "✅ Audio sedang diputar di device server."
        else:
            return "❌ Gagal mendownload audio. Pastikan URL valid dan dapat diakses langsung."

    @staticmethod
    async def stop_audio() -> str:
        """Stop audio playback."""
        await ExecService.run_command("termux-media-player stop")
        return "⏹️ Playback dihentikan."

    @staticmethod
    async def set_brightness(level: int) -> str:
        """Set screen brightness (0-255)."""
        # Clamp value
        level = max(0, min(255, level))
        await ExecService.run_command(f"termux-brightness {level}")
        return f"🔆 Brightness set to <code>{level}</code>"

    @staticmethod
    async def set_volume(stream: str, volume: int) -> str:
        """Set volume for a specific stream."""
        await ExecService.run_command(f"termux-volume {stream} {volume}")
        return f"🔊 Volume for <code>{stream}</code> set to <code>{volume}</code>"

    @staticmethod
    async def speech_to_text() -> str:
        """Perform Speech-to-Text and return recognized text."""
        # This command usually shows a dialog on the device
        output = await ExecService.run_command("termux-speech-to-text", timeout=30)
        return output
