"""
Главный файл приложения Место репетитора с поддержкой нескольких портов
"""

from flask import Flask, render_template, request, jsonify
from flask_login import LoginManager
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
from dotenv import load_dotenv
from collections import defaultdict
import os
import socket
import threading
import time
import requests
from werkzeug.serving import make_server

# Загрузка переменных окружения
load_dotenv()

# Импорт конфигурации
from config import Config

# Импорт расширений БД
from models import db
from models.user import User
from models.tutor import Tutor
from models.chat import ChatMessage

# Импорт blueprint'ов
from routes.auth import auth_bp
from routes.main import main_bp
from routes.dashboard import dashboard_bp
from routes.tutor import tutor_bp
from routes.lesson import lesson_bp
from routes.payment import payment_bp
from routes.admin import admin_bp

# Инициализация расширений
login_manager = LoginManager()
socketio = SocketIO(
    cors_allowed_origins="*",  # Только один раз!
    async_mode='threading',
    logger=True,
    engineio_logger=True,
    ping_timeout=60,
    ping_interval=25
)


class MultiPortServer:
    """Класс для управления несколькими портами"""
    
    def __init__(self, app, socketio_instance):
        self.app = app
        self.socketio = socketio_instance
        self.servers = []
        self.threads = []
        self.running = False
        self.local_ip = Config.get_local_ip()
        
    def start_server_on_port(self, port, is_websocket=False):
        """Запуск сервера на указанном порту"""
        try:
            if is_websocket:
                # Для WebSocket используем socketio.run в отдельном потоке
                def run_ws():
                    self.socketio.run(
                        self.app,
                        host=Config.HOST,
                        port=port,
                        debug=False,
                        allow_unsafe_werkzeug=True,
                        use_reloader=False
                    )
                
                thread = threading.Thread(target=run_ws, daemon=True)
                thread.start()
                self.threads.append(thread)
                print(f"  ✅ WebSocket сервер запущен на порту {port}")
                
            else:
                # Для HTTP используем werkzeug сервер
                server = make_server(Config.HOST, port, self.app, threaded=True)
                self.servers.append(server)
                
                def run_http():
                    server.serve_forever()
                
                thread = threading.Thread(target=run_http, daemon=True)
                thread.start()
                self.threads.append(thread)
                print(f"  ✅ HTTP сервер запущен на порту {port}")
                
            return True
            
        except Exception as e:
            print(f"  ❌ Ошибка запуска на порту {port}: {e}")
            return False
    
    def start_all(self):
        """Запуск всех серверов"""
        print("\n" + "=" * 60)
        print("🚀 ЗАПУСК МНОГОПОРТОВОГО СЕРВЕРА")
        print("=" * 60)
        
        # Запускаем основной HTTP сервер
        print(f"\n📡 Запуск HTTP серверов:")
        self.start_server_on_port(Config.MAIN_PORT, is_websocket=False)
        
        # Запускаем WebSocket на отдельном порту
        print(f"\n🔌 Запуск WebSocket сервера:")
        self.start_server_on_port(Config.WS_PORT, is_websocket=True)
        
        # Запускаем дополнительные HTTP порты
        print(f"\n🔀 Запуск дополнительных портов:")
        for port in Config.ALT_PORTS:
            self.start_server_on_port(port, is_websocket=False)
        
        self.running = True
        self.print_access_info()
        
    def print_access_info(self):
        """Вывод информации о доступе"""
        print("\n" + "=" * 60)
        print("📱 ДОСТУП К СЕРВЕРУ")
        print("=" * 60)
        
        # Основные порты
        print("\n🔹 ОСНОВНЫЕ ПОРТЫ:")
        print(f"   📡 HTTP:  http://{self.local_ip}:{Config.MAIN_PORT}")
        print(f"   🔌 WebSocket:  ws://{self.local_ip}:{Config.WS_PORT}")
        print(f"   📡 Локальный:  http://127.0.0.1:{Config.MAIN_PORT}")
        
        # Дополнительные порты
        print("\n🔸 ДОПОЛНИТЕЛЬНЫЕ ПОРТЫ:")
        for i, port in enumerate(Config.ALT_PORTS, 1):
            print(f"   {i}. http://{self.local_ip}:{port}")
        
        # Информация о сети
        print("\n🌐 СЕТЕВЫЕ ИНТЕРФЕЙСЫ:")
        interfaces = self.get_network_interfaces()
        for name, ip in interfaces.items():
            if ip and not ip.startswith('127.'):
                print(f"   • {name}: http://{ip}:{Config.MAIN_PORT}")
        
        # Тестирование соединений
        print("\n🔄 ПРОВЕРКА СОЕДИНЕНИЙ:")
        self.test_connections()
        
        print("\n" + "=" * 60)
        print("✅ СЕРВЕР УСПЕШНО ЗАПУЩЕН")
        print("=" * 60 + "\n")
    
    def get_network_interfaces(self):
        """Получение всех сетевых интерфейсов"""
        interfaces = {}
        
        try:
            import netifaces
            for iface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(iface)
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        ip = addr['addr']
                        if not ip.startswith('127.'):
                            interfaces[iface] = ip
        except ImportError:
            # Если netifaces не установлен, используем базовый метод
            hostname = socket.gethostname()
            try:
                local_ip = socket.gethostbyname(hostname)
                interfaces['default'] = local_ip
            except:
                interfaces['default'] = self.local_ip
        
        return interfaces
    
    def test_connections(self):
        """Тестирование доступности портов"""
        test_ports = [Config.MAIN_PORT, Config.WS_PORT] + Config.ALT_PORTS[:2]
        
        for port in test_ports:
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(1)
            result = sock.connect_ex((self.local_ip, port))
            sock.close()
            
            status = "✅ ДОСТУПЕН" if result == 0 else "❌ НЕ ДОСТУПЕН"
            protocol = "WebSocket" if port == Config.WS_PORT else "HTTP"
            print(f"   • Порт {port} ({protocol}): {status}")
    
    def stop_all(self):
        """Остановка всех серверов"""
        print("\n🛑 Остановка серверов...")
        
        for server in self.servers:
            server.shutdown()
        
        # Принудительное завершение потоков
        self.running = False
        print("✅ Все серверы остановлены")


