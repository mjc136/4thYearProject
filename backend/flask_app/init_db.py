from backend.common.extensions import bcrypt
from backend.models import db, User
from backend.flask_app.flask_app import app

with app.app_context():
    db.create_all()

    if not User.query.filter_by(username="adminb").first():
        admin_user = User(
            username="admin",
            password=bcrypt.generate_password_hash("adminpass").decode('utf-8'),
            language="english",
            proficiency="beginner",
            xp=0,
            level=1,
            admin=True
        )
        db.session.add(admin_user)

    if not User.query.filter_by(username="testuser").first():
        regular_user = User(
            username="testuser",
            password=bcrypt.generate_password_hash("testpass").decode('utf-8'),
            language="spanish",
            proficiency="beginner",
            xp=0,
            level=1,
            admin=False
        )
        db.session.add(regular_user)

    db.session.commit()
    print("Database created with default users.")
