import csv
import io
import re
from pathlib import Path
from typing import Tuple, Optional
from app.config import Config

TEXT_FILE_EXTS = {
    ".txt", ".md", ".py", ".json", ".csv", ".log", ".ini", ".yaml", ".yml", ".toml"
}

class FileService:
    @staticmethod
    def sanitize_filename(name: str) -> str:
        name = re.sub(r"[^a-zA-Z0-9._-]+", "_", name)
        return name[:120] or "file"

    @staticmethod
    def extract_text(path: Path) -> Tuple[Optional[str], str]:
        ext = path.suffix.lower()
        if ext not in TEXT_FILE_EXTS:
            return None, f"File saved, but extension {ext or '(none)'} not auto-parsed."

        try:
            raw = path.read_text(encoding="utf-8", errors="replace")
            if ext == ".csv":
                reader = csv.reader(io.StringIO(raw))
                rows = [" | ".join(row) for i, row in enumerate(reader) if i < 30]
                if len(rows) >= 30: rows.append("... [rows truncated]")
                raw = "\n".join(rows)

            limit = Config.MAX_FILE_CHARS
            text = raw if len(raw) <= limit else raw[:limit] + "\n...[truncated]"
            return text, "Text extracted successfully."
        except Exception as e:
            return None, f"Failed to read file: {e}"