def create_app(config_class=Config):
    """
    Фабрика приложений Flask
    """
    app = Flask(__name__)
    app.config.from_object(config_class)
    
    # Настройка CORS для нескольких портов
    cors_origins = [
        "http://127.0.0.1:8000",
        "http://127.0.0.1:8001",
        "http://127.0.0.1:8002",
        "http://127.0.0.1:8003",
        "http://127.0.0.1:8004",
        "http://127.0.0.1:8005",
        f"http://{Config.get_local_ip()}:8000",
        f"http://{Config.get_local_ip()}:8001",
        f"http://{Config.get_local_ip()}:8002",
        f"http://{Config.get_local_ip()}:8003",
        f"http://{Config.get_local_ip()}:8004",
        f"http://{Config.get_local_ip()}:8005",
        "*"
    ]
    
    CORS(app, resources={
        r"/*": {
            "origins": cors_origins,
            "methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS"],
            "allow_headers": ["Content-Type", "Authorization"],
            "supports_credentials": True
        }
    })
    
    # Инициализация расширений
    db.init_app(app)
    login_manager.init_app(app)
    
    # Настройка LoginManager
    login_manager.login_view = 'auth.login'
    login_manager.login_message = 'Пожалуйста, войдите в систему для доступа к этой странице.'
    login_manager.login_message_category = 'info'
    
    # Регистрация blueprint'ов
    register_blueprints(app)
    
    # Регистрация контекстных процессоров
    register_context_processors(app)
    
    # Регистрация обработчиков ошибок
    register_error_handlers(app)
    
    # Создание директорий
    ensure_directories(app)
    
    # Создание таблиц БД
    with app.app_context():
        db.create_all()
        create_admin_if_not_exists()
        print("[OK] База данных инициализирована")
    
    # Добавляем эндпоинт для информации о портах
    @app.route('/api/ports-info')
    def ports_info():
        """Информация о доступных портах"""
        return jsonify({
            'main_port': Config.MAIN_PORT,
            'ws_port': Config.WS_PORT,
            'alt_ports': Config.ALT_PORTS,
            'local_ip': Config.get_local_ip(),
            'all_ports': [Config.MAIN_PORT, Config.WS_PORT] + Config.ALT_PORTS
        })
    
    return app


