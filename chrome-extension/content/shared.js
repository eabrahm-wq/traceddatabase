const TRACED = {
  API_BASE: "http://localhost:5001/api",
  CACHE_TTL_MS: 24 * 60 * 60 * 1000,
  OWNERSHIP_CONFIG: {
    independent: { color: "#22c55e", label: "Independent", short: "INDEP" },
    acquired:    { color: "#ef4444", label: "Acquired",    short: "CORP"  },
    chain:       { color: "#f59e0b", label: "Chain",       short: "CHAIN" },
    pe:          { color: "#8b5cf6", label: "PE-Backed",   short: "PE"    },
    public:      { color: "#f59e0b", label: "Public Co.",  short: "PUBLIC"},
    unknown:     { color: "#4a5060", label: "Unknown",     short: "?"     },
  },
  getOwnershipConfig(brand) {
    if (!brand) return this.OWNERSHIP_CONFIG.unknown;
    if (brand.pe_owned) return this.OWNERSHIP_CONFIG.pe;
    if (brand.independent) return this.OWNERSHIP_CONFIG.independent;
    if (brand.owner) return this.OWNERSHIP_CONFIG.acquired;
    return this.OWNERSHIP_CONFIG.unknown;
  },
  async lookup(rawName, surface) {
    const cacheKey = "traced_" + rawName.toLowerCase().trim();
    try {
      const cached = await chrome.storage.local.get(cacheKey);
      if (cached[cacheKey]) {
        const { data, ts } = cached[cacheKey];
        if (Date.now() - ts < this.CACHE_TTL_MS) return data;
      }
    } catch(e) {}
    try {
      const url = this.API_BASE + "/lookup?name=" + encodeURIComponent(rawName) + (surface ? "&surface=" + surface : "");
      const res = await fetch(url);
      if (!res.ok) return null;
      const data = await res.json();
      try { await chrome.storage.local.set({ [cacheKey]: { data, ts: Date.now() } }); } catch(e) {}
      return data;
    } catch(e) {
      console.warn("[Traced] lookup failed:", e.message);
      return null;
    }
  },
  buildPanel(brand) {
    const cfg = this.getOwnershipConfig(brand);
    const owner = brand.owner || "Independent";
    const year = brand.acquired_year ? " · Acquired " + brand.acquired_year : "";
    const pe = brand.pe_owned ? " · PE-Backed" : "";
    const formula = brand.formula_changed ? '<div class="traced-panel-flag">⚠ Formula changed post-acquisition</div>' : "";
    const profileUrl = "https://tracedhealth.com/brand/" + (brand.slug || "");
    const shareText = brand.share_text || (brand.name + " is owned by " + owner + ". #Traced");
    return `<div class="traced-panel">
      <div class="traced-panel-header" style="border-left:3px solid ${cfg.color}">
        <div class="traced-panel-status">
          <span class="traced-dot-lg" style="background:${cfg.color};box-shadow:0 0 8px ${cfg.color}88"></span>
          <span class="traced-panel-label" style="color:${cfg.color}">${cfg.label}</span>
        </div>
        <div class="traced-panel-name">${brand.name}</div>
        <div class="traced-panel-owner">${owner}${year}${pe}</div>
      </div>
      ${brand.headline_finding ? `<div class="traced-panel-finding">${brand.headline_finding}</div>` : ""}
      ${formula}
      <div class="traced-panel-actions">
        <a class="traced-btn traced-btn-primary" href="${profileUrl}" target="_blank">Full Profile →</a>
        <button class="traced-btn traced-btn-copy" id="traced-copy-btn">Copy for Instagram</button>
      </div>
      <div class="traced-panel-footer">
        <span class="traced-credit">via <a href="https://tracedhealth.com" target="_blank">Traced</a></span>
        <button class="traced-flag" onclick="window.open('mailto:hello@tracedhealth.com?subject=Correction: ${encodeURIComponent(brand.name)}')">Flag error</button>
      </div>
    </div>`;
  }
};
window.__TRACED__ = TRACED;
console.log("[Traced Maps] loaded");

document.addEventListener("click", function(e) {
  if (e.target && e.target.id === "traced-copy-btn") {
    const panel = e.target.closest(".traced-panel");
    if (!panel) return;
    const brandSlug = panel.querySelector(".traced-panel-name");
    const ownerEl = panel.querySelector(".traced-panel-owner");
    const text = brandSlug.textContent + " — " + ownerEl.textContent + " #Traced #FoodTransparency";
    navigator.clipboard.writeText(text).then(() => {
      e.target.textContent = "Copied ✓";
      setTimeout(() => e.target.textContent = "Copy for Instagram", 2000);
    });
  }
});
