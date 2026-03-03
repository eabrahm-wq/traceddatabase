/**
 * Traced — content.js
 * Detects product names on grocery sites, fetches Traced API, shows badges.
 */

const API_BASE = 'https://tracedhealth.com';  // change to http://127.0.0.1:5001 for local dev

// ── Site-specific product card selectors ────────────────────────
const SITE_CONFIG = {
  'instacart.com': {
    cards: '[data-testid="item-card"], .item-card, [class*="ProductCard"]',
    nameEl: '[data-testid="item-name"], .item-name, [class*="product-name"], h2, h3',
  },
  'amazon.com': {
    cards: '[data-asin]:not([data-asin=""]), .s-result-item, .octopus-pc-item, [data-component-type="s-search-result"]',
    nameEl: '.a-size-base-plus, .a-size-medium, [class*="product-title"], h2 a span',
  },
  'wholefoodsmarket.com': {
    cards: '[class*="product-tile"], [class*="ProductTile"], .w-pie-countable',
    nameEl: '[class*="product-name"], [class*="ProductName"], h2, h3',
  },
  'safeway.com': {
    cards: '[class*="product-card"], [class*="ProductCard"], .product-item',
    nameEl: '[class*="product-title"], [class*="ProductTitle"], a[class*="name"]',
  },
  'walmart.com': {
    cards: '[data-item-id], [class*="search-result-gridview-item"], [class*="Grid-module__sku"]',
    nameEl: '[class*="product-title"], [class*="ProductTitle"], span[class*="f6"]',
  },
  'target.com': {
    cards: '[data-test="product-grid-item"], [class*="ProductCardWrapper"], [class*="styles__CardWrapper"]',
    nameEl: '[data-test="product-title"], a[class*="productCardTitle"]',
  },
  'kroger.com': {
    cards: '[class*="ProductCard"], [class*="product-card"], article[class*="ProductCard"]',
    nameEl: '[class*="product-title"], [class*="ProductTitle"], p[class*="kds-Text"]',
  },
};

// ── Cache + inflight tracker ─────────────────────────────────────
const cache = {};
const inflight = new Set();

function getSiteConfig() {
  const host = window.location.hostname.replace('www.', '');
  for (const [domain, cfg] of Object.entries(SITE_CONFIG)) {
    if (host.includes(domain)) return cfg;
  }
  return null;
}

function extractBrandName(nameEl) {
  if (!nameEl) return null;
  const text = (nameEl.textContent || nameEl.innerText || '').trim();
  // Take first 1-3 words as likely brand name
  const words = text.split(/\s+/).slice(0, 3).join(' ');
  return words.length > 1 ? words : null;
}

function scoreColor(score) {
  if (score >= 70) return '#c44444';
  if (score >= 40) return '#d4952a';
  return '#3a8a5a';
}

function dotColor(score, independent) {
  if (independent && score < 20) return '#3a8a5a';  // green
  if (score >= 70) return '#c44444';                 // red
  if (score >= 40) return '#d4952a';                 // amber/yellow
  return '#3a8a5a';                                  // green
}

function createBadge(data) {
  const badge = document.createElement('div');
  badge.className = 'traced-badge';
  const col = dotColor(data.contradiction_score || 0, data.independent);
  badge.innerHTML = `<span class="traced-dot" style="background:${col}"></span>`;
  badge.dataset.tracedSlug = data.brand_id || '';
  badge.dataset.tracedData = JSON.stringify(data);
  badge.setAttribute('aria-label', `Traced: ${data.name}`);
  return badge;
}

