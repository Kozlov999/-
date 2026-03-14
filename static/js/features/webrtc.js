// WebRTC для видеоуроков
export class VideoConference {
    constructor(roomId, userId, socket) {
        this.roomId = roomId;
        this.userId = userId;
        this.socket = socket;
        this.localStream = null;
        this.remoteStream = null;
        this.peerConnection = null;
        this.isMuted = false;
        this.isScreenSharing = false;
        
        this.rtcConfiguration = {
            iceServers: [
                { urls: 'stun:stun.l.google.com:19302' },
                { urls: 'stun:stun1.l.google.com:19302' }
            ]
        };
    }

    async start() {
        try {
            await this.checkDevices();
            this.localStream = await navigator.mediaDevices.getUserMedia({
                video: { width: 1280, height: 720 },
                audio: true
            });
            
            this.updateUI('started');
            this.createPeerConnection();
            this.addTracks();
            
            return true;
        } catch (error) {
            this.handleError(error);
            return false;
        }
    }

    async checkDevices() {
        if (navigator.mediaDevices && navigator.mediaDevices.enumerateDevices) {
            const devices = await navigator.mediaDevices.enumerateDevices();
            const hasCamera = devices.some(d => d.kind === 'videoinput');
            const hasMic = devices.some(d => d.kind === 'audioinput');
            
            if (!hasCamera || !hasMic) {
                const missing = [];
                if (!hasCamera) missing.push('камера');
                if (!hasMic) missing.push('микрофон');
                UI.showAlert(`Внимание: не найдена ${missing.join(' и ')}`, 'warning');
            }
        }
    }

    stop() {
        if (this.localStream) {
            this.localStream.getTracks().forEach(track => track.stop());
            this.localStream = null;
        }
        if (this.peerConnection) {
            this.peerConnection.close();
            this.peerConnection = null;
        }
        this.updateUI('stopped');
    }

    toggleMute() {
        if (this.localStream) {
            const audioTracks = this.localStream.getAudioTracks();
            audioTracks.forEach(track => {
                track.enabled = this.isMuted;
            });
            this.isMuted = !this.isMuted;
            this.updateMuteUI();
        }
    }

    async shareScreen() {
        try {
            if (this.isScreenSharing) {
                await this.stopScreenSharing();
            } else {
                await this.startScreenSharing();
            }
        } catch (error) {
            console.error('Screen sharing error:', error);
            UI.showAlert('Ошибка при демонстрации экрана', 'danger');
        }
    }

    async startScreenSharing() {
        const screenStream = await navigator.mediaDevices.getDisplayMedia({ 
            video: true, 
            audio: true 
        });
        
        const videoTrack = this.localStream.getVideoTracks()[0];
        await videoTrack.replaceTrack(screenStream.getVideoTracks()[0]);
        
        screenStream.getVideoTracks()[0].addEventListener('ended', () => {
            this.stopScreenSharing();
        });
        
        this.isScreenSharing = true;
    }

    async stopScreenSharing() {
        const newStream = await navigator.mediaDevices.getUserMedia({ 
            video: true, 
            audio: true 
        });
        
        const videoTrack = this.localStream.getVideoTracks()[0];
        await videoTrack.replaceTrack(newStream.getVideoTracks()[0]);
        
        this.isScreenSharing = false;
    }

    createPeerConnection() {
        this.peerConnection = new RTCPeerConnection(this.rtcConfiguration);
        
        this.peerConnection.onicecandidate = (event) => {
            if (event.candidate) {
                this.socket.emit('ice_candidate', {
                    room: this.roomId,
                    candidate: event.candidate
                });
            }
        };
        
        this.peerConnection.ontrack = (event) => {
            this.remoteStream = event.streams[0];
            document.getElementById('remoteVideo').srcObject = this.remoteStream;
            document.getElementById('waiting-message').style.display = 'none';
        };
        
        this.peerConnection.onconnectionstatechange = () => {
            console.log('Connection state:', this.peerConnection.connectionState);
            if (this.peerConnection.connectionState === 'failed') {
                UI.showAlert('Соединение не удалось установить', 'danger');
            }
        };
    }

    addTracks() {
        this.localStream.getTracks().forEach(track => {
            this.peerConnection.addTrack(track, this.localStream);
        });
    }

    async createOffer() {
        if (!this.peerConnection) return;
        
        try {
            const offer = await this.peerConnection.createOffer();
            await this.peerConnection.setLocalDescription(offer);
            this.socket.emit('offer', {
                room: this.roomId,
                offer: offer
            });
        } catch (error) {
            console.error('Error creating offer:', error);
        }
    }

    async handleOffer(offer) {
        if (!this.peerConnection) {
            this.createPeerConnection();
            this.addTracks();
        }
        
        try {
            await this.peerConnection.setRemoteDescription(new RTCSessionDescription(offer));
            const answer = await this.peerConnection.createAnswer();
            await this.peerConnection.setLocalDescription(answer);
            this.socket.emit('answer', {
                room: this.roomId,
                answer: answer
            });
        } catch (error) {
            console.error('Error handling offer:', error);
        }
    }

    async handleAnswer(answer) {
        try {
            await this.peerConnection.setRemoteDescription(new RTCSessionDescription(answer));
        } catch (error) {
            console.error('Error handling answer:', error);
        }
    }

    async handleIceCandidate(candidate) {
        try {
            await this.peerConnection.addIceCandidate(new RTCIceCandidate(candidate));
        } catch (error) {
            console.error('Error adding ICE candidate:', error);
        }
    }

    updateUI(state) {
        const elements = {
            startBtn: document.getElementById('startBtn'),
            stopBtn: document.getElementById('stopBtn'),
            muteBtn: document.getElementById('muteBtn'),
            shareBtn: document.getElementById('shareScreenBtn'),
            localVideo: document.getElementById('localVideo')
        };
        
        if (state === 'started') {
            elements.startBtn.style.display = 'none';
            elements.stopBtn.style.display = 'inline-block';
            elements.muteBtn.style.display = 'inline-block';
            elements.shareBtn.style.display = 'inline-block';
            elements.localVideo.srcObject = this.localStream;
        } else {
            elements.startBtn.style.display = 'inline-block';
            elements.stopBtn.style.display = 'none';
            elements.muteBtn.style.display = 'none';
            elements.shareBtn.style.display = 'none';
            elements.localVideo.srcObject = null;
            document.getElementById('remoteVideo').srcObject = null;
            document.getElementById('waiting-message').style.display = 'block';
        }
    }

    updateMuteUI() {
        document.getElementById('muteBtn').style.display = this.isMuted ? 'none' : 'inline-block';
        document.getElementById('unmuteBtn').style.display = this.isMuted ? 'inline-block' : 'none';
    }

    handleError(error) {
        console.error('Camera/microphone error:', error);
        let message = 'Не удалось получить доступ к камере/микрофону. ';
        
        const errors = {
            'NotAllowedError': 'Разрешите доступ к камере и микрофону.',
            'NotFoundError': 'Камера или микрофон не найдены.',
            'NotReadableError': 'Устройство уже используется другим приложением.',
            'OverconstrainedError': 'Устройство не поддерживает требуемые параметры.',
            'TypeError': 'Неверные параметры запроса.'
        };
        
        message += errors[error.name] || 'Проверьте подключение устройств и разрешения браузера.';
        UI.showAlert(message, 'danger');
    }
}