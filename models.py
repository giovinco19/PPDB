from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from datetime import datetime

db = SQLAlchemy()

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True)
    password = db.Column(db.String(100))
    nama_lengkap = db.Column(db.String(100))
    no_hp = db.Column(db.String(20))
    alamat = db.Column(db.Text)
    role = db.Column(db.String(20), default='user')  # 'admin' or 'user'
    email = db.Column(db.String(120), unique=True)
    pendaftaran = db.relationship('Pendaftaran', backref='user', uselist=False)

    def is_admin(self):
        return self.role == 'admin'

class Pendaftaran(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    nama_lengkap = db.Column(db.String(100))
    asal_sekolah = db.Column(db.String(100))
    nama_ortu = db.Column(db.String(100))
    alamat = db.Column(db.Text)
    tempat_lahir = db.Column(db.String(100))
    tanggal_lahir = db.Column(db.String(10))
    jenis_kelamin = db.Column(db.String(10))
    tahun_lulus = db.Column(db.String(4))
    jurusan = db.Column(db.String(100))
    waktu_kuliah = db.Column(db.String(50))
    gelombang = db.Column(db.String(20))
    status_pendaftaran = db.Column(db.String(20), default='pending')
    status_pembayaran = db.Column(db.String(20), default='belum')
    progress = db.Column(db.Integer, default=50)  # Start at 50% when form submitted
    foto = db.Column(db.String(100))
    ijazah = db.Column(db.String(100))
    bukti_pembayaran = db.Column(db.String(100))
    status_pembayaran = db.Column(db.String(20), default='belum')  # belum/pending/diterima/ditolak
    tanggal_pembayaran = db.Column(db.DateTime)
    notification_shown = db.Column(db.Boolean, default=False)
    payment_notification_shown = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    agama = db.Column(db.String(20))  # Tambahkan kolom agama

class JadwalPendaftaran(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    gelombang = db.Column(db.String(50))
    tanggal_mulai = db.Column(db.Date)
    tanggal_selesai = db.Column(db.Date)
    tanggal_pengumuman = db.Column(db.Date)
    status = db.Column(db.String(20), default='upcoming')  # 'active' atau 'upcoming'
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, onupdate=datetime.utcnow)
