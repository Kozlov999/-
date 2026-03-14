// Управление заметками
export class NotesManager {
    constructor(bookingId, roomId, socket) {
        this.bookingId = bookingId;
        this.roomId = roomId;
        this.socket = socket;
        this.container = document.querySelector('.notes-container');
        this.form = document.querySelector('form[action*="add-note"]');
        
        this.init();
    }

    init() {
        this.loadNotes();
        this.setupWebSocket();
        this.setupForm();
    }

    setupWebSocket() {
        this.socket.on('note_added', (data) => {
            this.addNoteToUI(data.note, data.author, data.timestamp);
        });
    }

    setupForm() {
        if (this.form) {
            this.form.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const input = this.form.querySelector('input[name="content"]');
                const content = input.value.trim();
                
                if (!content) return;
                
                try {
                    const response = await fetch(`/api/notes/add/${this.bookingId}`, {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json',
                        },
                        body: JSON.stringify({ content })
                    });
                    
                    const data = await response.json();
                    
                    if (data.success) {
                        input.value = '';
                        this.socket.emit('new_note', {
                            room: this.roomId,
                            note: data.note
                        });
                    } else {
                        UI.showAlert(data.error, 'danger');
                    }
                } catch (error) {
                    console.error('Error adding note:', error);
                    UI.showAlert('Ошибка при добавлении заметки', 'danger');
                }
            });
        }
    }

    async loadNotes() {
        try {
            const response = await fetch(`/api/notes/${this.bookingId}`);
            const notes = await response.json();
            
            this.container.innerHTML = '';
            notes.forEach(note => {
                this.addNoteToUI(
                    note.content, 
                    note.author_name, 
                    note.timestamp,
                    note.author_id
                );
            });
        } catch (error) {
            console.error('Error loading notes:', error);
        }
    }

    

    addNoteToUI(content, author, timestamp, authorId = null) {
        const currentUserId = document.getElementById('video-container')?.dataset.userId;
        const isCurrentUser = authorId && authorId == currentUserId;
        
        const noteElement = document.createElement('div');
        noteElement.className = `card mb-2 ${isCurrentUser ? 'bg-light' : ''}`;
        noteElement.innerHTML = `
            <div class="card-body p-2">
                <div class="d-flex justify-content-between">
                    <small class="text-muted">${isCurrentUser ? 'Вы' : author}</small>
                    <small class="text-muted">${timestamp}</small>
                </div>
                <p class="mb-0 small">${this.escapeHtml(content)}</p>
            </div>
        `;
        
        this.container.insertBefore(noteElement, this.container.firstChild);
    }

    escapeHtml(text) {
        const div = document.createElement('div');
        div.textContent = text;
        return div.innerHTML;
    }
    
}
function addNoteWithAnimation(note) {
    const container = document.getElementById('notesContainer');
    const emptyState = container.querySelector('.notes-empty');
    
    // Удаляем пустое состояние если есть
    if (emptyState) {
        emptyState.remove();
    }
    
    // Создаем элемент заметки
    const noteElement = document.createElement('div');
    noteElement.className = `note-card ${note.author_id == userId ? 'my-note' : ''}`;
    noteElement.style.animation = 'slideIn 0.3s ease';
    
    noteElement.innerHTML = `
        <div class="note-header">
            <div class="note-author">
                <div class="note-avatar">${note.author_initials}</div>
                <div class="note-author-info">
                    <span class="note-author-name">${note.author_name}</span>
                    ${note.is_tutor ? '<span class="note-author-badge">Репетитор</span>' : ''}
                </div>
            </div>
            <div class="note-time">
                <i class="far fa-clock"></i>
                ${note.timestamp}
            </div>
        </div>
        <div class="note-content">${escapeHtml(note.content)}</div>
    `;
    
    container.appendChild(noteElement);
    scrollToBottom();
}