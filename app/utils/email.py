from flask import render_template, current_app
from flask_mail import Message
from threading import Thread
from app import mail

def send_async_email(app, msg):
    with app.app_context():
        try:
            mail.send(msg)
        except Exception as e:
            print(f"Erreur d'envoi d'email: {str(e)}")

def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    Thread(target=send_async_email,
           args=(current_app._get_current_object(), msg)).start()

def send_coparent_invitation_email(sender, recipient_email, recipient_first_name, recipient_last_name):
    """Envoie l'email d'invitation au co-parent"""
    subject = f"{sender.username} vous invite à rejoindre 2familles"
    
    # Générer le texte de l'email
    text_body = f"""
    Bonjour {recipient_first_name},

    Je t'invite à rejoindre 2familles, une plateforme dédiée à la coparentalité. 2familles est un facilitateur de coparentalité qui permet de simplifier le quotidien des parents séparés. Elle propose un agenda partagé, une banque d'informations et des outils pour gérer les finances communes concernant les enfants.

    L'objectif est d'aider les parents à maintenir une communication efficace et constructive, en plaçant l'intérêt de l'enfant au centre de leurs préoccupations.

    J'espère que tu accepteras cette invitation !

    Pour accepter l'invitation, clique sur le lien suivant :
    {url_for('coparent.accept_invitation', token=generate_invitation_token(), _external=True)}
    """

    # Envoyer l'email
    send_email(
        subject=subject,
        sender=current_app.config['MAIL_DEFAULT_SENDER'],
        recipients=[recipient_email],
        text_body=text_body,
        html_body=render_template('email/coparent_invitation.html',
                                sender=sender,
                                recipient_first_name=recipient_first_name,
                                recipient_last_name=recipient_last_name)
    )