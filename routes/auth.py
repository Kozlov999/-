"""
Маршруты для аутентификации
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_user, logout_user, login_required, current_user
from models import db
from models.user import User

auth_bp = Blueprint('auth', __name__)


@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Регистрация нового пользователя"""
    if request.method == 'POST':
        email = request.form.get('email', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')
        first_name = request.form.get('first_name', '').strip()
        last_name = request.form.get('last_name', '').strip()
        phone = request.form.get('phone', '').strip()
        role = request.form.get('role', '').strip()
        
        # Проверка пароля
        if password != confirm_password:
            flash('Пароли не совпадают!', 'danger')
            return redirect(url_for('auth.register'))
        
        if len(password) < 6:
            flash('Пароль должен содержать не менее 6 символов', 'danger')
            return redirect(url_for('auth.register'))
        
        # Проверка существующего пользователя
        if User.query.filter_by(email=email).first():
            flash('Пользователь с таким email уже существует!', 'danger')
            return redirect(url_for('auth.register'))
        
        # Создание пользователя
        user = User(
            email=email,
            first_name=first_name,
            last_name=last_name,
            phone=phone if phone else None,
            role=role
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        flash('Регистрация прошла успешно!', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('register.html')


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Вход в систему"""
    if request.method == 'POST':
        email = request.form.get('email', '')
        password = request.form.get('password', '')
        
        user = User.query.filter_by(email=email).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Вы успешно вошли в систему!', 'success')
            return redirect(url_for('dashboard.dashboard'))
        else:
            flash('Неверный email или пароль!', 'danger')
    
    return render_template('login.html')


@auth_bp.route('/logout')
@login_required
def logout():
    """Выход из системы"""
    logout_user()
    flash('Вы вышли из системы.', 'info')
    return redirect(url_for('main.index'))