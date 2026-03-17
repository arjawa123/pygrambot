# Pygram - Advanced AI Telegram Assistant

Pygram adalah asisten AI modular yang menggabungkan kekuatan Groq/OpenRouter dengan memori persisten, manajemen file, dan ekstraksi konten web.

## ✨ Fitur Unggulan

- **🧠 Persistent Memory**: Bot bisa mengingat fakta atau preferensi Anda melalui command `/remember`.
- **🌐 Web Reader**: Ekstraksi konten teks dari URL secara langsung menggunakan `/web <url>`.
- **📁 Advanced File Management**: Unggah, daftar (`/files`), dan hapus file dokumen secara individu atau massal.
- **🤖 Multi-Provider LLM**: Menggunakan Groq sebagai provider utama dengan fallback otomatis ke OpenRouter.
- **🖥️ Host Information**: Pantau kondisi server tempat bot berjalan via `/hostinfo`.
- **📊 Chat Statistics**: Lihat statistik pesan, file, dan memori per chat.

## 📜 Daftar Command

| Command | Deskripsi |
| --- | --- |
| `/start` | Memulai bot dan melihat salam pembuka |
| `/help` | Menampilkan daftar bantuan lengkap |
| `/remember <teks>` | Menyimpan fakta penting ke memori jangka panjang |
| `/memories` | Melihat daftar memori yang tersimpan di chat ini |
| `/forget <id>` | Menghapus memori berdasarkan ID |
| `/web <url>` | Membaca konten dari sebuah website |
| `/files` | Melihat daftar file dokumen yang sudah diunggah |
| `/deletefile <id>` | Menghapus file tertentu berdasarkan ID |
| `/clearfiles` | Menghapus semua file di chat ini |
| `/reset` | Menghapus riwayat percakapan chat (History saja) |
| `/stats` | Melihat statistik penggunaan (Pesan, File, Memori) |
| `/model` | Melihat model AI dan provider yang aktif |
| `/ping` | Mengecek status koneksi bot |
| `/hostinfo` | Melihat informasi sistem server (Admin Only) |

## 🚀 Instalasi & Penggunaan

1. **Install Dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Konfigurasi Environment:**
   Salin `.env.example` menjadi `.env` dan isi API Key Anda.

3. **Jalankan Bot:**
   ```bash
   python bot.py
   ```

## 🛡️ Keamanan
Jangan pernah membagikan file `.env` atau mengunggahnya ke kontrol versi publik karena mengandung kunci API sensitif.
