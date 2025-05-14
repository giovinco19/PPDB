import os
from flask import Flask, render_template, redirect, url_for, request, flash, send_from_directory
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User, Pendaftaran
from functools import wraps
from flask_migrate import Migrate
from datetime import datetime

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
    return render_template('home.html', show_admin=True)

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
                progress=50  # Set initial progress to 50%
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
    pendaftaran.status_pendaftaran = 'diterima'
    update_progress(pendaftaran)  # This will add 25%
    db.session.commit()
    flash('Pendaftaran diterima.')
    return redirect(url_for('admin_dashboard'))

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
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('admin_dashboard'))
        return redirect(url_for('dashboard'))

    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        if not username or not password:
            flash('Harap isi username dan password')
            return redirect(url_for('admin_login'))

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

@app.route('/admin/verify_payment/<int:id>/<status>')
@login_required
@admin_required
def verify_payment(id, status):
    pendaftaran = Pendaftaran.query.get_or_404(id)
    old_status = pendaftaran.status_pembayaran
    pendaftaran.status_pembayaran = status
    
    # Update progress based on new status
    if status == 'diterima':
        if old_status != 'diterima':  # Only add progress if it wasn't already approved
            pendaftaran.progress += 25
    elif old_status == 'diterima':  # If removing approval
        pendaftaran.progress -= 25
            
    db.session.commit()
    flash(f'Status pembayaran diubah menjadi {status}')
    return redirect(url_for('detail_pendaftaran', id=id))
