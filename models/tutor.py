"""
Модель репетитора
"""

from . import db
from datetime import datetime


class Tutor(db.Model):
    """Модель репетитора"""
    
    __tablename__ = 'tutors'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    subjects = db.Column(db.String(200), nullable=False)
    education = db.Column(db.Text)
    experience = db.Column(db.Text)
    hourly_rate = db.Column(db.Numeric(10, 2), nullable=False)
    about = db.Column(db.Text)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships - используем уникальные имена
    user = db.relationship('User', foreign_keys=[user_id], back_populates='tutor_profile')
    bookings = db.relationship('Booking', backref='booking_tutor', lazy='dynamic')
    availability = db.relationship('Availability', backref='availability_tutor', lazy='dynamic')
    reviews = db.relationship('Review', backref='review_tutor', lazy='dynamic')
    payments = db.relationship('Payment', foreign_keys='Payment.tutor_id', backref='payment_tutor', lazy='dynamic')
    
    def get_average_rating(self):
        reviews_list = self.reviews.all()
        if not reviews_list:
            return None
        ratings = [r.rating for r in reviews_list]
        return round(sum(ratings) / len(ratings), 1)
    
    def get_reviews_count(self):
        return self.reviews.count()