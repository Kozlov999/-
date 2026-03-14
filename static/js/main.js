// Главный файл приложения
import { UI } from './core/ui.js';
import { FormHandler } from './features/forms.js';
import { VideoConference } from './features/webrtc.js';
import { NotesManager } from './features/notes.js';

// Глобальные переменные
let videoConference = null;
let notesManager = null;

document.addEventListener('DOMContentLoaded', () => {
    // Инициализация базовых компонентов
    UI.initAutoHideAlerts();
    UI.initTooltips();
    FormHandler.init();
    
    // Инициализация lazy loading
    initLazyLoading();
    
    // Инициализация видео для урока
    if (document.getElementById('video-container')) {
        initVideoConference();
    }
    
    // Инициализация заметок
    if (document.querySelector('.notes-container')) {
        initNotes();
    }
    
    // Инициализация счетчиков
    initCountdowns();
});

function initVideoConference() {
    const roomId = document.getElementById('video-container').dataset.roomId;
    const userId = document.getElementById('video-container').dataset.userId;
    
    const socket = io();
    videoConference = new VideoConference(roomId, userId, socket);
    
    socket.on('connect', () => {
        console.log('Connected to server');
        socket.emit('join_lesson', { room: roomId });
    });
    
    socket.on('offer', async (data) => {
        if (data.from != userId) {
            await videoConference.handleOffer(data.offer);
        }
    });
    
    socket.on('answer', async (data) => {
        if (data.from != userId) {
            await videoConference.handleAnswer(data.answer);
        }
    });
    
    socket.on('ice_candidate', async (data) => {
        if (data.from != userId && data.candidate) {
            await videoConference.handleIceCandidate(data.candidate);
        }
    });
    
    socket.on('user_joined', (data) => {
        console.log('User joined:', data.user);
        document.getElementById('waiting-message').style.display = 'block';
        if (videoConference.localStream) {
            setTimeout(() => videoConference.createOffer(), 1000);
        }
    });
    
    socket.on('user_left', (data) => {
        console.log('User left:', data.user);
        document.getElementById('waiting-message').style.display = 'block';
        if (videoConference.peerConnection) {
            videoConference.peerConnection.close();
            videoConference.peerConnection = null;
        }
    });
}

function initNotes() {
    const roomId = document.getElementById('video-container').dataset.roomId;
    const bookingId = window.location.pathname.split('/').pop();
    const socket = io();
    
    notesManager = new NotesManager(bookingId, roomId, socket);
}

function initCountdowns() {
    document.querySelectorAll('[data-countdown]').forEach(element => {
        const minutes = parseInt(element.dataset.countdown);
        if (!isNaN(minutes)) {
            UI.startCountdown(element.id, minutes);
        }
    });
}

function initLazyLoading() {
    const images = document.querySelectorAll('img[data-src]');
    
    const imageObserver = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                const img = entry.target;
                img.src = img.dataset.src;
                img.removeAttribute('data-src');
                imageObserver.unobserve(img);
            }
        });
    });
    
    images.forEach(img => imageObserver.observe(img));
}

// Глобальные функции для HTML вызовов
window.startVideo = () => videoConference?.start();
window.stopVideo = () => videoConference?.stop();
window.toggleMute = () => videoConference?.toggleMute();
window.shareScreen = () => videoConference?.shareScreen();