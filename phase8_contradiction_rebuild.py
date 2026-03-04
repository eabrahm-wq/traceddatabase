"""
Phase 8 — Rebuild contradiction scores using new multi-dimensional rubric.

Rubric (max 100, capped):
  ownership_score        max 35
    - pe_firm ownership:          +35
    - public_conglomerate:        +28
    - subsidiary of pharma:       +25
    - private_conglomerate:       +20
    - public_standalone:          +10
    - independent:                 +0

  brand_positioning_score  max 25
    - "organic" + acquired:       +20
    - "natural" + acquired:       +15
    - "clean" / "simple" claims:  +12
    - "family" / "founder" story: +10
    - any acquired brand:          +8

  parent_regulatory_score  max 30
    - fines > $100M:              +30
    - fines $10M-$100M:           +20
    - fines $1M-$10M:             +10
    - fines < $1M:                 +5
    - any FDA recall at parent:    +8
    - lobbying issues:             +5 per issue, max +15

  ingredient_integrity_score  max 15
    - formula_changed_post_acq:   +15
    - brand discontinued by acq:  +15
    - ingredient drift detected:  +10
    - no change known:             +0

Total capped at 100.
"""
import sqlite3, json, re
DB = '/Users/evan/Desktop/Traceddatabase/traced.db'
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
c = conn.cursor()
conn.execute("PRAGMA journal_mode=WAL")

# Pull all brands with parent company data
c.execute("""
    SELECT b.id, b.name, b.slug, b.acquired_year, b.independent,
           b.pe_owned, b.formula_changed_post_acquisition,
           b.marketing_claims, b.certifications, b.origin_story,
           b.headline_finding, b.share_text,
           co.id as co_id, co.name as co_name, co.ownership_type,
           co.pe_firm as co_pe_firm
    FROM brands b
    LEFT JOIN companies co ON b.parent_company_id=co.id
""")
brands = [dict(r) for r in c.fetchall()]
print(f"Scoring {len(brands)} brands...")

