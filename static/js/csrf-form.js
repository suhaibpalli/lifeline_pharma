// A login in another tab rotates Django's CSRF cookie. Keep an already-open
// form aligned with that current cookie without relaxing server validation.
(function () {
    function refresh(form) {
        if (!form || form.tagName !== 'FORM' || form.method.toLowerCase() !== 'post') return;
        if (new URL(form.action, window.location.href).origin !== window.location.origin) return;
        const input = form.querySelector('input[name="csrfmiddlewaretoken"]');
        // Match Django's last-value-wins cookie parser if a browser retains a
        // legacy cookie with the same name at another path/domain.
        const cookie = document.cookie.split(';').map(part => part.trim()).filter(part => part.startsWith('csrftoken=')).pop();
        if (input && cookie) input.value = decodeURIComponent(cookie.substring('csrftoken='.length));
    }
    function refreshAll() { document.querySelectorAll('form').forEach(refresh); }
    document.addEventListener('submit', event => refresh(event.target), true);
    window.addEventListener('pageshow', refreshAll);
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', refreshAll);
    else refreshAll();
}());
