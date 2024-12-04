from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models.expense import Expense
from datetime import datetime

bp = Blueprint('expenses', __name__, url_prefix='/expenses')

@bp.route('/')
@login_required
def index():
    expenses = Expense.query.filter_by(family_id=current_user.user_family.id).all()
    return render_template('expenses/index.html', expenses=expenses)

@bp.route('/add', methods=['POST'])
@login_required
def add_expense():
    try:
        expense = Expense(
            title=request.form['title'],
            amount=float(request.form['amount']),
            category=request.form.get('category', 'Autre'),
            description=request.form.get('description', ''),
            date=datetime.strptime(request.form['date'], '%Y-%m-%d'),
            creator_id=current_user.id,
            family_id=current_user.user_family.id
        )
        db.session.add(expense)
        db.session.commit()
        flash('Dépense ajoutée avec succès', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de l\'ajout de la dépense : {str(e)}', 'danger')
    
    return redirect(url_for('dashboard'))