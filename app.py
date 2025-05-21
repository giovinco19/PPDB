import os
from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory, jsonify
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User, Pendaftaran, JadwalPendaftaran
from functools import wraps
from flask_migrate import Migrate
from datetime import datetime, timedelta

app = Flask(__name__)
app.secret_key = 'rahasia'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ppdb.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

db.init_app(app)
migrate = Migrate(app, db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or not current_user.is_admin():
            flash('Anda tidak memiliki akses ke halaman ini.')
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/')
def home():
    # Get all jadwal and sort by tanggal_mulai
    jadwals = JadwalPendaftaran.query.order_by(JadwalPendaftaran.tanggal_mulai).all()
    return render_template('home.html', jadwals=jadwals)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Check if email already exists
        if User.query.filter_by(email=request.form['email']).first():
            flash('Email sudah terdaftar!')
            return redirect(url_for('register'))
            
        hashed_pw = generate_password_hash(request.form['password'])
        user = User(
            username=request.form['username'],
            email=request.form['email'],
            password=hashed_pw,
            nama_lengkap=request.form['nama_lengkap'],
            no_hp=request.form['no_hp'],
            alamat=request.form['alamat']
        )
        db.session.add(user)
        db.session.commit()
        flash('Registrasi berhasil. Silakan login.')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(username=request.form['username']).first()
        if user and check_password_hash(user.password, request.form['password']):
            login_user(user)
            if user.is_admin():
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        flash('Username atau password salah.')
    return render_template('login.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('home'))

@app.route('/dashboard')
@login_required
def dashboard():
    pendaftaran = current_user.pendaftaran
    return render_template('user_dashboard.html', pendaftaran=pendaftaran, current_user=current_user)

# Create upload directories if they don't exist
for dir in ['uploads/photos', 'uploads/ijazah', 'uploads/payments']:
    os.makedirs(os.path.join(app.root_path, dir), exist_ok=True)

@app.route('/pendaftaran', methods=['GET', 'POST'])
@login_required
def form_pendaftaran():
    if current_user.pendaftaran:
        flash('Anda sudah mengisi formulir.')
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        try:
            # Handle file uploads
            if 'foto' not in request.files or 'ijazah' not in request.files:
                flash('File foto dan ijazah harus diupload')
                return redirect(request.url)
                
            foto = request.files['foto']
            ijazah = request.files['ijazah']
            
            if foto.filename == '' or ijazah.filename == '':
                flash('File belum dipilih')
                return redirect(request.url)

            if not (allowed_file(foto.filename) and allowed_file(ijazah.filename)):
                flash('Format file tidak diizinkan')
                return redirect(request.url)

            # Save files
            foto_filename = secure_filename(foto.filename)
            ijazah_filename = secure_filename(ijazah.filename)
            
            foto.save(os.path.join(app.root_path, 'uploads/photos', foto_filename))
            ijazah.save(os.path.join(app.root_path, 'uploads/ijazah', ijazah_filename))

            # Create pendaftaran record
            pendaftaran = Pendaftaran(
                user_id=current_user.id,
                nama_lengkap=request.form.get('nama_lengkap'),
                asal_sekolah=request.form.get('asal_sekolah'),
                nama_ortu=request.form.get('nama_ortu'),
                alamat=request.form.get('alamat'),
                tempat_lahir=request.form.get('tempat_lahir'),
                tanggal_lahir=request.form.get('tanggal_lahir'),
                jenis_kelamin=request.form.get('jenis_kelamin'),
                tahun_lulus=request.form.get('tahun_lulus'),
                jurusan=request.form.get('jurusan'),
                waktu_kuliah=request.form.get('waktu_kuliah'),
                gelombang=request.form.get('gelombang'),
                foto=foto_filename,
                ijazah=ijazah_filename,
                status_pendaftaran='pending',
                progress=50,  # Set initial progress to 50%
                agama=request.form.get('agama')  # Tambahkan field agama
            )
            
            db.session.add(pendaftaran)
            db.session.commit()
            
            flash('Formulir berhasil dikirim. Menunggu verifikasi admin.')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            print(f"Error: {str(e)}")  # For debugging
            flash('Terjadi kesalahan saat mengirim formulir')
            return redirect(request.url)
            
    return render_template('form_pendaftaran.html', user=current_user)

@app.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    data = Pendaftaran.query.all()
    return render_template('admin_dashboard.html', data=data)

def update_progress(pendaftaran):
    progress = 0
    
    # Initial form submission
    if pendaftaran.status_pendaftaran:
        progress += 50  # Set to 50% when form is submitted
    
    # After admin verification
    if pendaftaran.status_pendaftaran == 'diterima':
        progress += 25  # Add 25% after admin approves
    
    # After payment verification
    if pendaftaran.status_pembayaran == 'diterima':
        progress += 25  # Add final 25% after payment approval
    
    pendaftaran.progress = progress
    db.session.commit()

@app.route('/admin/approve/<int:id>')
@login_required
@admin_required
def approve(id):
    pendaftaran = Pendaftaran.query.get_or_404(id)
    old_status = pendaftaran.status_pendaftaran
    pendaftaran.status_pendaftaran = 'diterima'
    # Reset notification flag when status changes
    pendaftaran.notification_shown = False
    update_progress(pendaftaran)
    db.session.commit()
    flash('Pendaftaran diterima.')
    return redirect(url_for('admin_dashboard'))

@app.route('/mark_notification_shown/<int:id>')
@login_required
def mark_notification_shown(id):
    pendaftaran = Pendaftaran.query.get_or_404(id)
    if pendaftaran.user_id == current_user.id:
        pendaftaran.notification_shown = True
        db.session.commit()
    return {'status': 'success'}

@app.route('/mark_payment_notification_shown/<int:id>')
@login_required
def mark_payment_notification_shown(id):
    pendaftaran = Pendaftaran.query.get_or_404(id)
    if pendaftaran.user_id == current_user.id:
        pendaftaran.payment_notification_shown = True
        db.session.commit()
    return {'status': 'success'}

@app.route('/admin/reject/<int:id>')
@login_required
@admin_required
def reject(id):
    pendaftaran = Pendaftaran.query.get_or_404(id)
    pendaftaran.status_pendaftaran = 'ditolak'
    db.session.commit()
    flash('Pendaftaran ditolak.')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/detail/<int:id>')
@login_required
@admin_required
def detail_pendaftaran(id):
    pendaftaran = Pendaftaran.query.get_or_404(id)
    return render_template('detail_pendaftaran.html', pendaftaran=pendaftaran)

@app.route('/admin/verifikasi')
@login_required
@admin_required
def verifikasi_user():
    # Get pending applications
    pending_data = Pendaftaran.query.filter_by(status_pendaftaran='pending').all()
    return render_template('verifikasi_user.html', data=pending_data)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.role == 'admin' and check_password_hash(user.password, password):
            login_user(user)
            flash('Login admin berhasil!')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Username atau password admin salah!')
    
    return render_template('admin_login.html')

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/upload_pembayaran/<int:id>', methods=['POST'])
@login_required
def upload_pembayaran(id):
    pendaftaran = Pendaftaran.query.get_or_404(id)
    
    if 'bukti_pembayaran' not in request.files:
        flash('File bukti pembayaran harus diupload')
        return redirect(url_for('dashboard'))
        
    file = request.files['bukti_pembayaran']
    if file.filename == '':
        flash('File belum dipilih')
        return redirect(url_for('dashboard'))

    if not allowed_file(file.filename):
        flash('Format file tidak diizinkan')
        return redirect(url_for('dashboard'))

    try:
        filename = secure_filename(file.filename)
        file.save(os.path.join(app.root_path, 'uploads/payments', filename))
        
        pendaftaran.bukti_pembayaran = filename
        pendaftaran.status_pembayaran = 'pending'
        pendaftaran.tanggal_pembayaran = datetime.now()
        db.session.commit()
        
        flash('Bukti pembayaran berhasil dikirim dan sedang diverifikasi')
        return redirect(url_for('dashboard'))
    except:
        flash('Terjadi kesalahan saat upload bukti pembayaran')
        return redirect(url_for('dashboard'))

@app.route('/admin/verify_payment/<int:id>')
@login_required
@admin_required
def verify_payment(id):
    pendaftaran = Pendaftaran.query.get_or_404(id)
    if pendaftaran.status_pembayaran == 'pending':
        pendaftaran.status_pembayaran = 'diterima'
        pendaftaran.payment_notification_shown = False  # Reset notification flag
        pendaftaran.progress = 100
        db.session.commit()
        flash('Pembayaran telah diverifikasi')
    return redirect(url_for('detail_pendaftaran', id=id))

@app.route('/admin/reports')
@login_required
@admin_required
def admin_reports():
    all_pendaftar = Pendaftaran.query.all()
    total_pendaftar = len(all_pendaftar)

    # Hitung statistik jenis kelamin
    jk_stats = {
        'laki_laki': len([p for p in all_pendaftar if p.jenis_kelamin == 'Laki-laki']),
        'perempuan': len([p for p in all_pendaftar if p.jenis_kelamin == 'Perempuan'])
    }
    
    # Hitung rata-rata umur
    from datetime import datetime
    total_umur = 0
    for p in all_pendaftar:
        if p.tanggal_lahir:
            tgl_lahir = datetime.strptime(p.tanggal_lahir, '%Y-%m-%d')
            umur = datetime.now().year - tgl_lahir.year
            total_umur += umur
    
    avg_umur = round(total_umur / len(all_pendaftar)) if all_pendaftar else 0
    
    # Hitung statistik asal sekolah
    sekolah_count = {}
    for p in all_pendaftar:
        if p.asal_sekolah:
            sekolah_count[p.asal_sekolah] = sekolah_count.get(p.asal_sekolah, 0) + 1
    
    # Hitung statistik alamat dengan persentase
    alamat_count = {}
    for p in all_pendaftar:
        if p.alamat:
            alamat_parts = p.alamat.split(',')
            if len(alamat_parts) > 1:
                kota = alamat_parts[-1].strip()
            else:
                kota = p.alamat
            alamat_count[kota] = alamat_count.get(kota, 0) + 1

    # Hitung persentase untuk setiap alamat
    alamat_stats = {
        'labels': [],
        'data': [],
        'percentages': []
    }
    
    for kota, jumlah in alamat_count.items():
        percentage = round((jumlah / total_pendaftar) * 100, 1) if total_pendaftar > 0 else 0
        alamat_stats['labels'].append(kota)
        alamat_stats['data'].append(jumlah)
        alamat_stats['percentages'].append(percentage)

    # Hitung statistik agama
    agama_count = {}
    for p in all_pendaftar:
        if p.agama:
            agama_count[p.agama] = agama_count.get(p.agama, 0) + 1
    
    # Hitung persentase untuk setiap agama
    agama_stats = {
        'labels': list(agama_count.keys()),
        'data': list(agama_count.values()),
        'percentages': []
    }
    
    for jumlah in agama_count.values():
        percentage = round((jumlah / total_pendaftar) * 100, 1) if total_pendaftar > 0 else 0
        agama_stats['percentages'].append(percentage)

    stats = {
        'total_pendaftar': len(all_pendaftar),
        'diterima': len([p for p in all_pendaftar if p.status_pendaftaran == 'diterima']),
        'pending': len([p for p in all_pendaftar if p.status_pendaftaran == 'pending']),
        'ditolak': len([p for p in all_pendaftar if p.status_pendaftaran == 'ditolak']),
        'jurusan_labels': [],
        'jurusan_data': [],
        'pembayaran_lunas': len([p for p in all_pendaftar if p.status_pembayaran == 'diterima']),
        'pembayaran_pending': len([p for p in all_pendaftar if p.status_pembayaran == 'pending']),
        'pembayaran_belum': len([p for p in all_pendaftar if p.status_pembayaran == 'belum']),
        'total_pembayaran': len([p for p in all_pendaftar if p.status_pembayaran == 'diterima']) * 6000000,
        'persentase_kelulusan': round(len([p for p in all_pendaftar if p.status_pendaftaran == 'diterima']) / len(all_pendaftar) * 100 if all_pendaftar else 0, 1),
        # Tambahkan statistik baru
        'jenis_kelamin': jk_stats,
        'rata_rata_umur': avg_umur,
        'sekolah_stats': {
            'labels': list(sekolah_count.keys()),
            'data': list(sekolah_count.values())
        },
        'alamat_stats': alamat_stats,
        'agama_stats': agama_stats
    }
    
    # Get jurusan distribution
    jurusan_count = {}
    for p in all_pendaftar:
        jurusan_count[p.jurusan] = jurusan_count.get(p.jurusan, 0) + 1
    
    stats['jurusan_labels'] = list(jurusan_count.keys())
    stats['jurusan_data'] = list(jurusan_count.values())
    
    # Get actual registration trends for last 7 days
    
    trend_labels = []
    trend_data = []
    
    # Calculate registrations for each of the last 7 days
    for i in range(6, -1, -1):
        date = datetime.now().date() - timedelta(days=i)
        next_date = date + timedelta(days=1)
        
        # Count registrations for this day
        day_registrations = [p for p in all_pendaftar if p.created_at 
                           and p.created_at.date() == date]
        count = len(day_registrations)
        
        # Add to trend data
        trend_labels.append(date.strftime('%d/%m'))
        trend_data.append(count)

    stats['trend_labels'] = trend_labels
    stats['trend_data'] = trend_data

    return render_template('admin_reports.html', stats=stats)

@app.route('/admin/jadwal')
@login_required
@admin_required
def admin_jadwal():
    jadwals = JadwalPendaftaran.query.order_by(JadwalPendaftaran.tanggal_mulai).all()
    return render_template('admin_jadwal.html', jadwals=jadwals)

@app.route('/admin/jadwal/add', methods=['POST'])
@login_required
@admin_required
def admin_jadwal_add():
    jadwal = JadwalPendaftaran(
        gelombang=request.form['gelombang'],
        tanggal_mulai=datetime.strptime(request.form['tanggal_mulai'], '%Y-%m-%d'),
        tanggal_selesai=datetime.strptime(request.form['tanggal_selesai'], '%Y-%m-%d'),
        tanggal_pengumuman=datetime.strptime(request.form['tanggal_pengumuman'], '%Y-%m-%d')
    )
    db.session.add(jadwal)
    db.session.commit()
    return redirect(url_for('admin_jadwal'))

@app.route('/admin/jadwal/edit/<int:id>', methods=['POST'])
@login_required
@admin_required
def admin_jadwal_edit(id):
    jadwal = JadwalPendaftaran.query.get_or_404(id)
    jadwal.gelombang = request.form['gelombang']
    jadwal.tanggal_mulai = datetime.strptime(request.form['tanggal_mulai'], '%Y-%m-%d')
    jadwal.tanggal_selesai = datetime.strptime(request.form['tanggal_selesai'], '%Y-%m-%d')
    jadwal.tanggal_pengumuman = datetime.strptime(request.form['tanggal_pengumuman'], '%Y-%m-%d')
    db.session.commit()
    return redirect(url_for('admin_jadwal'))

@app.route('/admin/jadwal/get/<int:id>')
@login_required
@admin_required
def admin_jadwal_get(id):
    jadwal = JadwalPendaftaran.query.get_or_404(id)
    return jsonify({
        'gelombang': jadwal.gelombang,
        'tanggal_mulai': jadwal.tanggal_mulai.strftime('%Y-%m-%d'),
        'tanggal_selesai': jadwal.tanggal_selesai.strftime('%Y-%m-%d'),
        'tanggal_pengumuman': jadwal.tanggal_pengumuman.strftime('%Y-%m-%d')
    })

@app.route('/admin/jadwal/toggle/<int:id>', methods=['POST'])
@login_required
@admin_required
def admin_jadwal_toggle(id):
    data = request.get_json()
    jadwal = JadwalPendaftaran.query.get_or_404(id)
    jadwal.status = data['status']
    db.session.commit()
    return jsonify({'success': True})

@app.route('/admin/jadwal/delete/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def admin_jadwal_delete(id):
    jadwal = JadwalPendaftaran.query.get_or_404(id)
    db.session.delete(jadwal)
    db.session.commit()
    return jsonify({'success': True})

@app.route('/jurusan/<string:nama_jurusan>')
def detail_jurusan(nama_jurusan):
    jurusan_data = {
        'tkj': {
            'nama': 'Teknik Komputer & Jaringan',
            'image': 'teknik-komputer.png',
            'deskripsi': 'Program keahlian yang mempelajari tentang pemrograman, jaringan komputer, dan hardware.',
            'keunggulan': [
                'Lab Komputer Modern',
                'Sertifikasi Internasional',
                'Kerjasama dengan Industri IT'
            ],
            'prospek_kerja': [
                'Network Engineer',
                'Software Developer',
                'IT Support Specialist',
                'System Administrator'
            ],
            'fasilitas': [
                'Lab Komputer dengan PC Terbaru',
                'Cisco Networking Academy',
                'Workshop Hardware',
                'Software Development Studio'
            ]
        },
        'multimedia': {
            'nama': 'Multimedia & Desain',
            'image': 'perhotelan.png',
            'deskripsi': 'Program keahlian yang fokus pada pengembangan konten digital dan desain kreatif.',
            'keunggulan': [
                'Studio Multimedia Lengkap',
                'Project Based Learning',
                'Portfolio Development'
            ],
            'prospek_kerja': [
                'Graphic Designer',
                'Video Editor',
                '3D Artist',
                'Content Creator'
            ],
            'fasilitas': [
                'Adobe Creative Suite',
                'Motion Capture Studio',
                'Audio Recording Room',
                'Video Editing Suite'
            ]
        },
        'mesin': {
            'nama': 'Teknik Mesin',
            'image': 'tsm.png',
            'deskripsi': 'Program keahlian yang mempelajari tentang permesinan, pengelasan, dan desain teknik.',
            'keunggulan': [
                'Workshop Berstandar Industri',
                'Praktisi Berpengalaman',
                'Sertifikasi Keahlian'
            ],
            'prospek_kerja': [
                'Teknisi Mesin',
                'Operator CNC',
                'Welder Specialist',
                'CAD Designer'
            ],
            'fasilitas': [
                'CNC Workshop',
                'Welding Laboratory',
                'CAD/CAM Studio',
                'Quality Control Lab'
            ]
        }
    }
    
    jurusan = jurusan_data.get(nama_jurusan.lower())
    if not jurusan:
        return redirect(url_for('home'))
        
    return render_template('detail_jurusan.html', jurusan=jurusan)

@app.route('/admin/delete/<int:id>', methods=['POST'])
@login_required
@admin_required
def delete_pendaftaran(id):
    pendaftaran = Pendaftaran.query.get_or_404(id)
    
    try:
        # Hapus file yang terkait
        if pendaftaran.foto:
            os.remove(os.path.join(app.root_path, 'uploads/photos', pendaftaran.foto))
        if pendaftaran.ijazah:
            os.remove(os.path.join(app.root_path, 'uploads/ijazah', pendaftaran.ijazah))
        if pendaftaran.bukti_pembayaran:
            os.remove(os.path.join(app.root_path, 'uploads/payments', pendaftaran.bukti_pembayaran))
            
        db.session.delete(pendaftaran)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Data berhasil dihapus'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500
