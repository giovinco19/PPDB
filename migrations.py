from flask_migrate import Migrate
from app import app, db

migrate = Migrate(app, db)

if __name__ == '__main__':
    with app.app_context():
        # Create initial admin user
        from models import User
        from werkzeug.security import generate_password_hash
        
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(
                username='admin',
                password=generate_password_hash('admin123'),
                nama_lengkap='Administrator',
                no_hp='0',
                alamat='Admin Address',
                role='admin'
            )
            db.session.add(admin)
            db.session.commit()
            print("✅ Admin user created successfully")
