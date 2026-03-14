"""
Модель пользователя
"""

from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db
from datetime import datetime


class User(UserMixin, db.Model):
    """Модель пользователя"""
    
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    first_name = db.Column(db.String(50), nullable=False)
    last_name = db.Column(db.String(50), nullable=False)
    phone = db.Column(db.String(20))
    role = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships - используем уникальные имена для backref
    tutor_profile = db.relationship('Tutor', back_populates='user', uselist=False, cascade='all, delete-orphan')
    student_bookings = db.relationship('Booking', foreign_keys='Booking.student_id', back_populates='student', lazy='dynamic')
    uploaded_materials = db.relationship('LessonMaterial', back_populates='uploader', lazy='dynamic')
    authored_notes = db.relationship('LessonNote', back_populates='author', lazy='dynamic')
    chat_messages = db.relationship('ChatMessage', back_populates='user', lazy='dynamic')
    reviews_given = db.relationship('Review', foreign_keys='Review.student_id', back_populates='student', lazy='dynamic')
    payments_made = db.relationship('Payment', foreign_keys='Payment.student_id', back_populates='student', lazy='dynamic')
    admin_logs = db.relationship('AdminLog', back_populates='admin', lazy='dynamic')
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}"
    
    @property
    def initials(self):
        return f"{self.first_name[0]}{self.last_name[0]}"