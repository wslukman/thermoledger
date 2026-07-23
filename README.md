# 🌡️ THERMOLEDGER: Physics-as-Computation Blockchain

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-green.svg)](https://fastapi.tiangolo.com/)
[![SQLite](https://img.shields.io/badge/SQLite-3-blue.svg)](https://www.sqlite.org/)
[![License](https://img.shields.io/badge/License-MIT-purple.svg)](LICENSE)

**Thermoledger** adalah paradigma baru dalam teknologi buku besar terdesentralisasi (*decentralized ledger*) yang meninggalkan komputasi digital biner tradisional yang kaku dan boros energi. Protokol ini menggunakan arsitektur **Physics-as-Computation (Termodinamika)**, di mana validasi konsensus dan perpindahan nilai diatur secara langsung oleh kesetimbangan hukum fisika alami.

Jaringan ini berjalan dengan efisiensi energi hingga **99% lebih hemat dibandingkan Ethereum Virtual Machine (EVM)** karena kompresi transaksinya didasarkan pada minimalisasi magnetic friction.

---

## 🔬 Core Concepts (Konsep Utama)

1.  **State Energy Proof (SEP) - L1 Consensus**:
    Menggantikan balapan hashing Proof of Work (PoW). SEP memetakan validasi blok transaksi ke jalur energi terkecil (*Minimum Energy Path*) dari model **Kisi Spin Magnetik 2D (Ising Lattice)** menuju kesetimbangan ekuilibrium termal global.
2.  **Least Action Principle - L2 Compression**:
    Melalui enkapsulasi Layer 2 (*Local Thermodynamic Ponds*), bot-bot arbitrase bersaing menyusun urutan transaksi agar *magnetic friction* (gesekan termal) minimal. Transaksi yang saling berlawanan dibatalkan secara alami, menekan biaya gas L2 hingga **0.00 Joule (Bebas Biaya)**.
3.  **TTS-20 (Thermoledger Token Standard)**:
    Standar pembuatan token deklaratif di atas Thermoledger. Mendukung pengaturan suplai (mintable/burnable) dan *Friction Burn Rate* transaktif yang secara otomatis membakar pecahan token menjadi energi panas ke alamat mati (`0x000000000000000000000000000000000000DEAD`).
4.  **Self-Healing Failsafe (Cooling-Off)**:
    Validator memantau suhu kisi jaringan secara fisik. Jika aktivitas spam/anomali melonjak di atas $5.0^\circ\text{C}$, sistem secara mandiri membekukan penulisan blok (*Failsafe Safe Mode*) untuk mendinginkan sirkuit dan mencair kembali secara otomatis saat normal.

---

## 📂 Project Structure (Struktur Folder)

```text
thermoledger/
├── main.py                 # FastAPI web server, routing, SSE data streams & Chatbot API
├── test_engine.py          # Unit testing untuk validasi konsensus & database persistence
├── requirements.txt        # Dependensi modul python
├── engine/                 # Inti Mesin Blockchain
│   ├── noise.py            # Simulasi Physical Thermal Noise (One-Time Pad entropy salt)
│   ├── consensus.py        # Algoritma 2D Ising Lattice & State Energy Proof
│   ├── blockchain.py       # Logika L1 Chain, L2 Mempool, dan Arbitrage Bots
│   └── db.py               # Integrasi penyimpanan SQLite (duit_chain.db)
└── static/                 # Portal & Antarmuka Pengembang (Frontend Web UI)
    ├── index.html          # Landing Page Utama (Ethereum.org-style)
    ├── scan.html           # Thermoscan Explorer & Aplikasi Ritel Kasir DuitLap
    ├── docs.html           # Portal Panduan Pengembang (Developer Docs Hub)
    ├── playground.html     # Remix-Style IDE Playground (dengan AI Assistant terintegrasi)
    └── app.js              # Pemrosesan sensor grafis visualisasi kisi & telemetry stream
```

---

## ⚡ Quick Start (Panduan Memulai Cepat)

### 1. Klon Repositori & Instal Dependensi
Pastikan Anda menggunakan Python 3.11 atau versi lebih tinggi.
```bash
git clone https://github.com/universal-digital-property/thermoledger.git
cd thermoledger
pip install -r requirements.txt
```
*Dependensi utama:* `fastapi`, `uvicorn`, `sse-starlette`, `google-genai` (opsional untuk AI assistant).

### 2. Konfigurasi Kunci AI Assistant (Opsional)
Jika ingin menggunakan asisten AI interaktif di dalam IDE Playground:
1. Buat file `.env` di folder utama.
2. Isi dengan API Key Gemini Anda (dapatkan gratis di [Google AI Studio](https://aistudio.google.com/)):
   ```env
   GEMINI_API_KEY=AIzaSyYourKeyHere...
   ```

### 3. Jalankan Node Server
```bash
python main.py
```
Server lokal akan aktif di **`http://127.0.0.1:8000`**.

---

## 🖥️ Antarmuka Portal Pengembang

Setelah server menyala, Anda dapat membuka halaman berikut di browser Anda:
*   **Homepage Utama**: `http://127.0.0.1:8000/` &mdash; Mengenalkan PT Universal Digital Property dan performa statistik jaringan real-time.
*   **Thermoscan Explorer & Kasir**: `http://127.0.0.1:8000/scan` &mdash; Eksplorasi transaksi di database SQLite secara real-time dan demo transaksi kasir tap-to-pay ritel.
*   **Developer Portal**: `http://127.0.0.1:8000/docs` &mdash; Spesifikasi lengkap client SDK Dart, API Node, dan parameter keamanan fisik (Threat Model).
*   **Remix IDE Playground**: `http://127.0.0.1:8000/playground` &mdash; Tampilan multi-pane IDE untuk menulis skrip kontrak TTS-20, menguji kompilasi, deploy ke VM, dan mengobrol dengan asisten AI.

---

## ⚙️ Core Node APIs

### 1. `POST /api/v1/transaction/prepare`
Menyiapkan draf transaksi dengan menangkap parameter keacakan salt entropi terupdate.

### 2. `POST /api/v1/transaction/commit`
Mengirimkan bukti energi *Signed Energy Proof* (SEP) hasil tanda tangan kartu fisik NFC/hardwallet untuk dimasukkan ke blok L1.

### 3. `POST /api/v1/faucet`
Mengirimkan `10 $DUIT` gratis dari rekening treasury kas negara (`0x01a2b3`) ke dompet target pengembang untuk kebutuhan pengujian saldo.

### 4. `POST /api/v1/chat`
Mengirimkan pertanyaan seputar ekosistem Thermoledger ke asisten AI yang didukung model **Gemini 3.5 Flash**.

---

## 📄 License
Proyek ini dilisensikan di bawah **MIT License** &mdash; Hak Cipta &copy; 2026 PT Universal Digital Property.
