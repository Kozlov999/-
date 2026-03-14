// Обработка форм
import { Validation } from '../core/validation.js';
import { UI } from '../core/ui.js';

export const FormHandler = {
    init() {
        this.initPasswordForm();
        this.initDateInputs();
        this.initPhoneMask();
        this.initFileUploads();
        this.initCancelForms();
    },

    initPasswordForm() {
        const passwordForm = document.getElementById('passwordForm');
        if (passwordForm) {
            passwordForm.addEventListener('submit', (e) => {
                const password = document.getElementById('password').value;
                const confirmPassword = document.getElementById('confirmPassword').value;
                
                const result = Validation.validatePassword(password, confirmPassword);
                if (!result.valid) {
                    e.preventDefault();
                    UI.showAlert(result.message, 'danger');
                }
            });
        }
    },

    initDateInputs() {
        const today = new Date().toISOString().split('T')[0];
        const maxDate = new Date();
        maxDate.setDate(maxDate.getDate() + 90);
        
        document.querySelectorAll('input[type="date"]').forEach(input => {
            input.min = today;
            input.max = maxDate.toISOString().split('T')[0];
        });
        
        document.querySelectorAll('input[type="time"]').forEach(input => {
            input.min = '09:00';
            input.max = '21:00';
            if (!input.value) input.value = '14:00';
        });
    },

    initPhoneMask() {
        document.querySelectorAll('input[type="tel"]').forEach(input => {
            input.addEventListener('input', function(e) {
                let value = e.target.value.replace(/\D/g, '');
                
                if (value.startsWith('8') || value.startsWith('7')) {
                    value = '+7' + value.substring(1);
                }
                
                let formattedValue = '+7';
                if (value.length > 2) {
                    formattedValue += ' (' + value.substring(2, 5);
                }
                if (value.length >= 6) {
                    formattedValue += ') ' + value.substring(5, 8);
                }
                if (value.length >= 9) {
                    formattedValue += '-' + value.substring(8, 10);
                }
                if (value.length >= 11) {
                    formattedValue += '-' + value.substring(10, 12);
                }
                
                e.target.value = formattedValue;
            });
        });
    },

    initFileUploads() {
        document.querySelectorAll('input[type="file"]').forEach(input => {
            input.addEventListener('change', (e) => {
                if (e.target.files.length > 0) {
                    const file = e.target.files[0];
                    if (!Validation.validateFileSize(file)) {
                        UI.showAlert('Файл слишком большой. Максимальный размер: 16MB', 'danger');
                        e.target.value = '';
                    }
                }
            });
        });
    },

    initCancelForms() {
        document.querySelectorAll('form[data-confirm]').forEach(form => {
            form.addEventListener('submit', (e) => {
                if (!confirm(form.dataset.confirm || 'Вы уверены?')) {
                    e.preventDefault();
                }
            });
        });
    }
};