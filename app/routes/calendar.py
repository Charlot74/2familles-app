from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, send_file
from flask_login import login_required, current_user
from app import db
from app.models.event import Event
from app.models.child import Child
from datetime import datetime
import csv
from io import StringIO, BytesIO
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, landscape
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph
from reportlab.lib.styles import getSampleStyleSheet

bp = Blueprint('calendar', __name__)

@bp.route('/calendar')
@login_required
def index():
    children = Child.query.filter_by(family_id=current_user.family.id).all()
    event_types = ['Médical', 'École', 'Activité', 'Garde', 'Autre']
    return render_template('calendar.html', 
                         children=children,
                         event_types=event_types)

@bp.route('/calendar/events')
@login_required
def get_events():
    events = Event.query.filter_by(family_id=current_user.family.id).all()
    event_list = []
    
    for event in events:
        # Préparation du titre avec le nom des enfants
        title = event.title
        if event.children:
            if len(event.children) == 1:
                title = f"{event.children[0].first_name} - {title}"
                event_color = event.children[0].color
            else:
                children_names = [child.first_name for child in event.children]
                title = f"{', '.join(children_names)} - {title}"
                event_color = "#3788d8"  # Couleur par défaut pour plusieurs enfants
        else:
            event_color = "#3788d8"  # Couleur par défaut si pas d'enfant

        event_list.append({
            'id': event.id,
            'title': title,
            'start': event.start_time.isoformat(),
            'end': event.end_time.isoformat(),
            'description': event.description,
            'location': event.location,
            'type': event.event_type,
            'backgroundColor': event_color,
            'borderColor': event_color,
            'children': [{'id': child.id, 'name': child.first_name, 'color': child.color} 
                        for child in event.children]
        })
    
    return jsonify(event_list)

@bp.route('/calendar/export/<format>')
@login_required
def export_events(format):
    events = Event.query.filter_by(family_id=current_user.family.id)\
                      .order_by(Event.start_time.asc()).all()
    
    if format == 'csv':
        output = StringIO()
        writer = csv.writer(output)
        
        # En-tête en français
        writer.writerow(['Date', 'Heure', 'Titre', 'Type', 'Lieu', 'Enfant(s)', 'Description'])
        
        for event in events:
            children_names = ', '.join([child.first_name for child in event.children])
            writer.writerow([
                event.start_time.strftime('%d/%m/%Y'),
                event.start_time.strftime('%H:%M'),
                event.title,
                event.event_type,
                event.location or '',
                children_names,
                event.description or ''
            ])
        
        output.seek(0)
        return send_file(
            StringIO(output.getvalue()),
            mimetype='text/csv',
            as_attachment=True,
            download_name=f'calendrier_{datetime.now().strftime("%d_%m_%Y")}.csv'
        )
    
    elif format == 'pdf':
        buffer = BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=landscape(letter),
            title=f'Calendrier 2Familles - {datetime.now().strftime("%d/%m/%Y")}'
        )
        elements = []
        styles = getSampleStyleSheet()
        
        # Titre du PDF
        title = Paragraph(
            f'Calendrier Familial - {datetime.now().strftime("%d/%m/%Y")}',
            styles['Title']
        )
        elements.append(title)
        
        # Données pour le tableau
        data = [['Date', 'Heure', 'Titre', 'Type', 'Lieu', 'Enfant(s)', 'Description']]
        
        for event in events:
            children_names = ', '.join([child.first_name for child in event.children])
            data.append([
                event.start_time.strftime('%d/%m/%Y'),
                event.start_time.strftime('%H:%M'),
                event.title,
                event.event_type,
                event.location or '',
                children_names,
                event.description or ''
            ])
        
        # Créer et styler le tableau
        table = Table(data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.blue),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('LEFTPADDING', (0, 0), (-1, -1), 6),
            ('RIGHTPADDING', (0, 0), (-1, -1), 6),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ]))
        
        elements.append(table)
        doc.build(elements)
        
        buffer.seek(0)
        return send_file(
            buffer,
            mimetype='application/pdf',
            as_attachment=True,
            download_name=f'calendrier_{datetime.now().strftime("%d_%m_%Y")}.pdf'
        )

@bp.route('/calendar/add', methods=['POST'])
@login_required
def add_event():
    try:
        event = Event(
            title=request.form['title'],
            start_time=datetime.strptime(request.form['start_time'], '%Y-%m-%dT%H:%M'),
            end_time=datetime.strptime(request.form['end_time'], '%Y-%m-%dT%H:%M'),
            description=request.form.get('description', ''),
            location=request.form.get('location', ''),
            event_type=request.form.get('event_type', 'Autre'),
            creator_id=current_user.id,
            family_id=current_user.family.id
        )

        selected_children = request.form.getlist('children')
        if selected_children:
            children = Child.query.filter(Child.id.in_(selected_children)).all()
            event.children.extend(children)
            if len(children) == 1:
                event.color = children[0].color
            else:
                event.color = "#3788d8"
        else:
            event.color = "#3788d8"

        db.session.add(event)
        db.session.commit()
        flash('Événement créé avec succès', 'success')
        return redirect(url_for('calendar.index'))
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la création : {str(e)}', 'danger')
        return redirect(url_for('calendar.index'))

@bp.route('/calendar/event/<int:id>', methods=['PUT', 'DELETE'])
@login_required
def manage_event(id):
    event = Event.query.get_or_404(id)
    
    if event.family_id != current_user.family.id:
        return jsonify({'error': 'Non autorisé'}), 403

    if request.method == 'DELETE':
        try:
            db.session.delete(event)
            db.session.commit()
            return jsonify({'message': 'Événement supprimé'}), 200
        except Exception as e:
            db.session.rollback()
            return jsonify({'error': str(e)}), 500

    try:
        data = request.get_json()
        for key, value in data.items():
            if hasattr(event, key):
                setattr(event, key, value)
        db.session.commit()
        return jsonify(event.to_dict())
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/calendar/event/<int:id>/edit', methods=['GET', 'POST'])
@login_required
def edit_event(id):
    event = Event.query.get_or_404(id)
    
    if event.family_id != current_user.family.id:
        flash('Vous n\'êtes pas autorisé à modifier cet événement', 'danger')
        return redirect(url_for('calendar.index'))

    if request.method == 'POST':
        try:
            event.title = request.form['title']
            event.description = request.form.get('description', '')
            event.start_time = datetime.strptime(request.form['start_time'], '%Y-%m-%dT%H:%M')
            event.end_time = datetime.strptime(request.form['end_time'], '%Y-%m-%dT%H:%M')
            event.location = request.form.get('location', '')
            event.event_type = request.form.get('event_type', 'Autre')

            event.children = []
            selected_children = request.form.getlist('children')
            if selected_children:
                children = Child.query.filter(Child.id.in_(selected_children)).all()
                event.children.extend(children)
                if len(children) == 1:
                    event.color = children[0].color
                else:
                    event.color = "#3788d8"
            else:
                event.color = "#3788d8"

            db.session.commit()
            flash('Événement mis à jour avec succès', 'success')
            return redirect(url_for('calendar.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la mise à jour : {str(e)}', 'danger')

    children = Child.query.filter_by(family_id=current_user.family.id).all()
    event_types = ['Médical', 'École', 'Activité', 'Garde', 'Autre']
    return render_template('calendar/edit_event.html', 
                         event=event, 
                         children=children,
                         event_types=event_types)