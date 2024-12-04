from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models.user import User
from app.models.family import Family
from app.models.child import Child
from app.models.event import Event
from app.models.budget import Budget
from app.models.information import Information
from datetime import datetime, timedelta

# Définition du Blueprint
bp = Blueprint('main', __name__)

@bp.route('/')
@bp.route('/index')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('main.dashboard'))
    return render_template('index.html')

@bp.route('/dashboard')
@login_required
def dashboard():
    # Récupérer la famille de l'utilisateur
    family = current_user.family

    # Récupérer les enfants
    children = Child.query.filter_by(family_id=family.id).all()

    # Récupérer le coparent
    coparent = User.query.filter(
        User.family_id == family.id,
        User.id != current_user.id
    ).first()

    # Récupérer les prochains événements
    upcoming_events = Event.query.filter(
        Event.family_id == family.id,
        Event.start_time >= datetime.now()
    ).order_by(Event.start_time).limit(5).all()

    # Calculer les dépenses du mois avec leurs devises
    start_of_month = datetime.now().replace(day=1, hour=0, minute=0, second=0)
    end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)

    monthly_expenses = Budget.query.filter(
        Budget.family_id == family.id,
        Budget.date.between(start_of_month, end_of_month)
    ).all()

    # Grouper les dépenses par devise
    expenses_by_currency = {}
    for expense in monthly_expenses:
        if expense.currency not in expenses_by_currency:
            expenses_by_currency[expense.currency] = 0
        expenses_by_currency[expense.currency] += expense.amount

    # Formater les totaux avec les symboles de devise
    formatted_expenses = []
    currency_symbols = {'EUR': '€', 'USD': '$', 'CHF': 'Frs.'}
    for currency, amount in expenses_by_currency.items():
        symbol = currency_symbols.get(currency, currency)
        formatted_expenses.append(f"{amount:.2f} {symbol}")

    # Récupérer les informations
    information = Information.query.filter_by(
        family_id=family.id
    ).order_by(Information.created_at.desc()).limit(5).all()

    return render_template('dashboard.html',
                         children=children,
                         coparent=coparent,
                         upcoming_events=upcoming_events,
                         monthly_expenses=formatted_expenses,
                         information=information)

@bp.route('/add_child', methods=['POST'])
@login_required
def add_child():
    try:
        first_name = request.form.get('first_name')
        last_name = request.form.get('last_name')
        birth_date = request.form.get('birth_date')
        color = request.form.get('color')

        if not all([first_name, last_name, birth_date, color]):
            flash('Tous les champs sont requis', 'danger')
            return redirect(url_for('main.dashboard'))

        child = Child(
            first_name=first_name,
            last_name=last_name,
            birth_date=datetime.strptime(birth_date, '%Y-%m-%d'),
            color=color,
            family_id=current_user.family.id
        )

        db.session.add(child)
        db.session.commit()
        flash('Enfant ajouté avec succès !', 'success')

    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de l\'ajout de l\'enfant : {str(e)}', 'danger')

    return redirect(url_for('main.dashboard'))

@bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if request.method == 'POST':
        try:
            current_user.username = request.form.get('username', current_user.username)
            current_user.email = request.form.get('email', current_user.email)

            if request.form.get('password'):
                current_user.set_password(request.form.get('password'))

            current_user.currency = request.form.get('currency', current_user.currency)

            db.session.commit()
            flash('Profil mis à jour avec succès !', 'success')
            return redirect(url_for('main.dashboard'))

        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la mise à jour du profil : {str(e)}', 'danger')

    return render_template('edit_profile.html')

@bp.route('/update_currency/<string:currency>')
@login_required
def update_currency(currency):
    currency_symbols = {'EUR': '€', 'USD': '$', 'CHF': 'Frs.'}
    if currency in currency_symbols:
        current_user.currency = currency
        db.session.commit()
        flash(f'Devise mise à jour en {currency_symbols[currency]}', 'success')
    else:
        flash('Devise non valide', 'error')
    return redirect(url_for('main.dashboard'))

@bp.route('/about')
def about():
    return render_template('about.html')

@bp.route('/contact')
def contact():
    return render_template('contact.html')

@bp.route('/legal')
def legal():
    return render_template('legal/index.html')

@bp.route('/privacy')
def privacy():
    return render_template('legal/privacy.html')

@bp.route('/terms')
def terms():
    return render_template('legal/terms.html')