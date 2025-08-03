// Wishlist functionality
document.addEventListener('DOMContentLoaded', function() {
    
    // Remove from wishlist
    document.querySelectorAll('.remove-wishlist').forEach(btn => {
        btn.addEventListener('click', function() {
            const itemId = this.dataset.itemId;
            removeFromWishlist(itemId);
        });
    });
    
    // Move to cart
    document.querySelectorAll('.move-to-cart').forEach(btn => {
        btn.addEventListener('click', function() {
            const itemId = this.dataset.itemId;
            moveToCart(itemId);
        });
    });
});

function removeFromWishlist(itemId) {
    if (!confirm('Remove this item from your wishlist?')) {
        return;
    }
    
    fetch(`/cart/wishlist/remove/${itemId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Remove item from DOM
            const itemElement = document.querySelector(`[data-item-id="${itemId}"]`);
            itemElement.remove();
            showToast(data.message, 'success');
        } else {
            showToast(data.message, 'error');
        }
    })
    .catch(error => {
        showToast('Error removing item', 'error');
    });
}

function moveToCart(itemId) {
    fetch(`/cart/wishlist/move-to-cart/${itemId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Remove item from wishlist
            const itemElement = document.querySelector(`[data-item-id="${itemId}"]`);
            itemElement.remove();
            
            // Update cart count
            updateCartUI(data);
            showToast(data.message, 'success');
        } else {
            showToast(data.message, 'error');
        }
    })
    .catch(error => {
        showToast('Error moving item to cart', 'error');
    });
}

function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
