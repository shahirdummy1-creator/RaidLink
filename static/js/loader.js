// PAYANUM global button loader
(function () {
    // Inject overlay once
    const overlay = document.createElement('div');
    overlay.id = 'payanum-loader';
    overlay.innerHTML = '<div class="payanum-dots"><span></span><span></span><span></span></div>';
    document.body.appendChild(overlay);

    function showLoader() { overlay.classList.add('active'); }
    window.payanumShowLoader = showLoader;

    // Exclude: toggle-password, nav links, logout (instant redirect is fine),
    // dropdown toggles, close buttons, and driver-home JS-only buttons (accept/decline handled separately)
    const SKIP = ['btn-close', 'btn-refresh', 'dropdown-toggle', 'navbar-toggler'];

    document.addEventListener('click', function (e) {
        const btn = e.target.closest('button, a.btn, a.dropdown-item, .btn-cancel, input[type=submit], input[type=button]');
        if (!btn) return;

        // Skip if any exclusion class present
        if (SKIP.some(c => btn.classList.contains(c))) return;

        // Skip toggle-password, map, swap, and other pure-UI buttons
        if (btn.getAttribute('onclick') && (
            btn.getAttribute('onclick').includes('togglePassword') ||
            btn.getAttribute('onclick').includes('openFullscreenMap') ||
            btn.getAttribute('onclick').includes('swapLocations') ||
            btn.getAttribute('onclick').includes('locateMe') ||
            btn.getAttribute('onclick').includes('closeFullscreenMap') ||
            btn.getAttribute('onclick').includes('setLocationFromFullscreen') ||
            btn.getAttribute('onclick').includes('confirmFsLocation') ||
            btn.getAttribute('onclick').includes('togglePw') ||
            btn.getAttribute('onclick').includes('openCamera') ||
            btn.getAttribute('onclick').includes('stopCamera') ||
            btn.getAttribute('onclick').includes('capturePhoto') ||
            btn.getAttribute('onclick').includes('selectUserType') ||
            btn.getAttribute('onclick').includes('previewPhoto')
        )) return;

        // Skip anchor buttons that open modals or have no real navigation
        if (btn.getAttribute('data-bs-toggle')) return;

        // Skip type=button with no form and no href UNLESS it has a known action onclick
        if (btn.type === 'button' && !btn.form && !btn.getAttribute('href')) {
            const oc = btn.getAttribute('onclick') || '';
            // Allow accept/cancel booking actions
            if (!oc.includes('acceptBooking') && !oc.includes('cancelBooking') && !oc.includes('verifyOtp') && !oc.includes('verifyOTP') && !oc.includes('sendOtp') && !oc.includes('resendOtp') && !oc.includes('verifyOtp') && !oc.includes('confirmFareCollected')) return;
        }

        // For anchor buttons — only show loader if href is a real page (not # or javascript:)
        if (btn.tagName === 'A') {
            const href = btn.getAttribute('href') || '';
            if (!href || href === '#' || href.startsWith('javascript') || href.startsWith('tel:') || href.startsWith('https://wa.me')) return;
        }

        showLoader();
    }, true);

    // Hide loader when page becomes visible again (back navigation)
    document.addEventListener('visibilitychange', function () {
        if (document.visibilityState === 'visible') overlay.classList.remove('active');
    });

    // Hide on pageshow (bfcache restore on mobile)
    window.addEventListener('pageshow', function () { overlay.classList.remove('active'); });
})();
