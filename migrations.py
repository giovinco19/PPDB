from flask_migrate import Migrate
from app import app, db
from models import User
from werkzeug.security import generate_password_hash
from datetime import datetime

migrate = Migrate(app, db)

def init_db():
    with app.app_context():
        print("Creating tables...")
        db.create_all()
        
        print("Creating admin user...")
        # Check if admin exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                password=generate_password_hash('admin123'),
                nama_lengkap='Administrator',
                no_hp='0',
                alamat='Admin Address',
                email='admin@admin.com',  # Tambahkan email karena required
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin created successfully!")
            print("Username: admin")
            print("Password: admin123")
        else:
            print("Admin user already exists")

if __name__ == '__main__':
    init_db()
