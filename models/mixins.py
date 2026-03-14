"""
Миксины для моделей - переиспользуемые компоненты
"""

from datetime import datetime
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from . import db


class TimestampMixin:
    """Миксин для автоматического добавления временных меток"""
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PasswordMixin(UserMixin):
    """Миксин для работы с паролями"""
    password_hash = db.Column(db.String(255), nullable=False)
    
    def set_password(self, password):
        """Установка пароля"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """Проверка пароля"""
        return check_password_hash(self.password_hash, password)


class MeetingMixin:
    """Миксин для видео-конференций"""
    meeting_id = db.Column(db.String(100), unique=True)
    meeting_started = db.Column(db.Boolean, default=False)
    meeting_ended = db.Column(db.Boolean, default=False)
    
    def generate_meeting_id(self):
        """Генерация ID для видеоконференции"""
        if not self.meeting_id:
            import uuid
            self.meeting_id = f"lesson_{self.id}_{uuid.uuid4().hex[:8]}"
        return self.meeting_id