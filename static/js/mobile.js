// Мобильные улучшения
document.addEventListener('DOMContentLoaded', function() {
    
    // Pull-to-refresh защита
    let startY = 0;
    document.addEventListener('touchstart', (e) => {
        startY = e.touches[0].pageY;
    }, { passive: true });
    
    document.addEventListener('touchmove', (e) => {
        const scrollTop = document.documentElement.scrollTop;
        if (scrollTop === 0 && e.touches[0].pageY > startY) {
            e.preventDefault();
        }
    }, { passive: false });
    
    // Свайп для закрытия модалок
    document.querySelectorAll('.modal').forEach(modal => {
        let touchStartY = 0;
        const modalContent = modal.querySelector('.modal-content');
        
        modal.addEventListener('touchstart', (e) => {
            touchStartY = e.touches[0].clientY;
        }, { passive: true });
        
        modal.addEventListener('touchmove', (e) => {
            const touchY = e.touches[0].clientY;
            const deltaY = touchY - touchStartY;
            
            if (deltaY > 50 && modal.classList.contains('show')) {
                const bsModal = bootstrap.Modal.getInstance(modal);
                if (bsModal) bsModal.hide();
            }
        }, { passive: true });
    });
    function initVideoGestures() {
    const videoContainer = document.getElementById('video-container');
    if (!videoContainer) return;
    
    let touchStartX = 0;
    let touchEndX = 0;
    
    videoContainer.addEventListener('touchstart', (e) => {
        touchStartX = e.changedTouches[0].screenX;
    }, { passive: true });
    
    videoContainer.addEventListener('touchend', (e) => {
        touchEndX = e.changedTouches[0].screenX;
        handleVideoSwipe();
    }, { passive: true });
    
    function handleVideoSwipe() {
        const swipeDistance = touchEndX - touchStartX;
        if (Math.abs(swipeDistance) > 100) {
            // Переключение между режимами видео
            toggleVideoLayout();
        }
    }
}
    
    // Улучшенные тач-события для каруселей
    document.querySelectorAll('.scrollable-cards').forEach(scrollable => {
        let isScrolling = false;
        
        scrollable.addEventListener('touchstart', () => {
            isScrolling = true;
        }, { passive: true });
        
        scrollable.addEventListener('touchend', () => {
            isScrolling = false;
            // Снап к ближайшей карточке
            const scrollLeft = scrollable.scrollLeft;
            const cardWidth = scrollable.querySelector('.card')?.offsetWidth || 0;
            const targetScroll = Math.round(scrollLeft / cardWidth) * cardWidth;
            
            scrollable.scrollTo({
                left: targetScroll,
                behavior: 'smooth'
            });
        }, { passive: true });
    });
});