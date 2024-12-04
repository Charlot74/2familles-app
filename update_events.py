from app import app, db
from app.models.event import Event

def update_event_types():
    with app.app_context():
        events = Event.query.all()
        updates_count = 0
        
        for event in events:
            updated = False
            if event.event_type == 'medical':
                event.event_type = 'Médical'
                updated = True
            elif event.event_type == 'school':
                event.event_type = 'École'
                updated = True
            elif event.event_type == 'activity':
                event.event_type = 'Activité'
                updated = True
            elif event.event_type == 'custody':
                event.event_type = 'Garde'
                updated = True
            
            if updated:
                updates_count += 1
        
        if updates_count > 0:
            try:
                db.session.commit()
                print(f"Mise à jour réussie ! {updates_count} événements modifiés.")
            except Exception as e:
                db.session.rollback()
                print(f"Erreur lors de la mise à jour : {str(e)}")
        else:
            print("Aucun événement à mettre à jour.")

if __name__ == '__main__':
    update_event_types()