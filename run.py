from app import app
from models import db

with app.app_context():
    db.create_all()
    print("✅ Semua tabel berhasil dibuat.")

from app import app

if __name__ == '__main__':
    app.run(debug=True)
