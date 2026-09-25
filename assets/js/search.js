/**
 * Me Alegro En Tu Palabra - Search Engine
 * Real-time fast search indexing titles, content, categories, and tags.
 */

(function () {
  'use strict';

  let searchIndex = [];
  let isIndexLoaded = false;
  let isLoading = false;
  let activeCategoryFilter = null;
  let activeTagFilter = null;
  let basePath = '';

  // Normalize string: lowercases and strips diacritics / accents
  function normalizeText(str) {
    if (!str) return '';
    return str
      .toLowerCase()
      .normalize('NFD')
      .replace(/[\u0300-\u036f]/g, '')
      .trim();
  }

  // Detect base path from meta or root
  function getBasePath() {
    const metaBase = document.querySelector('meta[name="base-path"]');
    if (metaBase) return metaBase.getAttribute('content') || '';
    return '';
  }

  async function loadSearchIndex() {
    if (isIndexLoaded || isLoading) return searchIndex;
    isLoading = true;
    basePath = getBasePath();
    const indexUrl = `${basePath}/search.json`.replace('//', '/');

    try {
      const resp = await fetch(indexUrl);
      if (!resp.ok) throw new Error(`HTTP error ${resp.status}`);
      searchIndex = await resp.json();
      isIndexLoaded = true;
    } catch (err) {
      console.error('Failed to load search index:', err);
    } finally {
      isLoading = false;
    }
    return searchIndex;
  }

  function highlightMatches(text, query) {
    if (!text || !query) return text || '';
    const cleanQuery = query.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
    try {
      const regex = new RegExp(`(${cleanQuery})`, 'gi');
      return text.replace(regex, '<mark class="highlight-match">$1</mark>');
    } catch (e) {
      return text;
    }
  }

  function search(query, categoryFilter = null, tagFilter = null) {
    if (!searchIndex || searchIndex.length === 0) return [];

    const normQuery = normalizeText(query);
    const queryTokens = normQuery.split(/\s+/).filter(t => t.length > 0);

    const normCat = categoryFilter ? normalizeText(categoryFilter) : null;
    const normTag = tagFilter ? normalizeText(tagFilter) : null;

    const results = [];

    for (const post of searchIndex) {
      const postCatNorm = normalizeText(post.category || '');
      const postCatsNorm = (post.categories || [post.category || '']).map(c => normalizeText(c));
      const postTagsNorm = (post.tags || []).map(t => normalizeText(t));

      // Category filter check
      if (normCat && normCat !== 'todos' && normCat !== 'all') {
        const matchesCat = postCatsNorm.includes(normCat) || postCatNorm === normCat;
        if (!matchesCat) {
          continue;
        }
      }

      // Tag filter check
      if (normTag && !postTagsNorm.includes(normTag)) {
        continue;
      }

      // If no text query, filter by category/tag alone
      if (queryTokens.length === 0) {
        if (normCat || normTag) {
          results.push({ post, score: 1, matchedIn: ['Filtro'] });
        }
        continue;
      }

      const postTitleNorm = normalizeText(post.title || '');
      const postSummaryNorm = normalizeText(post.summary || '');
      const postContentNorm = normalizeText(post.content || '');

      let score = 0;
      const matchedIn = [];

      for (const token of queryTokens) {
        let tokenMatched = false;

        // Title match
        if (postTitleNorm.includes(token)) {
          score += 15;
          tokenMatched = true;
          if (!matchedIn.includes('Título')) matchedIn.push('Título');
        }

        // Category match
        if (postCatsNorm.some(c => c.includes(token)) || postCatNorm.includes(token)) {
          score += 10;
          tokenMatched = true;
          if (!matchedIn.includes('Categoría')) matchedIn.push('Categoría');
        }

        // Tags match
        if (postTagsNorm.some(t => t.includes(token))) {
          score += 8;
          tokenMatched = true;
          if (!matchedIn.includes('Etiqueta')) matchedIn.push('Etiqueta');
        }

        // Summary match
        if (postSummaryNorm.includes(token)) {
          score += 5;
          tokenMatched = true;
          if (!matchedIn.includes('Resumen')) matchedIn.push('Resumen');
        }

        // Content match
        if (postContentNorm.includes(token)) {
          score += 2;
          tokenMatched = true;
          if (!matchedIn.includes('Contenido')) matchedIn.push('Contenido');
        }

        if (!tokenMatched) {
          score = 0;
          break; // all tokens must match somewhere
        }
      }

      if (score > 0) {
        results.push({ post, score, matchedIn });
      }
    }

    // Sort by relevance score descending, then by date descending
    results.sort((a, b) => {
      if (b.score !== a.score) return b.score - a.score;
      return new Date(b.post.date) - new Date(a.post.date);
    });

    return results;
  }

  // --- Render Results ---
  function renderResults(container, results, query) {
    if (!container) return;

    if (results.length === 0) {
      container.innerHTML = `
        <div style="padding: 2.5rem 1rem; text-align: center; color: var(--text-muted);">
          <svg style="margin: 0 auto 0.75rem; color: var(--text-light);" width="36" height="36" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5"><circle cx="11" cy="11" r="8"></circle><line x1="21" y1="21" x2="16.65" y2="16.65"></line></svg>
          <p style="font-weight: 600; font-size: 1.05rem; margin-bottom: 0.35rem;">No se encontraron artículos</p>
          <p style="font-size: 0.88rem;">Prueba buscando por otra palabra clave, autor o revisa las etiquetas sugeridas.</p>
        </div>
      `;
      return;
    }

    const html = results.map(item => {
      const p = item.post;
      const titleHighlighted = query ? highlightMatches(p.title, query) : p.title;
      const excerptHighlighted = query ? highlightMatches(p.summary, query) : p.summary;
      const matchPill = item.matchedIn && item.matchedIn.length > 0 && query
        ? `<span style="font-size: 0.7rem; background: var(--gold-bg); color: var(--gold); border: 1px solid var(--gold-border); padding: 1px 6px; border-radius: 4px;">Coincidencia en: ${item.matchedIn.join(', ')}</span>`
        : '';

      return `
        <a href="${p.url}" class="search-result-item">
          <div class="result-title">${titleHighlighted}</div>
          <div class="result-excerpt">${excerptHighlighted}</div>
          <div class="result-meta">
            <span style="font-weight: 600; color: var(--primary);">${p.category}</span>
            <span>•</span>
            <span>${p.date_formatted}</span>
            <span>•</span>
            <span>${p.reading_time || '3 min'}</span>
            ${matchPill ? `<span>•</span> ${matchPill}` : ''}
          </div>
        </a>
      `;
    }).join('');

    container.innerHTML = html;
  }

  // --- Search Modal Controller ---
  function initSearchModal() {
    const modal = document.querySelector('.search-modal');
    if (!modal) return;

    const input = modal.querySelector('.search-input');
    const resultsContainer = modal.querySelector('.search-results-list');
    const closeBtn = modal.querySelector('.search-close-btn');
    const categoryChips = modal.querySelectorAll('.filter-chip');

    let debounceTimer;

    function openModal() {
      modal.classList.add('active');
      document.body.style.overflow = 'hidden';
      loadSearchIndex();
      setTimeout(() => input && input.focus(), 100);
    }

    function closeModal() {
      modal.classList.remove('active');
      document.body.style.overflow = '';
      if (input) input.value = '';
      activeCategoryFilter = null;
      categoryChips.forEach(c => c.classList.remove('active'));
      const allChip = modal.querySelector('.filter-chip[data-cat="all"]');
      if (allChip) allChip.classList.add('active');
      if (resultsContainer) resultsContainer.innerHTML = '';
    }

    // Triggers
    document.querySelectorAll('.search-trigger').forEach(trigger => {
      trigger.addEventListener('click', (e) => {
        e.preventDefault();
        openModal();
      });
    });

    if (closeBtn) closeBtn.addEventListener('click', closeModal);

    modal.addEventListener('click', (e) => {
      if (e.target === modal) closeModal();
    });

    // Keyboard Shortcuts
    document.addEventListener('keydown', (e) => {
      // Cmd+K or Ctrl+K or /
      if ((e.metaKey || e.ctrlKey) && e.key.toLowerCase() === 'k') {
        e.preventDefault();
        if (modal.classList.contains('active')) closeModal();
        else openModal();
      } else if (e.key === 'Escape' && modal.classList.contains('active')) {
        closeModal();
      }
    });

    // Input Search with Debounce
    function executeSearch() {
      const q = input.value.trim();
      const results = search(q, activeCategoryFilter, activeTagFilter);
      renderResults(resultsContainer, results, q);

      if (q && typeof gtag === 'function') {
        gtag('event', 'search', { search_term: q });
      }
    }

    if (input) {
      input.addEventListener('input', () => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(executeSearch, 150);
      });
    }

    // Category filter chips
    categoryChips.forEach(chip => {
      chip.addEventListener('click', () => {
        categoryChips.forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        const cat = chip.getAttribute('data-cat');
        activeCategoryFilter = cat === 'all' ? null : cat;
        executeSearch();
      });
    });
  }

  // --- Dedicated Search Page Controller (/buscar/) ---
  function initSearchPage() {
    const pageContainer = document.querySelector('.search-page-container');
    if (!pageContainer) return;

    loadSearchIndex().then(() => {
      const input = pageContainer.querySelector('.page-search-input');
      const resultsContainer = pageContainer.querySelector('.page-search-results');
      const counterEl = pageContainer.querySelector('.search-counter');
      const categoryChips = pageContainer.querySelectorAll('.filter-chip');
      const tagChips = pageContainer.querySelectorAll('.tag-filter-chip');

      const urlParams = new URLSearchParams(window.location.search);
      const initialQuery = urlParams.get('q') || '';
      const initialCat = urlParams.get('categoria') || null;
      const initialTag = urlParams.get('etiqueta') || null;

      if (initialCat) activeCategoryFilter = initialCat;
      if (initialTag) activeTagFilter = initialTag;
      if (input && initialQuery) input.value = initialQuery;

      function runSearch() {
        const q = input ? input.value.trim() : '';
        const results = search(q, activeCategoryFilter, activeTagFilter);
        renderResults(resultsContainer, results, q);

        if (counterEl) {
          if (q || activeCategoryFilter || activeTagFilter) {
            counterEl.textContent = `Mostrando ${results.length} ${results.length === 1 ? 'artículo' : 'artículos'}`;
          } else {
            counterEl.textContent = `Total: ${searchIndex.length} artículos disponibles`;
          }
        }
      }

      if (input) {
        let timer;
        input.addEventListener('input', () => {
          clearTimeout(timer);
          timer = setTimeout(runSearch, 150);
        });
      }

      categoryChips.forEach(chip => {
        if (chip.getAttribute('data-cat') === activeCategoryFilter) {
          chip.classList.add('active');
        }
        chip.addEventListener('click', () => {
          categoryChips.forEach(c => c.classList.remove('active'));
          const cat = chip.getAttribute('data-cat');
          if (activeCategoryFilter === cat && cat !== 'all') {
            activeCategoryFilter = null;
          } else {
            chip.classList.add('active');
            activeCategoryFilter = cat === 'all' ? null : cat;
          }
          runSearch();
        });
      });

      tagChips.forEach(chip => {
        if (chip.getAttribute('data-tag') === activeTagFilter) {
          chip.classList.add('active');
        }
        chip.addEventListener('click', () => {
          const tag = chip.getAttribute('data-tag');
          if (activeTagFilter === tag) {
            activeTagFilter = null;
            chip.classList.remove('active');
          } else {
            tagChips.forEach(t => t.classList.remove('active'));
            chip.classList.add('active');
            activeTagFilter = tag;
          }
          runSearch();
        });
      });

      // Run initial search
      runSearch();
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    initSearchModal();
    initSearchPage();
  });

  window.maetpSearch = {
    load: loadSearchIndex,
    search: search
  };
})();
