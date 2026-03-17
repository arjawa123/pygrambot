import os
import time
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Telegram
    BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "").strip()
    ALLOWED_USER_IDS = {
        int(x.strip()) for x in os.getenv("ALLOWED_USER_IDS", "").split(",") if x.strip().isdigit()
    }

    # Database & Storage
    DB_PATH = os.getenv("BOT_DB_PATH", "bot.db").strip()
    FILES_DIR = Path(os.getenv("BOT_FILES_DIR", "bot_files").strip())
    FILES_DIR.mkdir(parents=True, exist_ok=True)
    
    # Logging Configuration
    LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
    LOG_FILE_PATH = os.getenv("LOG_FILE_PATH", "logs/bot.log").strip()
    LOG_TO_STDOUT = os.getenv("LOG_TO_STDOUT", "true").lower() == "true"
    
    # Create logs directory if it doesn't exist
    log_dir = Path(LOG_FILE_PATH).parent
    log_dir.mkdir(parents=True, exist_ok=True)

    # Runtime Info
    BOT_START_TIME = time.time()

    # Web Scraper Configuration
    WEB_FETCH_TIMEOUT = int(os.getenv("WEB_FETCH_TIMEOUT", "20"))
    WEB_MAX_CHARS = int(os.getenv("WEB_MAX_CHARS", "12000"))
    WEB_MAX_CONTENT_LENGTH = int(os.getenv("WEB_MAX_CONTENT_LENGTH", "2000000")) # 2MB
    WEB_USER_AGENT = os.getenv("WEB_USER_AGENT", "PygramBot/1.0 (Telegram AI Assistant)")

    # LLM Providers
    PRIMARY_PROVIDER = os.getenv("PRIMARY_PROVIDER", "groq").lower()
    
    # Groq
    GROQ_API_KEY = os.getenv("GROQ_API_KEY", "").strip()
    GROQ_MODEL = os.getenv("GROQ_MODEL", "llama-3.3-70b-versatile").strip()
    
    # OpenRouter (Fallback)
    OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "").strip()
    OPENROUTER_MODEL_FREE = os.getenv("OPENROUTER_MODEL_FREE", "google/gemini-2.0-flash-lite-preview-02-05:free").strip()

    # Limits
    MAX_HISTORY = int(os.getenv("MAX_HISTORY_MESSAGES", "20"))
    MAX_FILE_CHARS = int(os.getenv("MAX_FILE_TEXT_CHARS", "12000"))
    MAX_REPLY_CHARS = int(os.getenv("MAX_REPLY_CHARS", "3500"))
    TIMEOUT = int(os.getenv("REQUEST_TIMEOUT", "60"))

    # System Info
    ENABLE_CODE_EXECUTION = os.getenv("ENABLE_CODE_EXECUTION", "true").lower() == "true"

    @classmethod
    def validate(cls):
        if not cls.BOT_TOKEN:
            raise ValueError("TELEGRAM_BOT_TOKEN must be set in .env")
        if not cls.GROQ_API_KEY and cls.PRIMARY_PROVIDER == "groq":
            raise ValueError("GROQ_API_KEY must be set when using groq as primary")
