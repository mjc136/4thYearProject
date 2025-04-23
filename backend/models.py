from backend.common.extensions import db
from datetime import datetime, timezone	

class User(db.Model):
    __tablename__ = 'user'  # explicitly name the table
    __table_args__ = {'extend_existing': True}  # allow redefinition if needed

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    language = db.Column(db.String(10), nullable=False)
    xp = db.Column(db.Integer, default=0)
    level = db.Column(db.Integer, default=1)
    streak = db.Column(db.Integer, default=0)
    last_login = db.Column(db.DateTime, nullable=True)
    admin = db.Column(db.Boolean, default=False)
    streak_count = db.Column(db.Integer, default=0)
    highest_streak = db.Column(db.Integer, default=0)
    last_activity_date = db.Column(db.Date, nullable=True)
    
class UserScenarioProgress(db.Model):
    __tablename__ = 'user_scenario_progress'
    __table_args__ = {'extend_existing': True}

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    scenario_name = db.Column(db.String(100), nullable=False)
    completed = db.Column(db.Boolean, default=False)
    score = db.Column(db.Integer, default=0)
    high_score = db.Column(db.Integer, default=0)
    completed_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc))

    user = db.relationship("User", backref=db.backref("scenario_progress", lazy=True))
