"""Phase 1 — Schema upgrades for v3 build"""
import sqlite3
DB = '/Users/evan/Desktop/Traceddatabase/traced.db'
conn = sqlite3.connect(DB)
conn.execute("PRAGMA journal_mode=WAL")
c = conn.cursor()

def add_col(table, col, defn):
    try:
        c.execute(f"ALTER TABLE {table} ADD COLUMN {col} {defn}")
        print(f"  + {table}.{col}")
    except Exception as e:
        if 'duplicate column' in str(e).lower():
            pass  # already exists
        else:
            print(f"  ! {table}.{col}: {e}")

# ── companies additions ──────────────────────────────────────────
add_col('companies', 'ownership_tier',  "TEXT")
add_col('companies', 'vc_investors',    "TEXT")
# pe_firm, founder_led, founded_year, description already exist

# ── brands additions ─────────────────────────────────────────────
add_col('brands', 'transparency_label',              "TEXT")
add_col('brands', 'transparency_label_reasons',      "TEXT")
add_col('brands', 'ownership_tier',                  "TEXT")
add_col('brands', 'ingredient_transparency',         "TEXT")
add_col('brands', 'ingredient_transparency_notes',   "TEXT")
add_col('brands', 'health_claim_flags',              "TEXT")
add_col('brands', 'certifications_maintained_post_acquisition', "INTEGER DEFAULT 0")
add_col('brands', 'certification_notes',             "TEXT")
add_col('brands', 'price_change_post_acquisition',   "TEXT")
add_col('brands', 'watch_list',                      "INTEGER DEFAULT 0")
add_col('brands', 'watch_list_reason',               "TEXT")
add_col('brands', 'recently_acquired',               "INTEGER DEFAULT 0")
add_col('brands', 'acquisition_age_years',           "INTEGER")
add_col('brands', 'founder_still_involved',          "INTEGER")
add_col('brands', 'clean_swap_brands',               "TEXT")
add_col('brands', 'sub_category',                    "TEXT")  # may exist

# ── new tables ───────────────────────────────────────────────────
c.execute("""CREATE TABLE IF NOT EXISTS health_claims (
    id TEXT PRIMARY KEY,
    brand_id TEXT,
    claim_text TEXT,
    claim_type TEXT,
    challenged_by TEXT,
    outcome TEXT,
    year INTEGER,
    fine_amount REAL,
    source_url TEXT
)""")
print("  + table: health_claims")

c.execute("""CREATE TABLE IF NOT EXISTS certifications (
    id TEXT PRIMARY KEY,
    brand_id TEXT,
    certification_type TEXT,
    granted_year INTEGER,
    revoked_year INTEGER,
    maintained_post_acquisition INTEGER,
    notes TEXT,
    source_url TEXT
)""")
print("  + table: certifications")

c.execute("""CREATE TABLE IF NOT EXISTS clean_swaps (
    id TEXT PRIMARY KEY,
    brand_id TEXT,
    alternative_brand_id TEXT,
    category TEXT,
    reason TEXT,
    verified INTEGER DEFAULT 0
)""")
print("  + table: clean_swaps")

c.execute("""CREATE TABLE IF NOT EXISTS retailer_scores (
    id TEXT PRIMARY KEY,
    retailer_name TEXT,
    retailer_slug TEXT,
    independent_brand_pct REAL,
    conglomerate_brand_pct REAL,
    pe_brand_pct REAL,
    transparency_score INTEGER,
    total_brands_tracked INTEGER,
    notes TEXT
)""")
print("  + table: retailer_scores")

c.execute("""CREATE TABLE IF NOT EXISTS local_markets (
    id TEXT PRIMARY KEY,
    name TEXT,
    type TEXT,
    address TEXT,
    city TEXT,
    state TEXT,
    zip TEXT,
    lat REAL,
    lng REAL,
    hours TEXT,
    website TEXT,
    accepts_ebt INTEGER,
    organic_vendors INTEGER,
    year_round INTEGER
)""")
print("  + table: local_markets")

conn.commit()
conn.close()
print("Phase 1 DONE")
