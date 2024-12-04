from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.invitation import Invitation
from app.models.user import User
from app.models.family import FamilyInfo
from app.utils.email import send_invitation_email
from datetime import datetime

bp = Blueprint('invitation', __name__, url_prefix='/invitation')

@bp.route('/send', methods=['POST'])
@login_required
def send_invitation():
    email = request.form.get('email')
    if not email:
        flash('L\'adresse email est requise.', 'error')
        return redirect(url_for('main.dashboard'))

    # Vérifier si l'utilisateur existe déjà
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash('Un compte existe déjà avec cette adresse email.', 'warning')
        return redirect(url_for('main.dashboard'))

    # Vérifier si une invitation est en cours
    existing_invitation = Invitation.get_pending_for_email(email)
    if existing_invitation:
        flash('Une invitation est déjà en cours pour cette adresse email.', 'info')
        return redirect(url_for('main.dashboard'))

    # Créer et envoyer l'invitation
    invitation = Invitation(
        email=email,
        inviter_id=current_user.id
    )
    db.session.add(invitation)

    try:
        db.session.commit()
        send_invitation_email(invitation)
        flash('Invitation envoyée avec succès !', 'success')
    except Exception as e:
        db.session.rollback()
        flash('Erreur lors de l\'envoi de l\'invitation.', 'error')

    return redirect(url_for('main.dashboard'))

@bp.route('/cancel/<int:invitation_id>', methods=['POST'])
@login_required
def cancel_invitation(invitation_id):
    invitation = Invitation.query.get_or_404(invitation_id)
    
    if invitation.inviter_id != current_user.id:
        flash('Vous n\'avez pas l\'autorisation d\'annuler cette invitation.', 'error')
        return redirect(url_for('main.dashboard'))

    if invitation.cancel():
        db.session.commit()
        flash('Invitation annulée avec succès.', 'success')
    else:
        flash('Impossible d\'annuler cette invitation.', 'error')

    return redirect(url_for('main.dashboard'))

@bp.route('/accept/<token>')
def accept_invitation(token):
    invitation = Invitation.get_by_token(token)
    
    if not invitation:
        flash('Invitation invalide ou expirée.', 'error')
        return redirect(url_for('main.index'))

    if not invitation.is_pending:
        flash('Cette invitation n\'est plus valide.', 'error')
        return redirect(url_for('main.index'))

    if current_user.is_authenticated:
        if current_user.email != invitation.email:
            flash('Cette invitation ne vous est pas destinée.', 'error')
            return redirect(url_for('main.dashboard'))

        # Créer la relation co-parent
        family_info = FamilyInfo.query.filter_by(user_id=invitation.inviter_id).first()
        if not family_info:
            family_info = FamilyInfo(
                user_id=invitation.inviter_id,
                coparent_id=current_user.id,
                status='active'
            )
            db.session.add(family_info)
        else:
            family_info.coparent_id = current_user.id
            family_info.status = 'active'

        invitation.accept()
        db.session.commit()
        
        flash('Invitation acceptée ! Vous êtes maintenant co-parent.', 'success')
        return redirect(url_for('main.dashboard'))

    # Si non connecté, rediriger vers l'inscription
    return redirect(url_for('auth.register', invitation_token=token))

@bp.route('/status/<int:invitation_id>')
@login_required
def check_status(invitation_id):
    invitation = Invitation.query.get_or_404(invitation_id)
    if invitation.inviter_id != current_user.id:
        return jsonify({'error': 'Non autorisé'}), 403
    return jsonify(invitation.to_dict())

@bp.route('/list')
@login_required
def list_invitations():
    invitations = current_user.sent_invitations.order_by(Invitation.created_at.desc()).all()
    return render_template('invitation/list.html', invitations=invitations)