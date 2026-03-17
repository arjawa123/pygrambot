import platform
import socket
import sys
import os
import psutil
from datetime import datetime
from app.config import Config

class SystemService:
    @staticmethod
    def get_host_info() -> str:
        uptime = datetime.fromtimestamp(psutil.boot_time()).strftime("%Y-%m-%d %H:%M:%S")
        process_uptime = datetime.fromtimestamp(os.path.getmtime(__file__)).strftime("%Y-%m-%d %H:%M:%S") # Simple approach
        
        info = [
            "🖥️ **Host Information**",
            f"• **Hostname:** `{socket.gethostname()}`",
            f"• **Platform:** `{platform.system()} {platform.release()}`",
            f"• **Architecture:** `{platform.machine()}`",
            f"• **Python:** `{sys.version.split()[0]}`",
            f"• **Local IP:** `{socket.gethostbyname(socket.gethostname())}`",
            f"• **CWD:** `{os.getcwd()}`",
            f"• **System Boot:** `{uptime}`",
            f"• **Server Time:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`",
        ]
        return "\n".join(info)
