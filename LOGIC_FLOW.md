# Pygram Logic Flow

Dokumen ini menjelaskan alur kerja internal Pygram AI Assistant.

## 1. Message Handling Flow
Setiap pesan teks dari user diproses melalui `ChatHandler.handle_message`:

1.  **Ingestion**: Pesan simpan ke database `messages`.
2.  **Context Building**:
    *   **Memory**: Mengambil fakta dari tabel `memories`.
    *   **Web**: Mengambil konten URL terbaru dari `context.chat_data` (jika ada).
    *   **Files**: Mengambil 2 file teks terbaru yang diunggah dari tabel `files`.
    *   **History**: Mengambil N pesan terakhir dari tabel `messages`.
3.  **Prompt Construction**: Menggabungkan `SYSTEM_PROMPT` dengan semua konteks di atas menjadi satu instruksi terstruktur untuk LLM.
4.  **LLM Execution**: Mengirim ke `LLMManager` yang mencoba Primary Provider (Groq) lalu Fallback (OpenRouter) jika terjadi rate limit.
5.  **Response**: Jawaban AI disimpan ke database dan dikirim ke user (dipecah jika terlalu panjang).

## 2. File Processing Flow
Saat user mengirim dokumen (`FileHandler.handle_document`):

1.  **Sanitization**: Nama file dibersihkan.
2.  **Storage**: File diunduh ke `bot_files/<chat_id>/`.
3.  **Extraction**: `FileService` mengekstrak teks (mendukung .txt, .md, .py, .csv, dll).
4.  **Indexing**: Metadata file dan teks yang diekstrak disimpan ke database `files`.

## 3. Web Scraping Flow (`/web <url>`)
1.  **Validation**: Memastikan URL valid.
2.  **Fetching**: Mengunduh HTML menggunakan `httpx`.
3.  **Parsing**: Menggunakan regex untuk mengekstrak Title dan membersihkan boilerplate (nav, footer, script).
4.  **Session Storage**: Konten disimpan di `chat_data` agar bisa ditanyakan langsung oleh user tanpa perlu upload file.

## 4. Security & Permissions
*   Command sensitif (`/logs`, `/exec`, `/hostinfo`) dilindungi oleh decorator `@admin_only`.
*   Hanya user ID yang terdaftar di `ALLOWED_USER_IDS` (.env) yang dapat mengeksekusi command tersebut.

## 5. LLM Fallback Mechanism
`LLMManager` mengatur failover otomatis:
*   **Primary**: Default Groq (Cepat).
*   **Fallback**: OpenRouter (Reliable/Gratis).
*   Jika Primary terkena `429 Rate Limit`, bot otomatis berpindah ke Fallback untuk request tersebut.
