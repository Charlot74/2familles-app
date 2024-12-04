// Document Ready Handler
document.addEventListener('DOMContentLoaded', function() {
    // Initialize Bootstrap tooltips
    var tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl);
    });

    // Initialize Bootstrap popovers
    var popoverTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="popover"]'));
    popoverTriggerList.map(function (popoverTriggerEl) {
        return new bootstrap.Popover(popoverTriggerEl);
    });

    // Auto-hide alerts after 5 seconds
    setTimeout(function() {
        var alerts = document.querySelectorAll('.alert:not(.alert-permanent)');
        alerts.forEach(function(alert) {
            var bsAlert = new bootstrap.Alert(alert);
            bsAlert.close();
        });
    }, 5000);

    // Form validation
    var forms = document.querySelectorAll('.needs-validation');
    Array.prototype.slice.call(forms).forEach(function (form) {
        form.addEventListener('submit', function (event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
            }
            form.classList.add('was-validated');
        }, false);
    });

    // Toggle password visibility
    document.querySelectorAll('.toggle-password').forEach(button => {
        button.addEventListener('click', function() {
            const input = this.previousElementSibling;
            const type = input.getAttribute('type') === 'password' ? 'text' : 'password';
            input.setAttribute('type', type);
            
            // Toggle eye icon
            const icon = this.querySelector('i');
            icon.classList.toggle('bi-eye');
            icon.classList.toggle('bi-eye-slash');
        });
    });

    // Handle mobile menu
    const navbarToggler = document.querySelector('.navbar-toggler');
    if (navbarToggler) {
        navbarToggler.addEventListener('click', function() {
            document.querySelector('.navbar-collapse').classList.toggle('show');
        });
    }

    // Handle calendar if present
    const calendarEl = document.getElementById('calendar');
    if (calendarEl) {
        const calendar = new FullCalendar.Calendar(calendarEl, {
            initialView: 'dayGridMonth',
            headerToolbar: {
                left: 'prev,next today',
                center: 'title',
                right: 'dayGridMonth,timeGridWeek,dayGridDay'
            },
            locale: 'fr',
            firstDay: 1,
            selectable: true,
            editable: true,
            eventClick: function(info) {
                handleEventClick(info);
            },
            select: function(info) {
                handleDateSelect(info);
            },
            events: '/custody/calendar'
        });
        calendar.render();
    }

    // Handle file inputs
    document.querySelectorAll('.custom-file-input').forEach(input => {
        input.addEventListener('change', function() {
            let fileName = this.files[0].name;
            let label = this.nextElementSibling;
            label.textContent = fileName;
        });
    });

    // Confirm actions
    document.querySelectorAll('[data-confirm]').forEach(element => {
        element.addEventListener('click', function(e) {
            if (!confirm(this.dataset.confirm || 'Êtes-vous sûr ?')) {
                e.preventDefault();
            }
        });
    });
});

// Utility Functions
function showAlert(message, type = 'info', duration = 5000) {
    const alertHtml = `
        <div class="alert alert-${type} alert-dismissible fade show" role="alert">
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
        </div>
    `;
    const alertContainer = document.createElement('div');
    alertContainer.innerHTML = alertHtml;
    document.querySelector('.container').insertAdjacentElement('afterbegin', alertContainer.firstChild);

    if (duration) {
        setTimeout(() => {
            const alert = new bootstrap.Alert(alertContainer.firstChild);
            alert.close();
        }, duration);
    }
}

function formatDate(date) {
    return new Date(date).toLocaleDateString('fr-FR', {
        year: 'numeric',
        month: 'long',
        day: 'numeric',
        hour: '2-digit',
        minute: '2-digit'
    });
}

function handleEventClick(info) {
    const event = info.event;
    if (window.eventModal) {
        document.getElementById('eventTitle').value = event.title;
        document.getElementById('eventStart').value = event.start.toISOString().slice(0, 16);
        document.getElementById('eventEnd').value = event.end ? event.end.toISOString().slice(0, 16) : '';
        document.getElementById('eventId').value = event.id || '';
        window.eventModal.show();
    }
}

function handleDateSelect(info) {
    if (window.eventModal) {
        document.getElementById('eventStart').value = info.start.toISOString().slice(0, 16);
        document.getElementById('eventEnd').value = info.end.toISOString().slice(0, 16);
        document.getElementById('eventId').value = '';
        window.eventModal.show();
    }
}

// API Functions
async function fetchApi(url, options = {}) {
    try {
        const defaultOptions = {
            headers: {
                'Content-Type': 'application/json',
                'X-Requested-With': 'XMLHttpRequest'
            },
            credentials: 'same-origin'
        };
        
        const response = await fetch(url, { ...defaultOptions, ...options });
        
        if (!response.ok) {
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        
        const data = await response.json();
        return { success: true, data };
    } catch (error) {
        console.error('API Error:', error);
        showAlert('Une erreur est survenue', 'danger');
        return { success: false, error };
    }
}

// Export functions for other scripts
window.showAlert = showAlert;
window.formatDate = formatDate;
window.fetchApi = fetchApi;