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
    "Utama": "🏠",
    "AI & Search": "🔍",
    "Tools": "🛠️",
    "Memori": "🧠",
    "File": "📁",
    "Web": "🌐",
    "Sistem": "⚙️",
    "Kontrol Device": "📱",
    "Sensor & Info": "ℹ️"
}

# Single Source of Truth for all bot commands
COMMAND_REGISTRY: List[BotCommandInfo] = [
    # Utama
    BotCommandInfo("start", "Mulai bot & perkenalan", "Utama"),
    BotCommandInfo("help", "Lihat bantuan command", "Utama"),
    BotCommandInfo("ping", "Cek status koneksi", "Utama"),
    BotCommandInfo("stats", "Statistik penggunaan", "Utama"),
    BotCommandInfo("reset", "Hapus riwayat chat", "Utama"),
    
    # AI & Search
    BotCommandInfo("search", "Cari informasi di internet", "AI & Search", usage="/search <query>"),
    BotCommandInfo("model", "Info model AI aktif", "AI & Search"),
    BotCommandInfo("setmodel", "Ubah provider AI utama", "AI & Search", admin_only=True),
    BotCommandInfo("py", "Jalankan kode Python (Multi-line)", "AI & Search", admin_only=True, usage="/py <code>"),
    
    # Tools
    BotCommandInfo("remindme", "Set pengingat fleksibel", "Tools", usage="/remindme <waktu> <pesan>"),
    BotCommandInfo("reminders", "Daftar pengingat aktif", "Tools"),
    
    # Memori
    BotCommandInfo("remember", "Simpan fakta baru", "Memori", usage="/remember <teks>"),
    BotCommandInfo("memories", "Daftar memori chat", "Memori"),
    BotCommandInfo("forget", "Hapus memori by ID", "Memori", usage="/forget <id>"),
    
    # File
    BotCommandInfo("files", "Daftar file diunggah", "File"),
    BotCommandInfo("deletefile", "Hapus file by ID", "File", usage="/deletefile <id>"),
    BotCommandInfo("clearfiles", "Hapus semua file", "File"),
    
    # Web
    BotCommandInfo("web", "Baca konten website", "Web", usage="/web <url>"),
    BotCommandInfo("saveweb", "Simpan konten web ke memory", "Web"),
    BotCommandInfo("exitweb", "Keluar dari mode tanya-jawab web", "Web"),
    
    # Sistem (Admin Only)
    BotCommandInfo("hostinfo", "Info host/device", "Sistem", admin_only=True),
    BotCommandInfo("logs", "Lihat log terbaru", "Sistem", admin_only=True, usage="/logs <n>"),
    BotCommandInfo("exec", "Eksekusi CLI command", "Sistem", admin_only=True, usage="/exec <command>"),
    BotCommandInfo("restart", "Restart bot script", "Sistem", admin_only=True),
    BotCommandInfo("git", "Update repository git", "Sistem", admin_only=True, usage="/git [pull]"),

    # Kontrol Device (Admin Only)
    BotCommandInfo("toast", "Tampilkan pesan toast", "Kontrol Device", admin_only=True, usage="/toast <pesan>"),
    BotCommandInfo("tts", "Suarakan teks (TTS)", "Kontrol Device", admin_only=True, usage="/tts <teks>"),
    BotCommandInfo("torch", "Nyalakan/matikan senter", "Kontrol Device", admin_only=True, usage="/torch on|off"),
    BotCommandInfo("vibrate", "Getarkan device", "Kontrol Device", admin_only=True, usage="/vibrate <ms>"),
    BotCommandInfo("clipboard", "Baca/tulis clipboard", "Kontrol Device", admin_only=True, usage="/clipboard [teks]"),
    BotCommandInfo("photo", "Ambil foto kamera", "Kontrol Device", admin_only=True, usage="/photo [0|1]"),
    BotCommandInfo("record", "Rekam audio mic", "Kontrol Device", admin_only=True, usage="/record <detik>"),
    BotCommandInfo("notify", "Kirim notifikasi Android", "Kontrol Device", admin_only=True, usage="/notify [judul|]isi"),
    BotCommandInfo("play", "Putar audio dari URL", "Kontrol Device", admin_only=True, usage="/play <url>"),
    BotCommandInfo("stopplay", "Hentikan audio", "Kontrol Device", admin_only=True),
    BotCommandInfo("brightness", "Atur kecerahan layar", "Kontrol Device", admin_only=True, usage="/brightness <0-255>"),
    BotCommandInfo("volume_set", "Atur volume stream", "Kontrol Device", admin_only=True, usage="/volume_set <stream> <level>"),
    BotCommandInfo("stt", "Speech-to-Text", "Kontrol Device", admin_only=True),
    BotCommandInfo("sms_send", "Kirim SMS", "Kontrol Device", admin_only=True, usage="/sms_send <nomor> <pesan>"),

    # Sensor & Info (Admin Only)
    BotCommandInfo("battery", "Cek status baterai", "Sensor & Info", admin_only=True),
    BotCommandInfo("location", "Cek lokasi GPS", "Sensor & Info", admin_only=True),
    BotCommandInfo("volume", "Cek volume semua stream", "Sensor & Info", admin_only=True),
    BotCommandInfo("wifi", "Scan jaringan WiFi", "Sensor & Info", admin_only=True),
    BotCommandInfo("telephony", "Cek info telepon", "Sensor & Info", admin_only=True),
    BotCommandInfo("sensor", "Daftar semua sensor", "Sensor & Info", admin_only=True),
]

def get_commands_by_category():
    """Groups commands for generating help text."""
    categories = {}
    for cmd in COMMAND_REGISTRY:
        if cmd.category not in categories:
            categories[cmd.category] = []
        categories[cmd.category].append(cmd)
    return categories
