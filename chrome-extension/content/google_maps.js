// TRACED Maps v5 — full profile panels with parent record, ingredient drift, founder story

(function() {
  'use strict';
  const TRACED_URL = 'https://tracedhealth.com';
  const API_BASE = 'http://localhost:5001/api';
  const cache = {};
  const injected = new Set();
  let debounceTimer = null;
  let lastInjectedName = null;

  const IGNORE_PATTERNS = /^(fillmore|market|mission|castro|haight|divisadero|valencia|geary|post|bush|pine|california|broadway|union|chestnut|lombard|columbus|north beach|the embarcadero|financial district|soma|nopa|richmond|sunset|st|ave|blvd|dr|rd|way|place|court|lane)\b/i;

  const TYPES = {
    conglomerate: { label: "Conglomerate",  color: "#d4a84b", bg: "rgba(212,168,75,0.12)"  },
    public:       { label: "Public Co.",    color: "#c8943a", bg: "rgba(200,148,58,0.12)"  },
    pe:           { label: "PE-Backed",     color: "#c94d3c", bg: "rgba(201,77,60,0.12)"   },
    private:      { label: "Corp-Owned",    color: "#d47a3c", bg: "rgba(212,122,60,0.12)"  },
    independent:  { label: "Independent",   color: "#4e9b6f", bg: "rgba(78,155,111,0.12)"  },
    unknown:      { label: "Unknown",       color: "#6b7280", bg: "rgba(107,114,128,0.12)" },
  };

  function getType(brand) {
    if (!brand) return TYPES.unknown;
    if (brand.independent) return TYPES.independent;
    if (brand.pe_owned) return TYPES.pe;
    if (brand.owner_type === 'conglomerate') return TYPES.conglomerate;
    if (brand.owner_type === 'public' || brand.owner_type === 'public_company') return TYPES.public;
    if (brand.owner) return TYPES.private;
    return TYPES.unknown;
  }

  function fmtLobbying(n) {
    if (!n) return null;
    return n >= 1000000 ? `$${(n/1000000).toFixed(1)}M/yr` : `$${(n/1000).toFixed(0)}K/yr`;
  }

  async function lookup(name) {
    const key = name.toLowerCase().trim();
    if (key in cache) return cache[key];
    try {
      const res = await fetch(`${API_BASE}/lookup?name=${encodeURIComponent(name)}&surface=google_maps&v=3`);
      const data = await res.json();
      cache[key] = data.matched ? data : null;
    } catch(e) { cache[key] = null; }
    return cache[key];
  }

  async function fetchNearby(category, priceTier, format) {
    if (!category) return [];
    try {
      const tierParam = priceTier ? `&price_tier=${priceTier}` : '';
      const fmtParam = format ? `&format=${encodeURIComponent(format)}` : '';
      const res = await fetch(`${API_BASE}/nearby?category=${encodeURIComponent(category)}&limit=2${tierParam}${fmtParam}`);
      const data = await res.json();
      return data.nearby || [];
    } catch(e) { return []; }
  }

  async function createDetailCard(result, rawName) {
    const brand = result.brand;
    const t = getType(brand);
    const slug = brand.slug || rawName.toLowerCase().replace(/[^a-z0-9]+/g, '-');
    const owner = brand.owner || 'Independent';
    const ultimate = brand.owner_type === 'public' ? `${owner} (NYSE/NASDAQ)` : owner;
    const isIndie = brand.independent;
    const pr = brand.parent_record;
    const profileUrl = `${TRACED_URL}/brand/${slug}`;
    const nearby = isIndie ? [] : await fetchNearby(brand.category, brand.price_tier, brand.format);

    const card = document.createElement('div');
    card.className = 'traced-card';

    // COMPACT ROW
    const compact = document.createElement('div');
    compact.className = 'traced-compact';
    const violationTeaser = pr && pr.violations ? `⚠ ${pr.violations} violations · ` : '';
    const lobbyTeaser = pr && pr.lobbying_annual ? fmtLobbying(pr.lobbying_annual) + ' lobbying' : '';
    const teaserLine = (violationTeaser || lobbyTeaser)
      ? `<div class="tc-teaser">${violationTeaser}${lobbyTeaser}</div>`
      : '';

    compact.innerHTML = `
      <div class="tc-row">
        <div class="tc-logo">T</div>
        <div class="tc-zone" style="color:${t.color};background:${t.bg};border-color:${t.color}30">
          <span class="tc-dot" style="background:${t.color}"></span>${t.label}
        </div>
        <div class="tc-owner">${owner}</div>
        <button class="tc-expand-btn">See why ↓</button>
      </div>
      <div class="tc-note">${brand.headline_finding || ''}</div>
      ${teaserLine}`;

    // EXPANDED PANEL
    const expanded = document.createElement('div');
    expanded.className = 'traced-expanded';
    expanded.style.display = 'none';

    let html = '';

    // OWNERSHIP CHAIN
    html += `
      <div class="te-section">
        <div class="te-section-label">OWNERSHIP CHAIN</div>
        <div class="te-chain">
          <div class="te-chain-item">
            <div class="te-chain-dot" style="border-color:#9a9284"></div>
            <div><div class="te-chain-name">${rawName}</div><div class="te-chain-role">THIS LOCATION</div></div>
          </div>
          <div class="te-chain-line"></div>
          <div class="te-chain-item">
            <div class="te-chain-dot" style="border-color:#625c50"></div>
            <div><div class="te-chain-name">${brand.name}</div><div class="te-chain-role">BRAND</div></div>
          </div>
          <div class="te-chain-line"></div>
          <div class="te-chain-item">
            <div class="te-chain-dot" style="border-color:${t.color}"></div>
            <div>
              <div class="te-chain-name" style="color:${t.color}">${ultimate}</div>
              <div class="te-chain-role">ULTIMATE OWNER</div>
            </div>
          </div>
        </div>
      </div>`;

    // FOUNDER STORY (both indie and acquired)
    if (brand.founder_story) {
      const sectionColor = isIndie ? '#4e9b6f' : '#9ca3af';
      const sectionBg = isIndie ? 'te-section-green' : '';
      html += `
        <div class="te-section ${sectionBg}">
          <div class="te-section-label" style="color:${sectionColor}">${isIndie ? 'FOUNDER STORY' : 'ORIGIN'}</div>
          <div class="te-founder-story">${brand.founder_story}</div>
        </div>`;
    } else if (brand.founded_year && !isIndie) {
      html += `
        <div class="te-section">
          <div class="te-section-label">ORIGIN</div>
          <div class="te-stat-row"><span class="te-stat-label">Founded</span><span class="te-stat-val">${brand.founded_year}</span></div>
          ${brand.acquired_year ? `<div class="te-stat-row"><span class="te-stat-label">Acquired</span><span class="te-stat-val">${brand.acquired_year}${brand.acquisition_price ? ` · $${(brand.acquisition_price/1e9).toFixed(2)}B` : ''}</span></div>` : ''}
        </div>`;
    }

    // PARENT COMPANY RECORD
    if (pr && pr.violations && !isIndie) {
      const lf = fmtLobbying(pr.lobbying_annual);
      html += `
        <div class="te-section te-section-warn">
          <div class="te-section-label" style="color:#c94d3c">PARENT COMPANY RECORD</div>
          <div class="te-stat-row">
            <span class="te-stat-label">Violations</span>
            <span class="te-stat-val te-stat-red">${pr.violations} documented</span>
          </div>
          <div class="te-violation-note">${pr.violation_summary}</div>
          ${lf ? `<div class="te-stat-row" style="margin-top:8px">
            <span class="te-stat-label">Lobbying</span>
            <span class="te-stat-val te-stat-amber">${lf}</span>
          </div>
          <div class="te-violation-note">${pr.lobbying_issues}</div>` : ''}
        </div>`;
    }

    // INGREDIENT DRIFT
    if (brand.ingredient_drift && brand.ingredient_drift_note) {
      html += `
        <div class="te-section te-section-warn">
          <div class="te-section-label" style="color:#f59e0b">⚗ INGREDIENT DRIFT</div>
          <div class="te-violation-note">${brand.ingredient_drift_note}</div>
        </div>`;
    }

    // BETTER NEARBY
    if (nearby.length > 0) {
      const items = nearby.map(n => `
        <div class="te-nearby-item">
          <span class="te-nearby-dot" style="background:#4e9b6f"></span>
          <div>
            <div class="te-nearby-name">${n.name}</div>
            <div class="te-nearby-note">${n.note || n.neighborhood || ''}</div>
          </div>
        </div>`).join('');
      html += `
        <div class="te-section te-section-green">
          <div class="te-section-label" style="color:#4e9b6f">BETTER NEARBY</div>
          ${items}
        </div>`;
    }

    // ACTIONS
    const ctaLabel = pr && pr.violations
      ? `See ${pr.violations} violations on TracedHealth →`
      : `Full profile on TracedHealth →`;
    html += `
      <div class="te-actions">
        <button class="te-btn-copy" id="te-copy-${slug}">Copy finding</button>
        <a class="te-btn-full" href="${profileUrl}" target="_blank">${ctaLabel}</a>
      </div>
      <div class="te-footer">Powered by TracedHealth · tracedhealth.com</div>`;

    expanded.innerHTML = html;
    card.appendChild(compact);
    card.appendChild(expanded);

    setTimeout(() => {
      card.querySelector('.tc-expand-btn').addEventListener('click', e => {
        e.stopPropagation();
        const open = expanded.style.display !== 'none';
        expanded.style.display = open ? 'none' : 'block';
        card.querySelector('.tc-expand-btn').textContent = open ? 'See why ↓' : 'Collapse ↑';
      });
      const cb = card.querySelector(`#te-copy-${slug}`);
      if (cb) cb.addEventListener('click', () => {
        const text = brand.share_text || `${brand.name} — ${t.label}: ${ultimate}\n${brand.headline_finding || ''}\n${profileUrl}\nPowered by TracedHealth`;
        navigator.clipboard.writeText(text).then(() => {
          cb.textContent = 'Copied! ✓';
          cb.style.background = '#4e9b6f';
          setTimeout(() => { cb.textContent = 'Copy finding'; cb.style.background = ''; }, 2000);
        });
      });
    }, 50);

    return card;
  }

  async function inject() {
    const panel = document.querySelector('[role="main"]');
    if (!panel) return;
    if (document.querySelector('.traced-card')) return;
    const h1 = panel.querySelector('h1');
    if (!h1 || injected.has(h1)) return;
    const name = h1.textContent.trim();
    if (name.length < 3 || name.length > 80) return;
    if (IGNORE_PATTERNS.test(name)) return;
    if (name === lastInjectedName) return;
    const result = await lookup(name);
    if (!result) return;
    if (document.querySelector('.traced-card')) return;
    lastInjectedName = name;
    injected.add(h1);
    const card = await createDetailCard(result, name);
    h1.parentElement.insertBefore(card, h1.nextSibling);
  }

  function scheduleInject() {
    clearTimeout(debounceTimer);
    debounceTimer = setTimeout(inject, 600);
  }

  function init() {
    setTimeout(inject, 1500);
    new MutationObserver(scheduleInject).observe(document.body, { childList: true, subtree: true });
    let lastUrl = location.href;
    setInterval(() => {
      if (location.href !== lastUrl) {
        lastUrl = location.href;
        injected.clear();
        lastInjectedName = null;
        document.querySelectorAll('.traced-card').forEach(e => e.remove());
        setTimeout(inject, 1500);
      }
    }, 1000);
  }

  document.readyState === 'loading'
    ? document.addEventListener('DOMContentLoaded', init)
    : init();

  console.log('[Traced Maps v5] active');
})();
