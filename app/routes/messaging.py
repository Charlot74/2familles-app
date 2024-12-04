from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models.message import Message
from app.models.user import User
from datetime import datetime

bp = Blueprint('messaging', __name__, url_prefix='/messaging')

@bp.route('/')
@login_required
def index():
    messages = Message.query.filter(
        (Message.recipient_id == current_user.id) | 
        (Message.sender_id == current_user.id)
    ).order_by(Message.timestamp.desc()).all()
    return render_template('messaging/index.html', messages=messages)

@bp.route('/send', methods=['GET', 'POST'])
@login_required
def send_message():
    if request.method == 'POST':
        recipient_id = request.form.get('recipient_id')
        content = request.form.get('content')
        
        if not recipient_id or not content:
            flash('Tous les champs sont requis', 'error')
            return redirect(url_for('messaging.send_message'))
        
        message = Message(
            sender_id=current_user.id,
            recipient_id=recipient_id,
            content=content
        )
        
        db.session.add(message)
        db.session.commit()
        flash('Message envoyé avec succès', 'success')
        return redirect(url_for('messaging.index'))
    
    # Pour le formulaire GET, récupérer la liste des destinataires possibles
    recipients = User.query.filter(User.id != current_user.id).all()
    return render_template('messaging/send.html', recipients=recipients)

@bp.route('/view/<int:message_id>')
@login_required
def view_message(message_id):
    message = Message.query.get_or_404(message_id)
    if message.recipient_id != current_user.id and message.sender_id != current_user.id:
        flash('Vous n\'êtes pas autorisé à voir ce message', 'error')
        return redirect(url_for('messaging.index'))
    
    if message.recipient_id == current_user.id and not message.read:
        message.read = True
        message.read_at = datetime.utcnow()
        db.session.commit()
    
    return render_template('messaging/view.html', message=message)

@bp.route('/delete/<int:message_id>')
@login_required
def delete_message(message_id):
    message = Message.query.get_or_404(message_id)
    if message.recipient_id != current_user.id and message.sender_id != current_user.id:
        flash('Vous n\'êtes pas autorisé à supprimer ce message', 'error')
        return redirect(url_for('messaging.index'))
    
    db.session.delete(message)
    db.session.commit()
    flash('Message supprimé avec succès', 'success')
    return redirect(url_for('messaging.index'))