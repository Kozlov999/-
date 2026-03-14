// UI компоненты
export const UI = {
    showAlert(message, type = 'info', container = null) {
        const alertDiv = document.createElement('div');
        alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
        alertDiv.innerHTML = `
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        const target = container || document.querySelector('.container') || document.querySelector('.page-shell');
        target.insertBefore(alertDiv, target.firstChild);
        
        setTimeout(() => {
            const bsAlert = new bootstrap.Alert(alertDiv);
            bsAlert.close();
        }, 5000);
    },

    initAutoHideAlerts() {
        document.querySelectorAll('.alert').forEach(alert => {
            setTimeout(() => {
                const bsAlert = new bootstrap.Alert(alert);
                bsAlert.close();
            }, 5000);
        });
    },

    initTooltips() {
        const tooltipList = document.querySelectorAll('[data-bs-toggle="tooltip"]');
        return [...tooltipList].map(el => new bootstrap.Tooltip(el));
    },

    startCountdown(elementId, minutes) {
        let seconds = minutes * 60;
        const element = document.getElementById(elementId);
        
        if (!element) return;
        
        const timer = setInterval(() => {
            const mins = Math.floor(seconds / 60);
            const secs = seconds % 60;
            
            element.textContent = `${mins}:${secs < 10 ? '0' : ''}${secs}`;
            
            if (seconds <= 0) {
                clearInterval(timer);
                element.textContent = 'Время вышло!';
            }
            
            seconds--;
        }, 1000);
    },

    exportData(data, filename, type = 'application/json') {
        const blob = new Blob([JSON.stringify(data, null, 2)], { type });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        URL.revokeObjectURL(url);
    }
};