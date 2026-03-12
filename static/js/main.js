/* ── HomeMade Pickles & Snacks – main.js ── */

document.addEventListener('DOMContentLoaded', () => {

    /* ── Sticky Navbar ──────────────────────────────────────────── */
    const nav = document.getElementById('mainNav');
    window.addEventListener('scroll', () => {
        nav?.classList.toggle('scrolled', window.scrollY > 60);
    }, { passive: true });

    /* ── Mobile Hamburger ───────────────────────────────────────── */
    const hamburger = document.getElementById('hamburger');
    const navLinks = document.getElementById('navLinks');
    hamburger?.addEventListener('click', () => {
        navLinks?.classList.toggle('open');
        hamburger.classList.toggle('active');
    });

    /* ── Dropdown: close when clicking outside ──────────────────── */
    document.addEventListener('click', (e) => {
        if (!e.target.closest('.dropdown')) {
            document.querySelectorAll('.dropdown-menu').forEach(m => m.style.opacity = '');
        }
    });

    /* ── Cart Badge ─────────────────────────────────────────────── */
    function updateCartBadge() {
        fetch('/cart/count')
            .then(r => r.json())
            .then(data => {
                const badge = document.getElementById('cartBadge');
                if (badge) {
                    badge.textContent = data.count || 0;
                    badge.style.display = data.count > 0 ? 'flex' : 'none';
                }
            })
            .catch(() => { });
    }
    updateCartBadge();

    /* ── Flash auto-dismiss ─────────────────────────────────────── */
    document.querySelectorAll('.flash').forEach(el => {
        setTimeout(() => el.style.opacity = '0', 4000);
        setTimeout(() => el.remove(), 4500);
    });

    /* ── Add-to-cart button feedback ───────────────────────────── */
    document.querySelectorAll('.add-cart-form').forEach(form => {
        form.addEventListener('submit', function () {
            const btn = this.querySelector('.add-cart-btn');
            if (btn) {
                btn.innerHTML = '<i class="fa fa-check"></i> Added!';
                btn.disabled = true;
            }
        });
    });

    /* ── Scroll-reveal product cards ────────────────────────────── */
    const observer = new IntersectionObserver(entries => {
        entries.forEach(e => {
            if (e.isIntersecting) {
                e.target.classList.add('visible');
                observer.unobserve(e.target);
            }
        });
    }, { threshold: 0.1 });

    document.querySelectorAll('.product-card, .cat-card, .testimonial-card').forEach(el => {
        el.classList.add('reveal');
        observer.observe(el);
    });

});
