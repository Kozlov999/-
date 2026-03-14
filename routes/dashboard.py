"""
Маршруты для личного кабинета
"""

from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_required, current_user
from models import db, Tutor, Booking, Review
from datetime import datetime, timedelta

dashboard_bp = Blueprint('dashboard', __name__)


@dashboard_bp.route('/')
@login_required
def dashboard():
    """Личный кабинет пользователя"""
    now = datetime.now()
    upcoming_lessons = []
    
    if current_user.role == 'tutor':
        # Для репетитора
        tutor = Tutor.query.filter_by(user_id=current_user.id).first()
        bookings = Booking.query.filter_by(tutor_id=tutor.id).all() if tutor else []
        
        # Ближайшие уроки
        if tutor:
            upcoming_lessons = Booking.query.filter(
                Booking.tutor_id == tutor.id,
                Booking.status == 'confirmed',
                Booking.lesson_date >= now.date(),
                Booking.lesson_date <= (now + timedelta(days=7)).date()
            ).order_by(Booking.lesson_date, Booking.lesson_time).all()
        
        return render_template('dashboard.html', tutor=tutor, bookings=bookings, upcoming_lessons=upcoming_lessons)
    
    else:
        # Для студента
        bookings = Booking.query.filter_by(student_id=current_user.id).all()
        
        upcoming_lessons = Booking.query.filter(
            Booking.student_id == current_user.id,
            Booking.status == 'confirmed',
            Booking.lesson_date >= now.date(),
            Booking.lesson_date <= (now + timedelta(days=7)).date()
        ).order_by(Booking.lesson_date, Booking.lesson_time).all()
        
        return render_template('dashboard.html', bookings=bookings, upcoming_lessons=upcoming_lessons)


@dashboard_bp.route('/history')
@login_required
def history():
    """История уроков"""
    if current_user.role == 'tutor':
        tutor = Tutor.query.filter_by(user_id=current_user.id).first()
        if tutor:
            completed_bookings = Booking.query.filter(
                Booking.tutor_id == tutor.id,
                Booking.status == 'completed'
            ).order_by(Booking.lesson_date.desc()).all()
            return render_template('history.html', bookings=completed_bookings, role='tutor')
    else:
        completed_bookings = Booking.query.filter(
            Booking.student_id == current_user.id,
            Booking.status == 'completed'
        ).order_by(Booking.lesson_date.desc()).all()
        return render_template('history.html', bookings=completed_bookings, role='student')
    
    return redirect(url_for('dashboard.dashboard'))


@dashboard_bp.route('/add-review/<int:booking_id>', methods=['POST'])
@login_required
def add_review(booking_id):
    """Добавление отзыва"""
    try:
        booking = Booking.query.get_or_404(booking_id)
        
        # Проверка прав
        if current_user.role != 'student' or booking.student_id != current_user.id:
            flash('Только студент может оставить отзыв!', 'danger')
            return redirect(url_for('dashboard.history'))
        
        # Проверка статуса урока
        if booking.status != 'completed':
            flash('Отзыв можно оставить только после завершенного урока!', 'danger')
            return redirect(url_for('dashboard.history'))
        
        # Проверка, не оставлен ли уже отзыв
        existing_review = Review.query.filter_by(booking_id=booking_id).first()
        if existing_review:
            flash('Отзыв уже оставлен для этого урока!', 'danger')
            return redirect(url_for('dashboard.history'))
        
        # Получение данных из формы
        rating = request.form.get('rating')
        comment = request.form.get('comment', '').strip()
        
        # Валидация
        if not rating:
            flash('Пожалуйста, поставьте оценку!', 'danger')
            return redirect(url_for('dashboard.history'))
        
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                flash('Оценка должна быть от 1 до 5!', 'danger')
                return redirect(url_for('dashboard.history'))
        except ValueError:
            flash('Некорректная оценка!', 'danger')
            return redirect(url_for('dashboard.history'))
        
        # Создание отзыва
        review = Review(
            booking_id=booking_id,
            student_id=current_user.id,
            tutor_id=booking.tutor_id,
            rating=rating,
            comment=comment if comment else None
        )
        
        db.session.add(review)
        db.session.commit()
        
        flash('Спасибо! Ваш отзыв успешно добавлен.', 'success')
        
    except Exception as e:
        db.session.rollback()
        print(f"Ошибка при добавлении отзыва: {e}")
        flash('Произошла ошибка при добавлении отзыва. Пожалуйста, попробуйте позже.', 'danger')
    
    return redirect(url_for('dashboard.history'))