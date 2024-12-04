from app import db
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, timedelta
import jwt
from flask import current_app

CURRENCY_CHOICES = {
    'EUR': '€',
    'USD': '$',
    'CHF': 'Fr.'
}

class User(UserMixin, db.Model):
    __tablename__ = 'user'

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(64), index=True, unique=True)
    email = db.Column(db.String(120), index=True, unique=True)
    password_hash = db.Column(db.String(128))
    family_id = db.Column(db.Integer, db.ForeignKey('family.id'))
    currency = db.Column(db.String(3), default='EUR')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_seen = db.Column(db.DateTime, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    is_admin = db.Column(db.Boolean, default=False)  # Nouveau champ
    first_name = db.Column(db.String(64))
    last_name = db.Column(db.String(64))
    phone = db.Column(db.String(20))
    address = db.Column(db.String(256))
    reset_password_token = db.Column(db.String(100), unique=True)
    reset_password_expires = db.Column(db.DateTime)

    # Relations
    family = db.relationship('Family', backref='members')
    events_created = db.relationship('Event', backref='creator',
                                   foreign_keys='Event.creator_id',
                                   lazy='dynamic')
    messages_sent = db.relationship('Message',
                                  foreign_keys='Message.sender_id',
                                  backref='sender',
                                  lazy='dynamic')
    messages_received = db.relationship('Message',
                                      foreign_keys='Message.recipient_id',
                                      backref='recipient',
                                      lazy='dynamic')
    information_created = db.relationship('Information',
                                        foreign_keys='Information.creator_id',
                                        backref='creator',
                                        lazy='dynamic')
    budget_items_created = db.relationship('Budget',
                                         foreign_keys='Budget.creator_id',
                                         backref='creator',
                                         lazy='dynamic')
    sent_invitations = db.relationship('CoparentInvitation',
                                     foreign_keys='CoparentInvitation.sender_id',
                                     backref='sender',
                                     lazy='dynamic')

    def __repr__(self):
        return f'<User {self.username}>'

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    def get_token(self, expires_in=3600):
        now = datetime.utcnow()
        if self.reset_password_token and self.reset_password_expires > now + timedelta(seconds=60):
            return self.reset_password_token
        payload = {
            'user_id': self.id,
            'email': self.email,
            'exp': now + timedelta(seconds=expires_in),
            'iat': now,
            'is_admin': self.is_admin  # Inclure is_admin dans le token
        }
        token = jwt.encode(
            payload,
            current_app.config['SECRET_KEY'],
            algorithm='HS256'
        )
        self.reset_password_token = token
        self.reset_password_expires = now + timedelta(seconds=expires_in)
        db.session.commit()
        return token

    @staticmethod
    def verify_token(token):
        try:
            payload = jwt.decode(
                token,
                current_app.config['SECRET_KEY'],
                algorithms=['HS256']
            )
            user = User.query.get(payload['user_id'])
            if user and user.is_active:  # Vérifier que l'utilisateur est actif
                return user
            return None
        except:
            return None

    def get_reset_password_token(self, expires_in=3600):
        return self.get_token(expires_in)

    @property
    def currency_symbol(self):
        return CURRENCY_CHOICES.get(self.currency, '€')

    def get_unread_messages_count(self):
        return Message.query.filter_by(
            recipient_id=self.id,
            read=False
        ).count()

    def get_children(self):
        from app.models.child import Child
        return Child.query.filter_by(family_id=self.family_id).all()

    def get_coparent(self):
        if not self.family_id:
            return None
        return User.query.filter(
            User.family_id == self.family_id,
            User.id != self.id
        ).first()

    def get_monthly_expenses(self, year=None, month=None):
        from app.models.budget import Budget
        if year is None:
            year = datetime.now().year
        if month is None:
            month = datetime.now().month

        start_date = datetime(year, month, 1)
        if month == 12:
            end_date = datetime(year + 1, 1, 1)
        else:
            end_date = datetime(year, month + 1, 1)

        return Budget.query.filter(
            Budget.family_id == self.family_id,
            Budget.date >= start_date,
            Budget.date < end_date
        ).all()

    def get_full_name(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        return self.username

    def update_last_seen(self):
        self.last_seen = datetime.utcnow()
        db.session.commit()

    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'family_id': self.family_id,
            'currency': self.currency,
            'currency_symbol': self.currency_symbol,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'phone': self.phone,
            'address': self.address,
            'is_admin': self.is_admin,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'last_seen': self.last_seen.isoformat() if self.last_seen else None
        }

    def from_dict(self, data):
        for field in ['username', 'email', 'first_name', 'last_name', 'phone', 'address', 'currency']:
            if field in data:
                setattr(self, field, data[field])
        if 'password' in data:
            self.set_password(data['password'])

    @property
    def is_administrator(self):
        """Helper pour vérifier si l'utilisateur est un administrateur"""
        return self.is_admin