"""
Модель для сообщений чата
"""

from . import db
from datetime import datetime


class ChatMessage(db.Model):
    """Модель сообщения чата"""
    
    __tablename__ = 'chat_messages'
    
    id = db.Column(db.Integer, primary_key=True)
    booking_id = db.Column(db.Integer, db.ForeignKey('bookings.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    message = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    is_read = db.Column(db.Boolean, default=False)
    
    # Relationships
    user = db.relationship('User', back_populates='chat_messages')
    booking = db.relationship('Booking', back_populates='chat_messages')
    
    def __repr__(self):
        return f'<ChatMessage {self.id}>'