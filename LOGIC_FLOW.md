# Dokumentasi Logika & Alur Proyek Pygram

Dokumen ini menjelaskan arsitektur, alur data, dan logika operasional dari proyek Pygram untuk memandu rencana pengembangan selanjutnya.

## 🏗️ Arsitektur Sistem

Pygram terdiri dari dua komponen utama yang berjalan secara independen namun berbagi ekosistem file yang sama:
1.  **Telegram AI Bot (`bot.py`)**: Bot asinkron yang terhubung ke Groq API dan menggunakan SQLite untuk persistensi.
2.  **CLI Notes (`notes.py`)**: Aplikasi terminal sederhana untuk manajemen catatan berbasis teks.

---

## 🤖 Alur Logika Telegram Bot (`bot.py`)

### 1. Inisialisasi & Konfigurasi
- **Loading Environment**: Membaca `.env` untuk API Keys dan parameter konfigurasi.
- **Database Setup**: Menjalankan `init_db()` untuk memastikan tabel `messages` dan `files` tersedia di SQLite dengan mode `WAL` (Write-Ahead Logging) untuk performa konkuren.
- **Client Setup**: Inisialisasi `httpx.AsyncClient` dengan base URL Groq API.

### 2. Siklus Penanganan Pesan (Message Handling)
Setiap pesan yang masuk melalui Telegram melewati alur berikut:

1.  **Penerimaan**: Bot menerima `Update` dari Telegram.
2.  **Filter Keamanan**: Memeriksa apakah `user_id` diizinkan (jika `ALLOWED_USER_IDS` dikonfigurasi).
3.  **Persistensi Pesan**: Pesan user disimpan ke tabel `messages` via `db_add_message()`.
4.  **Pengambilan Konteks**:
    - Mengambil $N$ riwayat pesan terakhir dari database.
    - Mengambil konteks dari 3 file terakhir yang diunggah di chat tersebut.
5.  **Permintaan LLM (`ask_llm`)**:
    - Menyusun prompt sistem + konteks file + riwayat chat + pesan baru.
    - Mengirim ke Groq API dengan mekanisme *retry* (`tenacity`) jika gagal.
6.  **Penyimpanan Respon**: Jawaban dari AI disimpan kembali ke database sebagai role `assistant`.
7.  **Pengiriman**: Mengirimkan respon ke user, dipecah menjadi beberapa bagian jika melebihi batas karakter Telegram.

### 3. Penanganan File & Dokumen
- **Download**: File diunduh ke direktori lokal `bot_files/`.
- **Ekstraksi Teks**: Mendukung `.txt`, `.md`, `.py`, `.json`, `.csv`, dll.
- **Metadata**: Menyimpan nama file, path lokal, dan hasil ekstraksi teks ke tabel `files`.
- **Konteks AI**: Hasil ekstraksi dikirimkan ke AI sebagai bagian dari `system prompt` agar AI bisa "membaca" isi file tersebut.

### 4. Database Schema
- **`messages`**: `id`, `chat_id`, `user_id`, `role` (system/user/assistant), `content`, `created_at`.
- **`files`**: `id`, `chat_id`, `user_id`, `file_name`, `local_path`, `extracted_text`, `note`, `created_at`.

---

## 🛠️ Rencana Pengembangan Lanjutan (Development Plan)

### Fase 1: Integrasi Komponen
- [ ] **Sinkronisasi Catatan**: Hubungkan `notes.py` dengan database `bot.db` agar catatan CLI juga bisa diakses via Telegram Bot dan sebaliknya.
- [ ] **Global Search**: Fitur pencarian pesan dan file di seluruh riwayat chat.

### Fase 2: Peningkatan Kemampuan AI
- [ ] **RAG (Retrieval-Augmented Generation)**: Alih-alih hanya 3 file terakhir, gunakan pencarian vektor (vector search) untuk mengambil konteks file yang paling relevan.
- [ ] **Python Interpreter**: Implementasi penuh fitur `/py` untuk mengeksekusi kode Python secara aman di lingkungan terisolasi.

### Fase 3: UI/UX & Manajemen
- [ ] **Web Dashboard**: Interface berbasis Next.js untuk melihat riwayat chat dan file di browser.
- [ ] **Multi-Model Support**: Pilihan untuk berganti model AI (misal: Llama 3, Mixtral) secara dinamis via perintah bot.

---

## ⚠️ Catatan Teknis Penting
- **Konkurensi**: Gunakan `asyncio.Semaphore` untuk membatasi jumlah permintaan API simultan guna menghindari *rate limiting*.
- **Keamanan**: Pastikan file database (`bot.db`) dan folder `bot_files` masuk ke `.gitignore`.
