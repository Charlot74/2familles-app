from app import db
from datetime import datetime, timedelta
import secrets

class CoparentInvitation(db.Model):
    __tablename__ = 'coparent_invitations'

    id = db.Column(db.Integer, primary_key=True)
    token = db.Column(db.String(100), unique=True, nullable=False)
    sender_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    recipient_email = db.Column(db.String(120), nullable=False)
    status = db.Column(db.String(20), default='pending')  # pending, accepted, rejected, expired
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    expires_at = db.Column(db.DateTime)
    accepted_at = db.Column(db.DateTime)
    rejected_at = db.Column(db.DateTime)

    # Relations
    sender = db.relationship('User', 
                           foreign_keys=[sender_id],
                           backref=db.backref('invitations_sent', lazy='dynamic'))

    def __init__(self, **kwargs):
        super(CoparentInvitation, self).__init__(**kwargs)
        self.token = secrets.token_urlsafe(32)
        self.expires_at = datetime.utcnow() + timedelta(days=7)

    def __repr__(self):
        return f'<CoparentInvitation {self.recipient_email}>'

    @property
    def is_expired(self):
        return datetime.utcnow() > self.expires_at

    @property
    def is_pending(self):
        return self.status == 'pending' and not self.is_expired

    def accept(self):
        """Accepte l'invitation si elle est toujours valide"""
        if not self.is_pending:
            return False
        self.status = 'accepted'
        self.accepted_at = datetime.utcnow()
        return True

    def reject(self):
        """Rejette l'invitation si elle est toujours valide"""
        if not self.is_pending:
            return False
        self.status = 'rejected'
        self.rejected_at = datetime.utcnow()
        return True

    def expire(self):
        """Marque l'invitation comme expirée"""
        if self.status == 'pending':
            self.status = 'expired'
            return True
        return False

    @staticmethod
    def get_by_token(token):
        """Récupère une invitation par son token"""
        return CoparentInvitation.query.filter_by(token=token).first()

    @staticmethod
    def get_pending_for_email(email):
        """Récupère les invitations en attente pour un email"""
        return CoparentInvitation.query.filter_by(
            recipient_email=email,
            status='pending'
        ).first()

    def to_dict(self):
        """Convertit l'invitation en dictionnaire"""
        return {
            'id': self.id,
            'sender_id': self.sender_id,
            'recipient_email': self.recipient_email,
            'status': self.status,
            'created_at': self.created_at.isoformat(),
            'expires_at': self.expires_at.isoformat(),
            'accepted_at': self.accepted_at.isoformat() if self.accepted_at else None,
            'rejected_at': self.rejected_at.isoformat() if self.rejected_at else None,
            'is_expired': self.is_expired,
            'is_pending': self.is_pending,
            'sender': {
                'id': self.sender.id,
                'email': self.sender.email,
                'name': f"{self.sender.first_name} {self.sender.last_name}"
            } if self.sender else None
        }

    def notify_sender(self):
        """Envoie une notification au sender"""
        from app.utils.email import send_invitation_status_email
        send_invitation_status_email(self)

    def notify_recipient(self):
        """Envoie une notification au recipient"""
        from app.utils.email import send_invitation_email
        send_invitation_email(self)

    def validate_token(self, token):
        """Vérifie si le token est valide"""
        return secrets.compare_digest(self.token, token)

    @property
    def time_remaining(self):
        """Retourne le temps restant avant expiration"""
        if self.is_expired:
            return timedelta(0)
        return self.expires_at - datetime.utcnow()

    @property
    def status_display(self):
        """Retourne le statut pour affichage"""
        if self.is_expired:
            return 'Expirée'
        status_map = {
            'pending': 'En attente',
            'accepted': 'Acceptée',
            'rejected': 'Rejetée',
            'expired': 'Expirée'
        }
        return status_map.get(self.status, self.status)