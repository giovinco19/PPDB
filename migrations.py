from flask_migrate import Migrate
from app import app, db
from models import User
from werkzeug.security import generate_password_hash

migrate = Migrate(app, db)

def init_db():
    with app.app_context():
        # Create all tables
        db.drop_all()  # Drop existing tables
        db.create_all()  # Create new tables with updated schema
        
        # Create admin user with proper role
        admin = User(
            username='admin',
            password=generate_password_hash('admin123'),
            nama_lengkap='Administrator',
            no_hp='0',
            alamat='Admin Address',
            email='admin@admin.com',
            role='admin'  # Pastikan role adalah 'admin'
        )
        
        try:
            db.session.add(admin)
            db.session.commit()
            print("✅ Database initialized with admin user")
            print("Username: admin")
            print("Password: admin123")
        except Exception as e:
            print(f"❌ Error creating admin: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    init_db()
