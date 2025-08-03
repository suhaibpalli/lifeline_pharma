// Checkout functionality
document.addEventListener('DOMContentLoaded', function() {
    
    // Coupon functionality
    const applyCouponBtn = document.getElementById('apply-coupon');
    const removeCouponBtn = document.getElementById('remove-coupon');
    const couponCodeInput = document.getElementById('coupon-code');
    
    if (applyCouponBtn) {
        applyCouponBtn.addEventListener('click', applyCoupon);
    }
    
    if (removeCouponBtn) {
        removeCouponBtn.addEventListener('click', removeCoupon);
    }
    
    // Form submission
    const checkoutForm = document.getElementById('checkout-form');
    if (checkoutForm) {
        checkoutForm.addEventListener('submit', function(e) {
            if (!validateCheckoutForm()) {
                e.preventDefault();
            } else {
                showLoading();
            }
        });
    }
});

// Apply coupon
function applyCoupon() {
    const couponCode = document.getElementById('coupon-code').value.trim();
    
    if (!couponCode) {
        showCouponMessage('Please enter a coupon code', 'error');
        return;
    }
    
    fetch('/orders/apply-coupon/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
        body: JSON.stringify({
            coupon_code: couponCode
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showCouponMessage(data.message, 'success');
            updatePricing(data);
            showAppliedCoupon(couponCode);
        } else {
            showCouponMessage(data.message, 'error');
        }
    })
    .catch(error => {
        showCouponMessage('Error applying coupon', 'error');
    });
}

// Remove coupon
function removeCoupon() {
    fetch('/orders/remove-coupon/', {
        method: 'POST',
        headers: {
            'X-CSRFToken': getCookie('csrftoken')
        }
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            showCouponMessage(data.message, 'success');
            updatePricing(data);
            hideAppliedCoupon();
        }
    })
    .catch(error => {
        showCouponMessage('Error removing coupon', 'error');
    });
}

// Update pricing display
function updatePricing(data) {
    const deliveryCharge = document.getElementById('delivery-charge');
    const discountRow = document.getElementById('discount-row');
    const discountAmount = document.getElementById('discount-amount');
    const totalAmount = document.getElementById('total-amount');
    
    if (deliveryCharge) {
        deliveryCharge.textContent = data.delivery_charge > 0 ? `₹${data.delivery_charge}` : 'FREE';
    }
    
    if (data.discount > 0) {
        discountRow.classList.remove('hidden');
        discountAmount.textContent = `-₹${data.discount}`;
    } else {
        discountRow.classList.add('hidden');
    }
    
    if (totalAmount) {
        totalAmount.textContent = `₹${data.total}`;
    }
}

// Show coupon message
function showCouponMessage(message, type) {
    const messageDiv = document.getElementById('coupon-message');
    messageDiv.textContent = message;
    messageDiv.className = `mt-2 text-sm ${type === 'success' ? 'text-green-600' : 'text-red-600'}`;
    messageDiv.classList.remove('hidden');
    
    setTimeout(() => {
        messageDiv.classList.add('hidden');
    }, 5000);
}

// Show applied coupon
function showAppliedCoupon(code) {
    const appliedCouponDiv = document.getElementById('applied-coupon');
    const appliedCouponCode = document.getElementById('applied-coupon-code');
    const couponCodeInput = document.getElementById('coupon-code');
    
    appliedCouponCode.textContent = code;
    appliedCouponDiv.classList.remove('hidden');
    couponCodeInput.value = '';
}

// Hide applied coupon
function hideAppliedCoupon() {
    const appliedCouponDiv = document.getElementById('applied-coupon');
    appliedCouponDiv.classList.add('hidden');
}

// Validate checkout form
function validateCheckoutForm() {
    const addressSelected = document.querySelector('input[name="address"]:checked');
    const paymentMethodSelected = document.querySelector('input[name="payment_method"]:checked');
    
    if (!addressSelected) {
        showToast('Please select a delivery address', 'error');
        return false;
    }
    
    if (!paymentMethodSelected) {
        showToast('Please select a payment method', 'error');
        return false;
    }
    
    return true;
}

// Show loading overlay
function showLoading() {
    const overlay = document.getElementById('loading-overlay');
    if (overlay) {
        overlay.classList.remove('hidden');
        overlay.classList.add('flex');
    }
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
