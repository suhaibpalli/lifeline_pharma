document.addEventListener('DOMContentLoaded', function () {
    const checkoutForm = document.getElementById('checkout-form');
    const loadingOverlay = document.getElementById('loading-overlay');

    // Coupon logic
    const applyBtn = document.getElementById('apply-coupon');
    const removeBtn = document.getElementById('remove-coupon');
    const couponInput = document.getElementById('coupon-code');

    if (applyBtn) {
        applyBtn.addEventListener('click', async function () {
            const code = couponInput.value.trim();
            if (!code) return showCouponMsg('Enter a coupon code', 'error');
            const res = await fetch(window.APPLY_COUPON_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': window.CSRF_TOKEN },
                body: JSON.stringify({ coupon_code: code }),
            });
            const data = await res.json();
            if (data.success) {
                showCouponMsg(data.message, 'success');
                document.getElementById('discount-row').classList.remove('hidden');
                document.getElementById('discount-amount').textContent = '−₹' + data.discount.toFixed(2);
                document.getElementById('delivery-charge').textContent = data.delivery_charge > 0
                    ? '₹' + data.delivery_charge.toFixed(2) : 'FREE';
                document.getElementById('total-amount').textContent = '₹' + data.total.toFixed(2);
                document.getElementById('applied-coupon').classList.remove('hidden');
                document.getElementById('applied-coupon-code').textContent = code.toUpperCase();
            } else {
                showCouponMsg(data.message, 'error');
            }
        });
    }

    if (removeBtn) {
        removeBtn.addEventListener('click', async function () {
            const res = await fetch(window.REMOVE_COUPON_URL, {
                method: 'POST',
                headers: { 'X-CSRFToken': window.CSRF_TOKEN },
            });
            const data = await res.json();
            if (data.success) {
                document.getElementById('applied-coupon').classList.add('hidden');
                document.getElementById('discount-row').classList.add('hidden');
                document.getElementById('total-amount').textContent = '₹' + data.total.toFixed(2);
                document.getElementById('delivery-charge').textContent = data.delivery_charge > 0
                    ? '₹' + data.delivery_charge.toFixed(2) : 'FREE';
                couponInput.value = '';
                showCouponMsg('Coupon removed', 'info');
            }
        });
    }

    function showCouponMsg(msg, type) {
        const el = document.getElementById('coupon-message');
        el.textContent = msg;
        el.className = 'mt-2 text-sm ' + (type === 'success' ? 'text-green-600' : type === 'error' ? 'text-red-600' : 'text-gray-600');
        el.classList.remove('hidden');
    }

    // Form submission
    if (checkoutForm) {
        checkoutForm.addEventListener('submit', async function (e) {
            e.preventDefault();
            const paymentMethod = document.querySelector('input[name="payment_method"]:checked')?.value;

            if (paymentMethod === 'ONLINE') {
                await handleRazorpayPayment();
            } else {
                loadingOverlay.classList.remove('hidden');
                loadingOverlay.classList.add('flex');
                checkoutForm.submit();
            }
        });
    }

    // Razorpay flow
    async function handleRazorpayPayment() {
        loadingOverlay.classList.remove('hidden');
        loadingOverlay.classList.add('flex');

        const formData = new FormData(checkoutForm);

        try {
            const res = await fetch(window.INITIATE_URL, {
                method: 'POST',
                headers: { 'X-CSRFToken': window.CSRF_TOKEN },
                body: formData,
            });
            const data = await res.json();

            if (!data.success) {
                loadingOverlay.classList.add('hidden');
                loadingOverlay.classList.remove('flex');
                alert(data.message || 'Failed to initiate payment. Please try again.');
                return;
            }

            loadingOverlay.classList.add('hidden');
            loadingOverlay.classList.remove('flex');

            const options = {
                key: data.key_id,
                amount: data.amount,
                currency: data.currency,
                name: 'Lifeline Healthcare',
                description: 'Order Payment',
                order_id: data.razorpay_order_id,
                prefill: data.prefill,
                theme: { color: '#2563EB' },
                handler: async function (response) {
                    await verifyPayment(response, data.order_number);
                },
                modal: {
                    ondismiss: async function () {
                        await markFailed(data.order_number);
                        alert('Payment was cancelled. Your cart is unchanged, so you can retry checkout.');
                    },
                },
            };

            const rzp = new Razorpay(options);
            rzp.open();

        } catch (err) {
            loadingOverlay.classList.add('hidden');
            loadingOverlay.classList.remove('flex');
            alert('Network error. Please try again.');
        }
    }

    async function verifyPayment(response, orderNumber) {
        loadingOverlay.classList.remove('hidden');
        loadingOverlay.classList.add('flex');
        try {
            const res = await fetch(window.VERIFY_URL, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json', 'X-CSRFToken': window.CSRF_TOKEN },
                body: JSON.stringify({
                    razorpay_payment_id: response.razorpay_payment_id,
                    razorpay_order_id: response.razorpay_order_id,
                    razorpay_signature: response.razorpay_signature,
                    order_number: orderNumber,
                }),
            });
            const data = await res.json();
            if (data.success) {
                window.location.href = data.redirect_url;
            } else {
                loadingOverlay.classList.add('hidden');
                loadingOverlay.classList.remove('flex');
                alert(data.message || 'Payment verification failed.');
            }
        } catch (err) {
            loadingOverlay.classList.add('hidden');
            loadingOverlay.classList.remove('flex');
            alert('Verification error. Contact support with your payment ID.');
        }
    }

    async function markFailed(orderNumber) {
        await fetch(window.FAILED_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json', 'X-CSRFToken': window.CSRF_TOKEN },
            body: JSON.stringify({ order_number: orderNumber }),
        });
    }
});
