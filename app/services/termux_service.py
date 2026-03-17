import json
import logging
from typing import Dict, Any, Optional
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
        await ExecService.run_command(f"termux-toast -d {duration} '{text}'")

    @staticmethod
    async def tts_speak(text: str):
        """Speak text using Text-to-Speech."""
        await ExecService.run_command(f"termux-tts-speak '{text}'")

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
        await ExecService.run_command(f"termux-vibrate -d {duration_ms}")

    @staticmethod
    async def get_clipboard() -> str:
        """Get the current clipboard content."""
        return await ExecService.run_command("termux-clipboard-get")

    @staticmethod
    async def set_clipboard(text: str):
        """Set the clipboard content."""
        await ExecService.run_command(f"termux-clipboard-set '{text}'")

    @staticmethod
    async def take_photo(camera_id: int = 0, file_path: str = "bot_files/camera_photo.jpg") -> str:
        """Take a photo and save it to a file."""
        await ExecService.run_command(f"termux-camera-photo -c {camera_id} {file_path}")
        return file_path

    @staticmethod
    async def get_volume() -> Optional[Dict[str, Any]]:
        """Get volume status for all streams."""
        output = await ExecService.run_command("termux-volume")
        try:
            # termux-volume returns multiple JSON objects (one per stream), not a single array
            # We'll try to wrap it if it's not already an array
            if not output.strip().startswith("["):
                output = "[" + output.replace("}", "},").rstrip(",") + "]"
            return json.loads(output)
        except (json.JSONDecodeError, Exception) as e:
            logger.error(f"Error parsing volume info: {e}")
            return None

    @staticmethod
    async def send_sms(number: str, message: str):
        """Send an SMS to a specified number."""
        await ExecService.run_command(f"termux-sms-send -n {number} '{message}'")
