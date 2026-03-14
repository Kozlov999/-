"""
Инициализация маршрутов (blueprints)
"""

from .auth import auth_bp
from .main import main_bp
from .dashboard import dashboard_bp
from .tutor import tutor_bp
from .lesson import lesson_bp
from .payment import payment_bp
from .admin import admin_bp

# Удаляем from .user import User - это не нужно

# Список всех blueprint'ов для экспорта
__all__ = [
    'auth_bp',
    'main_bp',
    'dashboard_bp',
    'tutor_bp',
    'lesson_bp',
    'payment_bp',
    'admin_bp'
]