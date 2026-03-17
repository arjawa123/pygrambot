import platform
import socket
import sys
import os
import psutil
import time
from datetime import datetime
from app.config import Config

class SystemService:
    @staticmethod
    def is_termux() -> bool:
        """Detect if the environment is Termux."""
        return "TERMUX_VERSION" in os.environ or os.path.exists("/data/data/com.termux")

    @classmethod
    def get_detailed_info(cls) -> dict:
        """Collect comprehensive system and host information."""
        # Calculate process uptime
        uptime_seconds = time.time() - Config.BOT_START_TIME
        days, rem = divmod(uptime_seconds, 86400)
        hours, rem = divmod(rem, 3600)
        minutes, seconds = divmod(rem, 60)
        process_uptime = f"{int(days)}d {int(hours)}h {int(minutes)}m {int(seconds)}s"

        # Try to get local IP safely
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(("8.8.8.8", 80))
            local_ip = s.getsockname()[0]
            s.close()
        except Exception:
            local_ip = "Unknown"

        # Platform details
        is_termux = cls.is_termux()
        
        return {
            "is_termux": is_termux,
            "hostname": socket.gethostname(),
            "system": platform.system(),
            "release": platform.release(),
            "version": platform.version(),
            "machine": platform.machine(),
            "processor": platform.processor() or "N/A",
            "python_version": sys.version.split()[0],
            "python_executable": sys.executable,
            "cwd": os.getcwd(),
            "local_ip": local_ip,
            "shell": os.environ.get("SHELL", "N/A"),
            "user": os.environ.get("USER") or os.environ.get("LOGNAME") or "Unknown",
            "process_uptime": process_uptime,
            "current_time": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "memory_usage": f"{psutil.Process(os.getpid()).memory_info().rss / 1024 / 1024:.2f} MB"
        }

    @classmethod
    def get_host_info_formatted(cls) -> str:
        """Return host info formatted for Telegram."""
        info = cls.get_detailed_info()
        
        termux_tag = " (Termux 📱)" if info["is_termux"] else ""
        
        lines = [
            "🖥️ **Host Information**",
            f"• **Status:** `Online`{termux_tag}",
            f"• **Hostname:** `{info['hostname']}`",
            f"• **Platform:** `{info['system']} {info['release']}`",
            f"• **Arch:** `{info['machine']}`",
            f"• **Python:** `{info['python_version']}`",
            f"• **User:** `{info['user']}`",
            f"• **Local IP:** `{info['local_ip']}`",
            f"• **Uptime:** `{info['process_uptime']}`",
            f"• **Memory:** `{info['memory_usage']}`",
            f"• **Server Time:** `{info['current_time']}`",
            "",
            "📂 **Environment**",
            f"• **CWD:** `{info['cwd']}`",
            f"• **Shell:** `{info['shell']}`",
            f"• **Exec:** `{info['python_executable']}`"
        ]
        return "\n".join(lines)