updated = 0
for b in brands:
    reasons = []
    score = 0

    co_id = b.get('co_id')
    otype = (b.get('ownership_type') or '').lower()
    marketing = (b.get('marketing_claims') or '').lower()
    certs = (b.get('certifications') or '').lower()
    headline = b.get('headline_finding') or ''
    origin = (b.get('origin_story') or '').lower()

    # ── OWNERSHIP SCORE ────────────────────────────────────────────
    ownership_score = 0
    if b.get('pe_owned'):
        ownership_score = 35
        reasons.append("PE firm ownership (3-7 year exit cycle)")
    elif co_id:
        if otype == 'pe_firm':
            ownership_score = 35
            reasons.append("PE firm ownership")
        elif otype == 'public_conglomerate':
            ownership_score = 28
            reasons.append("Publicly traded conglomerate ownership")
        elif otype == 'subsidiary':
            ownership_score = 25
            reasons.append("Subsidiary of pharmaceutical/large corporation")
        elif otype == 'private_conglomerate':
            ownership_score = 20
            reasons.append("Private conglomerate ownership")
        elif co_id:
            ownership_score = 18
            reasons.append("Corporate parent ownership")
    # independent: 0

    # ── BRAND POSITIONING SCORE ────────────────────────────────────
    bp_score = 0
    if co_id:  # Only applies to acquired brands
        has_organic = 'organic' in marketing or 'organic' in certs
        has_natural = 'natural' in marketing or 'all natural' in marketing
        has_clean = 'clean' in marketing or 'simple' in marketing or 'minimal' in marketing
        has_family = 'family' in marketing or 'family' in origin or 'founder' in origin
        has_wellness = 'wellness' in marketing or 'gut health' in marketing or 'immune' in marketing

        if has_organic:
            bp_score = max(bp_score, 20)
            reasons.append("'Organic' branding under conglomerate ownership")
        if has_natural:
            bp_score = max(bp_score, 15)
            reasons.append("'Natural' branding under conglomerate ownership")
        if has_clean:
            bp_score = max(bp_score, 12)
            reasons.append("Clean/simple claims under conglomerate ownership")
        if has_family:
            bp_score = max(bp_score, 10)
            reasons.append("Family/founder story while conglomerate-owned")
        if has_wellness:
            bp_score = max(bp_score, 12)
            reasons.append("Wellness claims under conglomerate ownership")
        if bp_score == 0 and co_id:
            bp_score = 8
    bp_score = min(bp_score, 25)

    # ── PARENT REGULATORY SCORE ────────────────────────────────────
    reg_score = 0
    if co_id:
        # Fines
        c.execute("SELECT SUM(fine_amount) FROM violations WHERE company_id=? AND fine_amount IS NOT NULL", (co_id,))
        fines = c.fetchone()[0] or 0
        if fines >= 100e6:
            reg_score += 30; reasons.append(f"${round(fines/1e6)}M+ documented fines against parent")
        elif fines >= 10e6:
            reg_score += 20; reasons.append(f"${round(fines/1e6)}M documented fines against parent")
        elif fines >= 1e6:
            reg_score += 10; reasons.append(f"${round(fines/1e6)}M documented fines against parent")
        elif fines > 0:
            reg_score += 5; reasons.append("Documented fines against parent company")

        # FDA recalls
        c.execute("SELECT COUNT(*) FROM violations WHERE company_id=? AND violation_type='FDA recall'", (co_id,))
        recalls = c.fetchone()[0]
        if recalls > 0:
            reg_score += min(recalls * 2, 8)
            reasons.append(f"{recalls} FDA recall(s) at parent company")

        # Lobbying
        c.execute("SELECT issues FROM lobbying_records WHERE company_id=? ORDER BY year DESC LIMIT 5", (co_id,))
        lobby_rows = c.fetchall()
        lobby_issues_seen = set()
        for row in lobby_rows:
            for issue in (row[0] or '').split(','):
                issue = issue.strip()
                if issue and issue not in lobby_issues_seen:
                    lobby_issues_seen.add(issue)
        if lobby_issues_seen:
            lobby_add = min(len(lobby_issues_seen) * 5, 15)
            reg_score += lobby_add
            sample = list(lobby_issues_seen)[:2]
            reasons.append("Parent lobbied on: " + ", ".join(sample))

    reg_score = min(reg_score, 30)

    # ── INGREDIENT INTEGRITY SCORE ──────────────────────────────────
    ing_score = 0
    if b.get('formula_changed_post_acquisition'):
        ing_score = 15
        reasons.append("Formula changed after acquisition")
    else:
        # Check ingredient drift records
        c.execute("SELECT COUNT(*) FROM ingredient_drift WHERE brand_id=? AND ingredients_removed != ''", (b['id'],))
        drift_count = c.fetchone()[0]
        if drift_count > 0:
            ing_score = 10
            reasons.append("Ingredient drift documented post-acquisition")
        # Check if brand was discontinued (look for event)
        c.execute("SELECT COUNT(*) FROM brand_events WHERE brand_id=? AND event_type='formulation_change' AND headline LIKE '%discontinu%'", (b['id'],))
        disc = c.fetchone()[0]
        if disc:
            ing_score = 15
            reasons.append("Brand discontinued by acquiring parent")
    ing_score = min(ing_score, 15)

    # ── TOTAL ──────────────────────────────────────────────────────
    total = min(ownership_score + bp_score + reg_score + ing_score, 100)

    # Preserve manually set high scores if we don't have full parent data
    current = b.get('contradiction_score') or 0
    # If brand has specific headline/override reasons stored, blend
    existing_reasons_raw = c.execute("SELECT contradiction_reasons FROM brands WHERE id=?", (b['id'],)).fetchone()
    existing_reasons = []
    if existing_reasons_raw and existing_reasons_raw[0]:
        try:
            existing_reasons = json.loads(existing_reasons_raw[0])
        except:
            pass

    # Merge: if existing reasons are more specific (from manual entry), keep them
    final_reasons = reasons if len(reasons) > len(existing_reasons) else existing_reasons
    # Cap reasons at 5
    final_reasons = final_reasons[:5]

    # Headline: update if none set
    current_headline = c.execute("SELECT headline_finding FROM brands WHERE id=?", (b['id'],)).fetchone()[0] or ''
    final_headline = current_headline
    if not final_headline and co_id and b.get('co_name'):
        yr = b.get('acquired_year')
        yr_str = (" in " + str(yr)) if yr else ""
        final_headline = b['name'] + " is owned by " + b['co_name'] + yr_str + "."

    # Share text
    current_share = c.execute("SELECT share_text FROM brands WHERE id=?", (b['id'],)).fetchone()[0] or ''
    final_share = current_share
    if not final_share and co_id and b.get('co_name'):
        final_share = b['name'] + " is owned by " + b['co_name'] + ". Check it on Traced: tracedhealth.com/brand/" + (b['slug'] or '')

    c.execute("""UPDATE brands SET
        contradiction_score=?,
        contradiction_reasons=?,
        headline_finding=?,
        share_text=?
        WHERE id=?""", (
        total,
        json.dumps(final_reasons),
        final_headline,
        final_share,
        b['id']
    ))
    updated += 1

conn.commit()
print(f"Updated {updated} brands with new contradiction scores")

# Stats
c.execute("SELECT contradiction_score, COUNT(*) as cnt FROM brands GROUP BY contradiction_score ORDER BY contradiction_score DESC LIMIT 20")
print("\nTop score distribution:")
for row in c.fetchall():
    print(f"  Score {row[0]}: {row[1]} brands")

c.execute("SELECT name, slug, contradiction_score FROM brands ORDER BY contradiction_score DESC LIMIT 20")
print("\nTop 20 highest contradiction brands:")
for row in c.fetchall():
    print(f"  {row[2]:3d}  {row[0]} ({row[1]})")

c.execute("SELECT name, slug, contradiction_score FROM brands WHERE parent_company_id IS NULL ORDER BY contradiction_score ASC LIMIT 15")
print("\nLowest contradiction independent brands:")
for row in c.fetchall():
    print(f"  {row[2]:3d}  {row[0]}")

conn.close()
print("\nPhase 8 COMPLETE")
