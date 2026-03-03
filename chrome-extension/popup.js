const API_BASE = 'https://tracedhealth.com'; // change to http://127.0.0.1:5001 for local dev

function scoreColor(score) {
  if (score >= 70) return '#c44444';
  if (score >= 40) return '#d4952a';
  return '#3a8a5a';
}
function scoreLabel(score) {
  if (score >= 70) return 'HIGH CONTRADICTION';
  if (score >= 40) return 'MODERATE';
  return 'CLEAN';
}

function renderBrand(data) {
  const result = document.getElementById('result');
  if (!data || data.error) {
    result.innerHTML = `<div class="status">Brand not found. Try another name.</div>`;
    return;
  }
  const sc = data.contradiction_score || 0;
  const col = scoreColor(sc);
  const lbl = scoreLabel(sc);
  const parent = data.parent_company;
  const slug = data.brand_id || data.name.toLowerCase().replace(/[^a-z0-9]+/g, '-');

  const findings = [];
  if (data.acquired_year) findings.push(`Acquired by ${parent} in ${data.acquired_year}`);
  if (data.lobbying_issues && data.lobbying_issues.length)
    findings.push(`${parent} lobbied: ${data.lobbying_issues.slice(0,2).join(', ')}`);
  else if (data.fines_total > 1e6)
    findings.push(`$${Math.round(data.fines_total/1e6)}M in documented fines`);
  if (data.recall_count > 0) findings.push(`${data.recall_count} FDA recalls`);

  const findingsHtml = findings.slice(0, 3).map(f =>
    `<div class="finding">• ${f}</div>`
  ).join('');

  result.innerHTML = `
    <div class="brand-card">
      <div class="brand-name">${data.name}</div>
      <div class="brand-owner ${!parent ? 'independent' : ''}">
        ${parent ? `Owned by ${parent}` : '✓ Independent'}
      </div>
      <div class="score-row">
        <div class="score" style="color:${col}">${sc}</div>
        <div class="bar-bg">
          <div class="bar" style="width:${sc}%;background:${col}"></div>
        </div>
        <div style="font-size:8px;color:${col};letter-spacing:.08em;white-space:nowrap">${lbl}</div>
      </div>
      <div class="findings">${findingsHtml}</div>
      <div class="card-actions">
        <a href="https://tracedhealth.com/brand/${slug}" target="_blank" class="btn btn-primary">View Profile</a>
        <button class="btn btn-secondary" id="share-btn">Share</button>
      </div>
    </div>
  `;

  document.getElementById('share-btn').addEventListener('click', () => {
    fetch(`${API_BASE}/share/text/${slug}`)
      .then(r => r.json())
      .then(d => {
        navigator.clipboard.writeText(d.share_text || `Check ${data.name} on Traced: tracedhealth.com/brand/${slug}`);
        document.getElementById('share-btn').textContent = 'Copied!';
        setTimeout(() => document.getElementById('share-btn').textContent = 'Share', 2000);
      })
      .catch(() => {
        navigator.clipboard.writeText(`tracedhealth.com/brand/${slug}`);
        document.getElementById('share-btn').textContent = 'Copied!';
        setTimeout(() => document.getElementById('share-btn').textContent = 'Share', 2000);
      });
  });
}

async function lookupBrand(name) {
  document.getElementById('result').innerHTML = `<div class="status">Looking up ${name}...</div>`;
  try {
    // Ask content script for cached data first
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const fromContent = await chrome.tabs.sendMessage(tab.id, { type: 'LOOKUP_BRAND', name })
      .catch(() => null);
    if (fromContent && fromContent.data && !fromContent.data.error) {
      renderBrand(fromContent.data);
      return;
    }
    // Fallback: direct fetch
    const res = await fetch(`${API_BASE}/api/brand/${encodeURIComponent(name)}`);
    const data = await res.json();
    renderBrand(data);
  } catch (e) {
    document.getElementById('result').innerHTML = `<div class="status">Could not connect to Traced API.</div>`;
  }
}

// ── Init ──────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  const input = document.getElementById('search-input');
  let searchTimer;

  input.addEventListener('input', () => {
    clearTimeout(searchTimer);
    const q = input.value.trim();
    if (q.length < 2) return;
    searchTimer = setTimeout(() => lookupBrand(q), 400);
  });
  input.addEventListener('keydown', e => {
    if (e.key === 'Enter') { clearTimeout(searchTimer); lookupBrand(input.value.trim()); }
  });

  // Show brands detected on current page
  try {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    const res = await chrome.tabs.sendMessage(tab.id, { type: 'GET_PAGE_BRANDS' }).catch(() => null);
    if (res && res.brands && res.brands.length > 0) {
      const wrap = document.getElementById('page-brands-wrap');
      const chips = document.getElementById('page-brand-chips');
      wrap.style.display = 'block';
      res.brands.forEach(name => {
        const chip = document.createElement('span');
        chip.className = 'page-brand-chip';
        chip.textContent = name;
        chip.addEventListener('click', () => {
          input.value = name;
          lookupBrand(name);
        });
        chips.appendChild(chip);
      });
    }
  } catch (e) {}
});
