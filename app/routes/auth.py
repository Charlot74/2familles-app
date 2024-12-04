from flask import Blueprint, render_template, flash, redirect, url_for, request
from flask_login import login_user, logout_user, current_user, login_required
from werkzeug.urls import url_parse
from app import db
from app.models.user import User
from app.models.family import Family  # Changé de FamilyInfo à Family

bp = Blueprint('auth', __name__)

@bp.route('/login', methods=['GET', 'POST'])
def login():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user is None or not user.check_password(request.form['password']):
            flash('Email ou mot de passe invalide', 'danger')
            return redirect(url_for('auth.login'))
            
        login_user(user)
        next_page = request.args.get('next')
        if not next_page or url_parse(next_page).netloc != '':
            next_page = url_for('main.dashboard')
        return redirect(next_page)
        
    return render_template('auth/login.html', title='Connexion')

@bp.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('main.index'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
        
    if request.method == 'POST':
        # Créer une nouvelle famille
        family = Family(name=f"Famille {request.form['username']}")
        db.session.add(family)
        db.session.flush()  # Pour obtenir l'ID de la famille
        
        # Créer le nouvel utilisateur
        user = User(
            username=request.form['username'],
            email=request.form['email'],
            family_id=family.id
        )
        user.set_password(request.form['password'])
        db.session.add(user)
        
        try:
            db.session.commit()
            flash('Félicitations, vous êtes maintenant inscrit!', 'success')
            login_user(user)
            return redirect(url_for('main.dashboard'))
        except:
            db.session.rollback()
            flash('Erreur lors de l\'inscription. Veuillez réessayer.', 'danger')
            
    return render_template('auth/register.html', title='Inscription')