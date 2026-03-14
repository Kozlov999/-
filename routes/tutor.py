"""
Маршруты для репетиторов
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, User, Tutor, Booking
from datetime import datetime

tutor_bp = Blueprint('tutor', __name__)


@tutor_bp.route('/register', methods=['GET', 'POST'])
@login_required
def register():
    """Регистрация профиля репетитора"""
    if current_user.role != 'tutor':
        flash('Эта страница доступна только для репетиторов!', 'danger')
        return redirect(url_for('dashboard.dashboard'))
    
    if Tutor.query.filter_by(user_id=current_user.id).first():
        flash('Профиль репетитора уже создан!', 'info')
        return redirect(url_for('dashboard.dashboard'))
    
    if request.method == 'POST':
        subjects = request.form.get('subjects', '').strip()
        education = request.form.get('education', '').strip()
        experience = request.form.get('experience', '').strip()
        hourly_rate = request.form.get('hourly_rate', '').strip()
        about = request.form.get('about', '').strip()
        
        # Валидация
        if not subjects:
            flash('Укажите предметы, которые вы преподаете!', 'danger')
            return redirect(url_for('tutor.register'))
        
        try:
            rate = float(hourly_rate)
            if rate <= 0:
                flash('Ставка должна быть положительным числом!', 'danger')
                return redirect(url_for('tutor.register'))
        except ValueError:
            flash('Некорректное значение ставки!', 'danger')
            return redirect(url_for('tutor.register'))
        
        tutor = Tutor(
            user_id=current_user.id,
            subjects=subjects,
            education=education if education else None,
            experience=experience if experience else None,
            hourly_rate=rate,
            about=about if about else None,
            is_verified=False
        )
        
        db.session.add(tutor)
        db.session.commit()
        
        flash('Ваш профиль репетитора успешно создан!', 'success')
        return redirect(url_for('dashboard.dashboard'))
    
    return render_template('tutor_register.html')


@tutor_bp.route('/find')
@login_required
def find():
    """Поиск репетиторов"""
    # Получаем параметры фильтрации
    subject = request.args.get('subject', '').strip()
    min_rate = request.args.get('min_rate', type=float)
    max_rate = request.args.get('max_rate', type=float)
    search = request.args.get('search', '').strip()
    
    # Базовый запрос
    query = Tutor.query.filter_by(is_verified=True)
    
    # Фильтры
    if subject:
        query = query.filter(Tutor.subjects.ilike(f'%{subject}%'))
    
    if min_rate:
        query = query.filter(Tutor.hourly_rate >= min_rate)
    
    if max_rate:
        query = query.filter(Tutor.hourly_rate <= max_rate)
    
    if search:
        query = query.join(User).filter(
            db.or_(
                User.first_name.ilike(f'%{search}%'),
                User.last_name.ilike(f'%{search}%'),
                Tutor.education.ilike(f'%{search}%'),
                Tutor.experience.ilike(f'%{search}%')
            )
        )
    
    tutors = query.all()
    
    # Получаем все предметы для фильтра
    all_subjects = set()
    for t in Tutor.query.filter_by(is_verified=True).all():
        for s in t.subjects.split(','):
            all_subjects.add(s.strip())
    all_subjects = sorted(list(all_subjects))
    
    return render_template('find_tutor.html', 
                         tutors=tutors,
                         all_subjects=all_subjects,
                         current_filters={
                             'subject': subject,
                             'min_rate': min_rate,
                             'max_rate': max_rate,
                             'search': search
                         })


@tutor_bp.route('/book/<int:tutor_id>', methods=['POST'])
@login_required
def book(tutor_id):
    """Бронирование урока"""
    if current_user.role != 'student':
        flash('Только студенты могут бронировать уроки!', 'danger')
        return redirect(url_for('dashboard.dashboard'))
    
    tutor = Tutor.query.get_or_404(tutor_id)
    
    subject = request.form.get('subject', '').strip()
    lesson_date = request.form.get('lesson_date', '').strip()
    lesson_time = request.form.get('lesson_time', '').strip()
    duration = request.form.get('duration', '').strip()
    
    # Валидация
    if not subject or not lesson_date or not lesson_time or not duration:
        flash('Заполните все поля!', 'danger')
        return redirect(url_for('tutor.find'))
    
    try:
        date_obj = datetime.strptime(lesson_date, '%Y-%m-%d').date()
        time_obj = datetime.strptime(lesson_time, '%H:%M').time()
        duration_int = int(duration)
    except ValueError:
        flash('Некорректные данные!', 'danger')
        return redirect(url_for('tutor.find'))
    
    # Проверка на прошедшую дату
    if date_obj < datetime.now().date():
        flash('Нельзя забронировать урок на прошедшую дату!', 'danger')
        return redirect(url_for('tutor.find'))
    
    # Создание бронирования
    booking = Booking(
        student_id=current_user.id,
        tutor_id=tutor_id,
        subject=subject,
        lesson_date=date_obj,
        lesson_time=time_obj,
        duration=duration_int
    )
    booking.generate_meeting_id()
    
    db.session.add(booking)
    db.session.commit()
    
    flash('Урок успешно забронирован! Ожидайте подтверждения.', 'success')
    return redirect(url_for('dashboard.dashboard'))


@tutor_bp.route('/update-status/<int:booking_id>', methods=['POST'])
@login_required
def update_booking_status(booking_id):
    """Обновление статуса бронирования"""
    booking = Booking.query.get_or_404(booking_id)
    
    if current_user.role == 'tutor':
        tutor = Tutor.query.filter_by(user_id=current_user.id).first()
        if not tutor or booking.tutor_id != tutor.id:
            flash('У вас нет прав!', 'danger')
            return redirect(url_for('dashboard.dashboard'))
    
    new_status = request.form.get('status', '').strip()
    
    if new_status in ['confirmed', 'cancelled']:
        booking.status = new_status
        if new_status == 'confirmed' and not booking.meeting_id:
            booking.generate_meeting_id()
        db.session.commit()
        flash(f'Статус обновлен: {new_status}', 'success')
    else:
        flash('Некорректный статус!', 'danger')
    
    return redirect(url_for('dashboard.dashboard'))