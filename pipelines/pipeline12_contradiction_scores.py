"""
Pipeline: Add and populate contradiction_score on brands table.

Score = 0–100, composed of:
  - acquired_by_big_food         : +20 if brand has parent company that is in list of "big food" corps
  - parent_ftc_actions           : +5 per FTC violation (parent), max +25
  - parent_lobbying_anti_brand   : +20 if parent lobbied on issues that contradict brand values
  - parent_lobbying_spend        : +10 if parent total lobbying spend > $50M
  - parent_recall_severity       : +5 per Class I recall (parent), max +15
  - brand_is_natural_organic     : +10 if brand positions as natural/organic/sustainable
  - post_acquisition_events      : +5 if brand had reformulation or controversy event post-acquisition
"""
import sqlite3

conn = sqlite3.connect('/Users/evan/Desktop/Traceddatabase/traced.db')
c = conn.cursor()

# --- Add column if needed ---
c.execute("PRAGMA table_info(brands)")
cols = {r[1] for r in c.fetchall()}
if 'contradiction_score' not in cols:
    c.execute("ALTER TABLE brands ADD COLUMN contradiction_score INTEGER DEFAULT 0")
    conn.commit()
    print("Added contradiction_score column")
else:
    print("contradiction_score column already exists")

# --- Constants ---
BIG_FOOD = {
    'nestle', 'kraft-heinz', 'pepsico', 'coca-cola', 'general-mills',
    'kelloggs', 'unilever', 'unilever-uk', 'campbell', 'conagra',
    'jm-smucker', 'hershey', 'mars', 'mondelez', 'tyson', 'jbs',
    'hormel', 'post-consumer-brands', 'treehouse-foods',
    'associated-british-foods', 'danone', 'lactalis', 'reckitt', 'church-dwight'
}

ANTI_BRAND_ISSUES = [
    'gmo labeling', 'sugar tax', 'sugar taxes', 'organic standards',
    'antibiotic use', 'animal welfare', 'palm oil', 'plastic packaging',
    'nutrition labeling', 'nutrition standards', 'supplement health claims',
    'infant formula marketing', 'who code', 'worker safety',
    'environmental regulations', 'environmental standards',
    'sustainability reporting'
]

NATURAL_KEYWORDS = [
    'organic', 'natural', 'honest', 'clean', 'pure', 'naked', 'earth',
    'green', 'garden', 'harvest', 'farm', 'wild', 'simple', 'real',
    'wholesome', 'innocent', 'good', 'bright', 'sunshine', 'meadow',
    'spring', 'artisan', 'craft', 'raw', 'bare', 'true', 'nature'
]

# Pre-fetch data
c.execute("SELECT id, name, parent_company_id, acquired_year, notes FROM brands")
all_brands = c.fetchall()

# FTC violations per company
c.execute("""SELECT company_id, COUNT(*) FROM violations 
             WHERE violation_type LIKE '%FTC%' OR description LIKE '%FTC%'
             GROUP BY company_id""")
ftc_by_co = dict(c.fetchall())

# Class I recalls per company
c.execute("""SELECT company_id, COUNT(*) FROM violations 
             WHERE (description LIKE '%Class I%' OR description LIKE '%Class 1%')
             GROUP BY company_id""")
recalls_by_co = dict(c.fetchall())

# Lobbying anti-brand issues per company
c.execute("SELECT company_id, issues FROM lobbying_records WHERE issues IS NOT NULL")
lobby_rows = c.fetchall()
lobby_anti = {}
for co_id, issues in lobby_rows:
    if not issues:
        continue
    lo = issues.lower()
    if any(kw in lo for kw in ANTI_BRAND_ISSUES):
        lobby_anti[co_id] = True

# Lobbying total spend per company
c.execute("SELECT company_id, SUM(total_spend) FROM lobbying_records GROUP BY company_id")
lobby_spend = dict(c.fetchall())

# Post-acquisition controversy/reformulation events per brand
c.execute("""SELECT brand_id, COUNT(*) FROM brand_events 
             WHERE event_type IN ('reformulation','controversy','lawsuit','violation')
             GROUP BY brand_id""")
controversy_events = dict(c.fetchall())

print(f"Scoring {len(all_brands):,} brands...")

scores = []
for brand_id, brand_name, parent_id, acq_year, notes in all_brands:
    score = 0
    
    # 1. Acquired by big food
    if parent_id and parent_id.lower() in BIG_FOOD:
        score += 20
    
    # 2. FTC actions on parent (5 each, max 25)
    if parent_id:
        ftc_count = ftc_by_co.get(parent_id, 0)
        score += min(ftc_count * 5, 25)
    
    # 3. Lobbying contradicts brand values
    if parent_id and parent_id in lobby_anti:
        score += 20
    
    # 4. High lobbying spend (>$50M total)
    if parent_id:
        spend = lobby_spend.get(parent_id, 0) or 0
        if spend > 50_000_000:
            score += 10
    
    # 5. Class I recalls (5 each, max 15)
    if parent_id:
        recall_count = recalls_by_co.get(parent_id, 0)
        score += min(recall_count * 5, 15)
    
    # 6. Brand markets as natural/organic
    name_lo = (brand_name or '').lower()
    notes_lo = (notes or '').lower()
    if any(kw in name_lo or kw in notes_lo for kw in NATURAL_KEYWORDS):
        score += 10
    
    # 7. Post-acquisition controversy events
    evts = controversy_events.get(brand_id, 0)
    if evts > 0 and acq_year:
        score += min(evts * 5, 5)
    
    scores.append((min(score, 100), brand_id))

conn.executemany("UPDATE brands SET contradiction_score = ? WHERE id = ?", scores)
conn.commit()

# Summary stats
c.execute("SELECT contradiction_score, COUNT(*) FROM brands GROUP BY contradiction_score ORDER BY contradiction_score DESC LIMIT 10")
print("\nScore distribution (top scores):")
for score, cnt in c.fetchall():
    print(f"  score={score}: {cnt} brands")

c.execute("""SELECT b.name, co.name, b.contradiction_score
             FROM brands b JOIN companies co ON co.id = b.parent_company_id
             WHERE b.contradiction_score >= 50
             ORDER BY b.contradiction_score DESC
             LIMIT 20""")
print("\nTop 20 highest-contradiction brands:")
for bname, coname, score in c.fetchall():
    print(f"  [{score:3d}] {bname} — {coname}")

c.execute("SELECT AVG(contradiction_score), MAX(contradiction_score) FROM brands WHERE contradiction_score > 0")
avg, mx = c.fetchone()
c.execute("SELECT COUNT(*) FROM brands WHERE contradiction_score >= 50")
high = c.fetchone()[0]
c.execute("SELECT COUNT(*) FROM brands WHERE contradiction_score > 0")
nonzero = c.fetchone()[0]
print(f"\nAvg score (nonzero): {avg:.1f}  |  Max: {mx}  |  High-contradiction (>=50): {high}  |  Total scored: {nonzero}")

conn.close()
