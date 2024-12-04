from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for
from flask_login import login_required, current_user
from app import db
from app.models.family import Family
from app.models.expense import Expense
from datetime import datetime, timedelta

bp = Blueprint('finances', __name__, url_prefix='/finances')

@bp.route('/')
@login_required
def index():
    # Récupérer le total des dépenses du mois en cours
    start_of_month = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0)
    end_of_month = (start_of_month + timedelta(days=32)).replace(day=1) - timedelta(seconds=1)
    expenses = Expense.query.filter(
        Expense.family_id == current_user.family_id,
        Expense.date.between(start_of_month, end_of_month)
    ).all()
    
    total_expenses = sum(expense.amount for expense in expenses)
    expenses_by_category = {}
    for expense in expenses:
        if expense.category not in expenses_by_category:
            expenses_by_category[expense.category] = 0
        expenses_by_category[expense.category] += expense.amount

    return render_template('finances/index.html',
                         expenses=expenses,
                         total_expenses=total_expenses,
                         expenses_by_category=expenses_by_category)

@bp.route('/summary', methods=['GET'])
@login_required
def get_summary():
    period = request.args.get('period', 'month')
    if period == 'month':
        start_date = datetime.utcnow().replace(day=1)
    elif period == 'year':
        start_date = datetime.utcnow().replace(month=1, day=1)
    else:
        start_date = datetime.utcnow() - timedelta(days=30)

    expenses = Expense.query.filter(
        Expense.family_id == current_user.family_id,
        Expense.date >= start_date
    ).all()

    summary = {
        'total': sum(expense.amount for expense in expenses),
        'by_category': {}
    }

    for expense in expenses:
        if expense.category not in summary['by_category']:
            summary['by_category'][expense.category] = 0
        summary['by_category'][expense.category] += expense.amount

    return jsonify(summary)

@bp.route('/export')
@login_required
def export_data():
    flash('Export non disponible pour le moment', 'info')
    return redirect(url_for('finances.index'))