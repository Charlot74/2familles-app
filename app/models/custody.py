from app import db
from datetime import datetime

class CustodySchedule(db.Model):
    __tablename__ = 'custody_schedules'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    child_id = db.Column(db.Integer, db.ForeignKey('family_info.id'), nullable=False)
    start_date = db.Column(db.DateTime, nullable=False)
    end_date = db.Column(db.DateTime, nullable=False)
    type = db.Column(db.String(50), default='regular')
    status = db.Column(db.String(50), default='confirmed')
    description = db.Column(db.String(500))
    color = db.Column(db.String(20), default='#BB2D0C')
    recurrence = db.Column(db.String(50))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relations
    parent = db.relationship('User', backref='custody_schedules')  # Changé de user à parent
    child = db.relationship('FamilyInfo', backref='custody_schedules')

    def to_dict(self):
        return {
            'id': self.id,
            'child_id': self.child_id,
            'start_date': self.start_date.isoformat(),
            'end_date': self.end_date.isoformat(),
            'type': self.type,
            'status': self.status,
            'description': self.description,
            'color': self.color,
            'recurrence': self.recurrence,
            'created_at': self.created_at.isoformat(),
            'updated_at': self.updated_at.isoformat()
        }