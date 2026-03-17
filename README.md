# Pygram - Advanced AI Telegram Assistant

Pygram adalah asisten AI modular yang menggabungkan kekuatan Groq/OpenRouter dengan memori persisten, manajemen file, ekstraksi konten web, dan sistem logging profesional.

## ✨ Fitur Unggulan

- **🧠 Persistent Memory**: Bot bisa mengingat fakta atau preferensi Anda melalui command `/remember`.
- **🔍 Smart File Search (RAG)**: Mencari informasi secara cerdas di seluruh file dokumen yang pernah diunggah.
- **⏰ Scheduler & Reminders**: Atur pengingat waktu agar bot mengirim pesan di waktu tertentu via `/remindme`.
- **🌍 Free Web Search**: Cari berita atau info terbaru di internet secara gratis via `/search`.
- **🌐 Web Reader**: Ekstraksi konten teks dari URL secara langsung menggunakan `/web <url>`.
- **📁 Advanced File Management**: Unggah, daftar (`/files`), dan hapus file dokumen secara individu atau massal.
- **🤖 Multi-Provider LLM**: Menggunakan Groq sebagai provider utama dengan fallback otomatis ke OpenRouter.
- **📱 Termux Optimized**: Berjalan mulus di Android via Termux dengan deteksi host yang cerdas.
- **🐍 Python Interpreter**: Eksekusi kode Python langsung (Admin Only) via `/py`.
- **📜 Remote Logs**: Cek log bot langsung dari Telegram via command `/logs` (Admin Only).
- **🖥️ Host Information**: Pantau kondisi server/device via `/hostinfo`.

## 📜 Daftar Command Utama

| Command | Deskripsi | Kategori |
| --- | --- | --- |
| `/search <query>` | Cari informasi terbaru di internet | General |
| `/remindme <menit> <msg>` | Set pengingat waktu (contoh: `/remindme 5 beli kopi`) | General |
| `/py <code>` | Jalankan kode Python (Admin Only) | General |
| `/setmodel` | Ubah provider AI utama secara real-time (Admin Only) | General |
| `/remember <teks>` | Simpan fakta baru ke memori permanen | Memory |
| `/memories` | Lihat semua daftar memori tersimpan | Memory |
| `/web <url>` | Baca isi konten dari sebuah website | Web |
| `/files` | Lihat daftar file yang pernah di-upload | Files |
| `/hostinfo` | Info detail host/device (CPU, RAM, Storage) | System |
| `/logs` | Menu interaktif untuk melihat log bot | System |
| `/exec <cmd>` | Eksekusi CLI command di host (Admin Only) | System |
| `/stats` | Statistik penggunaan pesan, file, dan memori | General |
| `/model` | Info engine AI dan provider yang sedang aktif | General |

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
