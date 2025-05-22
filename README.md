# Sistem Informasi PPDB SMK KARYA BANGSA

Sistem Informasi Penerimaan Peserta Didik Baru (PPDB) SMK KARYA BANGSA berbasis web menggunakan Flask Python.

## Screenshots

### Homepage - Hero Section
![Homepage Hero](static/img/jurusan/Screenshot%202025-05-22%20104037.png)

### Homepage - Program Jurusan 
![Homepage Programs](static/img/Screenshot%202025-05-22%20104945.png)

### Homepage - Features Section
![Homepage Features](static/img/Screenshot%202025-05-22%20105028.png)

### Homepage - Jadwal Section
![Homepage Schedule](static/img/Screenshot%202025-05-22%20105052.png)

### Homepage - CTA Section
![Homepage CTA](static/img/Screenshot%202025-05-22%20105105.png)

## Fitur

### User (Calon Siswa)
- Register dan Login
- Form pendaftaran dengan upload dokumen
- Dashboard siswa dengan status pendaftaran
- Upload bukti pembayaran
- Progress tracking pendaftaran
- Detail informasi jurusan (TKJ, Multimedia, Teknik Mesin)

### Admin
- Login admin
- Dashboard admin
- Manajemen data pendaftaran
- Verifikasi pendaftaran
- Verifikasi pembayaran 
- Manajemen jadwal PPDB
- Laporan dan statistik pendaftaran

## Teknologi yang Digunakan

- Python Flask
- SQLAlchemy (Database ORM)
- Flask-Login (Autentikasi)
- Flask-Migrate (Database Migration)
- SQLite Database
- HTML/CSS
- JavaScript
- Bootstrap 5
- Font Awesome 5
- DataTables
- SweetAlert2
- Chart.js (untuk visualisasi data)

## Struktur Database

### Tabel Users
- id (Primary Key)
- username
- password (hashed)
- email
- nama_lengkap 
- no_hp
- alamat
- role (admin/user)

### Tabel Pendaftaran
- id (Primary Key)
- user_id (Foreign Key)
- nama_lengkap
- asal_sekolah
- nama_ortu
- alamat
- tempat_lahir
- tanggal_lahir
- jenis_kelamin
- tahun_lulus
- jurusan
- waktu_kuliah
- gelombang
- status_pendaftaran (pending/diterima/ditolak)
- status_pembayaran (belum/pending/diterima/ditolak)
- progress
- foto
- ijazah
- bukti_pembayaran
- created_at
- agama

### Tabel JadwalPendaftaran
- id (Primary Key)
- gelombang
- tanggal_mulai
- tanggal_selesai  
- tanggal_pengumuman
- status (active/upcoming)
- created_at
- updated_at

## Instalasi

1. Clone repository
```bash
git clone https://github.com/username/PPDB-.git
cd PPDB-
```

2. Buat virtual environment
```bash
python -m venv venv
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows
```

3. Install dependencies
```bash
pip install -r requirements.txt
```

4. Setup database dan migrasi
```bash
flask db init
flask db migrate
flask db upgrade
```

5. Jalankan aplikasi
```bash
python run.py
```

6. Buka browser dan akses `http://localhost:5000`

## Struktur Folder

