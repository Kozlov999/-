// Утилиты
export const Utils = {
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    },

    formatDate(dateString) {
        const options = { 
            weekday: 'short', 
            year: 'numeric', 
            month: 'long', 
            day: 'numeric' 
        };
        return new Date(dateString).toLocaleDateString('ru-RU', options);
    },

    formatTime(timeString) {
        if (!timeString) return '';
        const [hours, minutes] = timeString.split(':');
        return `${hours}:${minutes}`;
    },

    calculateLessonCost(hourlyRate, durationMinutes) {
        const hours = durationMinutes / 60;
        return Math.round(hourlyRate * hours * 100) / 100;
    },

    copyToClipboard(text) {
        navigator.clipboard.writeText(text).then(() => {
            UI.showAlert('Скопировано в буфер обмена', 'success');
        }).catch(err => {
            console.error('Ошибка копирования:', err);
            UI.showAlert('Не удалось скопировать', 'danger');
        });
    },

    smoothScrollTo(elementId) {
        const element = document.getElementById(elementId);
        if (element) {
            element.scrollIntoView({
                behavior: 'smooth',
                block: 'start'
            });
        }
    }
};