from app import app
from models import db

with app.app_context():
    db.create_all()
    print("✅ Semua tabel berhasil dibuat.")

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')  # Fixed the host parameter
