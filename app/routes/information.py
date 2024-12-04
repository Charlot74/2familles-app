import os
from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, send_file, send_from_directory, safe_join
from flask_login import login_required, current_user
from werkzeug.utils import secure_filename
from app import db
from app.models.information import Information
from app.models.child import Child
from datetime import datetime
import mimetypes

bp = Blueprint('information', __name__, url_prefix='/information')

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in current_app.config['ALLOWED_EXTENSIONS']

def get_file_extension(filename):
    return filename.rsplit('.', 1)[1].lower() if '.' in filename else ''

@bp.route('/')
@login_required
def index():
    information = Information.query.filter_by(family_id=current_user.family_id).all()
    children = Child.query.filter_by(family_id=current_user.family_id).all()
    return render_template('information/index.html',
                         information=information,
                         children=children)

@bp.route('/medical', methods=['GET', 'POST'])
@login_required
def medical():
    if request.method == 'POST':
        try:
            info = Information(
                type='medical',
                title=f"{request.form.get('type')} - {request.form.get('child_name', '')}",
                content=request.form.get('description', ''),
                family_id=current_user.family_id,
                child_id=request.form.get('child_id'),
                creator_id=current_user.id
            )
            db.session.add(info)
            db.session.commit()
            flash('Information médicale ajoutée avec succès', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
        return redirect(url_for('information.index'))
    return render_template('information/index.html')

@bp.route('/school', methods=['GET', 'POST'])
@login_required
def school():
    if request.method == 'POST':
        try:
            content = f"""
            Type: {request.form.get('type')}
            Information: {request.form.get('information')}
            Détails: {request.form.get('details', '')}
            """
            info = Information(
                type='school',
                title=f"{request.form.get('type')} - {request.form.get('child_name', '')}",
                content=content.strip(),
                family_id=current_user.family_id,
                child_id=request.form.get('child_id'),
                creator_id=current_user.id
            )
            db.session.add(info)
            db.session.commit()
            flash('Information scolaire ajoutée avec succès', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
        return redirect(url_for('information.index'))
    return render_template('information/index.html')

@bp.route('/documents', methods=['GET', 'POST'])
@login_required
def documents():
    if request.method == 'POST':
        try:
            if not os.path.exists(current_app.config['UPLOAD_FOLDER']):
                os.makedirs(current_app.config['UPLOAD_FOLDER'])

            if 'document' not in request.files:
                flash('Aucun fichier sélectionné', 'danger')
                return redirect(url_for('information.index'))
            
            file = request.files['document']
            if file.filename == '':
                flash('Aucun fichier sélectionné', 'danger')
                return redirect(url_for('information.index'))
            
            if file and allowed_file(file.filename):
                filename = secure_filename(file.filename)
                file_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                filename = file_timestamp + filename
                
                file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                file.save(file_path)

                content = f"""
                Type: {request.form.get('type')}
                Description: {request.form.get('description', '')}
                Fichier: {filename}
                """
                
                info = Information(
                    type='document',
                    title=request.form.get('title'),
                    content=content.strip(),
                    family_id=current_user.family_id,
                    child_id=request.form.get('child_id'),
                    creator_id=current_user.id,
                    file_path=filename
                )
                
                db.session.add(info)
                db.session.commit()
                flash('Document ajouté avec succès', 'success')
            else:
                flash('Type de fichier non autorisé', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de l\'ajout du document : {str(e)}', 'danger')
        return redirect(url_for('information.index'))
    return render_template('information/index.html')

@bp.route('/emergency', methods=['GET', 'POST'])
@login_required
def emergency():
    if request.method == 'POST':
        try:
            content = f"""
            Relation: {request.form.get('relation')}
            Téléphone: {request.form.get('phone_primary')}
            Téléphone secondaire: {request.form.get('phone_secondary', 'Non renseigné')}
            Email: {request.form.get('email', 'Non renseigné')}
            Adresse: {request.form.get('address', 'Non renseignée')}
            Notes: {request.form.get('notes', 'Aucune note')}
            """
            
            info = Information(
                type='emergency',
                title=request.form.get('name'),
                content=content.strip(),
                family_id=current_user.family_id,
                creator_id=current_user.id
            )
            db.session.add(info)
            db.session.commit()
            flash('Contact d\'urgence ajouté avec succès', 'success')
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur: {str(e)}', 'danger')
        return redirect(url_for('information.index'))
    return render_template('information/index.html')

@bp.route('/view/<int:id>')
@login_required
def view_document(id):
    try:
        info = Information.query.get_or_404(id)
        
        if info.family_id != current_user.family_id:
            flash('Accès non autorisé', 'danger')
            return redirect(url_for('information.index'))
        
        if not info.file_path:
            flash('Aucun fichier associé', 'danger')
            return redirect(url_for('information.index'))
        
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], info.file_path)
        
        if not os.path.exists(file_path):
            flash('Fichier non trouvé', 'danger')
            return redirect(url_for('information.index'))
        
        extension = get_file_extension(info.file_path)
        
        if extension in ['jpg', 'jpeg', 'png', 'gif']:
            return send_from_directory(
                current_app.config['UPLOAD_FOLDER'],
                info.file_path,
                mimetype=f'image/{extension}'
            )
        
        return send_file(
            file_path,
            as_attachment=True,
            download_name=info.file_path
        )

    except Exception as e:
        flash(f'Erreur lors de l\'accès au document : {str(e)}', 'danger')
        return redirect(url_for('information.index'))

