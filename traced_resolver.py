import re, sqlite3, os
from datetime import datetime

try:
    from rapidfuzz import fuzz, process
    RAPIDFUZZ_AVAILABLE = True
except ImportError:
    RAPIDFUZZ_AVAILABLE = False

DB_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'traced.db')
FUZZY_THRESHOLD = 88

LOCATION_PATTERNS = [
    r'\s*[-·|•]\s*[A-Z][^-·|•]*$',
    r',\s*(san francisco|sf|oakland|berkeley|los angeles|new york|chicago|seattle|portland)[^,]*$',
    r'\s+#\d+\s*$',
    r'\s+\(\d+\)\s*$',
    r'\s*\|\s*.*$',
]
LEGAL_SUFFIXES = [
    r'\s+(llc|inc|corp|co\.|ltd|limited|group|holdings|enterprises|international|worldwide)\.?\s*$',
]

def normalize(raw):
    s = raw.strip()
    for pat in LOCATION_PATTERNS:
        s = re.sub(pat, '', s, flags=re.IGNORECASE).strip()
    for pat in LEGAL_SUFFIXES:
        s = re.sub(pat, '', s, flags=re.IGNORECASE).strip()
    s = s.lower()
    s = re.sub(r"'s\b", '', s)
    s = re.sub(r"[^\w\s]", ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def get_db(db_path=None):
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def ensure_resolver_tables(db_path=None):
    conn = get_db(db_path)
    conn.execute("""CREATE TABLE IF NOT EXISTS brand_aliases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        alias_text TEXT NOT NULL,
        brand_id TEXT NOT NULL REFERENCES brands(id),
        source TEXT DEFAULT 'manual',
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(alias_text))""")
    conn.execute("""CREATE TABLE IF NOT EXISTS resolver_misses (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        raw_input TEXT NOT NULL,
        normalized TEXT NOT NULL,
        surface TEXT,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        reviewed BOOLEAN DEFAULT 0,
        resolved_to TEXT REFERENCES brands(id))""")
    conn.execute("CREATE INDEX IF NOT EXISTS idx_alias_text ON brand_aliases(alias_text)")
    conn.commit()
    conn.close()
    print("✓ Resolver tables ready")

SEED_ALIASES = [
    ("blue bottle coffee","Blue Bottle Coffee"),("blue bottle","Blue Bottle Coffee"),
    ("peets coffee","Peet's Coffee"),("peets","Peet's Coffee"),("peets coffee tea","Peet's Coffee"),
    ("philz coffee","Philz Coffee"),("philz","Philz Coffee"),
    ("ritual coffee roasters","Ritual Coffee Roasters"),("ritual coffee","Ritual Coffee Roasters"),
    ("sightglass coffee","Sightglass Coffee"),("sightglass","Sightglass Coffee"),
    ("starbucks coffee","Starbucks"),("starbucks reserve","Starbucks"),("starbucks","Starbucks"),
    ("whole foods market","Whole Foods Market"),("whole foods","Whole Foods Market"),
    ("safeway","Safeway"),("rainbow grocery cooperative","Rainbow Grocery"),
    ("rainbow grocery","Rainbow Grocery"),("rainbow","Rainbow Grocery"),
    ("bi-rite market","Bi-Rite Market"),("bi rite market","Bi-Rite Market"),("bi-rite","Bi-Rite Market"),
    ("trader joes","Trader Joe's"),("trader joe","Trader Joe's"),
    ("sweetgreen","Sweetgreen"),("shake shack","Shake Shack"),
    ("chipotle mexican grill","Chipotle"),("chipotle","Chipotle"),
    ("mcdonalds","McDonald's"),("patagonia","Patagonia"),
    ("gap","Gap"),("the gap","Gap"),("levis","Levi's"),("levi strauss","Levi's"),
    ("arcteryx","Arc'teryx"),("arc teryx","Arc'teryx"),
    ("north face","The North Face"),("the north face","The North Face"),
]

def seed_aliases(db_path=None):
    conn = get_db(db_path)
    c = conn.cursor()
    seeded = skipped = 0
    for alias_text, brand_name in SEED_ALIASES:
        c.execute("SELECT id FROM brands WHERE lower(name) = lower(?)", (brand_name,))
        row = c.fetchone()
        if not row:
            skipped += 1
            continue
        try:
            c.execute("INSERT OR IGNORE INTO brand_aliases (alias_text, brand_id, source) VALUES (?, ?, 'seed')",
                      (alias_text, row["id"]))
            if c.rowcount > 0:
                seeded += 1
        except Exception as e:
            print(f"  ERROR: {e}")
    conn.commit()
    conn.close()
    print(f"✓ Seeded {seeded} aliases, skipped {skipped} (brands not in DB)")
    return seeded, skipped

def add_alias(alias_text, brand_id, db_path=None):
    normalized = normalize(alias_text)
    conn = get_db(db_path)
    conn.execute("INSERT OR REPLACE INTO brand_aliases (alias_text, brand_id, source) VALUES (?, ?, 'manual')",
                 (normalized, brand_id))
    conn.commit()
    conn.close()
    print(f"✓ Added alias: '{normalized}' → {brand_id}")

def _format_brand(row):
    return {
        "name": row.get("name"), "slug": row.get("slug"),
        "category": row.get("category"), "owner": row.get("co_name"),
        "owner_type": row.get("co_type"), "ownership_tier": row.get("ownership_tier"),
        "independent": bool(row.get("independent")), "pe_owned": bool(row.get("pe_owned")),
        "acquired_year": row.get("acquired_year"), "acquisition_price": row.get("acquisition_price"),
        "founded_year": row.get("founded_year"), "overall_zone": row.get("overall_zone"),
        "headline_finding": row.get("headline_finding"), "share_text": row.get("share_text"),
        "formula_changed": bool(row.get("formula_changed_post_acquisition")),
        "watch_list": bool(row.get("watch_list")),
        "price_tier": row.get("price_tier"),
        "format": row.get("format"),
        "ingredient_drift": bool(row.get("ingredient_drift")),
        "ingredient_drift_note": row.get("ingredient_drift_note"),
        "founder_story": row.get("founder_story"),
        "parent_record": {
            "violations": row.get("co_violations"),
            "violation_summary": row.get("co_violation_summary"),
            "lobbying_annual": row.get("co_lobbying"),
            "lobbying_issues": row.get("co_lobbying_issues"),
        } if row.get("co_violations") else None,
    }

def _fetch_brand(brand_id, conn):
    c = conn.cursor()
    c.execute("""SELECT b.*, co.name as co_name, co.type as co_type,
                     co.violation_count as co_violations, co.violation_summary as co_violation_summary,
                     co.lobbying_annual as co_lobbying, co.lobbying_issues as co_lobbying_issues
                 FROM brands b LEFT JOIN companies co ON b.parent_company_id = co.id
                 WHERE b.id = ?""", (brand_id,))
    row = c.fetchone()
    return dict(row) if row else None

def _all_brand_names(conn):
    c = conn.cursor()
    c.execute("SELECT id, name FROM brands")
    return [(normalize(r["name"]), r["id"]) for r in c.fetchall()]

def resolve(raw_input, surface=None, db_path=None):
    if not raw_input or not raw_input.strip():
        return {"matched": False, "raw_input": raw_input, "normalized": "", "logged": False}
    normalized = normalize(raw_input)
    conn = get_db(db_path)
    try:
        c = conn.cursor()
        # Step 1: alias
        c.execute("SELECT brand_id FROM brand_aliases WHERE alias_text = ?", (normalized,))
        row = c.fetchone()
        if row:
            brand = _fetch_brand(row["brand_id"], conn)
            if brand:
                return {"matched": True, "confidence": 1.0, "match_method": "alias", "brand": _format_brand(brand)}
        # Step 2: fuzzy
        if RAPIDFUZZ_AVAILABLE:
            all_brands = _all_brand_names(conn)
            names = [b[0] for b in all_brands]
            ids = [b[1] for b in all_brands]
            result = process.extractOne(normalized, names, scorer=fuzz.token_sort_ratio, score_cutoff=FUZZY_THRESHOLD)
            if result:
                matched_name, score, idx = result
                brand = _fetch_brand(ids[idx], conn)
                if brand:
                    return {"matched": True, "confidence": round(score/100, 2), "match_method": "fuzzy", "brand": _format_brand(brand)}
        # Step 3: partial
        c.execute("""SELECT b.*, co.name as co_name, co.type as co_type
                     FROM brands b LEFT JOIN companies co ON b.parent_company_id = co.id
                     WHERE length(b.name) >= 8
                       AND (lower(b.name) LIKE '%' || lower(?) || '%'
                        OR (length(?) >= 12 AND lower(?) LIKE '%' || lower(b.name) || '%'))
                     ORDER BY length(b.name) DESC LIMIT 1""", (normalized, normalized, normalized))
        row = c.fetchone()
        if row:
            return {"matched": True, "confidence": 0.70, "match_method": "partial", "brand": _format_brand(dict(row))}
        # Miss
        conn.execute("INSERT INTO resolver_misses (raw_input, normalized, surface) VALUES (?, ?, ?)",
                     (raw_input, normalized, surface))
        conn.commit()
        return {"matched": False, "raw_input": raw_input, "normalized": normalized, "logged": True}
    finally:
        conn.close()

def get_misses(limit=50, db_path=None):
    conn = get_db(db_path)
    c = conn.cursor()
    c.execute("""SELECT id, raw_input, normalized, surface, timestamp, COUNT(*) as frequency
                 FROM resolver_misses WHERE reviewed = 0
                 GROUP BY normalized ORDER BY frequency DESC, timestamp DESC LIMIT ?""", (limit,))
    rows = [dict(r) for r in c.fetchall()]
    conn.close()
    return rows

def get_brand_names(db_path=None):
    conn = get_db(db_path)
    c = conn.cursor()
    c.execute("SELECT name FROM brands ORDER BY name")
    names = [r["name"] for r in c.fetchall()]
    conn.close()
    return names

def setup(db_path=None):
    print("Setting up Traced resolver...")
    ensure_resolver_tables(db_path)
    seed_aliases(db_path)
    print("✓ Done. Check misses with get_misses()")
