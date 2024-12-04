from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView
from flask_login import current_user
from flask import redirect, url_for, flash
from app import db
from app.models.user import User
from app.models.family import Family
from app.models.child import Child
from app.models.event import Event
from app.models.budget import Budget
from app.models.information import Information
from app.models.message import Message

admin = Admin(name='2Familles Admin', template_mode='bootstrap4')

# Classe de base sécurisée pour tous les ModelViews
class SecureModelView(ModelView):
    def is_accessible(self):
        return current_user.is_authenticated and current_user.is_admin

    def inaccessible_callback(self, name, **kwargs):
        flash('Accès refusé.', 'danger')
        return redirect(url_for('auth.login'))

# Views spécifiques pour chaque modèle
class UserAdmin(SecureModelView):
    column_exclude_list = ['password_hash']
    column_searchable_list = ['username', 'email']
    column_filters = ['is_active', 'created_at', 'last_seen']
    form_excluded_columns = ['password_hash']
    can_create = True
    can_edit = True
    can_delete = True
    
    def on_model_change(self, form, model, is_created):
        if form.password.data:
            model.set_password(form.password.data)

class FamilyAdmin(SecureModelView):
    column_searchable_list = ['name']
    column_filters = ['created_at']

class ChildAdmin(SecureModelView):
    column_searchable_list = ['first_name', 'last_name']
    column_filters = ['birth_date']

class EventAdmin(SecureModelView):
    column_searchable_list = ['title', 'description']
    column_filters = ['start_time', 'end_time', 'event_type']

class BudgetAdmin(SecureModelView):
    column_searchable_list = ['title']
    column_filters = ['date', 'category', 'currency']

class InformationAdmin(SecureModelView):
    column_searchable_list = ['title', 'content']
    column_filters = ['type', 'created_at']

class MessageAdmin(SecureModelView):
    column_searchable_list = ['content']
    column_filters = ['timestamp', 'read']

def init_admin(app):
    admin.init_app(app)
    
    # Ajout des vues d'administration
    admin.add_view(UserAdmin(User, db.session, name='Utilisateurs'))
    admin.add_view(FamilyAdmin(Family, db.session, name='Familles'))
    admin.add_view(ChildAdmin(Child, db.session, name='Enfants'))
    admin.add_view(EventAdmin(Event, db.session, name='Événements'))
    admin.add_view(BudgetAdmin(Budget, db.session, name='Budget'))
    admin.add_view(InformationAdmin(Information, db.session, name='Informations'))
    admin.add_view(MessageAdmin(Message, db.session, name='Messages'))