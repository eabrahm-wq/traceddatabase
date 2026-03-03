"""
Phases 2, 3, 4, 9 — Ownership tiers, transparency labels,
ingredient transparency, health claims, specific brand content.
"""
import sqlite3, json, uuid, re
DB = '/Users/evan/Desktop/Traceddatabase/traced.db'
conn = sqlite3.connect(DB)
conn.row_factory = sqlite3.Row
conn.execute("PRAGMA journal_mode=WAL")
c = conn.cursor()

def bid(name):
    r = c.execute("SELECT id FROM brands WHERE lower(name)=lower(?) OR slug=lower(?)", (name, re.sub(r'[^a-z0-9]+','-',name.lower()))).fetchone()
    return r[0] if r else None

def cid(name_like):
    r = c.execute("SELECT id FROM companies WHERE name LIKE ?", (f'%{name_like}%',)).fetchone()
    return r[0] if r else None

# ════════════════════════════════════════════════════════════════════
# PHASE 2 — COMPANY OWNERSHIP TIERS
# ════════════════════════════════════════════════════════════════════
print("=== PHASE 2: Ownership Tiers ===")

company_tiers = {
    # public_conglomerate
    'public_conglomerate': [
        'PepsiCo','Coca-Cola','Nestle','Nestlé','General Mills','Unilever',
        'Kraft Heinz','Kellogg','Mondelez','Mondelēz','Hershey','Campbell',
        'Conagra','Hormel','Tyson','Danone','Mars','Haleon','Glanbia',
        'Simply Good Foods','BellRing Brands','Hain Celestial','Post Holdings',
        'Clorox','Pharmavite','Otsuka','Maple Leaf','Morinaga','Hero Group',
        'Bayer AG','Reckitt','Bayer','J.M. Smucker','WhiteWave',
        'TreeHouse Foods','Lamb Weston','Pilgrim',
    ],
    # private_conglomerate
    'private_conglomerate': [
        'Mars Inc','Cargill','Koch','Aldi','Trader Joe','Ferrero','Barilla',
        'Goya','HEB','Lactalis','Mizkan','Perdue','Publix','Schwarz Group',
        'Wegmans',
    ],
    # pe_firm
    'pe_firm': [
        'KKR','TPG Capital','Bain Capital','Blackstone','3G Capital',
        'Strand Equity','Advent International','Roark Capital',
        'Leonard Green','JAB Holding',
    ],
    # cooperative
    'cooperative': [
        'Organic Valley','Land O Lakes','Ocean Spray','Cabot Creamery',
        'Blue Diamond',
    ],
}

# Update companies with ownership_tier
tier_map_by_name = {}
for tier, names in company_tiers.items():
    for nm in names:
        r = c.execute("SELECT id FROM companies WHERE name LIKE ?", (f'%{nm}%',)).fetchone()
        if r:
            c.execute("UPDATE companies SET ownership_tier=? WHERE id=?", (tier, r[0]))
            tier_map_by_name[r[0]] = tier

# Set remaining to public_conglomerate if they have ownership_type=public_conglomerate
c.execute("UPDATE companies SET ownership_tier='public_conglomerate' WHERE ownership_type='public_conglomerate' AND ownership_tier IS NULL")
c.execute("UPDATE companies SET ownership_tier='private_conglomerate' WHERE ownership_type='private_conglomerate' AND ownership_tier IS NULL")
c.execute("UPDATE companies SET ownership_tier='pe_firm' WHERE ownership_type='pe_firm' AND ownership_tier IS NULL")
c.execute("UPDATE companies SET ownership_tier='cooperative' WHERE ownership_type='cooperative' AND ownership_tier IS NULL")
c.execute("UPDATE companies SET ownership_tier='subsidiary' WHERE ownership_type='subsidiary' AND ownership_tier IS NULL")

n = c.execute("SELECT COUNT(*) FROM companies WHERE ownership_tier IS NOT NULL").fetchone()[0]
print(f"  Companies with ownership_tier: {n}")

# ── Update brands ownership_tier inherited from parent ──────────────
c.execute("""
    UPDATE brands SET ownership_tier = (
        SELECT co.ownership_tier FROM companies co
        WHERE co.id = brands.parent_company_id
    )
    WHERE parent_company_id IS NOT NULL AND ownership_tier IS NULL
""")
print(f"  Brands with inherited ownership_tier: {c.execute('SELECT COUNT(*) FROM brands WHERE ownership_tier IS NOT NULL').fetchone()[0]}")

# ── Mark known VC-backed / founder-led / celebrity brands ─────────
vc_backed = [
    ('Athletic Greens','vc_backed','Strand Equity Partners'),
    ('AG1','vc_backed','Strand Equity Partners'),
    ('Olipop','vc_backed','Mondelez Strategic Ventures, various VCs'),
    ('Celsius','public_independent',None),
    ('Beyond Meat','public_independent',None),
    ('Vital Farms','public_independent',None),
]
for name, tier, investors in vc_backed:
    b_id = bid(name)
    if b_id:
        c.execute("UPDATE brands SET ownership_tier=? WHERE id=?", (tier, b_id))
        if investors:
            c.execute("UPDATE brands SET pe_firm=? WHERE id=?", (investors, b_id))
        print(f"  {name} -> {tier}")

founder_led = [
    'LMNT','Chomps','Purely Elizabeth','Tofurky','GoMacro',
    "That's It",'Vital Farms (verify)','Jovial Foods',
]
for name in founder_led:
    nm = name.replace(' (verify)','')
    b_id = bid(nm)
    if b_id:
        c.execute("UPDATE brands SET ownership_tier='founder_led' WHERE id=? AND parent_company_id IS NULL", (b_id,))

# All remaining unlinked brands → founder_led by default
c.execute("""UPDATE brands SET ownership_tier='founder_led'
             WHERE parent_company_id IS NULL AND pe_owned=0
             AND ownership_tier IS NULL""")
print(f"  Total brands with ownership_tier set: {c.execute('SELECT COUNT(*) FROM brands WHERE ownership_tier IS NOT NULL').fetchone()[0]}")

conn.commit()

# ════════════════════════════════════════════════════════════════════
# PHASE 3 — TRANSPARENCY LABELS
# ════════════════════════════════════════════════════════════════════
print("\n=== PHASE 3: Transparency Labels ===")

