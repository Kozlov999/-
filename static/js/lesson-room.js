<script>
    // Глобальные переменные
    const roomId = "{{ booking.meeting_id }}";
    const userId = {{ current_user.id }};
    const userName = "{{ current_user.full_name }}";
    const userInitials = "{{ current_user.initials }}";
    const bookingId = {{ booking.id }};
    
    let socket = null;
    let localStream = null;
    let peerConnection = null;
    let remoteStream = null;
    let isMuted = false;
    let isScreenSharing = false;
    let typingTimeout = null;
    let lastMessageDate = null;
    let onlineUsers = new Set();
    let currentPort = window.location.port || 8000;
    let wsPort = 8001; // По умолчанию, будет обновлено с сервера

    // WebRTC configuration
    const rtcConfig = {
        iceServers: [
            { urls: 'stun:stun.l.google.com:19302' },
            { urls: 'stun:stun1.l.google.com:19302' },
            { urls: 'stun:stun2.l.google.com:19302' },
            { urls: 'stun:stun3.l.google.com:19302' },
            { urls: 'stun:stun4.l.google.com:19302' }
        ],
        iceCandidatePoolSize: 10
    };

    // Получение информации о портах
    async function fetchPortsInfo() {
        try {
            const response = await fetch('/api/ports-info');
            const data = await response.json();
            wsPort = data.ws_port;
            console.log(`📡 WebSocket порт: ${wsPort}, HTTP порт: ${data.main_port}`);
            return data;
        } catch (error) {
            console.error('Ошибка получения информации о портах:', error);
            return null;
        }
    }

    // Инициализация Socket.IO с выбором порта

    function initSocket() {
    console.log('🔌 Initializing Socket.IO...');
    
    // Показываем индикатор загрузки
    addSystemMessage('Подключение к серверу...');
    
    socket = io({
        transports: ['websocket', 'polling'],
        reconnection: true,
        reconnectionAttempts: 10,
        reconnectionDelay: 1000,
        timeout: 20000
    });
    
    socket.on('connect', function() {
        console.log('✅ Connected to server');
        console.log('Socket ID:', socket.id);
        
        updateOnlineStatus(true);
        addSystemMessage('Подключено к серверу');
        
        // Отправляем запрос на присоединение к комнате
        console.log('📤 Sending join_lesson with:', { 
            room: roomId, 
            user_name: userName, 
            user_id: userId 
        });
        
        socket.emit('join_lesson', {
            room: roomId,
            user_name: userName,
            user_id: userId
        });
        
        // Загружаем историю чата
        loadChatHistory();
    });
    
    socket.on('connect_error', function(error) {
        console.error('❌ Connection error:', error);
        addSystemMessage('Ошибка подключения к серверу. Переподключение...');
    });
    
    socket.on('disconnect', function(reason) {
        console.log('❌ Disconnected:', reason);
        updateOnlineStatus(false);
        addSystemMessage('Соединение с сервером потеряно');
    });
    
    socket.on('joined', function(data) {
        console.log('✅ Successfully joined room:', data);
        addSystemMessage('Вы подключились к уроку');
    });
    
    socket.on('new_chat_message', function(data) {
        console.log('📨 New message received:', data);
        let messageData = data.message || data;
        addMessageToChat(messageData, true);
        
        if (messageData.user_id !== userId) {
            markMessagesAsRead();
        }
        scrollToBottom();
    });
        
        setupSocketHandlers();
    }

    // Настройка обработчиков Socket.IO
    function setupSocketHandlers() {
        socket.on('connect', function() {
            console.log('✅ Подключено к серверу');
            console.log('📤 Отправка join_lesson...');
            
            updateOnlineStatus(true);
            
            socket.emit('join_lesson', {
                room: roomId,
                user_name: userName,
                user_id: userId
            });
            
            loadChatHistory();
        });
        
        socket.on('connected', function(data) {
            console.log('📡 Сервер подтвердил подключение:', data);
            if (data.ws_port) {
                wsPort = data.ws_port;
            }
        });
        
        socket.on('disconnect', function(reason) {
            console.log('❌ Отключено от сервера:', reason);
            updateOnlineStatus(false);
            addSystemMessage('Соединение с сервером потеряно. Попытка переподключения...');
        });
        
        socket.on('connect_error', function(error) {
            console.error('Ошибка подключения:', error);
            addSystemMessage('Ошибка подключения к серверу');
        });
        
        socket.on('joined', function(data) {
            console.log('✅ Присоединились к комнате:', data.room);
            addSystemMessage('Вы подключились к уроку');
        });
        
        socket.on('user_joined', function(data) {
            console.log('👤 Пользователь присоединился:', data.user);
            onlineUsers.add(data.user_id);
            updateOnlineCount();
            addSystemMessage(`${data.user} присоединился к уроку`);
            
            // Если мы репетитор и есть локальный поток, создаем offer
            {% if current_user.role == 'tutor' %}
            if (localStream && !peerConnection) {
                setTimeout(() => createOffer(), 1000);
            }
            {% endif %}
        });
        
        socket.on('user_left', function(data) {
            console.log('👋 Пользователь покинул:', data.user);
            onlineUsers.delete(data.user_id);
            updateOnlineCount();
            addSystemMessage(`${data.user} покинул урок`);
            
            // Закрываем peer connection если пользователь ушел
            if (peerConnection) {
                peerConnection.close();
                peerConnection = null;
                document.getElementById('waiting-message').style.display = 'flex';
            }
        });
        
        socket.on('new_chat_message', function(data) {
            console.log('📨 Новое сообщение:', data);
            let messageData = data.message || data;
            addMessageToChat(messageData, true);
            
            if (messageData.user_id !== userId) {
                markMessagesAsRead();
            }
            scrollToBottom();
        });
        
        socket.on('user_typing', function(data) {
            if (data.is_typing) {
                showTypingIndicator(data.user_name);
            } else {
                hideTypingIndicator();
            }
        });
        
        socket.on('messages_read', function(data) {
            updateMessagesReadStatus(data.user_id);
        });
        
        // WebRTC handlers
        socket.on('offer', async function(data) {
            if (data.from != userId) {
                await handleOffer(data.offer);
            }
        });
        
        socket.on('answer', async function(data) {
            if (data.from != userId) {
                await handleAnswer(data.answer);
            }
        });
        
        socket.on('ice_candidate', async function(data) {
            if (data.from != userId && data.candidate) {
                await handleIceCandidate(data.candidate);
            }
        });
        
        socket.on('error', function(data) {
            console.error('❌ Ошибка WebSocket:', data);
            addSystemMessage('Ошибка: ' + data.message);
        });
    }

    // Функция для создания peer connection
    function createPeerConnection() {
        try {
            if (peerConnection) {
                peerConnection.close();
            }
            
            peerConnection = new RTCPeerConnection(rtcConfig);
            console.log('✅ PeerConnection создан');
            
            peerConnection.onicecandidate = (event) => {
                if (event.candidate) {
                    console.log('📡 Отправка ICE candidate');
                    socket.emit('ice_candidate', {
                        room: roomId,
                        candidate: event.candidate,
                        user_id: userId
                    });
                }
            };
            
            peerConnection.oniceconnectionstatechange = () => {
                console.log('❄️ ICE состояние:', peerConnection.iceConnectionState);
                if (peerConnection.iceConnectionState === 'connected' || 
                    peerConnection.iceConnectionState === 'completed') {
                    document.getElementById('waiting-message').style.display = 'none';
                    addSystemMessage('✅ Соединение установлено');
                }
            };
            
            peerConnection.onconnectionstatechange = () => {
                console.log('🔌 Состояние соединения:', peerConnection.connectionState);
            };
            
            peerConnection.ontrack = (event) => {
                console.log('📹 Получен удаленный трек:', event.track.kind);
                
                if (!remoteStream) {
                    remoteStream = new MediaStream();
                }
                
                if (event.streams && event.streams[0]) {
                    remoteStream = event.streams[0];
                } else {
                    remoteStream.addTrack(event.track);
                }
                
                const remoteVideo = document.getElementById('remoteVideo');
                if (remoteVideo) {
                    remoteVideo.srcObject = remoteStream;
                    remoteVideo.onloadedmetadata = () => {
                        remoteVideo.play().catch(e => console.log('Auto-play prevented:', e));
                    };
                    document.getElementById('waiting-message').style.display = 'none';
                    addSystemMessage('👤 Другой участник подключился');
                }
            };
            
            if (localStream) {
                localStream.getTracks().forEach(track => {
                    peerConnection.addTrack(track, localStream);
                    console.log(`➕ Добавлен локальный трек: ${track.kind}`);
                });
            }
            
            return peerConnection;
            
        } catch (error) {
            console.error('❌ Ошибка создания PeerConnection:', error);
            return null;
        }
    }

    // Функция для начала видео
    async function startVideo() {
        try {
            console.log('🎥 Запуск видео...');
            
            const constraints = {
                video: {
                    width: { ideal: 1280 },
                    height: { ideal: 720 },
                    facingMode: 'user'
                },
                audio: {
                    echoCancellation: true,
                    noiseSuppression: true,
                    autoGainControl: true
                }
            };
            
            localStream = await navigator.mediaDevices.getUserMedia(constraints);
            console.log('✅ Получен локальный поток');
            
            const localVideo = document.getElementById('localVideo');
            if (localVideo) {
                localVideo.srcObject = localStream;
                localVideo.onloadedmetadata = () => {
                    localVideo.play().catch(e => console.log('Auto-play prevented:', e));
                };
            }
            
            document.getElementById('startBtn').style.display = 'none';
            document.getElementById('stopBtn').style.display = 'inline-block';
            document.getElementById('muteBtn').style.display = 'inline-block';
            document.getElementById('shareScreenBtn').style.display = 'inline-block';
            
            if (!peerConnection) {
                createPeerConnection();
            } else {
                localStream.getTracks().forEach(track => {
                    peerConnection.addTrack(track, localStream);
                });
            }
            
            addSystemMessage('✅ Вы включили видео');
            
            {% if current_user.role == 'tutor' %}
            setTimeout(() => {
                createOffer();
            }, 1000);
            {% endif %}
            
        } catch (error) {
            console.error('❌ Ошибка камеры:', error);
            let errorMessage = 'Ошибка доступа к камере/микрофону';
            
            if (error.name === 'NotAllowedError') {
                errorMessage = 'Доступ к камере запрещен. Разрешите доступ в настройках браузера.';
            } else if (error.name === 'NotFoundError') {
                errorMessage = 'Камера или микрофон не найдены.';
            } else if (error.name === 'NotReadableError') {
                errorMessage = 'Камера или микрофон заняты другим приложением.';
            }
            
            alert(errorMessage);
        }
    }

    // Функция для создания offer
    async function createOffer() {
        try {
            if (!peerConnection) {
                createPeerConnection();
            }
            
            console.log('📞 Создание offer...');
            const offer = await peerConnection.createOffer({
                offerToReceiveAudio: true,
                offerToReceiveVideo: true
            });
            
            await peerConnection.setLocalDescription(offer);
            console.log('✅ Локальное описание установлено');
            
            socket.emit('offer', {
                room: roomId,
                offer: peerConnection.localDescription,
                user_id: userId
            });
            
            console.log('📤 Offer отправлен');
            
        } catch (error) {
            console.error('❌ Ошибка создания offer:', error);
        }
    }

    // Обработка получения offer
    async function handleOffer(offer) {
        try {
            console.log('📥 Получен offer');
            
            if (!peerConnection) {
                createPeerConnection();
            }
            
            await peerConnection.setRemoteDescription(new RTCSessionDescription(offer));
            console.log('✅ Удаленное описание установлено');
            
            const answer = await peerConnection.createAnswer();
            await peerConnection.setLocalDescription(answer);
            console.log('✅ Answer создан');
            
            socket.emit('answer', {
                room: roomId,
                answer: peerConnection.localDescription,
                user_id: userId
            });
            
            console.log('📤 Answer отправлен');
            
        } catch (error) {
            console.error('❌ Ошибка обработки offer:', error);
        }
    }

    // Обработка получения answer
    async function handleAnswer(answer) {
        try {
            console.log('📥 Получен answer');
            
            if (!peerConnection) {
                console.error('Нет peer connection для answer');
                return;
            }
            
            await peerConnection.setRemoteDescription(new RTCSessionDescription(answer));
            console.log('✅ Удаленное описание установлено');
            
        } catch (error) {
            console.error('❌ Ошибка обработки answer:', error);
        }
    }

    // Обработка ICE candidate
    async function handleIceCandidate(candidate) {
        try {
            console.log('📥 Получен ICE candidate');
            
            if (!peerConnection) {
                console.error('Нет peer connection для ICE candidate');
                return;
            }
            
            await peerConnection.addIceCandidate(new RTCIceCandidate(candidate));
            console.log('✅ ICE candidate добавлен');
            
        } catch (error) {
            console.error('❌ Ошибка добавления ICE candidate:', error);
        }
    }

    // Функция остановки видео
    function stopVideo() {
        if (localStream) {
            localStream.getTracks().forEach(track => {
                track.stop();
            });
            localStream = null;
        }
        
        if (peerConnection) {
            peerConnection.close();
            peerConnection = null;
        }
        
        remoteStream = null;
        
        const localVideo = document.getElementById('localVideo');
        const remoteVideo = document.getElementById('remoteVideo');
        
        if (localVideo) localVideo.srcObject = null;
        if (remoteVideo) remoteVideo.srcObject = null;
        
        document.getElementById('startBtn').style.display = 'inline-block';
        document.getElementById('stopBtn').style.display = 'none';
        document.getElementById('muteBtn').style.display = 'none';
        document.getElementById('unmuteBtn').style.display = 'none';
        document.getElementById('shareScreenBtn').style.display = 'none';
        document.getElementById('waiting-message').style.display = 'flex';
        
        addSystemMessage('⏹ Вы выключили видео');
    }

    // Функция для переключения звука
    function toggleMute() {
        if (localStream) {
            const audioTracks = localStream.getAudioTracks();
            audioTracks.forEach(track => {
                track.enabled = !track.enabled;
            });
            isMuted = !isMuted;
            
            document.getElementById('muteBtn').style.display = isMuted ? 'none' : 'inline-block';
            document.getElementById('unmuteBtn').style.display = isMuted ? 'inline-block' : 'none';
            
            addSystemMessage(isMuted ? '🔇 Микрофон выключен' : '🎤 Микрофон включен');
        }
    }

    // Функция для демонстрации экрана
    async function shareScreen() {
        try {
            if (!peerConnection) {
                alert('Сначала включите видео');
                return;
            }
            
            if (isScreenSharing) {
                const stream = await navigator.mediaDevices.getUserMedia({ video: true });
                const videoTrack = stream.getVideoTracks()[0];
                
                const sender = peerConnection.getSenders().find(s => s.track && s.track.kind === 'video');
                if (sender) {
                    await sender.replaceTrack(videoTrack);
                }
                
                if (localStream) {
                    const oldScreenTrack = localStream.getVideoTracks().find(t => t.label.includes('screen'));
                    if (oldScreenTrack) {
                        oldScreenTrack.stop();
                        localStream.removeTrack(oldScreenTrack);
                    }
                    localStream.addTrack(videoTrack);
                }
                
                isScreenSharing = false;
                addSystemMessage('🖥 Демонстрация экрана завершена');
                
            } else {
                const screenStream = await navigator.mediaDevices.getDisplayMedia({ 
                    video: true,
                    audio: false
                });
                
                const screenTrack = screenStream.getVideoTracks()[0];
                
                const sender = peerConnection.getSenders().find(s => s.track && s.track.kind === 'video');
                if (sender) {
                    await sender.replaceTrack(screenTrack);
                }
                
                if (localStream) {
                    const oldVideoTrack = localStream.getVideoTracks()[0];
                    if (oldVideoTrack) {
                        localStream.removeTrack(oldVideoTrack);
                    }
                    localStream.addTrack(screenTrack);
                }
                
                screenTrack.onended = () => {
                    shareScreen();
                };
                
                isScreenSharing = true;
                addSystemMessage('📺 Вы начали демонстрацию экрана');
            }
            
        } catch (error) {
            console.error('❌ Ошибка демонстрации экрана:', error);
        }
    }

    // ==================== ФУНКЦИИ ЧАТА ====================

    function initChat() {
        const chatInput = document.getElementById('chatInput');
        const sendButton = document.getElementById('sendMessageBtn');
        
        if (!chatInput || !sendButton) {
            console.warn('Элементы чата не найдены, повтор через 500ms');
            setTimeout(initChat, 500);
            return;
        }
        
        chatInput.addEventListener('input', function() {
            sendButton.disabled = !this.value.trim();
            
            if (typingTimeout) clearTimeout(typingTimeout);
            
            socket.emit('chat_typing', {
                room: roomId,
                user_name: userName,
                is_typing: true
            });
            
            typingTimeout = setTimeout(function() {
                socket.emit('chat_typing', {
                    room: roomId,
                    user_name: userName,
                    is_typing: false
                });
            }, 1000);
        });
        
        chatInput.addEventListener('keypress', function(e) {
            if (e.key === 'Enter' && !e.shiftKey) {
                e.preventDefault();
                sendMessage();
            }
        });
        
        sendButton.addEventListener('click', sendMessage);
    }

    // Загрузка истории чата
    async function loadChatHistory() {
        try {
            const response = await fetch(`/lesson/api/chat/${bookingId}/messages`);
            const messages = await response.json();
            
            const container = document.getElementById('chatMessages');
            const loadingEl = document.getElementById('loadingMessages');
            
            if (loadingEl) loadingEl.remove();
            
            if (messages.error) {
                console.error('Ошибка загрузки сообщений:', messages.error);
                return;
            }
            
            if (container) {
                container.innerHTML = '';
                lastMessageDate = null;
                
                messages.forEach(msg => addMessageToChat(msg, false));
                scrollToBottom();
                markMessagesAsRead();
            }
            
        } catch (error) {
            console.error('Ошибка загрузки истории чата:', error);
        }
    }

    // Отправка сообщения
    async function sendMessage() {
        const input = document.getElementById('chatInput');
        const message = input.value.trim();
        
        if (!message) return;
        
        const sendButton = document.getElementById('sendMessageBtn');
        sendButton.disabled = true;
        
        try {
            const response = await fetch(`/lesson/api/chat/${bookingId}/send`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ message: message })
            });
            
            const data = await response.json();
            
            if (data.success) {
                input.value = '';
                
                if (typingTimeout) {
                    clearTimeout(typingTimeout);
                    socket.emit('chat_typing', {
                        room: roomId,
                        user_name: userName,
                        is_typing: false
                    });
                }
                
                console.log('✅ Сообщение отправлено');
            } else {
                console.error('Ошибка отправки:', data.error);
                alert(data.error || 'Ошибка отправки');
                sendButton.disabled = false;
            }
            
        } catch (error) {
            console.error('Ошибка отправки сообщения:', error);
            alert('Ошибка отправки сообщения');
            sendButton.disabled = false;
        }
    }

    // Добавление сообщения в чат
    function addMessageToChat(msg, animate = true) {
        const container = document.getElementById('chatMessages');
        if (!container) return;
        
        const loadingEl = document.getElementById('loadingMessages');
        if (loadingEl) loadingEl.remove();
        
        const msgDate = msg.date || getCurrentDate();
        if (lastMessageDate !== msgDate) {
            addDateDivider(msgDate);
            lastMessageDate = msgDate;
        }
        
        const wrapper = document.createElement('div');
        wrapper.className = `message-wrapper ${msg.user_id === userId ? 'my-message' : 'other-message'}`;
        if (animate) {
            wrapper.style.animation = 'fadeIn 0.3s ease';
        }
        
        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        
        const header = document.createElement('div');
        header.className = 'message-header';
        
        if (msg.user_id !== userId) {
            const avatar = document.createElement('div');
            avatar.className = 'message-avatar';
            avatar.textContent = msg.user_initials || msg.user_name.charAt(0).toUpperCase();
            header.appendChild(avatar);
        }
        
        const author = document.createElement('span');
        author.className = 'message-author';
        author.textContent = msg.user_id === userId ? 'Вы' : (msg.user_name || 'Пользователь');
        header.appendChild(author);
        
        const time = document.createElement('span');
        time.className = 'message-time';
        time.textContent = msg.timestamp || new Date().toLocaleTimeString('ru-RU', { hour: '2-digit', minute: '2-digit' });
        header.appendChild(time);
        
        bubble.appendChild(header);
        
        const content = document.createElement('div');
        content.className = 'message-content';
        content.textContent = msg.message;
        bubble.appendChild(content);
        
        wrapper.appendChild(bubble);
        container.appendChild(wrapper);
        scrollToBottom();
    }

    function addSystemMessage(text) {
        const container = document.getElementById('chatMessages');
        if (!container) return;
        
        const systemDiv = document.createElement('div');
        systemDiv.className = 'system-message';
        systemDiv.innerHTML = `<i class="fas fa-info-circle me-1"></i>${text}`;
        container.appendChild(systemDiv);
        scrollToBottom();
    }

    function addDateDivider(date) {
        const container = document.getElementById('chatMessages');
        if (!container) return;
        
        const divider = document.createElement('div');
        divider.className = 'date-divider';
        divider.innerHTML = `<span>${date}</span>`;
        container.appendChild(divider);
    }

    function getCurrentDate() {
        const now = new Date();
        return now.toLocaleDateString('ru-RU', {
            day: '2-digit',
            month: '2-digit',
            year: 'numeric'
        });
    }

    async function markMessagesAsRead() {
        try {
            await fetch(`/lesson/api/chat/${bookingId}/mark-read`, {
                method: 'POST'
            });
        } catch (error) {
            console.error('Ошибка отметки прочитанных:', error);
        }
    }

    function updateMessagesReadStatus(readerId) {
        if (readerId !== userId) {
            const myMessages = document.querySelectorAll('.my-message .message-status');
            myMessages.forEach(msg => {
                if (msg) msg.innerHTML = '<i class="fas fa-check-double"></i> Прочитано';
            });
        }
    }

    function showTypingIndicator(userName) {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) {
            indicator.textContent = `${userName} печатает...`;
            indicator.classList.add('show');
        }
    }

    function hideTypingIndicator() {
        const indicator = document.getElementById('typingIndicator');
        if (indicator) {
            indicator.classList.remove('show');
        }
    }

    function updateOnlineStatus(isOnline) {
        const statusEl = document.getElementById('onlineStatus');
        if (statusEl) {
            statusEl.innerHTML = isOnline ? 
                '<i class="fas fa-circle text-success"></i> <span id="onlineCount">1</span> онлайн' : 
                '<i class="fas fa-circle text-secondary"></i> Подключение...';
        }
    }

    function updateOnlineCount() {
        const countEl = document.getElementById('onlineCount');
        if (countEl) {
            countEl.textContent = onlineUsers.size + 1;
        }
    }

    function scrollToBottom() {
        const container = document.getElementById('chatMessages');
        if (container) {
            container.scrollTop = container.scrollHeight;
        }
    }

    // Инициализация при загрузке страницы
    document.addEventListener('DOMContentLoaded', function() {
        console.log('🚀 Страница загружена, инициализация...');
        console.log('ID комнаты:', roomId);
        console.log('ID пользователя:', userId);
        
        initSocket();
        initChat();
        
        {% if current_user.role == 'tutor' and not booking.meeting_ended %}
        setTimeout(() => {
            document.getElementById('startBtn')?.click();
        }, 1000);
        {% endif %}
    });
</script>