import os
from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User, Pendaftaran

app = Flask(__name__)
app.secret_key = 'rahasia'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///ppdb.db'
app.config['UPLOAD_FOLDER'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB

db.init_app(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'pdf'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

@app.route('/')
def home():
    return render_template('home.html', show_admin=True)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        hashed_pw = generate_password_hash(request.form['password'])
        user = User(
            username=request.form['username'],
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
            if user.username == 'admin':
                return redirect(url_for('admin_dashboard'))
            return redirect(url_for('dashboard'))
        flash('Username atau password salah.')
    is_admin = current_user.is_authenticated and current_user.username == 'admin'
    return render_template('login.html', is_admin=is_admin)

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
for dir in ['uploads/photos', 'uploads/ijazah']:
    os.makedirs(os.path.join(app.root_path, dir), exist_ok=True)

@app.route('/pendaftaran', methods=['GET', 'POST'])
@login_required
def form_pendaftaran():
    if current_user.pendaftaran:
        flash('Anda sudah mengisi formulir.')
        return redirect(url_for('dashboard'))
        
    if request.method == 'POST':
        # Handle file uploads first
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

        try:
            # Save files with secure filenames
            foto_filename = secure_filename(foto.filename)
            ijazah_filename = secure_filename(ijazah.filename)
            
            foto.save(os.path.join(app.root_path, 'uploads/photos', foto_filename))
            ijazah.save(os.path.join(app.root_path, 'uploads/ijazah', ijazah_filename))

            # Create pendaftaran record
            pendaftaran = Pendaftaran(
                user_id=current_user.id,
                asal_sekolah=request.form['asal_sekolah'],
                tahun_lulus=request.form['tahun_lulus'],
                jurusan=request.form['jurusan'],
                waktu_kuliah=request.form['waktu_kuliah'],
                gelombang=request.form['gelombang'],
                foto=foto_filename,
                ijazah=ijazah_filename
            )
            db.session.add(pendaftaran)
            db.session.commit()
            
            flash('Formulir berhasil dikirim. Menunggu verifikasi admin.')
            return redirect(url_for('dashboard'))
            
        except Exception as e:
            flash('Terjadi kesalahan saat upload file')
            return redirect(request.url)
            
    return render_template('form_pendaftaran.html')

@app.route('/admin/dashboard')
@login_required
def admin_dashboard():
    if current_user.username != 'admin':
        return "Akses ditolak", 403
    data = Pendaftaran.query.all()
    return render_template('admin_dashboard.html', data=data)

@app.route('/admin/approve/<int:id>')
@login_required
def approve(id):
    if current_user.username != 'admin':
        return "Akses ditolak", 403
    pendaftaran = Pendaftaran.query.get_or_404(id)
    pendaftaran.status_pendaftaran = 'diterima'
    db.session.commit()
    flash('Pendaftaran diterima.')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/reject/<int:id>')
@login_required
def reject(id):
    if current_user.username != 'admin':
        return "Akses ditolak", 403
    pendaftaran = Pendaftaran.query.get_or_404(id)
    pendaftaran.status_pendaftaran = 'ditolak'
    db.session.commit()
    flash('Pendaftaran ditolak.')
    return redirect(url_for('admin_dashboard'))

@app.route('/admin/detail/<int:id>')
@login_required
def detail_pendaftaran(id):
    if current_user.username != 'admin':
        return "Akses ditolak", 403
    pendaftaran = Pendaftaran.query.get_or_404(id)
    return render_template('detail_pendaftaran.html', pendaftaran=pendaftaran)

@app.route('/admin/verifikasi')
@login_required
def verifikasi_user():
    if current_user.username != 'admin':
        return "Akses ditolak", 403
    # Get pending applications
    pending_data = Pendaftaran.query.filter_by(status_pendaftaran='pending').all()
    return render_template('verifikasi_user.html', data=pending_data)

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if current_user.is_authenticated and current_user.username == 'admin':
        return redirect(url_for('admin_dashboard'))
        
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        # Ganti dengan kredensial admin yang sesuai
        if username == 'admin' and password == 'admin123':
            user = User.query.filter_by(username='admin').first()
            if not user:
                # Buat user admin jika belum ada
                user = User(
                    username='admin',
                    password=generate_password_hash('admin123'),
                    nama_lengkap='Administrator',
                    no_hp='0',
                    alamat='Admin Address'
                )
                db.session.add(user)
                db.session.commit()
            
            login_user(user)
            flash('Login admin berhasil!')
            return redirect(url_for('admin_dashboard'))
        else:
            flash('Username atau password admin salah!')
            
    return render_template('admin_login.html')

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
