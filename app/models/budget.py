from app import db
from datetime import datetime

class Budget(db.Model):
    __tablename__ = 'budget'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    amount = db.Column(db.Float, nullable=False)
    description = db.Column(db.Text)
    date = db.Column(db.Date, nullable=False)
    category = db.Column(db.String(50), nullable=False)
    currency = db.Column(db.String(3), nullable=False, default='EUR')
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    family_id = db.Column(db.Integer, db.ForeignKey('family.id'), nullable=False)
    child_id = db.Column(db.Integer, db.ForeignKey('child.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    creator = db.relationship('User', backref='created_expenses', foreign_keys=[creator_id])
    family = db.relationship('Family', backref='family_expenses')
    child = db.relationship('Child', backref='child_expenses')

    def __repr__(self):
        return f'<Budget {self.title}: {self.amount} {self.get_currency_symbol()}>'

    def get_currency_symbol(self):
        symbols = {
            'EUR': '€',
            'USD': '$',
            'CHF': 'Frs.'
        }
        return symbols.get(self.currency, '€')

    def formatted_amount(self):
        return f"{self.amount:.2f} {self.get_currency_symbol()}"

    def formatted_date(self):
        return self.date.strftime('%d/%m/%Y')