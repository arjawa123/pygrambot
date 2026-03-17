import logging
import sys
import os
from datetime import datetime
from app.config import Config

# ANSI Color Codes
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    CYAN = "\033[36m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    MAGENTA = "\033[35m"

class ColoredFormatter(logging.Formatter):
    """Custom formatter for console output with colors."""
    
    LEVEL_COLORS = {
        logging.DEBUG: Colors.CYAN,
        logging.INFO: Colors.GREEN,
        logging.WARNING: Colors.YELLOW,
        logging.ERROR: Colors.RED,
        logging.CRITICAL: Colors.BOLD + Colors.RED
    }

    def format(self, record):
        color = self.LEVEL_COLORS.get(record.levelno, Colors.RESET)
        
        # Format parts
        timestamp = datetime.fromtimestamp(record.created).strftime("%H:%M:%S")
        level_name = f"{record.levelname:<8}"
        logger_name = f"{record.name}"
        message = record.getMessage()

        # Build colored string: [HH:MM:SS] LEVEL  logger_name  message
        return f"[{timestamp}] {color}{level_name}{Colors.RESET} {Colors.CYAN}{logger_name}{Colors.RESET}  {message}"

def setup_logging():
    """Initializes the global logging configuration."""
    log_level = getattr(logging, Config.LOG_LEVEL, logging.INFO)
    
    # Root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Clear existing handlers
    if root_logger.hasHandlers():
        root_logger.handlers.clear()

    # File Handler (Plain text)
    file_formatter = logging.Formatter(
        "[%(asctime)s] %(levelname)-8s %(name)s: %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )
    try:
        file_handler = logging.FileHandler(Config.LOG_FILE_PATH, encoding="utf-8")
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    except Exception as e:
        print(f"Failed to setup file logging: {e}")

    # Console Handler (Colored)
    if Config.LOG_TO_STDOUT:
        console_handler = logging.StreamHandler(sys.stdout)
        # Only use colored formatter if terminal supports it
        if sys.stdout.isatty():
            console_handler.setFormatter(ColoredFormatter())
        else:
            console_handler.setFormatter(file_formatter)
        root_logger.addHandler(console_handler)

def get_logger(name: str):
    """Helper to get a logger instance."""
    return logging.getLogger(name)
