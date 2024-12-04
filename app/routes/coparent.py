from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.family import Family
from app.utils.email import send_coparent_invitation_email
from datetime import datetime

bp = Blueprint('coparent', __name__, url_prefix='/coparent')

@bp.route('/invite', methods=['POST'])
@login_required
def invite_coparent():
    # Récupérer les données du formulaire
    first_name = request.form.get('first_name')
    last_name = request.form.get('last_name')
    email = request.form.get('email')

    # Vérifier que tous les champs sont remplis
    if not all([first_name, last_name, email]):
        flash('Tous les champs sont requis.', 'error')
        return redirect(url_for('main.dashboard'))

    # Vérifier si l'utilisateur a déjà un co-parent
    coparent = current_user.get_coparent()
    if coparent:
        flash('Vous avez déjà un co-parent associé.', 'error')
        return redirect(url_for('main.dashboard'))

    # Vérifier si l'utilisateur existe déjà
    existing_user = User.query.filter_by(email=email).first()
    if existing_user:
        flash('Un utilisateur avec cette adresse email existe déjà.', 'error')
        return redirect(url_for('main.dashboard'))

    try:
        # Envoyer l'invitation par email avec les nouvelles informations
        send_coparent_invitation_email(
            current_user,
            recipient_email=email,
            recipient_first_name=first_name,
            recipient_last_name=last_name
        )
        flash(f'Invitation envoyée à {first_name} {last_name} ({email})', 'success')
    except Exception as e:
        flash(f'Erreur lors de l\'envoi de l\'invitation: {str(e)}', 'error')

    return redirect(url_for('main.dashboard'))