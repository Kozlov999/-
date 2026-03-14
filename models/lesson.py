"""
Модели материалов и заметок
"""

from . import db
from datetime import datetime


class LessonMaterial(db.Model):
    """Материалы урока"""
    
    __tablename__ = 'lesson_materials'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    filename = db.Column(db.String(255), nullable=False)
    original_filename = db.Column(db.String(255), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    uploaded_by = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    uploader = db.relationship('User', back_populates='uploaded_materials')
    booking = db.relationship('Booking', back_populates='materials')
    
    def __repr__(self):
        return f'<LessonMaterial {self.original_filename}>'


class LessonNote(db.Model):
    """Заметки к уроку"""
    
    __tablename__ = 'lesson_notes'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    author = db.relationship('User', back_populates='authored_notes')
    booking = db.relationship('Booking', back_populates='notes')
    
    def __repr__(self):
        return f'<LessonNote {self.id}>'