function createCard(data) {
  const sc = data.contradiction_score || 0;
  const col = scoreColor(sc);
  const colDot = dotColor(sc, data.independent);
  const parent = data.parent_company || 'Independent';
  const slug = data.brand_id || (data.name || '').toLowerCase().replace(/[^a-z0-9]+/g, '-');

  const findings = [];
  if (data.acquired_year) findings.push(`Acquired by ${parent} in ${data.acquired_year}`);
  if (data.lobbying_issues && data.lobbying_issues.length > 0)
    findings.push(`${parent} lobbied on: ${data.lobbying_issues.slice(0, 2).join(', ')}`);
  else if (data.fines_total > 1e6)
    findings.push(`$${Math.round(data.fines_total / 1e6)}M in documented fines`);
  if (data.recall_count > 0) findings.push(`${data.recall_count} FDA recalls`);

  const findingsHtml = findings.slice(0, 2).map(f =>
    `<div class="traced-finding">• ${f}</div>`
  ).join('');

  const card = document.createElement('div');
  card.className = 'traced-card';
  card.innerHTML = `
    <div class="traced-card-header">
      <div>
        <div class="traced-card-brand">${data.name || 'Unknown'}</div>
        <div class="traced-card-owner" style="color:${parent === 'Independent' ? '#3a8a5a' : '#d4952a'}">
          ${parent === 'Independent' ? '✓ Independent' : `Owned by ${parent}`}
        </div>
      </div>
      <div class="traced-score-wrap">
        <div class="traced-score" style="color:${col}">${sc}</div>
        <div class="traced-score-label" style="color:${col}">${sc >= 70 ? 'HIGH' : sc >= 40 ? 'MOD' : 'LOW'}</div>
      </div>
    </div>
    <div class="traced-bar-bg">
      <div class="traced-bar" style="width:${sc}%;background:${col}"></div>
    </div>
    ${findingsHtml}
    <div class="traced-card-footer">
      <a href="https://tracedhealth.com/brand/${slug}" target="_blank" class="traced-view-btn">View full profile →</a>
      <button class="traced-share-btn" onclick="navigator.clipboard.writeText('https://tracedhealth.com/brand/${slug}').then(()=>{this.textContent='Copied!';setTimeout(()=>this.textContent='Share',1500)})">Share</button>
    </div>
  `;
  return card;
}

async function fetchBrand(name) {
  if (cache[name]) return cache[name];
  if (inflight.has(name)) return null;
  inflight.add(name);
  try {
    const res = await fetch(`${API_BASE}/api/brand/${encodeURIComponent(name)}`);
    if (!res.ok) { inflight.delete(name); return null; }
    const data = await res.json();
    cache[name] = data;
    inflight.delete(name);
    return data;
  } catch (e) {
    inflight.delete(name);
    return null;
  }
}

function procesCards(cfg) {
  const cards = document.querySelectorAll(cfg.cards);
  cards.forEach(card => {
    if (card.querySelector('.traced-badge')) return; // already processed
    const nameEl = card.querySelector(cfg.nameEl);
    const brandName = extractBrandName(nameEl);
    if (!brandName) return;

    card.style.position = 'relative';
    const placeholder = document.createElement('div');
    placeholder.className = 'traced-badge traced-badge-loading';
    placeholder.innerHTML = '<span class="traced-dot" style="background:#444;animation:traced-pulse 1.2s infinite"></span>';
    card.appendChild(placeholder);

    fetchBrand(brandName).then(data => {
      if (!data || data.error) {
        placeholder.remove();
        return;
      }
      const badge = createBadge(data);
      placeholder.replaceWith(badge);

      // Toggle card on badge click
      badge.addEventListener('click', e => {
        e.stopPropagation();
        const existing = card.querySelector('.traced-card');
        if (existing) { existing.remove(); return; }
        const infoCard = createCard(data);
        card.appendChild(infoCard);
      });
    });
  });
}

// ── Init ─────────────────────────────────────────────────────────
const cfg = getSiteConfig();
if (cfg) {
  // Run on load + observe DOM changes (infinite scroll, SPA navigation)
  procesCards(cfg);
  const observer = new MutationObserver(() => procesCards(cfg));
  observer.observe(document.body, { childList: true, subtree: true });
}

// Listen for popup search requests
chrome.runtime.onMessage.addListener((msg, _sender, sendResponse) => {
  if (msg.type === 'LOOKUP_BRAND') {
    fetchBrand(msg.name).then(data => sendResponse({ data }));
    return true; // keep channel open for async
  }
  if (msg.type === 'GET_PAGE_BRANDS') {
    const detected = Object.keys(cache).slice(0, 5);
    sendResponse({ brands: detected, cacheData: cache });
  }
});