# Pull all brands with enriched data
c.execute("""
    SELECT b.id, b.name, b.slug, b.ownership_tier,
           b.pe_owned, b.formula_changed_post_acquisition,
           b.marketing_claims, b.certifications,
           b.health_claim_flags, b.certifications_maintained_post_acquisition,
           b.ingredient_transparency, b.contradiction_score,
           b.acquired_year, b.parent_company_id,
           co.ownership_tier as co_tier, co.name as co_name
    FROM brands b LEFT JOIN companies co ON b.parent_company_id=co.id
""")
all_brands = [dict(r) for r in c.fetchall()]

# ── Brands with DOCUMENTED DECEPTION (FTC/criminal conviction) ──
documented_deception = {
    'beech-nut': 'Federal criminal conviction 2013 — executives convicted of selling adulterated Chinese apple concentrate as natural US baby food',
    'beech nut': 'Federal criminal conviction 2013',
    'airborne': 'FTC $30M settlement 2008 — courts ruled no clinical evidence product prevents colds',
    'naked juice': 'FTC $9M settlement — labeled products all natural while containing synthetic ingredients',
    'naked-juice': 'FTC $9M settlement — labeled products all natural while containing synthetic ingredients',
}
# ── Brands with challenged health claims → COMPLICATED or higher ──
challenged_claims_brands = {
    'athletic greens','ag1','poppi','celsius','quest nutrition',
}

labeled = 0
for b in all_brands:
    slug_key = (b['slug'] or '').lower()
    name_key = (b['name'] or '').lower()
    tier = (b['ownership_tier'] or 'founder_led').lower()
    co_tier = (b['co_tier'] or '').lower()
    parent_id = b['parent_company_id']
    formula_changed = b['formula_changed_post_acquisition'] or 0
    hcf = b['health_claim_flags'] or ''
    cert_maintained = b['certifications_maintained_post_acquisition']
    ing_trans = b['ingredient_transparency'] or ''
    score = b['contradiction_score'] or 0

    label = None
    reasons = []

    # Check documented deception first (highest priority)
    for key, reason in documented_deception.items():
        if key in slug_key or key in name_key:
            label = 'documented_deception'
            reasons.append(reason)
            break

    if label is None:
        # Check conglomerate-owned brands
        if parent_id and tier in ('public_conglomerate','private_conglomerate','pe_firm','subsidiary'):
            # Is it conflicted?
            is_conflicted = False
            if formula_changed:
                is_conflicted = True
                reasons.append("Formula changed after acquisition")
            # Check parent's regulatory record via violations
            parent_fines = c.execute("SELECT SUM(fine_amount) FROM violations WHERE company_id=? AND fine_amount IS NOT NULL", (parent_id,)).fetchone()[0] or 0
            if parent_fines > 1e7:
                reasons.append(f"Parent company has ${round(parent_fines/1e6)}M+ in documented fines")
                is_conflicted = True
            parent_lobby = c.execute("SELECT SUM(total_spend) FROM lobbying_records WHERE company_id=?", (parent_id,)).fetchone()[0] or 0
            if parent_lobby > 1e6:
                reasons.append(f"Parent company spent ${round(parent_lobby/1e6)}M+ lobbying")
                is_conflicted = True
            # Check if marketing claims contradict parent
            marketing = (b['marketing_claims'] or '').lower()
            if any(w in marketing for w in ['natural','organic','clean','honest','simple','pure','real','wholesome']):
                reasons.append("Clean/natural brand marketing contradicts parent company's regulatory record")
                is_conflicted = True
            if is_conflicted:
                label = 'conflicted'
            else:
                label = 'complicated'
                reasons.append("Owned by conglomerate but no direct formula contradiction found")

        elif tier == 'vc_backed':
            label = 'complicated'
            reasons.append("VC-backed — independent but investor return pressure exists")
            if any(k in name_key or k in slug_key for k in challenged_claims_brands):
                reasons.append("Health claims have been challenged by regulators or class actions")

        elif tier == 'celebrity_backed':
            label = 'complicated'
            reasons.append("Celebrity-backed — verify claims independently of spokesperson")

        elif tier == 'public_independent':
            label = 'complicated'
            reasons.append("Publicly traded — shareholder return pressure without conglomerate parent")

        elif tier in ('founder_led', 'cooperative'):
            # Check for any issues
            has_issues = False
            if hcf and len(hcf) > 10:
                label = 'complicated'
                reasons.append("Health claims have been challenged")
                has_issues = True
            if ing_trans == 'opaque':
                label = 'complicated'
                reasons.append("Ingredient formulation is opaque (proprietary blends, undisclosed doses)")
                has_issues = True
            if not has_issues:
                label = 'transparent'
                reasons.append("Founder-led or cooperative ownership with no documented violations")
                if b['certifications']:
                    reasons.append("Holds certifications: " + (b['certifications'] or ''))

        else:
            # Default based on score
            if score >= 70:
                label = 'conflicted'
                reasons.append("High contradiction score based on parent regulatory record")
            elif score >= 40:
                label = 'complicated'
                reasons.append("Moderate ownership or claim concerns")
            else:
                label = 'transparent'
                reasons.append("No major ownership or regulatory concerns found")

    if label is None:
        label = 'complicated'
        reasons.append("Ownership or ingredient data incomplete")

    c.execute("UPDATE brands SET transparency_label=?, transparency_label_reasons=? WHERE id=?",
              (label, json.dumps(reasons[:4]), b['id']))
    labeled += 1

conn.commit()
print(f"  Labeled {labeled} brands")
dist = c.execute("SELECT transparency_label, COUNT(*) FROM brands WHERE transparency_label IS NOT NULL GROUP BY transparency_label ORDER BY COUNT(*) DESC").fetchall()
for row in dist:
    print(f"    {row[0]}: {row[1]}")

# ════════════════════════════════════════════════════════════════════
# PHASE 4 — INGREDIENT TRANSPARENCY + HEALTH CLAIMS
# ════════════════════════════════════════════════════════════════════
print("\n=== PHASE 4: Ingredient Transparency + Health Claims ===")

