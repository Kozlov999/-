"""
Модель отзывов
"""

from . import db
from datetime import datetime


class Review(db.Model):
    """Модель отзыва"""
    
    __tablename__ = 'reviews'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False, unique=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tutor_id = db.Column(db.Integer, db.ForeignKey('tutors.id'), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    comment = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    student = db.relationship('User', foreign_keys=[student_id], back_populates='reviews_given')
    tutor = db.relationship('Tutor', foreign_keys=[tutor_id], back_populates='reviews')
    booking = db.relationship('Booking', back_populates='review')