// Main JavaScript file

// DOM Content Loaded
document.addEventListener('DOMContentLoaded', function() {
    
    // Initialize tooltips and popovers if needed
    initializeComponents();
    
    // Mobile menu toggle
    initializeMobileMenu();
    
    // Search functionality
    initializeSearch();
    
    // Delivery zone checker
    initializeDeliveryChecker();
});

function initializeComponents() {
    // Add any component initialization here
    console.log('Components initialized');
}

function initializeMobileMenu() {
    const mobileMenuBtn = document.getElementById('mobile-menu-btn');
    const mobileMenu = document.getElementById('mobile-menu');
    
    if (mobileMenuBtn && mobileMenu) {
        mobileMenuBtn.addEventListener('click', function() {
            mobileMenu.classList.toggle('hidden');
        });
    }
}

function initializeSearch() {
    const searchInput = document.querySelector('input[placeholder*="Search"]');
    
    if (searchInput) {
        searchInput.addEventListener('input', function() {
            const query = this.value.trim();
            if (query.length > 2) {
                // Implement search suggestions
                // This will be enhanced when we add products
                console.log('Searching for:', query);
            }
        });
    }
}

function initializeDeliveryChecker() {
    // Will be implemented when we add this functionality
    console.log('Delivery checker ready');
}

// Utility functions
function showLoading(element) {
    element.innerHTML = '<div class="spinner mx-auto"></div>';
}

function hideLoading(element, originalContent) {
    element.innerHTML = originalContent;
}

// Helper to escape HTML entities
function escapeHtml(str) {
    if (typeof str !== 'string') return str;
    return str
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;')
        .replace(/'/g, '&#39;');
}

function showToast(message, type = 'info') {
    const toast = document.createElement('div');
    toast.className = `fixed top-4 right-4 p-4 rounded-lg shadow-lg z-50 ${getToastColor(type)}`;
    toast.innerHTML = `
        <div class="flex items-center justify-between">
            <span>${escapeHtml(message)}</span>
            <button onclick="this.parentElement.parentElement.remove()" class="ml-4">
                <i class="fas fa-times"></i>
            </button>
        </div>
    `;
    
    document.body.appendChild(toast);
    
    // Auto remove after 5 seconds
    setTimeout(() => {
        if (toast.parentElement) {
            toast.remove();
        }
    }, 5000);
}

function getToastColor(type) {
    const colors = {
        'success': 'bg-green-100 border border-green-400 text-green-700',
        'error': 'bg-red-100 border border-red-400 text-red-700',
        'warning': 'bg-yellow-100 border border-yellow-400 text-yellow-700',
        'info': 'bg-blue-100 border border-blue-400 text-blue-700'
    };
    return colors[type] || colors['info'];
}