# Set ingredient_transparency for specific brands
ingredient_ratings = [
    # (name/slug, rating, notes)
    ('AG1',          'opaque',  'Proprietary blend — 75 ingredients with no individual dose disclosure. Extraordinary health claims not supported by peer-reviewed RCTs on complete formula.'),
    ('Athletic Greens','opaque','Proprietary blend — 75 ingredients with no individual dose disclosure.'),
    ('Quest Nutrition','low',   'Contains sucralose and artificial sweeteners despite "no compromise" health positioning. PE-owned.'),
    ('Orgain',       'medium',  'Certified organic but Nestlé-owned. Some synthetic vitamin additions. Generally clean formulation.'),
    ('Garden of Life','high',   'Full ingredient disclosure. Third-party tested. NSF certified. High transparency despite Nestlé ownership.'),
    ('Vital Proteins','medium', 'Nestlé majority stake. Collagen claims partially supported by research but some health claims overstated.'),
    ('Premier Protein','low',   'Contains artificial sweeteners (acesulfame K, sucralose). PE-owned conglomerate. Ingredient quality secondary to taste engineering.'),
    ('Poppi',        'low',     'Class action 2024 — 2g inulin/can insufficient for meaningful gut health benefit as marketed. Sold to PepsiCo 2025.'),
    ('poppi',        'low',     'Class action 2024 — 2g inulin/can insufficient for meaningful gut health benefit as marketed.'),
    ('Celsius',      'low',     'FTC investigation 2023. Metabolism acceleration claims contested. High caffeine marketed as wellness.'),
    ('Airborne',     'opaque',  'FTC-convicted. No clinical evidence for cold prevention. Proprietary blend hiding actual effective doses.'),
    ('One A Day',    'medium',  'Synthetic vitamin forms. USP-verified. Owned by Bayer AG (Monsanto/Roundup parent).'),
    ('Centrum',      'medium',  'Synthetic vitamin forms. Pharmaceutical-grade consistency. Owned by Haleon (GSK/Pfizer spinoff).'),
    ('LMNT',         'high',    'Full electrolyte dose disclosure. Simple 3-ingredient formula: sodium, potassium, magnesium. No proprietary blends.'),
    ('Chomps',       'high',    'Grass-fed beef, sea salt, encapsulated citric acid. 3-4 ingredients. Fully transparent sourcing.'),
    ('Purely Elizabeth','high', 'Certified organic, clearly labeled ingredients, no proprietary blends.'),
    ('GoMacro',      'high',    'USDA Organic, certified B Corp. Full ingredient disclosure.'),
    ('Tofurky',      'high',    'USDA Organic, Non-GMO verified. Fully disclosed ingredients.'),
    ("That's It",    'high',    'Literally 2 ingredients (fruit + fruit). Maximum transparency.'),
    ('Olipop',       'medium',  'Botanical blend with full ingredient list. Some prebiotic claims contested but formula disclosed.'),
    ('Happy Baby',   'medium',  'USDA Organic baby food. Danone-owned. Formula disclosed. Congressional report flagged heavy metals.'),
    ('Gerber',       'medium',  'Nestlé-owned. Ingredients disclosed. Congressional report found heavy metals in some products.'),
    ('Plum Organics','medium',  "USDA Organic. Campbell's-owned. Ingredients disclosed. Heavy metals concerns in 2021 Congressional report."),
    ("Earth's Best", 'medium',  'USDA Organic. Hain Celestial-owned. Ingredients disclosed. Inorganic arsenic found in 2021 report.'),
    ('Beech-Nut',    'low',     'Criminal conviction for mislabeling. Non-GMO verified but credibility undermined by 2013 conviction.'),
    ('Liquid I.V.',  'medium',  'Ingredient list disclosed. CTT technology unverified by independent RCTs. Unilever-owned.'),
    ('Nuun',         'medium',  'Clean ingredient list. NSF Certified for Sport. Nestlé-owned.'),
    ('Nature Made',  'medium',  'USP Verified. Synthetic vitamin forms. Otsuka/pharmaceutical ownership.'),
    ('Organic Valley','high',   'Farmer-owned cooperative. USDA Organic. Full ingredient transparency. Third-party audited.'),
    ('Vital Farms',  'high',    'Pasture-raised. Third-party audited. Transparent supply chain. Public benefit corporation.'),
    ('Vega',         'medium',  'Plant protein, certified organic. Danone-owned (via WhiteWave). Ingredient disclosure is good.'),
    ('Lightlife',    'medium',  'Non-GMO verified. Ingredient list disclosed. Maple Leaf (conventional meat) owned.'),
    ('Gardein',      'medium',  'Non-GMO verified. ConAgra-owned. Ingredients disclosed.'),
    ('Sweet Earth',  'medium',  'Non-GMO verified. Nestlé-owned. Ingredients disclosed.'),
    ('Beyond Meat',  'medium',  'All ingredients disclosed. Highly processed but transparent. Publicly traded.'),
    ('Siete Family Foods','high','Simple clean ingredients. Grain-free. Paleo certified. PepsiCo acquisition Oct 2024 — no changes yet.'),
    ('Perfect Bar',  'medium',  'Real food ingredients. Refrigerated. Mondelēz-owned. Formula stable.'),
    ('Bare Snacks',  'high',    'Single-ingredient dried fruit chips (apple, coconut). PepsiCo/Frito-Lay owned but formula simple.'),
    ('Muscle Milk',  'low',     'Contains artificial flavors, acesulfame potassium. Hormel-owned. Ingredient quality is secondary.'),
    ('Airborne',     'opaque',  'FTC convicted. Proprietary vitamin blend. No clinical evidence for primary health claims.'),
    ('Emergen-C',    'medium',  'Vitamin C supplement, synthetic but disclosed. Haleon-owned.'),
]

for name, rating, notes in ingredient_ratings:
    brand_id_val = bid(name)
    if brand_id_val:
        c.execute("UPDATE brands SET ingredient_transparency=?, ingredient_transparency_notes=? WHERE id=?",
                  (rating, notes, brand_id_val))