def register_blueprints(app):
    """Регистрация blueprint'ов"""
    
    blueprints = [
        (main_bp, ''),
        (auth_bp, '/auth'),
        (dashboard_bp, '/dashboard'),
        (tutor_bp, '/tutor'),
        (lesson_bp, '/lesson'),
        (payment_bp, '/payment'),
        (admin_bp, '/admin')
    ]
    
    for blueprint, url_prefix in blueprints:
        app.register_blueprint(blueprint, url_prefix=url_prefix)
        print(f"[OK] Blueprint: {blueprint.name} -> {url_prefix or '/'}")


def register_context_processors(app):
    """Регистрация контекстных процессоров для шаблонов"""
    
    @app.context_processor
    def utility_processor():
        from datetime import datetime
        
        def get_server_ip():
            return Config.get_local_ip()
        
        def get_ws_port():
            return Config.WS_PORT
        
        def get_alt_ports():
            return Config.ALT_PORTS
        
        return dict(
            now=datetime.now,
            current_year=datetime.now().year,
            server_ip=get_server_ip,
            server_port=Config.MAIN_PORT,
            ws_port=get_ws_port,
            alt_ports=get_alt_ports,
            format_datetime=lambda v, f='%d.%m.%Y %H:%M': v.strftime(f) if isinstance(v, datetime) else v
        )
    
    print("[OK] Контекстные процессоры зарегистрированы")


