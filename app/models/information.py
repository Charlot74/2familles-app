from app import db
from datetime import datetime

class Information(db.Model):
    __tablename__ = 'information'

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(50), nullable=False)  # medical, school, document, emergency
    title = db.Column(db.String(200), nullable=False)
    content = db.Column(db.Text)
    file_path = db.Column(db.String(255))  # Chemin du fichier pour les documents
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Clés étrangères
    family_id = db.Column(db.Integer, db.ForeignKey('family.id'), nullable=False)
    child_id = db.Column(db.Integer, db.ForeignKey('child.id'))
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    # Relations
    family = db.relationship('Family', backref='information')
    child = db.relationship('Child', backref='information')
    creator = db.relationship('User', backref='created_information')

    def __repr__(self):
        return f'<Information {self.type}: {self.title}>'

    def to_dict(self):
        return {
            'id': self.id,
            'type': self.type,
            'title': self.title,
            'content': self.content,
            'file_path': self.file_path,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None,
            'family_id': self.family_id,
            'child_id': self.child_id,
            'creator_id': self.creator_id
        }

    def get_file_url(self):
        if self.file_path:
            return f'/static/uploads/{self.file_path}'
        return None