"""
Маршруты для уроков
"""

from flask import Blueprint, render_template, request, redirect, url_for, flash, send_from_directory, jsonify
from flask_login import login_required, current_user
from models import db, Booking, LessonMaterial, LessonNote, Tutor, ChatMessage
from models.user import User  # Добавляем этот импорт
from werkzeug.utils import secure_filename
from datetime import datetime
import os
import uuid

lesson_bp = Blueprint('lesson', __name__)


@lesson_bp.route('/<int:booking_id>')
@login_required
def room(booking_id):
    """Комната урока"""
    booking = Booking.query.get_or_404(booking_id)
    
    # Проверка доступа
    if not has_lesson_access(current_user, booking):
        flash('У вас нет доступа к этому уроку!', 'danger')
        return redirect(url_for('dashboard.dashboard'))
    
    materials = LessonMaterial.query.filter_by(booking_id=booking_id).all()
    
    return render_template('lesson_room.html', 
                         booking=booking, 
                         materials=materials)


@lesson_bp.route('/api/chat/<int:booking_id>/messages', methods=['GET'])
@login_required
def get_chat_messages(booking_id):
    """Получение истории чата"""
    try:
        booking = Booking.query.get_or_404(booking_id)
        
        # Проверка доступа
        if not has_lesson_access(current_user, booking):
            return jsonify({'error': 'Нет доступа'}), 403
        
        # Получаем сообщения
        messages = ChatMessage.query.filter_by(booking_id=booking_id)\
                                   .order_by(ChatMessage.created_at.asc())\
                                   .all()
        
        messages_data = []
        for msg in messages:
            # Получаем пользователя через db.session.get() вместо User.query.get()
            user = db.session.get(User, msg.user_id)
            if user:
                messages_data.append({
                    'id': msg.id,
                    'user_id': msg.user_id,
                    'user_name': user.full_name,
                    'user_initials': user.initials,
                    'message': msg.message,
                    'timestamp': msg.created_at.strftime('%H:%M'),
                    'date': msg.created_at.strftime('%d.%m.%Y'),
                    'is_read': msg.is_read
                })
        
        return jsonify(messages_data)
        
    except Exception as e:
        print(f"Error loading chat: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@lesson_bp.route('/api/chat/<int:booking_id>/send', methods=['POST'])
@login_required
def send_chat_message(booking_id):
    """Отправка сообщения в чат"""
    try:
        booking = Booking.query.get_or_404(booking_id)
        
        # Проверка доступа
        if not has_lesson_access(current_user, booking):
            return jsonify({'error': 'Нет доступа'}), 403
        
        data = request.get_json()
        if not data:
            return jsonify({'error': 'Нет данных'}), 400
            
        message_text = data.get('message', '').strip()
        
        if not message_text:
            return jsonify({'error': 'Сообщение не может быть пустым'}), 400
        
        if len(message_text) > 1000:
            return jsonify({'error': 'Сообщение слишком длинное'}), 400
        
        # Создаем сообщение
        message = ChatMessage(
            booking_id=booking_id,
            user_id=current_user.id,
            message=message_text
        )
        
        db.session.add(message)
        db.session.commit()
        
        # Получаем данные пользователя
        user = db.session.get(User, current_user.id)
        
        # Подготавливаем данные для отправки
        message_data = {
            'id': message.id,
            'user_id': current_user.id,
            'user_name': user.full_name,
            'user_initials': user.initials,
            'message': message_text,
            'timestamp': datetime.now().strftime('%H:%M'),
            'date': datetime.now().strftime('%d.%m.%Y'),
            'is_read': False
        }
        
        # Отправляем через WebSocket
        from app import socketio
        socketio.emit('new_chat_message', {
            'room': booking.meeting_id,
            'message': message_data
        }, room=booking.meeting_id)
        
        return jsonify({
            'success': True,
            'message': message_data
        })
        
    except Exception as e:
        db.session.rollback()
        print(f"Error sending message: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500


@lesson_bp.route('/api/chat/<int:booking_id>/mark-read', methods=['POST'])
@login_required
def mark_messages_read(booking_id):
    """Отметить сообщения как прочитанные"""
    try:
        booking = Booking.query.get_or_404(booking_id)
        
        # Проверка доступа
        if not has_lesson_access(current_user, booking):
            response = jsonify({'error': 'Нет доступа'})
            response.status_code = 403
            response.headers.add('Content-Type', 'application/json')
            return response
        
        # Отмечаем все непрочитанные сообщения от других пользователей
        ChatMessage.query.filter_by(
            booking_id=booking_id,
            is_read=False
        ).filter(ChatMessage.user_id != current_user.id)\
         .update({'is_read': True})
        
        db.session.commit()
        
        # Импортируем socketio
        from app import socketio
        
        # Уведомляем других участников
        socketio.emit('messages_read', {
            'room': booking.meeting_id,
            'user_id': current_user.id
        }, room=booking.meeting_id)
        
        response = jsonify({'success': True})
        response.headers.add('Content-Type', 'application/json')
        return response
        
    except Exception as e:
        db.session.rollback()
        print(f"Error marking messages as read: {e}")
        response = jsonify({'error': str(e)})
        response.status_code = 500
        response.headers.add('Content-Type', 'application/json')
        return response


@lesson_bp.route('/end/<int:booking_id>')
@login_required
def end(booking_id):
    """Завершение урока"""
    booking = Booking.query.get_or_404(booking_id)
    
    if current_user.role == 'tutor':
        tutor = Tutor.query.filter_by(user_id=current_user.id).first()
        if tutor and booking.tutor_id == tutor.id:
            booking.meeting_ended = True
            booking.status = 'completed'
            db.session.commit()
            flash('Урок завершен!', 'success')
        else:
            flash('Вы не можете завершить этот урок!', 'danger')
    else:
        flash('Только репетитор может завершить урок!', 'danger')
    
    return redirect(url_for('dashboard.dashboard'))


@lesson_bp.route('/cancel/<int:booking_id>', methods=['POST'])
@login_required
def cancel(booking_id):
    """Отмена урока"""
    booking = Booking.query.get_or_404(booking_id)
    
    if current_user.role != 'student' or booking.student_id != current_user.id:
        flash('У вас нет прав для отмены!', 'danger')
        return redirect(url_for('dashboard.dashboard'))
    
    if booking.status in ['completed', 'cancelled']:
        flash('Этот урок уже завершен или отменен!', 'danger')
        return redirect(url_for('dashboard.dashboard'))
    
    booking.status = 'cancelled'
    db.session.commit()
    
    flash('Урок отменен!', 'success')
    return redirect(url_for('dashboard.dashboard'))


@lesson_bp.route('/upload-material/<int:booking_id>', methods=['POST'])
@login_required
def upload_material(booking_id):
    """Загрузка материала"""
    booking = Booking.query.get_or_404(booking_id)
    
    # Проверка доступа
    if not has_lesson_access(current_user, booking):
        flash('У вас нет доступа!', 'danger')
        return redirect(url_for('dashboard.dashboard'))
    
    if 'file' not in request.files:
        flash('Файл не выбран!', 'danger')
        return redirect(url_for('lesson.room', booking_id=booking_id))
    
    file = request.files['file']
    if file.filename == '':
        flash('Файл не выбран!', 'danger')
        return redirect(url_for('lesson.room', booking_id=booking_id))
    
    # Разрешенные расширения
    allowed = {'pdf', 'doc', 'docx', 'txt', 'jpg', 'jpeg', 'png', 'ppt', 'pptx'}
    
    if '.' in file.filename and file.filename.rsplit('.', 1)[1].lower() in allowed:
        filename = secure_filename(file.filename)
        unique_filename = f"{uuid.uuid4().hex}_{filename}"
        
        # Создаем директорию если её нет
        os.makedirs('uploads', exist_ok=True)
        
        file_path = os.path.join('uploads', unique_filename)
        file.save(file_path)
        
        material = LessonMaterial(
            booking_id=booking_id,
            filename=unique_filename,
            original_filename=filename,
            file_path=file_path,
            uploaded_by=current_user.id
        )
        
        db.session.add(material)
        db.session.commit()
        
        flash('Файл загружен!', 'success')
    else:
        flash('Недопустимый тип файла!', 'danger')
    
    return redirect(url_for('lesson.room', booking_id=booking_id))

@lesson_bp.route('/download-material/<int:material_id>')
@login_required
def download_material(material_id):
    """Скачивание материала"""
    material = LessonMaterial.query.get_or_404(material_id)
    booking = material.booking
    
    # Проверка доступа
    if not has_lesson_access(current_user, booking):
        flash('У вас нет доступа!', 'danger')
        return redirect(url_for('dashboard.dashboard'))
    
    return send_from_directory(
        'uploads',
        material.filename,
        as_attachment=True,
        download_name=material.original_filename
    )


def has_lesson_access(user, booking):
    """Проверка доступа к уроку"""
    if user.role == 'student' and booking.student_id == user.id:
        return True
    elif user.role == 'tutor':
        tutor = Tutor.query.filter_by(user_id=user.id).first()
        return tutor and booking.tutor_id == tutor.id
    return False