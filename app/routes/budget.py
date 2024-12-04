from flask import Blueprint, render_template, request, flash, redirect, url_for, send_file
from flask_login import login_required, current_user
from app import db
from app.models.budget import Budget
from app.models.child import Child
from datetime import datetime
import csv
from io import StringIO, BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

bp = Blueprint('budget', __name__, url_prefix='/budget')

CURRENCIES = {
    'EUR': '€',
    'USD': '$',
    'CHF': 'Frs.'
}

@bp.route('/')
@login_required
def index():
    expenses = Budget.query.filter_by(family_id=current_user.family.id)\
                         .order_by(Budget.date.desc()).all()
    total_by_currency = {}
    for expense in expenses:
        if expense.currency not in total_by_currency:
            total_by_currency[expense.currency] = 0
        total_by_currency[expense.currency] += expense.amount
        
    children = Child.query.filter_by(family_id=current_user.family.id).all()
    return render_template('budget/index.html', 
                         expenses=expenses, 
                         total_by_currency=total_by_currency,
                         children=children,
                         currencies=CURRENCIES)

@bp.route('/export/<format>')
@login_required
def export_budget(format):
    expenses = Budget.query.filter_by(family_id=current_user.family.id)\
                         .order_by(Budget.date.desc()).all()
    
    if format == 'csv':
        output = StringIO()
        writer = csv.writer(output)
        
        # En-tête en français
        writer.writerow(['Date', 'Titre', 'Montant', 'Devise', 'Catégorie', 'Enfant', 'Description'])
        
        # Données
        for expense in expenses:
            writer.writerow([
                expense.formatted_date(),
                expense.title,
                f"{expense.amount:.2f}",
                expense.currency,
                expense.category,
                expense.child.first_name if expense.child else 'Tous',
                expense.description or ''
            ])
            
        output.seek(0)
        return send_file(
            StringIO(output.getvalue()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'budget_{datetime.now().strftime("%d_%m_%Y")}.csv'
        )
        
    elif format == 'pdf':
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=landscape(letter),
            title=f'Budget 2Familles - {datetime.now().strftime("%d/%m/%Y")}'
        )
        
        elements = []
        styles = getSampleStyleSheet()
        
        # Titre
        elements.append(Paragraph(
            f'Budget Familial - {datetime.now().strftime("%d/%m/%Y")}',
            styles['Title']
        ))
        
        # Total par devise
        total_by_currency = {}
        for expense in expenses:
            if expense.currency not in total_by_currency:
                total_by_currency[expense.currency] = 0
            total_by_currency[expense.currency] += expense.amount
            
        totals_text = []
        for currency, total in total_by_currency.items():
            symbol = CURRENCIES.get(currency, currency)
            totals_text.append(f"Total {currency}: {total:.2f} {symbol}")
            
        elements.append(Paragraph(
            "Résumé: " + " | ".join(totals_text),
            styles['Heading2']
        ))
        
        # Tableau des dépenses
        data = [['Date', 'Titre', 'Montant', 'Catégorie', 'Enfant', 'Description']]
        for expense in expenses:
            data.append([
                expense.formatted_date(),
                expense.title,
                f"{expense.amount:.2f} {CURRENCIES.get(expense.currency, expense.currency)}",
                expense.category,
                expense.child.first_name if expense.child else 'Tous',
                expense.description or ''
            ])
        
        # Création et style du tableau
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.white),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),  # Aligner les montants à droite
        ]))
        
        elements.append(table)
        doc.build(elements)
        
        buffer.seek(0)
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'budget_{datetime.now().strftime("%d_%m_%Y")}.pdf'
        )

@bp.route('/add', methods=['POST'])
@login_required
def add():
    try:
        budget = Budget(
            title=request.form.get('title'),
            amount=float(request.form.get('amount', 0)),
            date=datetime.strptime(request.form.get('date'), '%Y-%m-%d'),
            category=request.form.get('category'),
            description=request.form.get('description', ''),
            currency=request.form.get('currency', 'EUR'),
            creator_id=current_user.id,
            family_id=current_user.family.id,
            child_id=request.form.get('child_id')
        )
        
        db.session.add(budget)
        db.session.commit()
        flash('Dépense ajoutée avec succès', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de l\'ajout de la dépense : {str(e)}', 'danger')
    
    return redirect(url_for('budget.index'))

@bp.route('/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit(id):
    expense = Budget.query.get_or_404(id)
    
    if expense.family_id != current_user.family.id:
        flash('Vous n\'êtes pas autorisé à modifier cette dépense', 'danger')
        return redirect(url_for('budget.index'))

    if request.method == 'POST':
        try:
            expense.title = request.form['title']
            expense.amount = float(request.form['amount'])
            expense.category = request.form.get('category', 'Autre')
            expense.description = request.form.get('description', '')
            expense.date = datetime.strptime(request.form['date'], '%Y-%m-%d')
            expense.currency = request.form.get('currency', 'EUR')
            expense.child_id = request.form.get('child_id')

            db.session.commit()
            flash('Dépense mise à jour avec succès', 'success')
            return redirect(url_for('budget.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la mise à jour : {str(e)}', 'danger')

    children = Child.query.filter_by(family_id=current_user.family.id).all()
    return render_template('budget/edit.html', 
                         expense=expense,
                         children=children,
                         currencies=CURRENCIES)

@bp.route('/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    expense = Budget.query.get_or_404(id)
    
    if expense.family_id != current_user.family.id:
        flash('Vous n\'êtes pas autorisé à supprimer cette dépense', 'danger')
        return redirect(url_for('budget.index'))

    try:
        db.session.delete(expense)
        db.session.commit()
        flash('Dépense supprimée avec succès', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression : {str(e)}', 'danger')

    return redirect(url_for('budget.index'))