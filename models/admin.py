"""
Модель для администраторов
"""

from . import db
from datetime import datetime


class AdminLog(db.Model):
    """Лог действий администратора"""
    
    __tablename__ = 'admin_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    admin_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    action = db.Column(db.String(100), nullable=False)
    target_type = db.Column(db.String(50))
    target_id = db.Column(db.Integer)
    details = db.Column(db.Text)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationship
    admin = db.relationship('User', back_populates='admin_logs')
    
    def __repr__(self):
        return f'<AdminLog {self.id}: {self.action}>'