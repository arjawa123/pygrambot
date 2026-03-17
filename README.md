# Pygram - AI Telegram Bot & Interactive Notes

Pygram adalah proyek Python yang menggabungkan bot Telegram bertenaga AI (menggunakan Groq API). Proyek ini dirancang untuk efisiensi, menggunakan operasi asinkron dan integrasi database SQLite.

## ✨ Fitur Utama

- **AI-Powered Telegram Bot**: Terintegrasi dengan Groq API untuk respons cerdas dan cepat.
- **Asynchronous Processing**: Dibangun dengan `python-telegram-bot` dan `httpx` untuk performa tinggi.
- **Persistent Storage**: Menggunakan `aiosqlite` untuk manajemen database yang non-blocking.
- **File Handling**: Kemampuan untuk menangani file teks dan dokumen melalui bot.
- **Robustness**: Dilengkapi dengan logika *retry* menggunakan `tenacity` untuk menangani gangguan jaringan atau API.

## 🛠️ Prasyarat

Sebelum memulai, pastikan Anda memiliki:
- Python 3.10 atau versi yang lebih baru.
- Token Bot Telegram (didapat dari [@BotFather](https://t.me/botfather)).
- Groq API Key.

## 🚀 Instalasi

1. **Clone repositori ini:**
   ```bash
   git clone <repository-url>
   cd pygram
   ```

2. **Buat virtual environment (opsional tapi disarankan):**
   ```bash
   python -m venv venv
   source venv/bin/activate  # Untuk Linux/macOS
   # atau
   venv\Scripts\activate     # Untuk Windows
   ```

3. **Instal dependensi:**
   ```bash
   pip install -r requirements.txt
   ```

## ⚙️ Konfigurasi

Buat file `.env` di direktori akar dan isi dengan konfigurasi berikut:

```env
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
GROQ_API_KEY=your_groq_api_key
GROQ_MODEL=openai/gpt-oss-20b
BOT_DB_PATH=bot.db
BOT_FILES_DIR=bot_files
MAX_HISTORY_MESSAGES=20
ALLOWED_USER_IDS=12345678,87654321
```

## 📖 Penggunaan

### Menjalankan Bot Telegram
Untuk menjalankan bot, gunakan perintah:
```bash
python bot.py
```

## 📁 Struktur Proyek

- `bot.py`: Logika utama bot Telegram dan integrasi AI.
- `requirements.txt`: Daftar dependensi Python.
- `bot.db`: Database SQLite (dibuat otomatis).
- `bot_files/`: Direktori penyimpanan file yang diunggah.
- `.env`: File konfigurasi sensitif.

## 🛡️ Keamanan
Jangan pernah membagikan file `.env` atau mengunggahnya ke kontrol versi publik karena mengandung kunci API sensitif.
