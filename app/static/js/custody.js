document.addEventListener('DOMContentLoaded', function() {
    // Initialisation du calendrier
    const calendarEl = document.getElementById('calendar');
    const calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        locale: 'fr',
        firstDay: 1,
        selectable: true,
        editable: true,
        eventClick: handleEventClick,
        select: handleDateSelect,
        events: '/custody/calendar',
        eventContent: function(arg) {
            return {
                html: `
                    <div class="fc-content">
                        <div class="fc-title">${arg.event.title}</div>
                        ${arg.event.extendedProps.type === 'exchange' ? '<i class="fas fa-exchange-alt"></i>' : ''}
                    </div>
                `
            };
        }
    });
    calendar.render();

    // Gestion des filtres
    document.getElementById('childFilter')?.addEventListener('change', updateCalendarEvents);
    document.getElementById('typeFilter')?.addEventListener('change', updateCalendarEvents);

    function updateCalendarEvents() {
        const childId = document.getElementById('childFilter')?.value;
        const type = document.getElementById('typeFilter')?.value;
        
        let url = '/custody/calendar';
        const params = new URLSearchParams();
        if (childId) params.append('child_id', childId);
        if (type) params.append('type', type);
        if (params.toString()) url += '?' + params.toString();
        
        calendar.removeAllEventSources();
        calendar.addEventSource(url);
    }

    // Gestion des échanges
    const exchangeModal = new bootstrap.Modal(document.getElementById('exchangeModal'));

    function handleEventClick(info) {
        const event = info.event;
        document.getElementById('scheduleId').value = event.id;
        document.getElementById('proposedStart').value = event.start.toISOString().slice(0, 16);
        document.getElementById('proposedEnd').value = event.end.toISOString().slice(0, 16);
        exchangeModal.show();
    }

    function handleDateSelect(info) {
        document.getElementById('proposedStart').value = info.start.toISOString().slice(0, 16);
        document.getElementById('proposedEnd').value = info.end.toISOString().slice(0, 16);
    }

    // Envoi des demandes d'échange
    document.getElementById('submitExchange')?.addEventListener('click', function() {
        const data = {
            schedule_id: document.getElementById('scheduleId').value,
            proposed_start: document.getElementById('proposedStart').value,
            proposed_end: document.getElementById('proposedEnd').value,
            reason: document.getElementById('exchangeReason').value
        };

        fetch('/custody/exchange', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrf_token')
            },
            body: JSON.stringify(data)
        })
        .then(response => response.json())
        .then(data => {
            if (data.error) {
                showAlert(data.error, 'danger');
            } else {
                showAlert('Demande d\'échange envoyée avec succès', 'success');
                exchangeModal.hide();
                updateCalendarEvents();
            }
        })
        .catch(error => {
            console.error('Error:', error);
            showAlert('Erreur lors de l\'envoi de la demande', 'danger');
        });
    });

    // Réponse aux demandes d'échange
    document.querySelectorAll('.accept-exchange, .reject-exchange').forEach(button => {
        button.addEventListener('click', function() {
            const action = this.classList.contains('accept-exchange') ? 'accept' : 'reject';
            const exchangeId = this.dataset.exchangeId;

            fetch(`/custody/exchange/${exchangeId}/${action}`, {
                method: 'POST',
                headers: {
                    'X-CSRFToken': getCookie('csrf_token')
                }
            })
            .then(response => response.json())
            .then(data => {
                showAlert(data.message, 'success');
                setTimeout(() => location.reload(), 1000);
            })
            .catch(error => {
                console.error('Error:', error);
                showAlert('Erreur lors du traitement de la demande', 'danger');
            });
        });
    });

    // Fonctions utilitaires
    function showAlert(message, type) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        document.querySelector('.container').insertAdjacentElement('afterbegin', alertDiv);
        setTimeout(() => alertDiv.remove(), 5000);
    }

    function getCookie(name) {
        const value = `; ${document.cookie}`;
        const parts = value.split(`; ${name}=`);
        if (parts.length === 2) return parts.pop().split(';').shift();
    }
});