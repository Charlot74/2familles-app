from flask import jsonify, request, url_for, current_app
from app import db
from app.api import bp
from app.models.user import User
from app.models.family import Family
from app.models.coparent_invitation import CoparentInvitation
from app.api.errors import bad_request, error_response
from datetime import datetime, timedelta
import jwt
import secrets

@bp.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    
    # Validation des données requises
    if not data or not all(k in data for k in ('email', 'password', 'username')):
        return bad_request('Les champs email, password et username sont requis')
    
    # Vérifier si l'email existe déjà
    if User.query.filter_by(email=data['email']).first():
        return bad_request('Cet email est déjà utilisé')

    try:
        # Créer une nouvelle famille
        family = Family(name=f"Famille {data['username']}")
        db.session.add(family)
        db.session.flush()  # Pour obtenir l'ID de la famille

        # Créer le nouvel utilisateur
        user = User(
            username=data['username'],
            email=data['email'],
            family_id=family.id
        )
        user.set_password(data['password'])
        
        db.session.add(user)
        db.session.commit()

        # Générer le token
        token = user.get_token()
        
        return jsonify({
            'message': 'Inscription réussie',
            'user_id': user.id,
            'family_id': family.id,
            'token': token,
            'email': user.email
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return error_response(500, str(e))

@bp.route('/invite-coparent', methods=['POST'])
def invite_coparent():
    data = request.get_json()
    
    if not data or not all(k in data for k in ('email', 'family_id', 'sender_id')):
        return bad_request('Email, family_id et sender_id sont requis')

    try:
        # Générer un token unique pour l'invitation
        token = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=7)

        invitation = CoparentInvitation(
            sender_id=data['sender_id'],
            recipient_email=data['email'],
            family_id=data['family_id'],
            token=token,
            expires_at=expires_at
        )
        
        db.session.add(invitation)
        db.session.commit()

        # Ici, vous pouvez ajouter l'envoi d'email avec le lien d'invitation
        invitation_link = url_for('auth.join_family', token=token, _external=True)

        return jsonify({
            'message': 'Invitation envoyée avec succès',
            'invitation_id': invitation.id,
            'invitation_link': invitation_link,
            'expires_at': expires_at.isoformat()
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return error_response(500, str(e))

@bp.route('/join-family/<token>', methods=['POST'])
def join_family():
    data = request.get_json()
    
    if not data or not all(k in data for k in ('email', 'password', 'username')):
        return bad_request('Email, password et username sont requis')

    invitation = CoparentInvitation.query.filter_by(token=token, accepted=False).first()
    
    if not invitation or invitation.expires_at < datetime.utcnow():
        return bad_request('Invitation invalide ou expirée')

    if invitation.recipient_email != data['email']:
        return bad_request('Email ne correspond pas à l\'invitation')

    try:
        # Créer le compte du coparent
        coparent = User(
            username=data['username'],
            email=data['email'],
            family_id=invitation.family_id
        )
        coparent.set_password(data['password'])
        
        # Marquer l'invitation comme acceptée
        invitation.accepted = True
        invitation.accepted_at = datetime.utcnow()
        
        db.session.add(coparent)
        db.session.commit()

        # Générer le token
        token = coparent.get_token()
        
        return jsonify({
            'message': 'Compte coparent créé avec succès',
            'user_id': coparent.id,
            'family_id': invitation.family_id,
            'token': token,
            'email': coparent.email
        }), 201
        
    except Exception as e:
        db.session.rollback()
        return error_response(500, str(e))

@bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    
    if not data or not all(k in data for k in ('email', 'password')):
        return bad_request('Email et password sont requis')

    user = User.query.filter_by(email=data['email']).first()
    
    if user is None or not user.check_password(data['password']):
        return bad_request('Email ou mot de passe invalide')

    token = user.get_token()

    return jsonify({
        'token': token,
        'user_id': user.id,
        'family_id': user.family_id,
        'email': user.email,
        'username': user.username
    })