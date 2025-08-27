// Carousel functionality
class HeroCarousel {
    constructor() {
        this.currentSlideIndex = 0;
        this.slides = [];
        this.dots = [];
        this.autoSlideInterval = null;
        this.isTransitioning = false;
        
        this.init();
    }
    
    init() {
        this.slides = document.querySelectorAll('.carousel-slide');
        this.dots = document.querySelectorAll('.dot');
        
        if (this.slides.length === 0) return;
        
        // Set data attribute for single slide
        const carousel = document.querySelector('.hero-carousel');
        if (carousel && this.slides.length === 1) {
            carousel.setAttribute('data-single-slide', 'true');
        }
        
        if (this.slides.length > 1) {
            this.startAutoSlide();
            this.setupEventListeners();
        }
        
        // Ensure first slide is active
        this.slides[0]?.classList.add('active');
        this.dots[0]?.classList.add('active');
    }
    
    setupEventListeners() {
        const carousel = document.querySelector('.hero-carousel');
        
        // Pause auto-slide on hover
        carousel?.addEventListener('mouseenter', () => this.stopAutoSlide());
        carousel?.addEventListener('mouseleave', () => this.startAutoSlide());
        
        // Keyboard navigation
        document.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowLeft') this.changeSlide(-1);
            if (e.key === 'ArrowRight') this.changeSlide(1);
        });
        
        // Touch/swipe support
        let touchStartX = 0;
        let touchEndX = 0;
        
        carousel?.addEventListener('touchstart', (e) => {
            touchStartX = e.changedTouches[0].screenX;
        });
        
        carousel?.addEventListener('touchend', (e) => {
            touchEndX = e.changedTouches[0].screenX;
            this.handleSwipe(touchStartX, touchEndX);
        });
    }
    
    changeSlide(direction) {
        if (this.isTransitioning || this.slides.length <= 1) return;
        
        this.isTransitioning = true;
        
        // Remove active classes
        this.slides[this.currentSlideIndex]?.classList.remove('active');
        this.dots[this.currentSlideIndex]?.classList.remove('active');
        
        // Calculate new index
        this.currentSlideIndex += direction;
        
        if (this.currentSlideIndex >= this.slides.length) {
            this.currentSlideIndex = 0;
        } else if (this.currentSlideIndex < 0) {
            this.currentSlideIndex = this.slides.length - 1;
        }
        
        // Add active classes
        this.slides[this.currentSlideIndex]?.classList.add('active');
        this.dots[this.currentSlideIndex]?.classList.add('active');
        
        // Reset transition flag after animation
        setTimeout(() => {
            this.isTransitioning = false;
        }, 800);
        
        // Restart auto-slide
        this.stopAutoSlide();
        this.startAutoSlide();
    }
    
    goToSlide(index) {
        if (this.isTransitioning || this.slides.length <= 1) return;
        
        const direction = index - this.currentSlideIndex;
        if (direction === 0) return;
        
        this.changeSlide(direction);
    }
    
    startAutoSlide() {
        if (this.slides.length <= 1) return;
        
        this.stopAutoSlide();
        this.autoSlideInterval = setInterval(() => {
            this.changeSlide(1);
        }, 5000);
    }
    
    stopAutoSlide() {
        if (this.autoSlideInterval) {
            clearInterval(this.autoSlideInterval);
            this.autoSlideInterval = null;
        }
    }
    
    handleSwipe(startX, endX) {
        const swipeThreshold = 50;
        const swipeDistance = endX - startX;
        
        if (Math.abs(swipeDistance) > swipeThreshold) {
            if (swipeDistance > 0) {
                this.changeSlide(-1);
            } else {
                this.changeSlide(1);
            }
        }
    }
}

// Global functions for onclick handlers
function changeSlide(direction) {
    if (window.heroCarousel) {
        window.heroCarousel.changeSlide(direction);
    }
}

function currentSlide(n) {
    if (window.heroCarousel) {
        window.heroCarousel.goToSlide(n - 1);
    }
}

// Initialize carousel when DOM is loaded
document.addEventListener('DOMContentLoaded', function() {
    window.heroCarousel = new HeroCarousel();
});
