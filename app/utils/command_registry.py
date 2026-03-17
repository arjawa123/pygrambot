from dataclasses import dataclass
from typing import List, Optional

@dataclass
class BotCommandInfo:
    command: str
    description: str  # Short description for Telegram suggestion menu
    category: str
    admin_only: bool = False
    usage: Optional[str] = None

# Mapping icons to categories
CATEGORY_ICONS = {
    "General": "🤖",
    "Files": "📁",
    "Memory": "🧠",
    "Web": "🌐",
    "System": "⚙️"
}

# Single Source of Truth for all bot commands
COMMAND_REGISTRY: List[BotCommandInfo] = [
    # General
    BotCommandInfo("start", "Mulai bot & perkenalan", "General"),
    BotCommandInfo("help", "Lihat bantuan command", "General"),
    BotCommandInfo("ping", "Cek status koneksi", "General"),
    BotCommandInfo("model", "Info model AI aktif", "General"),
    BotCommandInfo("setmodel", "Ubah provider AI utama", "General", admin_only=True),
    BotCommandInfo("reset", "Hapus riwayat chat", "General"),
    BotCommandInfo("stats", "Statistik penggunaan", "General"),
    
    # Files
    BotCommandInfo("files", "Daftar file diunggah", "Files"),
    BotCommandInfo("deletefile", "Hapus file by ID", "Files", usage="/deletefile <id>"),
    BotCommandInfo("clearfiles", "Hapus semua file", "Files"),
    
    # Memory
    BotCommandInfo("remember", "Simpan fakta baru", "Memory", usage="/remember <teks>"),
    BotCommandInfo("memories", "Daftar memori chat", "Memory"),
    BotCommandInfo("forget", "Hapus memori by ID", "Memory", usage="/forget <id>"),
    
    # Web
    BotCommandInfo("web", "Baca konten website", "Web", usage="/web <url>"),
    BotCommandInfo("saveweb", "Simpan konten web ke memory", "Web"),
    BotCommandInfo("exitweb", "Keluar dari mode tanya-jawab web", "Web"),
    
    # System (Admin Only)
    BotCommandInfo("hostinfo", "Info host/device", "System", admin_only=True),
    BotCommandInfo("logs", "Lihat log terbaru", "System", admin_only=True, usage="/logs <n>"),
    BotCommandInfo("exec", "Eksekusi CLI command", "System", admin_only=True, usage="/exec <command>"),
]

def get_commands_by_category():
    """Groups commands for generating help text."""
    categories = {}
    for cmd in COMMAND_REGISTRY:
        if cmd.category not in categories:
            categories[cmd.category] = []
        categories[cmd.category].append(cmd)
    return categories
