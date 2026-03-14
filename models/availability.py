"""
Модель доступности репетитора
"""

from . import db


class Availability(db.Model):
    """Модель доступности"""
    
    __tablename__ = 'availability'
    
    id = db.Column(db.Integer, primary_key=True)
    tutor_id = db.Column(db.Integer, db.ForeignKey('tutors.id'), nullable=False)
    day_of_week = db.Column(db.Integer, nullable=False)  # 0-6 (Monday-Sunday)
    start_time = db.Column(db.Time, nullable=False)
    end_time = db.Column(db.Time, nullable=False)
    
    # Relationship
    tutor = db.relationship('Tutor', back_populates='availability')
    
    def __repr__(self):
        days = ['Пн', 'Вт', 'Ср', 'Чт', 'Пт', 'Сб', 'Вс']
        day_name = days[self.day_of_week]
        return f'<Availability {day_name}: {self.start_time}-{self.end_time}>'