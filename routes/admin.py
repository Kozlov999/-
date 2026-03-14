"""
Маршруты для администратора
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, User, Tutor, Booking, AdminLog, Review  # Добавлен Review
from datetime import datetime, timedelta
from sqlalchemy import func

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')


def admin_required(f):
    """Декоратор для проверки прав администратора"""
    from functools import wraps
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash('Пожалуйста, войдите в систему.', 'warning')
            return redirect(url_for('auth.login'))
        
        if current_user.role != 'admin':
            flash('Доступ запрещен. Только для администраторов.', 'danger')
            return redirect(url_for('main.index'))
            
        return f(*args, **kwargs)
    return decorated_function


@admin_bp.route('/')
@login_required
@admin_required
def dashboard():
    """Панель администратора"""
    # Статистика
    total_users = User.query.count()
    total_tutors = Tutor.query.count()
    total_students = User.query.filter_by(role='student').count()
    total_bookings = Booking.query.count()
    
    # Новые пользователи за последние 7 дней
    week_ago = datetime.now() - timedelta(days=7)
    new_users = User.query.filter(User.created_at >= week_ago).count()
    
    # Ожидающие подтверждения репетиторы
    pending_tutors = Tutor.query.filter_by(is_verified=False).count()
    
    # Статистика по статусам бронирований
    booking_stats = {
        'pending': Booking.query.filter_by(status='pending').count(),
        'confirmed': Booking.query.filter_by(status='confirmed').count(),
        'completed': Booking.query.filter_by(status='completed').count(),
        'cancelled': Booking.query.filter_by(status='cancelled').count()
    }
    
    # Последние действия
    recent_logs = AdminLog.query.order_by(AdminLog.created_at.desc()).limit(10).all()
    
    # Текущее время для шаблона
    current_time = datetime.now()
    
    return render_template('admin/dashboard.html',
                         total_users=total_users,
                         total_tutors=total_tutors,
                         total_students=total_students,
                         total_bookings=total_bookings,
                         new_users=new_users,
                         pending_tutors=pending_tutors,
                         booking_stats=booking_stats,
                         recent_logs=recent_logs,
                         current_time=current_time)


@admin_bp.route('/tutors')
@login_required
@admin_required
def tutors_list():
    """Список всех репетиторов"""
    # Фильтры
    status = request.args.get('status', 'all')
    search = request.args.get('search', '').strip()
    
    # Базовый запрос
    query = Tutor.query.join(User).add_columns(
        User.email, User.first_name, User.last_name, User.phone, User.created_at
    )
    
    # Фильтр по статусу верификации
    if status == 'pending':
        query = query.filter(Tutor.is_verified == False)
    elif status == 'verified':
        query = query.filter(Tutor.is_verified == True)
    
    # Поиск
    if search:
        query = query.filter(
            db.or_(
                User.first_name.ilike(f'%{search}%'),
                User.last_name.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
                Tutor.subjects.ilike(f'%{search}%')
            )
        )
    
    # Сортировка
    tutors = query.order_by(User.created_at.desc()).all()
    
    return render_template('admin/tutors.html', 
                         tutors=tutors, 
                         current_status=status,
                         search=search)


@admin_bp.route('/tutor/<int:tutor_id>')
@login_required
@admin_required
def tutor_detail(tutor_id):
    """Детальная информация о репетиторе"""
    tutor = Tutor.query.get_or_404(tutor_id)
    user = tutor.user
    
    # Статистика репетитора
    total_bookings = Booking.query.filter_by(tutor_id=tutor_id).count()
    completed_bookings = Booking.query.filter_by(tutor_id=tutor_id, status='completed').count()
    cancelled_bookings = Booking.query.filter_by(tutor_id=tutor_id, status='cancelled').count()
    
    # Средний рейтинг
    avg_rating = tutor.get_average_rating()
    
    # Последние бронирования
    recent_bookings = Booking.query.filter_by(tutor_id=tutor_id)\
                                  .order_by(Booking.created_at.desc())\
                                  .limit(10).all()
    
    return render_template('admin/tutor_detail.html',
                         tutor=tutor,
                         user=user,
                         total_bookings=total_bookings,
                         completed_bookings=completed_bookings,
                         cancelled_bookings=cancelled_bookings,
                         avg_rating=avg_rating,
                         recent_bookings=recent_bookings)


@admin_bp.route('/tutor/<int:tutor_id>/verify', methods=['POST'])
@login_required
@admin_required
def verify_tutor(tutor_id):
    """Подтверждение репетитора"""
    tutor = Tutor.query.get_or_404(tutor_id)
    
    # Переключаем статус верификации
    tutor.is_verified = not tutor.is_verified
    
    # Логируем действие
    log = AdminLog(
        admin_id=current_user.id,
        action='verify_tutor' if tutor.is_verified else 'unverify_tutor',
        target_type='tutor',
        target_id=tutor_id,
        details=f'Репетитор {tutor.user.email} {"верифицирован" if tutor.is_verified else "деверифицирован"}'
    )
    db.session.add(log)
    db.session.commit()
    
    status = 'подтвержден' if tutor.is_verified else 'отклонен'
    flash(f'Репетитор {tutor.user.full_name} {status}', 'success')
    
    return redirect(url_for('admin.tutor_detail', tutor_id=tutor_id))


@admin_bp.route('/users')
@login_required
@admin_required
def users_list():
    """Список всех пользователей"""
    role = request.args.get('role', 'all')
    search = request.args.get('search', '').strip()
    
    query = User.query
    
    if role != 'all':
        query = query.filter_by(role=role)
    
    if search:
        query = query.filter(
            db.or_(
                User.first_name.ilike(f'%{search}%'),
                User.last_name.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        )
    
    users = query.order_by(User.created_at.desc()).all()
    
    return render_template('admin/users.html', 
                         users=users, 
                         current_role=role,
                         search=search)


@admin_bp.route('/bookings')
@login_required
@admin_required
def bookings_list():
    """Список всех бронирований"""
    status = request.args.get('status', 'all')
    search = request.args.get('search', '').strip()
    
    query = Booking.query.join(User, Booking.student_id == User.id)\
                        .add_columns(User.first_name, User.last_name, User.email)
    
    if status != 'all':
        query = query.filter(Booking.status == status)
    
    if search:
        query = query.filter(
            db.or_(
                User.first_name.ilike(f'%{search}%'),
                User.last_name.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%'),
                Booking.subject.ilike(f'%{search}%')
            )
        )
    
    bookings = query.order_by(Booking.created_at.desc()).all()
    
    return render_template('admin/bookings.html', 
                         bookings=bookings, 
                         current_status=status,
                         search=search)


@admin_bp.route('/logs')
@login_required
@admin_required
def logs():
    """Просмотр логов действий"""
    page = request.args.get('page', 1, type=int)
    per_page = 20
    
    logs = AdminLog.query.order_by(AdminLog.created_at.desc())\
                        .paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/logs.html', logs=logs)


@admin_bp.route('/statistics')
@login_required
@admin_required
def statistics():
    """Детальная статистика"""
    try:
        from sqlalchemy import func
        from datetime import datetime, timedelta
        
        # Статистика по дням за последние 30 дней
        thirty_days_ago = datetime.now() - timedelta(days=30)
        
        # Новые пользователи по дням
        daily_users = db.session.query(
            func.date(User.created_at).label('date'),
            func.count().label('count')
        ).filter(User.created_at >= thirty_days_ago)\
         .group_by(func.date(User.created_at))\
         .order_by(func.date(User.created_at))\
         .all()
        
        # Новые бронирования по дням
        daily_bookings = db.session.query(
            func.date(Booking.created_at).label('date'),
            func.count().label('count')
        ).filter(Booking.created_at >= thirty_days_ago)\
         .group_by(func.date(Booking.created_at))\
         .order_by(func.date(Booking.created_at))\
         .all()
        
        # Топ репетиторов по количеству уроков
        top_tutors = []
        try:
            top_tutors = db.session.query(
                Tutor,
                func.count(Booking.id).label('booking_count'),
                func.coalesce(func.avg(Review.rating), 0).label('avg_rating')
            ).outerjoin(Booking, Booking.tutor_id == Tutor.id)\
             .outerjoin(Review, Review.tutor_id == Tutor.id)\
             .group_by(Tutor.id)\
             .order_by(func.count(Booking.id).desc())\
             .limit(10)\
             .all()
        except Exception as e:
            print(f"Ошибка при получении топ репетиторов: {e}")
            top_tutors = []
        
        # Конвертируем данные для шаблона
        users_data = []
        for item in daily_users:
            users_data.append({
                'date': item.date.strftime('%d.%m') if item.date else '',
                'count': item.count
            })
        
        bookings_data = []
        for item in daily_bookings:
            bookings_data.append({
                'date': item.date.strftime('%d.%m') if item.date else '',
                'count': item.count
            })
        
        tutors_data = []
        for tutor, booking_count, avg_rating in top_tutors:
            tutors_data.append({
                'name': tutor.user.full_name,
                'bookings': booking_count,
                'rating': round(avg_rating, 1) if avg_rating else 0
            })
        
        return render_template('admin/statistics.html',
                             daily_users=users_data,
                             daily_bookings=bookings_data,
                             top_tutors=tutors_data,
                             has_data=len(users_data) > 0 or len(bookings_data) > 0)
    
    except Exception as e:
        print(f"Ошибка в статистике: {e}")
        import traceback
        traceback.print_exc()
        flash('Ошибка при загрузке статистики', 'danger')
        return render_template('admin/statistics.html', 
                             daily_users=[], 
                             daily_bookings=[], 
                             top_tutors=[],
                             has_data=False)