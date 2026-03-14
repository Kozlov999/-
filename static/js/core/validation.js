// Валидация
export const Validation = {
    validatePassword(password, confirmPassword) {
        if (password !== confirmPassword) {
            return { valid: false, message: 'Пароли не совпадают' };
        }
        if (password.length < 6) {
            return { valid: false, message: 'Пароль должен содержать не менее 6 символов' };
        }
        return { valid: true };
    },

    validatePhone(phone) {
        if (!phone) return true;
        const regex = /^(\+7|8)[\s\-]?\(?[0-9]{3}\)?[\s\-]?[0-9]{3}[\s\-]?[0-9]{2}[\s\-]?[0-9]{2}$/;
        return regex.test(phone);
    },

    validateFileSize(file, maxSizeMB = 16) {
        const fileSize = file.size / 1024 / 1024;
        return fileSize <= maxSizeMB;
    },

    validateEmail(email) {
        const regex = /^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$/;
        return regex.test(email);
    }
};