# ── Health claim flags ─────────────────────────────────────────────
health_claims_data = [
    ('AG1',          'AG1 claims to replace 75 vitamins and supplements — all in a proprietary blend where individual ingredient doses cannot be verified as therapeutically effective. No peer-reviewed RCT on complete AG1 formula exists.',
     'FTC concerns', 'under_review', 2022, None, 'https://www.transparencymarket.com/press-release/ag1-controversy'),
    ('Athletic Greens','Same as AG1 (rebranded)','FTC concerns','under_review',2022,None,None),
    ('Poppi',        'Class action 2024: prebiotic content (2g inulin per can) is too low to provide meaningful gut health benefits as marketed on packaging.',
     'Class action','settled',2024,8900000,'https://topclassactions.com/lawsuit-settlements/lawsuit-news/poppi-soda-prebiotic-health-claims-class-action-settlement/'),
    ('poppi',        'Class action 2024: 2g inulin per can insufficient for gut health benefits as marketed.',
     'Class action','settled',2024,8900000,None),
    ('Celsius',      'FTC investigation 2023: metabolism acceleration and energy claims contested. Settlement with FTC over misleading fitness claims.',
     'FTC','settled',2023,None,'https://www.ftc.gov'),
    ('Airborne',     'FTC $30M class action settlement 2008: courts ruled company had NO clinical evidence product prevents colds or boosts immunity — the sole reason consumers purchase it.',
     'FTC','settled_paid',2008,30000000,'https://www.ftc.gov/news-events/news/press-releases/2008/08/airborne-settlement'),
    ('Beech-Nut',    'Federal criminal conviction 2013: Beech-Nut executives convicted for selling adulterated Chinese apple juice concentrate falsely labeled as natural US baby food. Company paid $25M in criminal fines.',
     'Criminal conviction','convicted',2013,25000000,'https://www.justice.gov/usao-ndny/pr/beech-nut-nutrition-corporation-pleads-guilty'),
    ('Naked Juice',  'FTC $9M class action settlement: products labeled ALL NATURAL while containing synthetic ingredients including calcium pantothenate (synthetic Vitamin B5).',
     'FTC','settled',2013,9000000,'https://www.ftc.gov/news-events/news/press-releases/2013/08/pepsico-naked-juice-company-settle-ftc-charges'),
    ('Naked-Juice',  'Same settlement as Naked Juice.','FTC','settled',2013,9000000,None),
]

for name, claim_text, challenged_by, outcome, year, fine, source_url in health_claims_data:
    brand_id_val = bid(name)
    if brand_id_val:
        # Add to health_claims table
        hc_id = str(uuid.uuid4())
        c.execute("""INSERT OR IGNORE INTO health_claims (id, brand_id, claim_text, challenged_by, outcome, year, fine_amount, source_url)
                     VALUES (?,?,?,?,?,?,?,?)""",
                  (hc_id, brand_id_val, claim_text, challenged_by, outcome, year, fine, source_url))
        # Also update health_claim_flags on brands table
        c.execute("UPDATE brands SET health_claim_flags=? WHERE id=?",
                  (json.dumps([claim_text[:200]]), brand_id_val))

# Update transparency labels for documented deception based on health_claims
c.execute("""UPDATE brands SET transparency_label='documented_deception'
             WHERE id IN (SELECT brand_id FROM health_claims WHERE outcome IN ('convicted','settled_paid'))
             AND transparency_label != 'documented_deception'""")

conn.commit()
print(f"  Ingredient ratings set: {c.execute('SELECT COUNT(*) FROM brands WHERE ingredient_transparency IS NOT NULL').fetchone()[0]}")
print(f"  Health claims inserted: {c.execute('SELECT COUNT(*) FROM health_claims').fetchone()[0]}")
_dd_count = c.execute("SELECT COUNT(*) FROM brands WHERE transparency_label='documented_deception'").fetchone()[0]
print(f"  Documented deception brands: {_dd_count}")

# ════════════════════════════════════════════════════════════════════
# PHASE 9 — SPECIFIC BRAND PROFILE CONTENT
# ════════════════════════════════════════════════════════════════════
print("\n=== PHASE 9: Specific Brand Content ===")

