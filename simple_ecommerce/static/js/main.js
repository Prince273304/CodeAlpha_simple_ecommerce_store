/**
 * NovaStore - Main Frontend JavaScript
 * Handles dynamic AJAX cart updates, toasts, and UI interactions
 */

document.addEventListener('DOMContentLoaded', () => {
    initAddToCartButtons();
    initDetailForm();
    initAlertAutoDismiss();
});

/**
 * Extract CSRF token from cookies
 */
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

/**
 * Show a floating toast notification
 */
function showToast(message) {
    const toastEl = document.getElementById('cartToast');
    const toastMsgEl = document.getElementById('toastMessage');
    if (toastEl && toastMsgEl) {
        toastMsgEl.textContent = message;
        const toast = new bootstrap.Toast(toastEl, { delay: 3500 });
        toast.show();
    }
}

/**
 * Update the navbar cart badge
 */
function updateCartBadge(count) {
    const badge = document.getElementById('cart-badge');
    if (badge) {
        badge.textContent = count;
        if (count > 0) {
            badge.classList.remove('d-none');
        } else {
            badge.classList.add('d-none');
        }
    }
}

/**
 * Attach AJAX handler to all "Add to Cart" buttons in catalog
 */
function initAddToCartButtons() {
    const buttons = document.querySelectorAll('.add-to-cart-btn');
    const csrftoken = getCookie('csrftoken');

    buttons.forEach(btn => {
        btn.addEventListener('click', async (e) => {
            e.preventDefault();
            const url = btn.getAttribute('data-url');
            const productName = btn.getAttribute('data-product-name');

            // Button loading feedback
            const originalContent = btn.innerHTML;
            btn.disabled = true;
            btn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Adding...`;

            try {
                const formData = new FormData();
                formData.append('quantity', '1');

                const response = await fetch(url, {
                    method: 'POST',
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': csrftoken || '',
                    },
                    body: formData
                });

                if (response.ok) {
                    const data = await response.json();
                    if (data.success) {
                        updateCartBadge(data.cart_count);
                        showToast(data.message || `Added "${productName}" to cart!`);
                    }
                } else {
                    // Fallback to traditional navigation if server requires standard redirect
                    window.location.href = url;
                }
            } catch (err) {
                console.warn('AJAX cart add failed, falling back to standard submit', err);
                window.location.href = url;
            } finally {
                btn.disabled = false;
                btn.innerHTML = originalContent;
            }
        });
    });
}

/**
 * Attach AJAX handler to the Product Detail "Add to Cart" form
 */
function initDetailForm() {
    const detailForm = document.getElementById('detail-cart-form');
    if (!detailForm) return;

    const csrftoken = getCookie('csrftoken');

    detailForm.addEventListener('submit', async (e) => {
        e.preventDefault();
        const submitBtn = detailForm.querySelector('button[type="submit"]');
        const qtyInput = document.getElementById('detail-quantity');
        const quantity = qtyInput ? qtyInput.value : 1;
        const originalContent = submitBtn.innerHTML;

        submitBtn.disabled = true;
        submitBtn.innerHTML = `<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Adding...`;

        try {
            const formData = new FormData(detailForm);
            const response = await fetch(detailForm.action, {
                method: 'POST',
                headers: {
                    'X-Requested-With': 'XMLHttpRequest',
                    'X-CSRFToken': csrftoken || '',
                },
                body: formData
            });

            if (response.ok) {
                const data = await response.json();
                if (data.success) {
                    updateCartBadge(data.cart_count);
                    showToast(data.message || `Added item to cart!`);
                }
            } else {
                detailForm.submit();
            }
        } catch (err) {
            detailForm.submit();
        } finally {
            submitBtn.disabled = false;
            submitBtn.innerHTML = originalContent;
        }
    });
}

/**
 * Auto-dismiss alerts after 5 seconds
 */
function initAlertAutoDismiss() {
    const alerts = document.querySelectorAll('.alert-dismissible');
    alerts.forEach(alert => {
        setTimeout(() => {
            const bsAlert = bootstrap.Alert.getInstance(alert);
            if (bsAlert) {
                bsAlert.close();
            }
        }, 5000);
    });
}
