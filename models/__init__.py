"""
Инициализация моделей
"""

from flask_sqlalchemy import SQLAlchemy

# Создание экземпляра SQLAlchemy
db = SQLAlchemy()

# Импорт моделей в правильном порядке
from .user import User
from .tutor import Tutor
from .booking import Booking
from .payment import Payment
from .lesson import LessonMaterial, LessonNote
from .review import Review
from .availability import Availability
from .admin import AdminLog
from .chat import ChatMessage

# Список всех моделей для экспорта
__all__ = [
    'db', 'User', 'Tutor', 'Booking', 'Payment',
    'LessonMaterial', 'LessonNote', 'Review', 'Availability',
    'AdminLog', 'ChatMessage'
]