import os
import re
from collections import deque
from app.config import Config

class LogService:
    @staticmethod
    def get_log_path() -> str:
        """Returns the current log file path."""
        return Config.LOG_FILE_PATH

    @classmethod
    def read_tail(cls, n_lines: int = 30) -> str:
        """Efficiently reads the last N lines of the log file."""
        log_path = cls.get_log_path()
        if not os.path.exists(log_path):
            return "Log file not found."

        try:
            with open(log_path, 'r', encoding='utf-8') as f:
                # Use deque to efficiently keep last N lines
                last_lines = deque(f, n_lines)
                
                content = "".join(last_lines).strip()
                if not content:
                    return "Log file is empty."
                
                return content
        except Exception as e:
            return f"Error reading logs: {str(e)}"

    @classmethod
    def get_logs_summary(cls, n_lines: int = 30, filter_level: str = None) -> str:
        """Get summarized logs, optionally filtered by level with clean formatting."""
        lines = cls.read_tail(300) 
        if "Log file not found" in lines or "Log file is empty" in lines:
            return lines

        line_list = lines.splitlines()
        
        if filter_level:
            level = filter_level.upper()
            line_list = [l for l in line_list if level in l]
            if not line_list:
                return f"No logs found with level: {level}"

        # Clean logs for Telegram (Narrow screen)
        cleaned_lines = []
        for line in line_list[-n_lines:]:
            # More robust regex to handle both file and console-like formats
            # Matches: [YYYY-MM-DD HH:MM:SS] LEVEL LOGGER: MESSAGE or [HH:MM:SS] LEVEL LOGGER MESSAGE
            match = re.search(r'\[(?:.*?\s)?(\d{2}:\d{2}:\d{2})\]\s+(\w+)\s+([\w\.]+):?\s+(.*)', line)
            if match:
                time_str, level, logger_name, msg = match.groups()
                # Simplified to: HH:MM:SS LEVEL Message
                line = f"{time_str} {level} {msg}"
            
            cleaned_lines.append(line)

        content = "\n".join(cleaned_lines)
        
        if len(content) > 3800:
            content = "..." + content[-3800:]
            
        return content
