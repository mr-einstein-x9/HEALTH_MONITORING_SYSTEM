# =============================================================================
# models.py — SQLAlchemy ORM Models
# Tables: users, daily_logs, alerts
# =============================================================================

from datetime import date, datetime
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


class User(db.Model):
    """Registered user account."""
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    logs = db.relationship('DailyLog', backref='user', lazy=True,
                           cascade='all, delete-orphan')
    alerts = db.relationship('Alert', backref='user', lazy=True,
                             cascade='all, delete-orphan')


class DailyLog(db.Model):
    """One row per user per day of health data."""
    __tablename__ = 'daily_logs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    date = db.Column(db.Date, nullable=False, default=date.today)
    steps = db.Column(db.Integer, default=0)
    sleep_hours = db.Column(db.Float, default=0.0)
    bp_systolic = db.Column(db.Integer, default=120)
    bp_diastolic = db.Column(db.Integer, default=80)
    heart_rate = db.Column(db.Integer, default=72)
    weight = db.Column(db.Float, default=0.0)
    water_intake = db.Column(db.Float, default=0.0)   # litres
    score = db.Column(db.Integer, default=0)

    __table_args__ = (
        db.UniqueConstraint('user_id', 'date', name='uq_user_date'),
    )


class Alert(db.Model):
    """Health alert tied to a user."""
    __tablename__ = 'alerts'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.String(300), nullable=False)
    severity = db.Column(db.String(20), nullable=False)   # 'warning' | 'critical'
    date = db.Column(db.Date, default=date.today)
    is_read = db.Column(db.Boolean, default=False)
