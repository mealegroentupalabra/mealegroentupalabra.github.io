/**
 * Me Alegro En Tu Palabra - Main JavaScript
 * Handles Theme Toggling, Mobile Nav, Sharing, Reading Progress, and Analytics
 */

(function () {
  'use strict';

  // --- Theme Management ---
  const THEME_KEY = 'maetp_theme';
  const htmlEl = document.documentElement;

  function initTheme() {
    const savedTheme = localStorage.getItem(THEME_KEY);
    if (savedTheme) {
      setTheme(savedTheme, false);
    } else {
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      setTheme(prefersDark ? 'dark' : 'light', false);
    }
  }

  function setTheme(theme, save = true) {
    htmlEl.setAttribute('data-theme', theme);
    if (save) {
      localStorage.setItem(THEME_KEY, theme);
      if (typeof gtag === 'function') {
        gtag('event', 'theme_change', { theme: theme });
      }
    }
    updateThemeIcon(theme);
  }

  function toggleTheme() {
    const current = htmlEl.getAttribute('data-theme') || 'light';
    const next = current === 'dark' ? 'light' : 'dark';
    setTheme(next);
  }

  function updateThemeIcon(theme) {
    const iconBtns = document.querySelectorAll('.theme-toggle-btn');
    iconBtns.forEach(btn => {
      if (theme === 'dark') {
        btn.innerHTML = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"></circle><line x1="12" y1="1" x2="12" y2="3"></line><line x1="12" y1="21" x2="12" y2="23"></line><line x1="4.22" y1="4.22" x2="5.64" y2="5.64"></line><line x1="18.36" y1="18.36" x2="19.78" y2="19.78"></line><line x1="1" y1="12" x2="3" y2="12"></line><line x1="21" y1="12" x2="23" y2="12"></line><line x1="4.22" y1="19.78" x2="5.64" y2="18.36"></line><line x1="18.36" y1="5.64" x2="19.78" y2="4.22"></line></svg>`;
        btn.setAttribute('aria-label', 'Cambiar a modo claro');
      } else {
        btn.innerHTML = `<svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M21 12.79A9 9 0 1 1 11.21 3 7 7 0 0 0 21 12.79z"></path></svg>`;
        btn.setAttribute('aria-label', 'Cambiar a modo oscuro');
      }
    });
  }

  // --- Mobile Navigation ---
  function initMobileMenu() {
    const toggleBtn = document.querySelector('.mobile-menu-toggle');
    const nav = document.querySelector('.site-nav');
    if (!toggleBtn || !nav) return;

    toggleBtn.addEventListener('click', () => {
      nav.classList.toggle('mobile-active');
      const isExpanded = nav.classList.contains('mobile-active');
      toggleBtn.setAttribute('aria-expanded', isExpanded);
      toggleBtn.innerHTML = isExpanded 
        ? `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`
        : `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>`;
    });

    // Close when clicking nav links on mobile
    nav.querySelectorAll('.nav-link').forEach(link => {
      link.addEventListener('click', () => {
        nav.classList.remove('mobile-active');
      });
    });
  }

  // --- Reading Progress Bar ---
  function initReadingProgress() {
    const bar = document.querySelector('.reading-progress');
    const content = document.querySelector('.post-content');
    if (!bar || !content) return;

    window.addEventListener('scroll', () => {
      const rect = content.getBoundingClientRect();
      const contentHeight = content.offsetHeight;
      const windowHeight = window.innerHeight;
      
      const scrollPos = -rect.top;
      const totalScroll = contentHeight - windowHeight + 100;
      
      if (scrollPos < 0) {
        bar.style.width = '0%';
      } else if (scrollPos > totalScroll) {
        bar.style.width = '100%';
      } else {
        const progress = Math.min(100, Math.max(0, (scrollPos / totalScroll) * 100));
        bar.style.width = `${progress}%`;
      }
    }, { passive: true });
  }

  // --- Toast Messages ---
  function showToast(message) {
    let toast = document.querySelector('.toast-msg');
    if (!toast) {
      toast = document.createElement('div');
      toast.className = 'toast-msg';
      document.body.appendChild(toast);
    }
    toast.textContent = message;
    toast.classList.add('show');
    setTimeout(() => {
      toast.classList.remove('show');
    }, 3000);
  }

  // --- Social Sharing ---
  function initShareButtons() {
    const shareContainer = document.querySelector('.share-bar');
    if (!shareContainer) return;

    const url = encodeURIComponent(window.location.href);
    const title = encodeURIComponent(document.title);

    // Native Web Share API if available
    const nativeBtn = shareContainer.querySelector('.share-btn.native');
    if (nativeBtn && navigator.share) {
      nativeBtn.style.display = 'inline-flex';
      nativeBtn.addEventListener('click', async () => {
        try {
          await navigator.share({ title: document.title, url: window.location.href });
          if (typeof gtag === 'function') gtag('event', 'share', { method: 'native' });
        } catch (e) {
          // Fallback or user canceled
        }
      });
    }

    // WhatsApp
    const waBtn = shareContainer.querySelector('.share-btn.whatsapp');
    if (waBtn) {
      waBtn.href = `https://api.whatsapp.com/send?text=${title}%20${url}`;
      waBtn.addEventListener('click', () => {
        if (typeof gtag === 'function') gtag('event', 'share', { method: 'whatsapp' });
      });
    }

    // Telegram
    const tgBtn = shareContainer.querySelector('.share-btn.telegram');
    if (tgBtn) {
      tgBtn.href = `https://t.me/share/url?url=${url}&text=${title}`;
      tgBtn.addEventListener('click', () => {
        if (typeof gtag === 'function') gtag('event', 'share', { method: 'telegram' });
      });
    }

    // Twitter / X
    const twBtn = shareContainer.querySelector('.share-btn.twitter');
    if (twBtn) {
      twBtn.href = `https://twitter.com/intent/tweet?text=${title}&url=${url}`;
      twBtn.addEventListener('click', () => {
        if (typeof gtag === 'function') gtag('event', 'share', { method: 'twitter' });
      });
    }

    // Facebook
    const fbBtn = shareContainer.querySelector('.share-btn.facebook');
    if (fbBtn) {
      fbBtn.href = `https://www.facebook.com/sharer/sharer.php?u=${url}`;
      fbBtn.addEventListener('click', () => {
        if (typeof gtag === 'function') gtag('event', 'share', { method: 'facebook' });
      });
    }

    // Copy Link
    const copyBtn = shareContainer.querySelector('.share-btn.copy');
    if (copyBtn) {
      copyBtn.addEventListener('click', async (e) => {
        e.preventDefault();
        try {
          await navigator.clipboard.writeText(window.location.href);
          showToast('✓ Enlace copiado al portapapeles');
          if (typeof gtag === 'function') gtag('event', 'share', { method: 'copy_link' });
        } catch (err) {
          showToast('No se pudo copiar el enlace');
        }
      });
    }
  }

  // --- Sorting Controls (Más recientes / Más antiguas con persistencia) ---
  const SORT_PREF_KEY = 'maetp_sort_order';

  function initSortControls() {
    const toggle = document.getElementById('sortToggle');
    if (!toggle) return;
    const grid = document.querySelector('.posts-grid');
    if (!grid) return;
    const cards = Array.from(grid.querySelectorAll('.post-card'));

    function applyOrder(order, save = false) {
      toggle.querySelectorAll('.sort-btn').forEach(b => {
        b.classList.toggle('active', b.getAttribute('data-order') === order);
      });
      cards.sort((a, b) => {
        const tA = parseInt(a.getAttribute('data-timestamp') || a.getAttribute('data-day') || '0', 10);
        const tB = parseInt(b.getAttribute('data-timestamp') || b.getAttribute('data-day') || '0', 10);
        return order === 'asc' ? (tA - tB) : (tB - tA);
      });
      cards.forEach(card => grid.appendChild(card));
      if (save) {
        try {
          localStorage.setItem(SORT_PREF_KEY, order);
        } catch (e) {}
      }
    }

    // Check saved preference or default to 'desc' (Más recientes)
    let savedOrder = 'desc';
    try {
      savedOrder = localStorage.getItem(SORT_PREF_KEY) || 'desc';
    } catch (e) {}

    // Apply saved preference if it's 'asc'
    if (savedOrder === 'asc') {
      applyOrder('asc', false);
    }

    toggle.querySelectorAll('.sort-btn').forEach(btn => {
      btn.addEventListener('click', () => {
        const order = btn.getAttribute('data-order');
        applyOrder(order, true);
      });
    });
  }

  // --- Global Event Attachments ---
  document.addEventListener('DOMContentLoaded', () => {
    initTheme();
    initMobileMenu();
    initReadingProgress();
    initShareButtons();
    initSortControls();

    document.querySelectorAll('.theme-toggle-btn').forEach(btn => {
      btn.addEventListener('click', toggleTheme);
    });
  });

  // Listen for OS theme changes
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
    if (!localStorage.getItem(THEME_KEY)) {
      setTheme(e.matches ? 'dark' : 'light', false);
    }
  });

  // Expose global helpers
  window.maetp = {
    showToast,
    toggleTheme
  };
})();
