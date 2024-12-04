from app import db
from datetime import datetime

class Child(db.Model):
    __tablename__ = 'child'
    
    id = db.Column(db.Integer, primary_key=True)
    first_name = db.Column(db.String(64), nullable=False)
    last_name = db.Column(db.String(64), nullable=False)
    birth_date = db.Column(db.Date, nullable=False)
    color = db.Column(db.String(20))  # Ajout du champ color
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    # Relations
    family_id = db.Column(db.Integer, db.ForeignKey('family.id'), nullable=False)
    family = db.relationship('Family', backref='family_children')

    def __repr__(self):
        return f'<Child {self.first_name} {self.last_name}>'

    def to_dict(self):
        return {
            'id': self.id,
            'first_name': self.first_name,
            'last_name': self.last_name,
            'birth_date': self.birth_date.strftime('%Y-%m-%d') if self.birth_date else None,
            'color': self.color,
            'family_id': self.family_id
        }

    @staticmethod
    def get_color_choices():
        return [
            '#FF6B6B',  # Rouge clair
            '#4ECDC4',  # Turquoise
            '#95E1D3',  # Vert menthe
            '#F7D794',  # Jaune pâle
            '#786FA6',  # Violet
            '#F8A5C2'   # Rose
        ]