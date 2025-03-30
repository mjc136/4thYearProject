from backend.flask_app.flask_app import app
from backend.models import db

with app.app_context():
    db.create_all()
    print("Database created.")