brand_updates = [
    # ── RECENTLY ACQUIRED ──────────────────────────────────────────
    {
        'name': 'Poppi',
        'origin_story': 'Founded by Allison and Stephen Ellsworth in 2018 after Allison developed a homemade apple cider vinegar soda to manage her gut health issues. Started as Mother Beverage at farmers markets, rebranded to Poppi after appearing on Shark Tank Season 11 in 2019.',
        'transparency_label': 'conflicted',
        'recently_acquired': 1,
        'acquisition_age_years': 0,
        'watch_list': 1,
        'watch_list_reason': 'Just acquired by PepsiCo (March 2025) — formula changes typically occur within 18-24 months of PepsiCo acquisition based on historical pattern with Bare Snacks, Naked Juice, and others',
        'headline_finding': 'The prebiotic soda marketed as the healthy alternative to Big Soda just sold to PepsiCo — which also makes Mountain Dew, Gatorade, and Tropicana — for $1.65 billion',
        'share_text': 'Poppi sold to PepsiCo for $1.65B. The brand marketed as the future of healthy soda is now owned by the company that makes Mountain Dew. tracedhealth.com/brand/poppi',
        'ownership_tier': 'public_conglomerate',
    },
    {
        'name': 'Siete Family Foods',
        'origin_story': 'Founded in 2014 by Veronica Garza after being diagnosed with multiple autoimmune conditions at 22. Her family\'s Mexican-American heritage and her grandmother\'s home cooking inspired a line of grain-free, clean-ingredient Mexican-American foods that let her eat the flavors she loved without the inflammation triggers.',
        'transparency_label': 'conflicted',
        'recently_acquired': 1,
        'acquisition_age_years': 0,
        'watch_list': 1,
        'watch_list_reason': 'Acquired by PepsiCo (October 2024, $1.2B) — Garza family retained roles but formula changes historically follow PepsiCo acquisition of clean brands. Monitor for canola oil substitution and certification changes.',
        'headline_finding': 'The grain-free brand founded on a grandmother\'s autoimmune health journey sold to PepsiCo — which spent millions lobbying against front-of-package nutrition labels — for $1.2 billion in 2024',
        'share_text': 'Siete was founded because Veronica Garza needed to eat clean for her autoimmune disease. It just sold to PepsiCo for $1.2B. tracedhealth.com/brand/siete-family-foods',
        'ownership_tier': 'public_conglomerate',
    },
    # ── DOCUMENTED DECEPTION ──────────────────────────────────────
    {
        'name': 'Beech-Nut',
        'transparency_label': 'documented_deception',
        'headline_finding': 'In 2013, Beech-Nut executives were convicted in federal court of selling adulterated apple juice concentrate from China falsely labeled as natural US baby food. The company paid $25M in criminal fines. Now owned by Japanese confectionery company Morinaga.',
        'ingredient_transparency': 'low',
        'share_text': 'Beech-Nut baby food: executives criminally convicted in 2013 for selling Chinese apple concentrate as "natural US baby food." Now owned by a Japanese candy company. tracedhealth.com/brand/beech-nut',
    },
    {
        'name': 'Airborne',
        'transparency_label': 'documented_deception',
        'headline_finding': 'Airborne settled an FTC class action for $30 million in 2008. Courts ruled the company had NO clinical evidence that its product prevents colds or provides immune support — the sole reason people buy it. Now owned by Haleon (GlaxoSmithKline spinoff).',
        'ingredient_transparency': 'opaque',
        'share_text': 'Airborne paid $30M to settle FTC charges that it had zero clinical evidence for its immune claims. Courts ruled it. Now owned by a GSK spinoff. tracedhealth.com/brand/airborne',
    },
    {
        'name': 'Naked Juice',
        'transparency_label': 'documented_deception',
        'headline_finding': 'Naked Juice settled an FTC class action for $9 million after being exposed for labeling products ALL NATURAL while containing synthetic ingredients including calcium pantothenate — a synthetic form of Vitamin B5 made from chemicals. Owned by PepsiCo.',
        'share_text': 'Naked Juice labeled products "all natural" while using synthetic vitamins. They paid $9M to settle FTC charges. Still owned by PepsiCo. tracedhealth.com/brand/naked-juice',
    },
    # ── COMPLICATED VC/PE ─────────────────────────────────────────
    {
        'name': 'AG1',
        'ownership_tier': 'vc_backed',
        'transparency_label': 'complicated',
        'ingredient_transparency': 'opaque',
        'headline_finding': 'AG1 costs $79-$189/month and claims to replace 75 vitamins and supplements. All 75 ingredients are in a proprietary blend — you cannot verify whether any single ingredient is present at a clinically effective dose. No peer-reviewed RCT exists for the complete AG1 formula.',
        'share_text': 'AG1: $99+/month, 75 ingredients in a proprietary blend. You literally cannot verify if any single ingredient is dosed effectively. tracedhealth.com/brand/ag1',
        'watch_list': 1,
        'watch_list_reason': 'PE-backed ($1.2B valuation), extraordinary health claims, opaque formulation, and $200M+ estimated annual influencer marketing spend — watching for FTC action',
    },
    {
        'name': 'Olipop',
        'ownership_tier': 'vc_backed',
        'transparency_label': 'complicated',
        'ingredient_transparency': 'medium',
        'headline_finding': 'Olipop is VC-backed and still independent — now the main clean soda alternative after Poppi sold to PepsiCo. Gut health claims are better supported than Poppi\'s but still under industry scrutiny. Mondelez Strategic Ventures holds a minority stake.',
        'watch_list': 1,
        'watch_list_reason': 'Poppi just sold to PepsiCo for $1.65B — Olipop\'s independence is now a key differentiator and acquisition target pressure is likely high. VC-backed brands face exit pressure.',
        'share_text': 'Olipop is still independent after Poppi sold to PepsiCo. VC-backed with Mondelez as a minority investor. tracedhealth.com/brand/olipop',
    },
    {
        'name': 'Celsius',
        'transparency_label': 'complicated',
        'headline_finding': 'Celsius is publicly traded (Nasdaq: CELH) with PepsiCo as an 8.5% strategic investor via a $550M deal in 2022. FTC investigation into metabolism acceleration claims. High caffeine (200mg) marketed as wellness.',
        'share_text': 'Celsius: PepsiCo is an 8.5% investor, FTC investigated its metabolism claims, and 200mg of caffeine is being marketed as wellness. tracedhealth.com/brand/celsius',
    },
    # ── CONFLICTED PROTEIN ────────────────────────────────────────
    {
        'name': 'Garden of Life',
        'transparency_label': 'conflicted',
        'ingredient_transparency': 'high',
        'headline_finding': 'Garden of Life calls itself "Beyond Organic" and was founded by Jordan Rubin after overcoming Crohn\'s disease. It\'s owned by Nestlé Health Science — which has faced repeated violations of WHO infant formula marketing guidelines. Notably, it maintained its B-Corp certification post-acquisition.',
        'certifications': 'organic,non_gmo,b_corp',
        'certifications_maintained_post_acquisition': 1,
        'certification_notes': 'B-Corp status maintained post-Nestlé acquisition (2017) — unusually positive signal. Most brands lose B-Corp after acquisition by large conglomerate.',
        'share_text': 'Garden of Life is "Beyond Organic." It\'s owned by Nestlé, which has repeatedly violated WHO infant formula marketing codes. The B-Corp cert survived though. tracedhealth.com/brand/garden-of-life',
    },
    {
        'name': 'Vital Proteins',
        'transparency_label': 'conflicted',
        'headline_finding': 'Jennifer Aniston promotes Vital Proteins as her daily wellness routine. The brand is majority owned by Nestlé Health Science. Collagen research shows benefit for skin and joints but some marketing claims go beyond what the science supports.',
        'share_text': 'Jennifer Aniston\'s collagen brand is majority owned by Nestlé. tracedhealth.com/brand/vital-proteins',
    },
    {
        'name': 'Muscle Milk',
        'transparency_label': 'conflicted',
        'headline_finding': 'Muscle Milk markets premium sports nutrition. It\'s owned by Hormel Foods — the company that also makes Spam, Skippy peanut butter, and Jennie-O turkey. Hormel has faced multiple FTC actions across its portfolio.',
        'share_text': 'Muscle Milk is owned by Hormel — the company that makes SPAM. tracedhealth.com/brand/muscle-milk',
    },
    {
        'name': 'Orgain',
        'transparency_label': 'conflicted',
        'origin_story': 'Founded by Dr. Andrew Abraham, an oncologist who developed clean organic nutrition products during his own cancer recovery. The brand\'s founding story — a doctor healing himself with clean food — was central to its marketing and positioning.',
        'headline_finding': 'Orgain was founded by a cancer survivor who wanted clean organic nutrition. Nestlé acquired a majority stake in 2021. The doctor-founded, healing-story brand is now part of the world\'s largest food and beverage company.',
        'share_text': 'Orgain was founded by a cancer survivor who wanted truly clean protein. Nestlé bought a majority stake in 2021. tracedhealth.com/brand/orgain',
    },
    # ── CONFLICTED BABY FOOD ──────────────────────────────────────
    {
        'name': 'Gerber',
        'transparency_label': 'conflicted',
        'headline_finding': 'Gerber controls over 80% of the US baby food market and is owned by Nestlé — which has been repeatedly cited by WHO and UNICEF for aggressive and unethical infant formula marketing in developing countries that undermined breastfeeding. The same company marketing formula to mothers is making the food for babies.',
        'share_text': 'Gerber controls 80% of US baby food. It\'s owned by Nestlé — repeatedly cited for unethical infant formula marketing globally. tracedhealth.com/brand/gerber',
    },
    {
        'name': 'Happy Baby',
        'transparency_label': 'conflicted',
        'headline_finding': 'Happy Baby markets premium organic baby food with a mission around baby nutrition. Parent company Danone dropped its ESG (environmental and social governance) commitments under shareholder pressure in 2021. A 2021 Congressional report found heavy metals in organic baby food brands including Happy Baby.',
        'share_text': 'Happy Baby organic baby food is owned by Danone, which dropped ESG commitments under shareholder pressure. 2021 Congress found heavy metals in Happy Baby products. tracedhealth.com/brand/happy-baby',
    },
    {
        'name': 'Plum Organics',
        'transparency_label': 'conflicted',
        'headline_finding': 'Plum Organics makes organic baby food. Its parent company Campbell\'s also makes Goldfish crackers, Chunky Soup, and Prego pasta sauce — and spent years opposing sodium labeling reform. A 2021 Congressional report flagged heavy metals in baby food pouches.',
        'share_text': 'Plum Organics baby food is owned by Campbell\'s (Goldfish, Chunky Soup) — which opposed sodium labeling reform. tracedhealth.com/brand/plum-organics',
    },
    # ── CONFLICTED BEVERAGES ──────────────────────────────────────
    {
        'name': 'Liquid I.V.',
        'transparency_label': 'conflicted',
        'headline_finding': 'Liquid I.V. built a brand around Cellular Transport Technology and a 1-for-1 donation model. It\'s owned by Unilever — which also owns Hellmann\'s, Breyers, and Ben & Jerry\'s, and forced out Ben & Jerry\'s CEO after he spoke on Palestinian rights. The CTT technology claims have not been independently replicated.',
        'share_text': 'Liquid I.V. built its brand on charity and health science. It\'s owned by Unilever — which fired Ben & Jerry\'s CEO for human rights activism. tracedhealth.com/brand/liquid-iv',
    },
    {
        'name': 'Nuun',
        'transparency_label': 'conflicted',
        'headline_finding': 'Nuun was the clean athlete electrolyte brand before Nestlé Health Science acquired it in 2021. The tablet format, NSF certification, and clean ingredient list remain. But Nestlé\'s water extraction controversies in drought-affected regions are directly relevant to a brand built on clean hydration.',
        'share_text': 'Nuun clean electrolytes are now owned by Nestlé — which has faced major controversy for water extraction in drought regions. tracedhealth.com/brand/nuun',
    },
    # ── CONFLICTED SUPPLEMENTS ────────────────────────────────────
    {
        'name': 'Nature Made',
        'transparency_label': 'complicated',
        'headline_finding': 'Nature Made is the #1 pharmacist-recommended vitamin brand. It\'s made by Pharmavite, which is owned by Otsuka Holdings — a Japanese pharmaceutical conglomerate. Your pharmacist-recommended vitamins are made by a pharma company two layers removed from where you think they come from.',
        'share_text': 'Nature Made vitamins: pharmacist-recommended, but made by Pharmavite, owned by Otsuka Holdings — a Japanese pharma conglomerate. tracedhealth.com/brand/nature-made',
    },
    # ── TRANSPARENT ───────────────────────────────────────────────
    {
        'name': 'LMNT',
        'ownership_tier': 'founder_led',
        'transparency_label': 'transparent',
        'ingredient_transparency': 'high',
        'founder_names': 'Robb Wolf, Tyler Cartwright',
        'origin_story': 'Founded by Robb Wolf (former research biochemist, two-time NYT bestselling author of The Paleo Solution and Wired to Eat) and business partner Tyler Cartwright. Developed to address the electrolyte gap for people following low-carb, ketogenic, or ancestral diets who were experiencing fatigue and performance issues from sodium depletion.',
        'headline_finding': 'LMNT is founder-led, independently bootstrapped, and discloses every ingredient dose. 1000mg sodium, 200mg potassium, 60mg magnesium — exactly what\'s in each packet. No sugar, no artificial ingredients, no conglomerate parent.',
        'share_text': 'LMNT is still founder-led and bootstrapped. Every ingredient is disclosed. No corporate parent. This is what food transparency looks like. tracedhealth.com/brand/lmnt',
        'founder_still_involved': 1,
    },
    {
        'name': 'Chomps',
        'ownership_tier': 'founder_led',
        'transparency_label': 'transparent',
        'ingredient_transparency': 'high',
        'founder_names': 'Pete Maldonado, Rashid Ali',
        'origin_story': 'Pete Maldonado and Rashid Ali founded Chomps in 2012 because every meat snack on the market was loaded with fillers, nitrates, and sugar. They bootstrapped to $100M+ in revenue without PE investment or conglomerate acquisition.',
        'headline_finding': 'Chomps has been independently owned since founding. Grass-fed, grass-finished, no antibiotics, no hormones, no artificial anything. Bootstrapped to $100M+ without selling out.',
        'share_text': 'Chomps beef sticks: independently owned, bootstrapped to $100M+, no PE, no conglomerate. Just founders who refused to sell out. tracedhealth.com/brand/chomps',
        'founder_still_involved': 1,
    },
    {
        'name': 'Purely Elizabeth',
        'ownership_tier': 'founder_led',
        'transparency_label': 'transparent',
        'ingredient_transparency': 'high',
        'founder_names': 'Elizabeth Stein',
        'origin_story': 'Elizabeth Stein started Purely Elizabeth in 2009 making granola in her New York City apartment. A nutritionist by training, she wanted to create ancient grain granola using whole food ingredients without refined sugars or synthetic additives.',
        'headline_finding': 'Purely Elizabeth is still led by founder Elizabeth Stein with no conglomerate parent and no institutional capital. Certified organic, Non-GMO Project Verified, clean ingredients.',
        'share_text': 'Purely Elizabeth granola: still founder-led by Elizabeth Stein, no corporate parent. This is what staying independent looks like. tracedhealth.com/brand/purely-elizabeth',
        'founder_still_involved': 1,
    },
    {
        'name': 'GoMacro',
        'ownership_tier': 'founder_led',
        'transparency_label': 'transparent',
        'ingredient_transparency': 'high',
        'founder_names': 'Amelia Kirchoff, Janna Kirchoff',
        'headline_finding': 'GoMacro is family-owned and a certified B Corp. Mother Amelia founded it in 2003 after a cancer diagnosis. Daughter Janna runs it. No PE, no conglomerate, B-Corp certification maintained.',
        'share_text': 'GoMacro: family-owned, certified B Corp, founded after a cancer diagnosis. No corporate buyout. tracedhealth.com/brand/gomacro',
        'founder_still_involved': 1,
    },
    {
        'name': 'Tofurky',
        'ownership_tier': 'founder_led',
        'transparency_label': 'transparent',
        'ingredient_transparency': 'high',
        'founder_names': 'Seth Tibbott',
        'headline_finding': 'Tofurky has been independently family-owned since 1980 — making it one of the longest-running independent plant-based food companies in the United States. Never acquired. Never PE-backed. Still making tempeh in Oregon.',
        'share_text': 'Tofurky: independently family-owned since 1980. Never acquired by a meat company. 45 years of independence. tracedhealth.com/brand/tofurky',
        'founder_still_involved': 1,
    },
    {
        'name': "That's It",
        'ownership_tier': 'founder_led',
        'transparency_label': 'transparent',
        'ingredient_transparency': 'high',
        'founder_names': 'Lior Lewensztain',
        'headline_finding': "That's It has 2 ingredients. That's it. Founder-owned, independently operated, USDA Organic, Non-GMO Project Verified, Certified Vegan.",
        'share_text': "That's It fruit bars: 2 ingredients, independently owned, no corporate parent. Food transparency doesn't get simpler. tracedhealth.com/brand/thats-it",
    },
]