@bp.route('/edit/<int:id>', methods=['GET', 'POST'])
@login_required
def edit(id):
    info = Information.query.get_or_404(id)
    if info.family_id != current_user.family_id:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('information.index'))

    children = Child.query.filter_by(family_id=current_user.family_id).all()

    if request.method == 'POST':
        try:
            if info.type == 'emergency':
                content = f"""
                Relation: {request.form.get('relation')}
                Téléphone: {request.form.get('phone_primary')}
                Téléphone secondaire: {request.form.get('phone_secondary', 'Non renseigné')}
                Email: {request.form.get('email', 'Non renseigné')}
                Adresse: {request.form.get('address', 'Non renseignée')}
                Notes: {request.form.get('notes', 'Aucune note')}
                """
                info.title = request.form.get('name')
                info.content = content.strip()
            else:
                info.title = request.form.get('title')
                info.content = request.form.get('content')
                info.child_id = request.form.get('child_id')

                if info.type == 'document' and 'document' in request.files:
                    file = request.files['document']
                    if file and file.filename != '' and allowed_file(file.filename):
                        if info.file_path:
                            old_file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], info.file_path)
                            if os.path.exists(old_file_path):
                                os.remove(old_file_path)

                        filename = secure_filename(file.filename)
                        file_timestamp = datetime.now().strftime('%Y%m%d_%H%M%S_')
                        filename = file_timestamp + filename
                        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], filename)
                        file.save(file_path)
                        info.file_path = filename

            info.updated_at = datetime.utcnow()
            db.session.commit()
            flash('Information mise à jour avec succès', 'success')
            return redirect(url_for('information.index'))
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la mise à jour : {str(e)}', 'danger')

    return render_template('information/edit.html', info=info, children=children)

@bp.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    info = Information.query.get_or_404(id)
    if info.family_id != current_user.family_id:
        flash('Accès non autorisé', 'danger')
        return redirect(url_for('information.index'))

    try:
        if info.type == 'document' and info.file_path:
            file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], info.file_path)
            if os.path.exists(file_path):
                os.remove(file_path)

        db.session.delete(info)
        db.session.commit()
        flash('Information supprimée avec succès', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f'Erreur lors de la suppression : {str(e)}', 'danger')
    
    return redirect(url_for('information.index'))