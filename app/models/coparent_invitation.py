from app import db
from datetime import datetime

class CoparentInvitation(db.Model):
    __tablename__ = 'coparent_invitations'
    
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_email = db.Column(db.String(120), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    accepted_at = db.Column(db.DateTime)
    expired_at = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected, expired

    # Relations
    sender = db.relationship('User', backref='sent_invitations', foreign_keys=[sender_id])

    def __repr__(self):
        return f'<CoparentInvitation {self.id} from {self.sender_id} to {self.recipient_email}>'

    def to_dict(self):
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'recipient_email': self.recipient_email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'accepted_at': self.accepted_at.isoformat() if self.accepted_at else None,
            'expired_at': self.expired_at.isoformat() if self.expired_at else None,
            'status': self.status
        }