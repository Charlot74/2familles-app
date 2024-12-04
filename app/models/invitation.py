from app import db
from datetime import datetime, timedelta
import secrets

class Invitation(db.Model):
    __tablename__ = 'invitations'

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), nullable=False)
    token = db.Column(db.String(100), unique=True, nullable=False)
    inviter_id = db.Column(db.Integer, db.ForeignKey('users.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, expired
    accepted_at = db.Column(db.DateTime)

    # Relations
    inviter = db.relationship('User', backref=db.backref('invitations', lazy='dynamic'))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.token = secrets.token_urlsafe(32)
        self.expires_at = datetime.utcnow() + timedelta(days=7)

    @property
    def is_expired(self):
        return datetime.utcnow() > self.expires_at

    @property
    def is_pending(self):
        return self.status == 'pending' and not self.is_expired

    def accept(self):
        if self.is_pending:
            self.status = 'accepted'
            self.accepted_at = datetime.utcnow()
            return True
        return False

    @staticmethod
    def get_by_token(token):
        return Invitation.query.filter_by(token=token).first()
