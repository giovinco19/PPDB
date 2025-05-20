from app import app
from models import db
from flask_migrate import Migrate

migrate = Migrate(app, db)

with app.app_context():
    db.create_all()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0')
