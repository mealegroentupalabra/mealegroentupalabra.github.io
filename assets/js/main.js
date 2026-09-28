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

    function openMenu() {
      nav.classList.add('mobile-active');
      toggleBtn.setAttribute('aria-expanded', 'true');
      toggleBtn.setAttribute('aria-label', 'Cerrar menú');
      toggleBtn.innerHTML = `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="18" y1="6" x2="6" y2="18"></line><line x1="6" y1="6" x2="18" y2="18"></line></svg>`;
      document.body.style.overflow = 'hidden';
    }

    function closeMenu() {
      nav.classList.remove('mobile-active');
      toggleBtn.setAttribute('aria-expanded', 'false');
      toggleBtn.setAttribute('aria-label', 'Abrir menú');
      toggleBtn.innerHTML = `<svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><line x1="3" y1="12" x2="21" y2="12"></line><line x1="3" y1="6" x2="21" y2="6"></line><line x1="3" y1="18" x2="21" y2="18"></line></svg>`;
      document.body.style.overflow = '';
    }

    toggleBtn.addEventListener('click', (e) => {
      e.stopPropagation();
      if (nav.classList.contains('mobile-active')) {
        closeMenu();
      } else {
        openMenu();
      }
    });

    // Close when clicking nav links on mobile
    nav.querySelectorAll('.nav-link').forEach(link => {
      link.addEventListener('click', () => {
        closeMenu();
      });
    });

    // Close on click outside
    document.addEventListener('click', (e) => {
      if (nav.classList.contains('mobile-active') && !nav.contains(e.target) && !toggleBtn.contains(e.target)) {
        closeMenu();
      }
    });

    // Close on Escape key
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && nav.classList.contains('mobile-active')) {
        closeMenu();
      }
    });

    // Reset if window is resized to desktop width
    window.addEventListener('resize', () => {
      if (window.innerWidth > 1040 && nav.classList.contains('mobile-active')) {
        closeMenu();
      }
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

  // --- Progressive Scroll Loading for Large Card Grids & Sorting ---
  const SORT_PREF_KEY = 'maetp_sort_order';

  function initProgressiveGrid() {
    const grid = document.querySelector('.posts-grid');
    if (!grid) return;

    let cards = Array.from(grid.querySelectorAll('.post-card'));
    if (!cards.length) return;

    const toggle = document.getElementById('sortToggle');
    const CHUNK_SIZE = 18;

    let observer = null;
    let currentCount = 0;
    let sortedCards = [...cards];

    let statusContainer = document.querySelector('.grid-scroll-status');
    if (!statusContainer && cards.length > CHUNK_SIZE) {
      statusContainer = document.createElement('div');
      statusContainer.className = 'grid-scroll-status';
      grid.parentNode.insertBefore(statusContainer, grid.nextSibling);
    }

    function renderNextChunk() {
      if (currentCount >= sortedCards.length) {
        showFinished();
        return;
      }
      const nextBatch = sortedCards.slice(currentCount, currentCount + CHUNK_SIZE);
      nextBatch.forEach(c => {
        c.removeAttribute('data-staged');
        c.classList.add('card-revealing');
      });
      currentCount += nextBatch.length;

      if (currentCount >= sortedCards.length) {
        showFinished();
      }
    }

    function showFinished() {
      if (observer) {
        observer.disconnect();
        observer = null;
      }
      if (statusContainer) {
        statusContainer.innerHTML = `<div class="grid-end-indicator">Mostrando todas las ${sortedCards.length} publicaciones</div>`;
      }
    }

    function applyOrderAndRefresh(order, save = false) {
      if (toggle) {
        toggle.querySelectorAll('.sort-btn').forEach(b => {
          b.classList.toggle('active', b.getAttribute('data-order') === order);
        });
      }

      sortedCards.sort((a, b) => {
        const tA = parseInt(a.getAttribute('data-timestamp') || a.getAttribute('data-day') || '0', 10);
        const tB = parseInt(b.getAttribute('data-timestamp') || b.getAttribute('data-day') || '0', 10);
        return order === 'asc' ? (tA - tB) : (tB - tA);
      });

      if (sortedCards.length > CHUNK_SIZE) {
        currentCount = 0;
        sortedCards.forEach((c, idx) => {
          if (idx < CHUNK_SIZE) {
            c.removeAttribute('data-staged');
          } else {
            c.setAttribute('data-staged', 'true');
          }
          c.classList.remove('card-revealing');
          grid.appendChild(c);
        });
        currentCount = Math.min(CHUNK_SIZE, sortedCards.length);

        if (statusContainer) {
          statusContainer.innerHTML = `
            <div class="grid-scroll-loader">
              <span class="spinner-dots"><span></span><span></span><span></span></span>
              <span>Cargando más publicaciones...</span>
            </div>
          `;
        }

        if (observer) observer.disconnect();
        if ('IntersectionObserver' in window && statusContainer) {
          observer = new IntersectionObserver((entries) => {
            if (entries[0].isIntersecting) {
              renderNextChunk();
            }
          }, { rootMargin: '450px 0px', threshold: 0.01 });
          observer.observe(statusContainer);
        } else {
          sortedCards.forEach(c => c.removeAttribute('data-staged'));
          showFinished();
        }
      } else {
        // Less than CHUNK_SIZE (e.g. index pagination)
        sortedCards.forEach(card => grid.appendChild(card));
      }

      if (save) {
        try {
          localStorage.setItem(SORT_PREF_KEY, order);
        } catch (e) {}
      }
    }

    // Read stored preference
    let savedOrder = 'desc';
    try {
      savedOrder = localStorage.getItem(SORT_PREF_KEY) || 'desc';
    } catch (e) {}

    applyOrderAndRefresh(savedOrder, false);

    if (toggle) {
      toggle.querySelectorAll('.sort-btn').forEach(btn => {
        btn.addEventListener('click', () => {
          const order = btn.getAttribute('data-order');
          applyOrderAndRefresh(order, true);
        });
      });
    }
  }

  // --- Pull Quotes Social Sharing ---
  function initPullQuoteSharing(root = document) {
    const quotes = root.querySelectorAll('.with-share, [data-share="true"]');
    if (!quotes.length) return;

    const pageUrl = window.location.href;
    const pageTitle = (typeof postTitle !== 'undefined' && postTitle && postTitle.value && postTitle.value.trim())
      || (document.title ? document.title.split('—')[0].trim() : 'Me Alegro En Tu Palabra');

    quotes.forEach(quoteEl => {
      if (quoteEl.querySelector('.quote-share-bar')) return;

      const citeEl = quoteEl.querySelector('cite, .pull-quote-cite, .scripture-cite');
      const citeText = citeEl ? citeEl.textContent.trim() : '';

      // Get text excluding cite and existing bars
      let clone = quoteEl.cloneNode(true);
      let cloneCite = clone.querySelector('cite, .pull-quote-cite, .scripture-cite');
      if (cloneCite) cloneCite.remove();
      let cloneBar = clone.querySelector('.quote-share-bar');
      if (cloneBar) cloneBar.remove();

      let rawText = (clone.textContent || '').trim().replace(/^«|»$/g, '').trim();
      if (!rawText) return;

      // Friendly formatted text for social sharing
      const quoteWithCite = citeText ? `«${rawText}» (${citeText})` : `«${rawText}»`;

      // Build sharing URLs
      const encodedUrl = encodeURIComponent(pageUrl);
      const waUrl = `https://api.whatsapp.com/send?text=${encodeURIComponent(quoteWithCite + '\n\n' + pageUrl)}`;
      const twUrl = `https://twitter.com/intent/tweet?text=${encodeURIComponent(quoteWithCite)}&url=${encodedUrl}`;
      const fbUrl = `https://www.facebook.com/sharer/sharer.php?u=${encodedUrl}&quote=${encodeURIComponent(quoteWithCite)}`;

      const bar = document.createElement('div');
      bar.className = 'quote-share-bar';
      bar.innerHTML = `
        <span class="quote-share-label">Compartir</span>
        <div class="quote-share-actions">
          <a href="${twUrl}" target="_blank" rel="noopener nofollow" class="quote-share-btn twitter" title="Compartir en X / Twitter" aria-label="Compartir en X">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="currentColor"><path d="M18.244 2.25h3.308l-7.227 8.26 8.502 11.24H16.17l-5.214-6.817L4.99 21.75H1.68l7.73-8.835L1.254 2.25H8.08l4.713 6.231zm-1.161 17.52h1.833L7.084 4.126H5.117z"/></svg>
          </a>
          <a href="${waUrl}" target="_blank" rel="noopener nofollow" class="quote-share-btn whatsapp" title="Compartir en WhatsApp" aria-label="Compartir en WhatsApp">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M17.472 14.382c-.301-.15-1.78-.879-2.056-.98-.276-.1-.477-.15-.678.15-.2.301-.778.98-.954 1.18-.175.201-.351.226-.652.075-.301-.15-1.272-.469-2.423-1.496-.896-.799-1.501-1.786-1.677-2.087-.175-.301-.019-.464.132-.614.136-.135.301-.351.452-.527.15-.175.201-.3.301-.5.101-.201.05-.376-.025-.526-.075-.15-.678-1.631-.929-2.233-.244-.586-.492-.507-.678-.516-.176-.008-.376-.01-.577-.01s-.527.075-.803.376c-.276.301-1.054 1.029-1.054 2.508 0 1.479 1.079 2.908 1.229 3.109.15.201 2.124 3.243 5.145 4.549.718.311 1.279.497 1.716.636.721.23 1.377.197 1.895.12.577-.086 1.78-.727 2.031-1.429.251-.702.251-1.304.176-1.429-.076-.125-.276-.201-.577-.351zM12 2C6.477 2 2 6.477 2 12c0 1.891.524 3.662 1.435 5.176L2 22l4.981-1.396A9.957 9.957 0 0 0 12 22c5.523 0 10-4.477 10-10S17.523 2 12 2z"/></svg>
          </a>
          <a href="${fbUrl}" target="_blank" rel="noopener nofollow" class="quote-share-btn facebook" title="Compartir en Facebook" aria-label="Compartir en Facebook">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.5 2 2 6.5 2 12c0 5 3.7 9.1 8.4 9.9v-7H7.9V12h2.5V9.8c0-2.5 1.5-3.9 3.8-3.9 1.1 0 2.2.2 2.2.2v2.5h-1.3c-1.2 0-1.6.8-1.6 1.6V12h2.8l-.4 2.9h-2.3v7C18.3 21.1 22 17 22 12c0-5.5-4.5-10-10-10z"/></svg>
          </a>
          <button type="button" class="quote-share-btn copy" title="Copiar cita en formato amigable" aria-label="Copiar cita">
            <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>
          </button>
        </div>
      `;

      const copyBtn = bar.querySelector('.quote-share-btn.copy');
      if (copyBtn) {
        copyBtn.addEventListener('click', async (e) => {
          e.preventDefault();
          const copyText = `${quoteWithCite}\n\n${pageTitle}\n${pageUrl}`;
          try {
            await navigator.clipboard.writeText(copyText);
            copyBtn.classList.add('copied');
            copyBtn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><polyline points="20 6 9 17 4 12"></polyline></svg>`;
            showToast('✓ Cita copiada en formato amigable');
            setTimeout(() => {
              copyBtn.classList.remove('copied');
              copyBtn.innerHTML = `<svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect><path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path></svg>`;
            }, 2500);
            if (typeof gtag === 'function') gtag('event', 'share', { method: 'copy_quote' });
          } catch (err) {
            showToast('No se pudo copiar');
          }
        });
      }

      quoteEl.appendChild(bar);
    });
  }

  // --- Global Event Attachments ---
  function initAll() {
    initTheme();
    initMobileMenu();
    initReadingProgress();
    initShareButtons();
    initProgressiveGrid();
    initPullQuoteSharing();

    document.querySelectorAll('.theme-toggle-btn').forEach(btn => {
      btn.addEventListener('click', toggleTheme);
    });
  }

  if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', initAll);
  } else {
    initAll();
  }

  // Listen for OS theme changes
  window.matchMedia('(prefers-color-scheme: dark)').addEventListener('change', e => {
    if (!localStorage.getItem(THEME_KEY)) {
      setTheme(e.matches ? 'dark' : 'light', false);
    }
  });

  // Expose global helpers
  window.maetp = {
    showToast,
    toggleTheme,
    initPullQuoteSharing
  };
})();
