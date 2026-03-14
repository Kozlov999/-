"""
Модель бронирования
"""

from . import db
from datetime import datetime
import uuid


class Booking(db.Model):
    """Модель бронирования урока"""
    
    __tablename__ = 'bookings'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    tutor_id = db.Column(db.Integer, db.ForeignKey('tutors.id'), nullable=False)
    subject = db.Column(db.String(100), nullable=False)
    lesson_date = db.Column(db.Date, nullable=False)
    lesson_time = db.Column(db.Time, nullable=False)
    duration = db.Column(db.Integer, nullable=False)
    status = db.Column(db.String(20), default='pending')
    meeting_id = db.Column(db.String(100), unique=True)
    meeting_started = db.Column(db.Boolean, default=False)
    meeting_ended = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships - используем уникальные имена
    student = db.relationship('User', foreign_keys=[student_id], back_populates='student_bookings')
    tutor = db.relationship('Tutor', foreign_keys=[tutor_id], back_populates='bookings')
    materials = db.relationship('LessonMaterial', backref='material_booking', lazy=True, cascade='all, delete-orphan')
    notes = db.relationship('LessonNote', backref='note_booking', lazy=True, cascade='all, delete-orphan')
    chat_messages = db.relationship('ChatMessage', backref='chat_booking', lazy=True, cascade='all, delete-orphan')
    payment = db.relationship('Payment', backref='payment_booking', uselist=False, cascade='all, delete-orphan')
    review = db.relationship('Review', backref='review_booking', uselist=False, cascade='all, delete-orphan')
    
    def generate_meeting_id(self):
        """Генерация ID для видеоконференции"""
        if not self.meeting_id:
            # Сначала сохраняем ID, если его нет
            if not self.id:
                # Если объект еще не сохранен, генерируем временный ID
                import uuid
                self.meeting_id = f"lesson_temp_{uuid.uuid4().hex[:8]}"
            else:
                # Если объект сохранен, используем его ID
                import uuid
                self.meeting_id = f"lesson_{self.id}_{uuid.uuid4().hex[:8]}"
        return self.meeting_id