from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models.family import FamilyInfo, CoparentInvitation
from app.models.user import User
from app.utils.email import send_invitation_email

bp = Blueprint('family', __name__, url_prefix='/family')

@bp.route('/invite', methods=['POST'])
@login_required
def invite_coparent():
    email = request.form.get('email')
    if not email:
        flash('L\'adresse email est requise.', 'error')
        return redirect(url_for('main.dashboard'))

    # Vérifier si l'utilisateur a déjà un co-parent
    family_info = FamilyInfo.query.filter_by(user_id=current_user.id).first()
    if family_info and family_info.coparent_id:
        flash('Vous avez déjà un co-parent associé.', 'error')
        return redirect(url_for('main.dashboard'))

    # Vérifier si une invitation est déjà en cours
    existing_invitation = CoparentInvitation.query.filter_by(
        inviter_id=current_user.id,
        email=email,
        status='pending'
    ).first()
    
    if existing_invitation:
        flash('Une invitation a déjà été envoyée à cette adresse email.', 'info')
        return redirect(url_for('main.dashboard'))

    # Créer la nouvelle invitation
    invitation = CoparentInvitation(
        inviter_id=current_user.id,
        email=email
    )
    db.session.add(invitation)
    db.session.commit()

    # Envoyer l'email d'invitation
    send_invitation_email(invitation)
    flash('L\'invitation a été envoyée avec succès.', 'success')
    return redirect(url_for('main.dashboard'))

@bp.route('/accept/<token>')
def accept_invitation(token):
    invitation = CoparentInvitation.get_by_token(token)
    
    if not invitation or not invitation.is_valid():
        flash('Cette invitation n\'est plus valide.', 'error')
        return redirect(url_for('main.index'))

    # Si l'utilisateur est déjà connecté
    if current_user.is_authenticated:
        if current_user.email != invitation.email:
            flash('Cette invitation ne vous est pas destinée.', 'error')
            return redirect(url_for('main.dashboard'))
            
        # Lier les utilisateurs comme co-parents
        family_info = FamilyInfo.query.filter_by(user_id=invitation.inviter_id).first()
        if family_info:
            family_info.coparent_id = current_user.id
            invitation.status = 'accepted'
            db.session.commit()
            flash('Vous êtes maintenant lié comme co-parent.', 'success')
            return redirect(url_for('main.dashboard'))
            
    # Si l'utilisateur n'est pas connecté, rediriger vers l'inscription
    return redirect(url_for('auth.register', invitation_token=token))