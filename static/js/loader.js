// PAYANUM global button loader
(function () {
    // Inject overlay once
    const overlay = document.createElement('div');
    overlay.id = 'payanum-loader';
    overlay.innerHTML = '<div class="payanum-dots"><span></span><span></span><span></span></div>';
    document.body.appendChild(overlay);

    function showLoader() { overlay.classList.add('active'); }

    // Exclude: toggle-password, nav links, logout (instant redirect is fine),
    // dropdown toggles, close buttons, and driver-home JS-only buttons (accept/decline handled separately)
    const SKIP = ['btn-close', 'btn-refresh', 'dropdown-toggle', 'navbar-toggler'];

    document.addEventListener('click', function (e) {
        const btn = e.target.closest('button, a.btn, a.dropdown-item, input[type=submit], input[type=button]');
        if (!btn) return;

        // Skip if any exclusion class present
        if (SKIP.some(c => btn.classList.contains(c))) return;

        // Skip toggle-password, map, swap buttons
        if (btn.getAttribute('onclick') && (
            btn.getAttribute('onclick').includes('togglePassword') ||
            btn.getAttribute('onclick').includes('openFullscreenMap') ||
            btn.getAttribute('onclick').includes('swapLocations') ||
            btn.getAttribute('onclick').includes('locateMe') ||
            btn.getAttribute('onclick').includes('closeFullscreenMap') ||
            btn.getAttribute('onclick').includes('setLocationFromFullscreen') ||
            btn.getAttribute('onclick').includes('confirmFsLocation')
        )) return;

        // Skip anchor buttons that open modals or have no real navigation
        if (btn.getAttribute('data-bs-toggle')) return;

        // Skip pure JS onclick buttons that don't navigate (driver home accept/decline handled in their own flow)
        if (btn.type === 'button' && !btn.form && !btn.getAttribute('href')) return;

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
