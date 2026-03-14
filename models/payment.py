"""
Модель платежей
"""

from . import db
from datetime import datetime


class Payment(db.Model):
    """Модель платежа"""
    
    __tablename__ = 'payments'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False, unique=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tutor_id = db.Column(db.Integer, db.ForeignKey('tutors.id'), nullable=False)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.String(20), default='pending')
    payment_method = db.Column(db.String(50))
    transaction_id = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    paid_at = db.Column(db.DateTime)
    
    # Relationships
    student = db.relationship('User', foreign_keys=[student_id], back_populates='payments_made')
    tutor = db.relationship('Tutor', foreign_keys=[tutor_id], back_populates='payments')
    booking = db.relationship('Booking', back_populates='payment')