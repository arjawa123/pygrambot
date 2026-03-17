# Pygram - Advanced AI Telegram Assistant

Pygram adalah asisten AI modular yang menggabungkan kekuatan Groq/OpenRouter dengan memori persisten, manajemen file, ekstraksi konten web, dan sistem logging profesional.

## ✨ Fitur Unggulan

- **🧠 Persistent Memory**: Bot bisa mengingat fakta atau preferensi Anda melalui command `/remember`.
- **🌐 Web Reader**: Ekstraksi konten teks dari URL secara langsung menggunakan `/web <url>`.
- **📁 Advanced File Management**: Unggah, daftar (`/files`), dan hapus file dokumen secara individu atau massal.
- **🤖 Multi-Provider LLM**: Menggunakan Groq sebagai provider utama dengan fallback otomatis ke OpenRouter.
- **📱 Termux Optimized**: Berjalan mulus di Android via Termux dengan deteksi host yang cerdas.
- **🎨 Colored Logging**: Log terminal berwarna untuk debugging yang lebih mudah di environment CLI.
- **📜 Remote Logs**: Cek log bot langsung dari Telegram via command `/logs` (Admin Only).
- **🖥️ Host Information**: Pantau kondisi server/device tempat bot berjalan via `/hostinfo`.

## 📜 Daftar Command Admin & System

| Command | Deskripsi |
| --- | --- |
| `/hostinfo` | Info detail host/device (Termux aware) |
| `/logs` | Melihat 30 baris log terbaru |
| `/exec <cmd>` | Eksekusi CLI command (Admin Only) |
| `/logs <n>` | Melihat N baris log terakhir (contoh: `/logs 50`) |
| `/logs <level>` | Filter log berdasarkan level (contoh: `/logs error`) |
| `/stats` | Statistik penggunaan pesan, file, dan memori |
| `/model` | Info engine AI dan provider aktif |

## 🚀 Instalasi di Termux

1. **Persiapan Environment:**
   ```bash
   pkg update && pkg upgrade
   pkg install python git
   ```

2. **Clone & Install Dependencies:**
   ```bash
   git clone <repository_url>
   cd pygram
   pip install -r requirements.txt
   ```

3. **Konfigurasi:**
   Salin `.env.example` ke `.env` dan isi token serta API keys.

4. **Jalankan Bot:**
   ```bash
   python bot.py
   ```

## ⚙️ Logging Configuration (Environment)

Anda bisa mengatur perilaku logging melalui file `.env`:
- `LOG_LEVEL`: Default `INFO` (DEBUG, INFO, WARNING, ERROR)
- `LOG_FILE_PATH`: Jalur penyimpanan file log (Default: `logs/bot.log`)
- `LOG_TO_STDOUT`: Tampilkan log di terminal (Default: `true`)

## 🛡️ Keamanan
Akses ke command system seperti `/logs` dan `/hostinfo` dibatasi hanya untuk user ID yang terdaftar di `ALLOWED_USER_IDS` pada file `.env`.
