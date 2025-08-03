// Orders functionality
document.addEventListener('DOMContentLoaded', function() {
    
    // Cancel order buttons
    document.querySelectorAll('.cancel-order').forEach(btn => {
        btn.addEventListener('click', function() {
            const orderNumber = this.dataset.orderNumber;
            cancelOrder(orderNumber);
        });
    });
});

// Cancel order function
function cancelOrder(orderNumber) {
    if (!confirm('Are you sure you want to cancel this order?')) {
        return;
    }
    
    fetch(`/orders/${orderNumber}/cancel/`, {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showToast(data.message, 'success');
            // Reload page after 2 seconds
            setTimeout(() => {
                location.reload();
            }, 2000);
        } else {
            showToast(data.message, 'error');
        }
    })
    .catch(error => {
        showToast('Error cancelling order', 'error');
    });
}

// Get CSRF token
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