def register_error_handlers(app):
    """Регистрация обработчиков ошибок"""
    
    @app.errorhandler(404)
    def not_found_error(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        return render_template('403.html'), 403


def ensure_directories(app):
    """Создание необходимых директорий"""
    upload_dir = app.config.get('UPLOAD_FOLDER', 'uploads')
    if not os.path.exists(upload_dir):
        os.makedirs(upload_dir)
        print(f"[OK] Создана директория: {upload_dir}")


def create_admin_if_not_exists():
    """Создание администратора по умолчанию"""
    admin_email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
    admin = User.query.filter_by(email=admin_email).first()
    
    if not admin:
        admin = User(
            email=admin_email,
            first_name='Admin',
            last_name='User',
            role='admin'
        )
        admin.set_password(os.getenv('ADMIN_PASSWORD', 'admin123'))
        db.session.add(admin)
        db.session.commit()
        print(f"[OK] Создан администратор: {admin_email}")


# Загрузчик пользователя
@login_manager.user_loader
def load_user(user_id):
    try:
        # Используем db.session.get() вместо User.query.get()
        from models import db
        return db.session.get(User, int(user_id))
    except Exception as e:
        print(f"Ошибка загрузки пользователя: {e}")
        return None


# ==================== WEBSOCKET HANDLERS ====================

# Хранилище данных клиентов
client_data = {}

@socketio.on('connect')
def handle_connect(auth=None):
    """Обработка подключения клиента"""
    print(f'[WebSocket] Client connected: {request.sid} from port {request.environ.get("REMOTE_PORT")}')
    emit('connected', {
        'data': 'Connected to server',
        'sid': request.sid,
        'ws_port': Config.WS_PORT,
        'http_port': Config.MAIN_PORT
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Обработка отключения клиента"""
    print(f'[WebSocket] Client disconnected: {request.sid}')
    if request.sid in client_data:
        del client_data[request.sid]


@socketio.on('join_lesson')
def handle_join_lesson(data):
    """Присоединение к комнате урока"""
    room = data.get('room')
    user_name = data.get('user_name')
    user_id = data.get('user_id')
    client_sid = request.sid

    print(f'[DEBUG] join_lesson: {data} from SID: {client_sid}')

    if not room or not user_name or not user_id:
        print(f'[WebSocket] Ошибка: отсутствуют данные пользователя')
        return

    client_data[client_sid] = {'user_name': user_name, 'user_id': user_id}
    join_room(room)
    print(f'[WebSocket] {user_name} (ID: {user_id}) вошел в комнату: {room}')

    emit('user_joined', {
        'user': user_name,
        'user_id': user_id,
        'sid': client_sid
    }, room=room, include_self=True)

    emit('joined', {
        'room': room,
        'user': user_name,
        'sid': client_sid,
        'ws_port': Config.WS_PORT
    }, room=client_sid)


@socketio.on('leave_lesson')
def handle_leave_lesson(data):
    """Выход из комнаты урока"""
    room = data.get('room')
    user_name = data.get('user_name')
    user_id = data.get('user_id')
    client_sid = request.sid
    
    if not user_name or not user_id:
        if client_sid in client_data:
            user_name = client_data[client_sid].get('user_name', 'Пользователь')
            user_id = client_data[client_sid].get('user_id', 0)
        else:
            return
    
    leave_room(room)
    print(f'[WebSocket] {user_name} покинул комнату: {room}')
    
    emit('user_left', {
        'user': user_name,
        'user_id': user_id
    }, room=room, include_self=False)
    
    if client_sid in client_data:
        del client_data[client_sid]


@socketio.on('offer')
def handle_offer(data):
    """WebRTC offer"""
    try:
        room = data.get('room')
        offer = data.get('offer')
        user_id = data.get('user_id')
        
        if not all([room, offer, user_id]):
            return
        
        print(f'[WebRTC] Offer from {user_id} in room {room}')
        emit('offer', {
            'offer': offer,
            'from': user_id
        }, room=room, include_self=False, skip_sid=request.sid)
        
    except Exception as e:
        print(f'[WebRTC] Error: {e}')


@socketio.on('answer')
def handle_answer(data):
    """WebRTC answer"""
    try:
        room = data.get('room')
        answer = data.get('answer')
        user_id = data.get('user_id')
        
        if not all([room, answer, user_id]):
            return
        
        print(f'[WebRTC] Answer from {user_id} in room {room}')
        emit('answer', {
            'answer': answer,
            'from': user_id
        }, room=room, include_self=False, skip_sid=request.sid)
        
    except Exception as e:
        print(f'[WebRTC] Error: {e}')


@socketio.on('ice_candidate')
def handle_ice_candidate(data):
    """WebRTC ICE candidate"""
    try:
        room = data.get('room')
        candidate = data.get('candidate')
        user_id = data.get('user_id')
        
        if not all([room, candidate, user_id]):
            return
        
        print(f'[WebRTC] ICE candidate from {user_id}')
        emit('ice_candidate', {
            'candidate': candidate,
            'from': user_id
        }, room=room, include_self=False, skip_sid=request.sid)
        
    except Exception as e:
        print(f'[WebRTC] Error: {e}')


@socketio.on('new_chat_message')
def handle_new_chat_message(data):
    """Новое сообщение в чате"""
    try:
        room = data.get('room')
        message_data = data.get('message')
        
        if not room or not message_data:
            return
        
        print(f'[Chat] New message in room {room}')
        emit('new_chat_message', {
            'message': message_data
        }, room=room)
        
    except Exception as e:
        print(f'[Chat] Error: {e}')


@socketio.on('chat_typing')
def handle_chat_typing(data):
    """Индикатор печатания"""
    room = data.get('room')
    user_name = data.get('user_name')
    is_typing = data.get('is_typing', False)
    
    if not room or not user_name:
        return
    
    emit('user_typing', {
        'user_name': user_name,
        'is_typing': is_typing
    }, room=room, include_self=False)


@socketio.on('chat_message_read')
def handle_chat_message_read(data):
    """Сообщения прочитаны"""
    room = data.get('room')
    user_id = data.get('user_id')
    
    if not room or not user_id:
        return
    
    emit('messages_read', {
        'user_id': user_id
    }, room=room, include_self=False)


@socketio.on_error()
def error_handler(e):
    """Глобальный обработчик ошибок WebSocket"""
    print(f'[WebSocket Error] {str(e)}')
    emit('error', {'message': 'Internal server error'})


# Создание приложения
app = create_app()

# Инициализируем socketio с приложением (без повторения cors_allowed_origins)
socketio.init_app(app, cors_allowed_origins="*")

# Создаем многопортовый сервер
multi_port_server = MultiPortServer(app, socketio)


if __name__ == '__main__':
    try:
        # Запускаем многопортовый сервер
        multi_port_server.start_all()
        
        # Держим главный поток активным
        while multi_port_server.running:
            time.sleep(1)
            
    except KeyboardInterrupt:
        print("\n\n🛑 Получен сигнал остановки...")
        multi_port_server.stop_all()
    except Exception as e:
        print(f"\n❌ Критическая ошибка: {e}")
        multi_port_server.stop_all()