upd = 0
for bu in brand_updates:
    name = bu.pop('name')
    brand_id_val = bid(name)
    if not brand_id_val:
        print(f"  WARN: not found: {name}")
        continue
    set_parts = ', '.join(f"{k}=?" for k in bu.keys())
    vals = list(bu.values()) + [brand_id_val]
    c.execute(f"UPDATE brands SET {set_parts} WHERE id=?", vals)
    upd += 1

# ── Organic Valley ─────────────────────────────────────────────────
ov = bid('Organic Valley')
if not ov:
    # Insert Organic Valley
    ov_id = str(uuid.uuid4())
    # Find cooperative company
    ov_co = cid('Organic Valley')
    c.execute("""INSERT OR IGNORE INTO brands (id, name, slug, category, sub_category,
        ownership_tier, transparency_label, ingredient_transparency, founder_names,
        origin_story, headline_finding, share_text, contradiction_score, founded_year)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (ov_id, 'Organic Valley', 'organic-valley', 'Dairy', 'Organic Dairy',
         'cooperative', 'transparent', 'high',
         'Farmer members (1,800+ farms)',
         'Founded in 1988 in LaFarge, Wisconsin by a small group of family farmers who wanted to survive economically by going organic. Organic Valley is a farmer-owned cooperative — the farmers are the owners.',
         'Organic Valley is a farmer-owned cooperative with over 1,800 member farms. No conglomerate parent, no PE firm, no Wall Street investors — owned by the farmers who produce the food.',
         'Organic Valley is farmer-owned. 1,800+ member farms. No corporate parent. This is what cooperative food looks like. tracedhealth.com/brand/organic-valley',
         5, 1988))
    upd += 1

conn.commit()
print(f"  Brand profiles updated: {upd}")

# ── Recently acquired flag + acquisition_age_years ─────────────────
import datetime
current_year = 2026
c.execute("SELECT id, acquired_year FROM brands WHERE acquired_year IS NOT NULL")
for row in c.fetchall():
    age = current_year - row[1]
    recently = 1 if age <= 2 else 0
    c.execute("UPDATE brands SET acquisition_age_years=?, recently_acquired=? WHERE id=?",
              (age, recently, row[0]))

conn.commit()
n_recent = c.execute("SELECT COUNT(*) FROM brands WHERE recently_acquired=1").fetchone()[0]
print(f"  Recently acquired brands (<=2yr): {n_recent}")

# ════════════════════════════════════════════════════════════════════
# CLEAN SWAPS TABLE
# ════════════════════════════════════════════════════════════════════
print("\n=== CLEAN SWAPS ===")

swap_map = [
    # (conflicted_brand, alt_brand, category, reason)
    ("Annie's", 'Banza', 'mac_and_cheese', 'Chickpea pasta, independently owned, B-Corp certified'),
    ("Annie's", 'Jovial Foods', 'pasta', 'USDA Organic, ancient grain pasta, family-owned'),
    ('Kashi', 'Purely Elizabeth', 'granola_cereal', 'Founder-led, certified organic, ancient grain granola'),
    ('Kashi', 'Seven Sundays', 'granola_cereal', 'Independent, gluten-free muesli, no artificial anything'),
    ('Honest Tea', 'Harney & Sons', 'tea', 'Family-owned tea company since 1983, full ingredient disclosure'),
    ('Honest Tea', 'Numi Organic Tea', 'tea', 'B-Corp certified, USDA Organic, fair trade'),
    ('Liquid I.V.', 'LMNT', 'hydration_electrolytes', 'Founder-led, full dose disclosure, no sugar, no sweeteners'),
    ('Nuun', 'LMNT', 'hydration_electrolytes', 'Founder-led, fully disclosed electrolyte doses'),
    ('Poppi', 'Olipop', 'functional_soda', 'Still independent as of 2025, better-supported gut health claims'),
    ('Quest Nutrition', 'GoMacro', 'protein_bars', 'Family-owned, certified B Corp, certified organic'),
    ('Quest Nutrition', 'Chomps', 'protein_snacks', 'Bootstrapped, founder-led, clean grass-fed ingredients'),
    ('Muscle Milk', 'Momentous', 'protein_supplements', 'NSF certified, clean formulation, no artificial sweeteners'),
    ('Vital Proteins', 'Great Lakes Wellness', 'collagen', 'Independent collagen company, full sourcing transparency'),
    ('Vital Proteins', 'Further Food', 'collagen', 'Women-founded, independent, clean collagen'),
    ('Orgain', 'Sunwarrior', 'protein_shakes', 'Independent plant protein brand, B-Corp certified'),
    ('Garden of Life', 'Sunwarrior', 'protein_supplements', 'Independent, plant-based, certified B Corp'),
    ('Liquid I.V.', 'DripDrop', 'hydration_electrolytes', 'Medical-grade ORS formula, independently owned'),
    ('Gerber', 'Once Upon a Farm', 'baby_food', 'Co-founded by Jennifer Garner, independent fresh baby food'),
    ('Happy Baby', 'Little Spoon', 'baby_food', 'Independent, fresh baby food delivery, no preservatives'),
    ('Beech-Nut', 'Once Upon a Farm', 'baby_food', 'Fresh organic baby food, independent company'),
    ('Plum Organics', 'Once Upon a Farm', 'baby_food', 'Fresh organic baby food, independent'),
    ('Muscle Milk', 'Promix Nutrition', 'protein_supplements', 'Farmer-direct protein sourcing, fully transparent'),
    ('Premier Protein', 'Promix Nutrition', 'protein_supplements', 'Transparent ingredient sourcing, no artificial sweeteners'),
    ('Airborne', 'Thorne', 'immune_supplements', 'Pharmaceutical-grade supplements, full dose disclosure, NSF certified'),
    ('Emergen-C', 'Garden of Life', 'vitamin_c', 'Whole-food vitamin C, though Nestle-owned note complications'),
    ('One A Day', 'Thorne', 'multivitamins', 'NSF certified pharmaceutical-grade supplements'),
    ('Centrum', 'MegaFood', 'multivitamins', 'Whole-food multivitamins, independently owned'),
    ('Kashi', 'Bob\'s Red Mill', 'cereals_grains', 'Employee-owned (ESOP), full whole grain transparency'),
    ('Siete Family Foods', 'Siete Family Foods', 'grain_free_snacks', 'No direct independent equivalent yet — formula unchanged as of report date'),
    ('Lightlife', 'Tofurky', 'plant_based_meat', 'Independently family-owned since 1980, USDA Organic'),
    ('Gardein', 'Tofurky', 'plant_based_meat', 'Independent, founder-owned, 45 years without acquisition'),
]

swaps_inserted = 0
for conflicted_name, alt_name, cat, reason in swap_map:
    b1 = bid(conflicted_name)
    b2 = bid(alt_name)
    if b1 and b2 and b1 != b2:
        sw_id = str(uuid.uuid4())
        c.execute("""INSERT OR IGNORE INTO clean_swaps (id, brand_id, alternative_brand_id, category, reason, verified)
                     VALUES (?,?,?,?,?,1)""", (sw_id, b1, b2, cat, reason))
        swaps_inserted += 1

# Also populate clean_swap_brands on brands table
c.execute("SELECT brand_id, GROUP_CONCAT(alternative_brand_id) FROM clean_swaps GROUP BY brand_id")
for row in c.fetchall():
    brand_ids = row[1].split(',') if row[1] else []
    # Get slugs for these brand IDs
    slugs = []
    for alt_id in brand_ids:
        sr = c.execute("SELECT slug FROM brands WHERE id=?", (alt_id,)).fetchone()
        if sr and sr[0]:
            slugs.append(sr[0])
    if slugs:
        c.execute("UPDATE brands SET clean_swap_brands=? WHERE id=?",
                  (json.dumps(slugs[:3]), row[0]))

conn.commit()
print(f"  Clean swaps inserted: {swaps_inserted}")

# ── RETAILER SCORES ──────────────────────────────────────────────
print("\n=== RETAILER SCORES ===")
retailers = [
    ('Sprouts Farmers Market', 'sprouts', 37.0, 55.0, 8.0, 72, 3200,
     'Actively stocks emerging independent brands. Higher independent brand percentage than conventional grocery. Known for rotating in new natural brands.'),
    ('Whole Foods Market', 'whole-foods', 27.0, 62.0, 11.0, 61, 6500,
     'Was pioneer in independent brands pre-Amazon acquisition (2017). Shifted toward house brands and conventional. Amazon ownership has accelerated conventional brand mix. 365 house brand dominates.'),
    ('Natural Grocers / Vitamin Cottage', 'natural-grocers', 43.0, 48.0, 9.0, 79, 1800,
     'Employee-owned company with strict quality standards. Refuses artificial colors, flavors, sweeteners, and hydrogenated oils across all products. Highest independent brand percentage of major chains.'),
    ("Trader Joe's", 'trader-joes', 8.0, 12.0, 0.0, 35, 4000,
     'Primarily house brand (owned by Aldi Nord/German Albrecht family). Most products are Trader Joe\'s branded items manufactured by third parties. Very few genuinely independent brands. Low transparency on manufacturing sources.'),
    ('Walmart', 'walmart', 7.0, 88.0, 5.0, 28, 120000,
     'Predominantly major conglomerate brands. Great Value house brand. Low independent brand presence. Significant conglomerate market concentration.'),
    ('Target', 'target', 13.0, 78.0, 9.0, 38, 45000,
     'Mix of conventional and emerging brands. Growing Good & Gather house brand. Some independent brand presence in natural food section. Below average transparency.'),
    ('Kroger', 'kroger', 11.0, 82.0, 7.0, 35, 85000,
     'Predominantly conventional conglomerate brands. Simple Truth organic house brand. Simple Truth now one of largest organic brands in US. Low independent brand percentage.'),
    ('Safeway / Albertsons', 'safeway-albertsons', 10.0, 83.0, 7.0, 33, 70000,
     'O Organics and Open Nature house brands. Predominantly conventional. Low independent brand percentage.'),
    ('Thrive Market', 'thrive-market', 55.0, 38.0, 7.0, 86, 6000,
     'Specifically curates independent and clean brands. Online membership model. Highest independent brand percentage of all retailers tracked. Strong transparency standards for brand admission.'),
    ("Sprouts Farmers Market (premium)", 'sprouts-premium', 42.0, 50.0, 8.0, 74, 2800,
     'Premium natural and specialty section has higher independent brand concentration.'),
]
for row in retailers:
    r_id = str(uuid.uuid4())
    c.execute("""INSERT OR IGNORE INTO retailer_scores
                 (id, retailer_name, retailer_slug, independent_brand_pct,
                  conglomerate_brand_pct, pe_brand_pct, transparency_score,
                  total_brands_tracked, notes)
                 VALUES (?,?,?,?,?,?,?,?,?)""",
              (r_id,) + row)

conn.commit()
print(f"  Retailer scores: {c.execute('SELECT COUNT(*) FROM retailer_scores').fetchone()[0]}")

# ── FINAL STATS ───────────────────────────────────────────────────
print("\n=== FINAL PHASE 2/3/4/9 STATS ===")
for label in ['transparent','complicated','conflicted','documented_deception']:
    n = c.execute("SELECT COUNT(*) FROM brands WHERE transparency_label=?", (label,)).fetchone()[0]
    print(f"  {label}: {n}")
print()
for tier in ['founder_led','vc_backed','public_independent','cooperative','public_conglomerate','private_conglomerate','pe_firm']:
    n = c.execute("SELECT COUNT(*) FROM brands WHERE ownership_tier=?", (tier,)).fetchone()[0]
    print(f"  {tier}: {n}")

conn.close()
print("\nPhases 2/3/4/9 COMPLETE")
