"""
Конфигурация приложения с поддержкой нескольких портов
"""

import socket
import os

class Config:
    """Базовые настройки"""
    
    # Безопасность
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')
    
    # База данных
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL', 'sqlite:///tutors.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Загрузка файлов
    UPLOAD_FOLDER = os.getenv('UPLOAD_FOLDER', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    
    # Настройки сервера - несколько портов
    HOST = '0.0.0.0'
    MAIN_PORT = 8000  # Основной порт для HTTP
    WS_PORT = 8001    # Отдельный порт для WebSocket
    ALT_PORTS = [8002, 8003, 8004, 8005]  # Дополнительные порты
    
    # Автоматический выбор порта
    PREFERRED_PORTS = [8000, 8001, 8002, 8003, 8004, 8005, 8080, 8081, 8082]
    
    # Настройки приложения
    DEBUG = True
    ENV = 'development'
    
    @staticmethod
    def get_local_ip():
        """Получение локального IP адреса"""
        try:
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.connect(('8.8.8.8', 80))
            ip = s.getsockname()[0]
            s.close()
            return ip
        except Exception:
            return '127.0.0.1'
    
    @staticmethod
    def find_available_ports(start_port=8000, count=5):
        """Поиск доступных портов"""
        import socket
        available_ports = []
        
        for port in range(start_port, start_port + 20):  # Проверяем 20 портов
            if len(available_ports) >= count:
                break
                
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            result = sock.connect_ex(('127.0.0.1', port))
            sock.close()
            
            if result != 0:  # Порт свободен
                available_ports.append(port)
        
        return available_ports