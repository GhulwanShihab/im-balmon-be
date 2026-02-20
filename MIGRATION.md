# Panduan Migrasi Database (IM-Balmon)

Dokumen ini menjelaskan langkah-langkah untuk memindahkan (migrasi) seluruh data dari database lama (`im-balmon`) ke database baru (`imbalmon`).

## Prasyarat

Pastikan Anda berada di direktori `backend` dan environment Python sudah aktif.

```bash
cd backend
```

## Langkah 1: Export Data Lama

Gunakan script `export_roles_old.py` (untuk role) dan `export_current_db.py` (untuk data lainnya) untuk mengambil data dari database lama.

_Catatan: Script ini didesain untuk mengambil data dari database lama meskipun file `.env` sudah menunjuk ke database baru, karena script `export_roles_old.py` menggunakan koneksi manual ke `im-balmon`._

```bash
# Export Roles & User Roles (dari DB lama)
python scripts/export_roles_old.py

# Export Data Lainnya (pastikan .env menunjuk ke DB yang benar jika ingin full export ulang,
# atau gunakan file data_backup.json yang sudah ada jika hanya ingin import)
python scripts/export_current_db.py
```

Hasil export akan disimpan di file `data_backup.json`.

## Langkah 2: Persiapkan Database Baru

Pastikan file `backend/.env` sudah dikonfigurasi ke database baru:

```env
POSTGRES_DB=imbalmon
POSTGRES_SERVER=127.0.0.1
POSTGRES_USER=postgres
POSTGRES_PASSWORD=password
```

Lalu jalankan script untuk membuat struktur tabel (schema):

```bash
python scripts/create_schema_and_stamp.py
```

## Langkah 3: Import Data ke Database Baru

Jalankan script import yang sudah disatukan (termasuk users, roles, devices, loans, dll):

```bash
python scripts/import_new_db.py
```

Script ini akan:

1. Membaca `data_backup.json`.
2. Mengisi tabel User, Role, UserRole.
3. Mengisi tabel data master (Locations, Employees, Devices).
4. Mengisi tabel transaksi (Loans, History) dengan penanganan error otomatis (misal: data orphan).
5. Mereset sequence ID agar auto-increment berjalan normal.

## Langkah 4: Verifikasi

Jalankan script verifikasi untuk memastikan jumlah baris data sama antara file backup dan database baru:

```bash
python scripts/verify_migration.py
```

Jika semua checklist ✅ (hijau), migrasi berhasil.

---

**Troubleshooting:**

- **Error Import Role**: Jika role tidak masuk, pastikan `data_backup.json` memiliki key `"roles"` dan `"user_roles"`. Jika tidak, jalankan langkah export lagi.
- **Aplikasi Error**: Pastikan Anda me-restart backend (`uvicorn`) setelah migrasi selesai agar koneksi database diperbarui.
