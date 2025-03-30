from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    language = db.Column(db.String(10), nullable=False)
    proficiency = db.Column(db.String(20), nullable=False)
    xp = db.Column(db.Integer, default=0)
