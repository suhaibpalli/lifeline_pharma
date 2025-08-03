// Cart functionality
document.addEventListener('DOMContentLoaded', function() {
    
    // Quantity controls
    document.querySelectorAll('.quantity-btn').forEach(btn => {
        btn.addEventListener('click', function() {
            const action = this.dataset.action;
            const itemId = this.dataset.itemId;
            const input = document.querySelector(`input[data-item-id="${itemId}"]`);
            
            let newValue = parseInt(input.value);
            if (action === 'increase') {
                newValue += 1;
            } else if (action === 'decrease' && newValue > 1) {
                newValue -= 1;
            }
            
            if (newValue !== parseInt(input.value)) {
                input.value = newValue;
                updateCartItem(itemId, newValue);
            }
        });
    });
    
    // Quantity input change
    document.querySelectorAll('.quantity-input').forEach(input => {
        input.addEventListener('change', function() {
            const itemId = this.dataset.itemId;
            const quantity = parseInt(this.value);
            
            if (quantity > 0) {
                updateCartItem(itemId, quantity);
            }
        });
    });
    
    // Remove item buttons
    document.querySelectorAll('.remove-item').forEach(btn => {
        btn.addEventListener('click', function() {
            const itemId = this.dataset.itemId;
            removeCartItem(itemId);
        });
    });
});

// Add to cart function (for product pages)
function addToCart(productId, quantity = 1) {
    showLoading();
    
    fetch('/cart/add/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            product_id: productId,
            quantity: quantity
        })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        
        if (data.success) {
            showToast(data.message, 'success');
            updateCartUI(data);
        } else {
            showToast(data.message, 'error');
        }
    })
    .catch(error => {
        hideLoading();
        showToast('Error adding item to cart', 'error');
    });
}

// Update cart item
function updateCartItem(itemId, quantity) {
    showLoading();
    
    fetch(`/cart/update/${itemId}/`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            quantity: quantity
        })
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        
        if (data.success) {
            // Update item total
            const itemElement = document.querySelector(`[data-item-id="${itemId}"]`);
            const itemTotal = itemElement.querySelector('.item-total');
            itemTotal.textContent = `₹${data.item_total}`;
            
            updateCartUI(data);
            showToast(data.message, 'success');
        } else {
            showToast(data.message, 'error');
        }
    })
    .catch(error => {
        hideLoading();
        showToast('Error updating cart', 'error');
    });
}

// Remove cart item
function removeCartItem(itemId) {
    if (!confirm('Are you sure you want to remove this item?')) {
        return;
    }
    
    showLoading();
    
    fetch(`/cart/remove/${itemId}/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        hideLoading();
        
        if (data.success) {
            // Remove item from DOM
            const itemElement = document.querySelector(`[data-item-id="${itemId}"]`);
            itemElement.remove();
            
            updateCartUI(data);
            showToast(data.message, 'success');
            
            // Check if cart is empty
            if (data.cart_items_count === 0) {
                location.reload();
            }
        } else {
            showToast(data.message, 'error');
        }
    })
    .catch(error => {
        hideLoading();
        showToast('Error removing item', 'error');
    });
}

// Update cart UI elements
function updateCartUI(data) {
    // Update cart count in header
    const cartCount = document.querySelector('#cart-count, .cart-count');
    if (cartCount) {
        cartCount.textContent = data.cart_items_count;
    }
    
    // Update cart badge in header
    const cartBadge = document.querySelector('.cart-badge');
    if (cartBadge) {
        cartBadge.textContent = data.cart_items_count;
    }
    
    // Update cart subtotal
    const cartSubtotal = document.querySelector('#cart-subtotal');
    if (cartSubtotal) {
        cartSubtotal.textContent = `₹${data.cart_subtotal}`;
    }
    
    // Update cart total
    const cartTotal = document.querySelector('#cart-total');
    if (cartTotal) {
        cartTotal.textContent = `₹${data.cart_subtotal}`;
    }
}

// Utility functions
function showLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.remove('hidden');
        overlay.classList.add('flex');
    }
}

function hideLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.add('hidden');
        overlay.classList.remove('flex');
    }
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
