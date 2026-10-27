# 🚀 24/7 Autonomous Fleet Minter (GitHub Actions Edition)

Menjalankan pemanenan akun AI (Dahl 100M tokens, dll.) secara **100% GRATIS 24/7 di cloud GitHub**, bahkan saat laptop dimatikan.

---

## ⚡ Cara Deploy (Hanya Butuh 1 Menit)

1. Buat Repository baru di GitHub (bisa **Public** atau **Private**).
   - *Tips:* Jika menggunakan repo **Public**, kuota GitHub Actions adalah **UNLIMITED (Tanpa batas)**.
2. Unggah seluruh isi folder ini ke repository tersebut:
   - `.github/workflows/harvest_cron.yml`
   - `runner.py`
   - `requirements.txt`
3. Masuk ke tab **Settings** repo -> **Actions** -> **General** -> scroll ke **Workflow permissions**:
   - Pilih: **Read and write permissions** (agar bot bisa auto-commit menyimpan hasil panen).
   - Klik **Save**.
4. Selesai! Bot akan otomatis berjalan setiap 20 menit dan menyimpan akun baru ke file `fleet_keys.jsonl` di dalam repository.

---

## 🔄 Sinkronisasi ke Laptop (9Router)

Kapan saja Anda menyalakan laptop, jalankan skrip sinkronisasi lokal:

```bash
python tools/sync_from_cloud.py --repo "USERNAME/REPO_NAME"
```

Semua akun yang dipanen saat laptop mati akan langsung terinjeksi ke 9Router dalam 1 detik!
