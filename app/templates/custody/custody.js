document.addEventListener('DOMContentLoaded', function() {
    // Initialisation du calendrier
    const calendarEl = document.getElementById('calendar');
    let calendar = new FullCalendar.Calendar(calendarEl, {
        initialView: 'dayGridMonth',
        headerToolbar: {
            left: 'prev,next today',
            center: 'title',
            right: 'dayGridMonth,timeGridWeek,timeGridDay'
        },
        locale: 'fr',
        firstDay: 1,
        slotMinTime: '06:00:00',
        slotMaxTime: '22:00:00',
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
    document.getElementById('childFilter').addEventListener('change', function(e) {
        updateCalendarEvents();
    });

    document.getElementById('typeFilter').addEventListener('change', function(e) {
        updateCalendarEvents();
    });

    function updateCalendarEvents() {
        const childId = document.getElementById('childFilter').value;
        const type = document.getElementById('typeFilter').value;
        
        let url = '/custody/calendar?';
        if (childId) url += `child_id=${childId}&`;
        if (type) url += `type=${type}`;
        
        calendar.removeAllEvents();
        calendar.addEventSource(url);
    }

    // Gestion des échanges
    const exchangeModal = new bootstrap.Modal(document.getElementById('exchangeModal'));
    let currentEventId = null;

    function handleEventClick(info) {
        const event = info.event;
        currentEventId = event.id;
        
        document.getElementById('scheduleId').value = event.id;
        document.getElementById('proposedStart').value = event.start.toISOString().slice(0, 16);
        document.getElementById('proposedEnd').value = event.end.toISOString().slice(0, 16);
        
        exchangeModal.show();
    }

    function handleDateSelect(info) {
        document.getElementById('proposedStart').value = info.start.toISOString().slice(0, 16);
        document.getElementById('proposedEnd').value = info.end.toISOString().slice(0, 16);
    }

    document.getElementById('submitExchange').addEventListener('click', function() {
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
        .catch(