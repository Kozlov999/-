"""
Маршруты для оплаты
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from models import db, Booking, Payment
from datetime import datetime
import uuid

payment_bp = Blueprint('payment', __name__)


@payment_bp.route('/<int:booking_id>', methods=['GET', 'POST'])
@login_required
def process(booking_id):
    """Обработка платежа"""
    booking = Booking.query.get_or_404(booking_id)
    
    if current_user.role != 'student' or booking.student_id != current_user.id:
        flash('У вас нет прав для оплаты этого урока!', 'danger')
        return redirect(url_for('dashboard.dashboard'))
    
    if booking.status != 'confirmed':
        flash('Оплата возможна только для подтвержденных уроков!', 'danger')
        return redirect(url_for('dashboard.dashboard'))
    
    existing_payment = Payment.query.filter_by(booking_id=booking_id).first()
    if existing_payment and existing_payment.status == 'completed':
        flash('Этот урок уже оплачен!', 'info')
        return redirect(url_for('dashboard.dashboard'))
    
    if request.method == 'POST':
        amount = float(booking.tutor.hourly_rate) * (booking.duration / 60)
        
        if existing_payment:
            payment = existing_payment
        else:
            payment = Payment(
                booking_id=booking_id,
                student_id=current_user.id,
                tutor_id=booking.tutor_id,
                amount=amount,
                payment_method='demo',
                transaction_id=f"DEMO_{uuid.uuid4().hex[:16]}"
            )
            db.session.add(payment)
        
        payment.status = 'completed'
        payment.paid_at = datetime.utcnow()
        db.session.commit()
        
        flash('Оплата успешно выполнена!', 'success')
        return redirect(url_for('dashboard.dashboard'))
    
    amount = float(booking.tutor.hourly_rate) * (booking.duration / 60)
    return render_template('payment.html', booking=booking, amount=amount)