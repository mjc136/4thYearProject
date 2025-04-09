from common.extensions import db


class User(db.Model):
    __tablename__ = 'user'  # explicitly name the table
    __table_args__ = {'extend_existing': True}  # allow redefinition if needed

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    language = db.Column(db.String(10), nullable=False)
    proficiency = db.Column(db.String(20), nullable=False)
    xp = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    streak = db.Column(db.Integer, default=0)
    last_login = db.Column(db.DateTime, nullable=True)
    admin = db.Column(db.Boolean, default=False)
