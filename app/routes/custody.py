from flask import Blueprint, flash, redirect, render_template, request, url_for, jsonify
from flask_login import login_required, current_user
from app import db
from app.models.custody import CustodySchedule, CustodyExchange
from app.models.family import FamilyInfo
from app.models.message import Notification
from datetime import datetime
from sqlalchemy import or_

bp = Blueprint('custody', __name__)

@bp.route('/custody')
@login_required
def index():
    children = FamilyInfo.query.filter_by(user_id=current_user.id).all()
    schedules = CustodySchedule.query.filter(
        or_(
            CustodySchedule.user_id == current_user.id,
            CustodySchedule.child_id.in_([child.id for child in children])
        )
    ).order_by(CustodySchedule.start_date.desc()).all()
    
    exchange_requests = CustodyExchange.query.filter(
        or_(
            CustodyExchange.requester_id == current_user.id,
            CustodyExchange.recipient_id == current_user.id
        ),
        CustodyExchange.status == 'pending'
    ).all()
    
    return render_template('custody/index.html',
                         schedules=schedules,
                         children=children,
                         exchange_requests=exchange_requests)

@bp.route('/custody/add', methods=['GET', 'POST'])
@login_required
def add():
    children = FamilyInfo.query.filter_by(user_id=current_user.id).all()
    
    if request.method == 'POST':
        try:
            child_id = request.form.get('child_id')
            start_date = datetime.strptime(request.form['start_date'], '%Y-%m-%d %H:%M')
            end_date = datetime.strptime(request.form['end_date'], '%Y-%m-%d %H:%M')
            description = request.form.get('description', '')
            schedule_type = request.form.get('type', 'regular')
            recurrence = request.form.get('recurrence', 'none')
            color = request.form.get('color', '#BB2D0C')

            schedule = CustodySchedule(
                user_id=current_user.id,
                child_id=child_id,
                start_date=start_date,
                end_date=end_date,
                description=description,
                type=schedule_type,
                recurrence=recurrence,
                color=color
            )
            
            db.session.add(schedule)
            db.session.commit()
            flash('Période de garde ajoutée avec succès!', 'success')
            return redirect(url_for('custody.index'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de l\'ajout: {str(e)}', 'danger')
            
    return render_template('custody/add.html', children=children)

@bp.route('/custody/<int:id>/delete', methods=['POST'])
@login_required
def delete(id):
    try:
        schedule = CustodySchedule.query.get_or_404(id)
        if schedule.user_id != current_user.id:
            flash('Accès non autorisé', 'danger')
            return redirect(url_for('custody.index'))

        db.session.delete(schedule)
        db.session.commit()
        flash('Période de garde supprimée avec succès!', 'success')
        
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression: {str(e)}', 'danger')
        
    return redirect(url_for('custody.index'))

@bp.route('/custody/calendar')
@login_required
def get_calendar_events():
    try:
        start = request.args.get('start', '')
        end = request.args.get('end', '')
        child_id = request.args.get('child_id', '')
        
        query = CustodySchedule.query
        
        if child_id:
            query = query.filter_by(child_id=child_id)
        
        if start and end:
            start_date = datetime.fromisoformat(start.replace('Z', '+00:00'))
            end_date = datetime.fromisoformat(end.replace('Z', '+00:00'))
            query = query.filter(
                CustodySchedule.start_date >= start_date,
                CustodySchedule.end_date <= end_date
            )
        
        schedules = query.all()
        events = [{
            'id': s.id,
            'title': f"{s.child.child_name} - {s.description}",
            'start': s.start_date.isoformat(),
            'end': s.end_date.isoformat(),
            'color': s.color,
            'extendedProps': {
                'child_id': s.child_id,
                'type': s.type,
                'status': s.status
            }
        } for s in schedules]
        
        return jsonify(events)
        
    except Exception as e:
        return jsonify({'error': str(e)}), 400

@bp.route('/custody/exchange', methods=['POST'])
@login_required
def request_exchange():
    try:
        data = request.get_json()
        
        schedule = CustodySchedule.query.get_or_404(data['schedule_id'])
        if schedule.user_id == current_user.id:
            return jsonify({'error': 'Vous ne pouvez pas demander un échange pour votre propre période'}), 400
            
        exchange = CustodyExchange(
            schedule_id=data['schedule_id'],
            requester_id=current_user.id,
            recipient_id=schedule.user_id,
            proposed_start=datetime.fromisoformat(data['proposed_start']),
            proposed_end=datetime.fromisoformat(data['proposed_end']),
            reason=data.get('reason', '')
        )
        
        db.session.add(exchange)
        notification = Notification(
            user_id=schedule.user_id,
            title="Nouvelle demande d'échange",
            content=f"{current_user.first_name} souhaite échanger une période de garde",
            type="custody_exchange"
        )
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({
            'message': 'Demande envoyée avec succès',
            'exchange': exchange.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500

@bp.route('/custody/exchange/<int:id>/<action>', methods=['POST'])
@login_required
def handle_exchange(id, action):
    try:
        exchange = CustodyExchange.query.get_or_404(id)
        
        if exchange.recipient_id != current_user.id:
            return jsonify({'error': 'Accès non autorisé'}), 403
            
        if action not in ['accept', 'reject']:
            return jsonify({'error': 'Action invalide'}), 400
            
        if action == 'accept':
            schedule = exchange.schedule
            original_start = schedule.start_date
            original_end = schedule.end_date
            
            schedule.start_date = exchange.proposed_start
            schedule.end_date = exchange.proposed_end
            
            new_schedule = CustodySchedule(
                user_id=exchange.requester_id,
                child_id=schedule.child_id,
                start_date=original_start,
                end_date=original_end,
                description=f"Échange avec {schedule.user.first_name}",
                type='exchange'
            )
            
            db.session.add(new_schedule)
            exchange.status = 'accepted'
            
        else:
            exchange.status = 'rejected'
            
        notification = Notification(
            user_id=exchange.requester_id,
            title="Réponse à votre demande d'échange",
            content=f"Votre demande a été {'acceptée' if action == 'accept' else 'refusée'}",
            type="custody_exchange_response"
        )
        
        db.session.add(notification)
        db.session.commit()
        
        return jsonify({'message': f'Demande {action}ée avec succès'})
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'error': str(e)}), 500