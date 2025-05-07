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
    return render_template('home.html')

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
    return render_template('user_dashboard.html', pendaftaran=pendaftaran)

@app.route('/pendaftaran', methods=['GET', 'POST'])
@login_required
def form_pendaftaran():
    if current_user.pendaftaran:
        flash('Anda sudah mengisi formulir.')
        return redirect(url_for('dashboard'))
    if request.method == 'POST':
        asal_sekolah = request.form['asal_sekolah']
        tahun_lulus = request.form['tahun_lulus']
        jurusan = request.form['jurusan']
        waktu_kuliah = request.form['waktu_kuliah']
        gelombang = request.form['gelombang']

        foto = request.files['foto']
        ijazah = request.files['ijazah']

        if not (foto and allowed_file(foto.filename)) or not (ijazah and allowed_file(ijazah.filename)):
            flash('File tidak valid.')
            return redirect(request.url)

        foto_filename = secure_filename(foto.filename)
        ijazah_filename = secure_filename(ijazah.filename)
        foto.save(os.path.join(app.config['UPLOAD_FOLDER'], 'photos', foto_filename))
        ijazah.save(os.path.join(app.config['UPLOAD_FOLDER'], 'ijazah', ijazah_filename))

        pendaftaran = Pendaftaran(
            user_id=current_user.id,
            asal_sekolah=asal_sekolah,
            tahun_lulus=tahun_lulus,
            jurusan=jurusan,
            waktu_kuliah=waktu_kuliah,
            gelombang=gelombang,
            foto=foto_filename,
            ijazah=ijazah_filename
        )
        db.session.add(pendaftaran)
        db.session.commit()
        flash('Formulir berhasil dikirim. Menunggu verifikasi admin.')
        return redirect(url_for('dashboard'))
    return render_template('form_pendaftaran.html')

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/pendaftaran', methods=['POST'])
def pendaftaran():
    if 'foto' not in request.files:
        return 'Tidak ada file foto', 400
    foto = request.files['foto']
    
    if foto and allowed_file(foto.filename):
        foto.save(f'./uploads/{foto.filename}')
        return 'Pendaftaran berhasil!'
    else:
        return 'File foto tidak valid', 400

    


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

@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)
