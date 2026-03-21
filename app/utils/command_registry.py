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
    "System": "⚙️",
    "Device": "📱"
}

# Single Source of Truth for all bot commands
COMMAND_REGISTRY: List[BotCommandInfo] = [
    # General
    BotCommandInfo("start", "Mulai bot & perkenalan", "General"),
    BotCommandInfo("help", "Lihat bantuan command", "General"),
    BotCommandInfo("ping", "Cek status koneksi", "General"),
    BotCommandInfo("search", "Cari informasi di internet", "General", usage="/search <query>"),
    BotCommandInfo("remindme", "Set pengingat fleksibel", "General", usage="/remindme <waktu> <pesan>"),
    BotCommandInfo("reminders", "Daftar pengingat aktif", "General"),
    BotCommandInfo("py", "Jalankan kode Python (Admin)", "General", admin_only=True, usage="/py <code>"),
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

    # Device (Termux API - Admin Only)
    BotCommandInfo("battery", "Cek status baterai device", "Device", admin_only=True),
    BotCommandInfo("toast", "Tampilkan pesan toast di device", "Device", admin_only=True, usage="/toast <pesan>"),
    BotCommandInfo("tts", "Suarakan teks di device (TTS)", "Device", admin_only=True, usage="/tts <teks>"),
    BotCommandInfo("location", "Cek lokasi GPS device", "Device", admin_only=True),
    BotCommandInfo("torch", "Nyalakan/matikan senter", "Device", admin_only=True, usage="/torch on|off"),
    BotCommandInfo("vibrate", "Getarkan device", "Device", admin_only=True, usage="/vibrate <ms>"),
    BotCommandInfo("clipboard", "Baca/tulis clipboard device", "Device", admin_only=True, usage="/clipboard [teks]"),
    BotCommandInfo("photo", "Ambil foto kamera device", "Device", admin_only=True, usage="/photo [0|1]"),
    BotCommandInfo("record", "Rekam audio dari microphone", "Device", admin_only=True, usage="/record <detik>"),
    BotCommandInfo("volume", "Cek volume audio device", "Device", admin_only=True),
    BotCommandInfo("wifi", "Scan jaringan WiFi di sekitar", "Device", admin_only=True),
    BotCommandInfo("notify", "Kirim notifikasi ke Android", "Device", admin_only=True, usage="/notify [judul|]isi"),
    BotCommandInfo("telephony", "Cek info telepon & device", "Device", admin_only=True),
    BotCommandInfo("sensor", "Daftar sensor yang tersedia", "Device", admin_only=True),
    BotCommandInfo("sms_send", "Kirim SMS dari device", "Device", admin_only=True, usage="/sms_send <nomor> <pesan>"),
    BotCommandInfo("play", "Putar audio dari URL di device", "Device", admin_only=True, usage="/play <url>"),
    BotCommandInfo("stopplay", "Hentikan putaran audio", "Device", admin_only=True),
]

def get_commands_by_category():
    """Groups commands for generating help text."""
    categories = {}
    for cmd in COMMAND_REGISTRY:
        if cmd.category not in categories:
            categories[cmd.category] = []
        categories[cmd.category].append(cmd)
    return categories
