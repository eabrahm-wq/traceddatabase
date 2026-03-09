#!/usr/bin/env python3
"""
seed_v3.py — Adds fast food chains + SF indie brands + enriches aliases
Run from: ~/Desktop/traceddatabase/
"""
import sqlite3, re, os, sys

DB = '/Users/evan/Desktop/Traceddatabase/.claude/worktrees/bold-johnson/traced.db'

# ─── normalize (mirrors traced_resolver.py) ───────────────────────────────────
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

conn = sqlite3.connect(DB)
c = conn.cursor()

print("=== seed_v3: fast food chains + SF indie brands ===\n")

# ═══════════════════════════════════════════════════════════════════════════════
# 1. NEW COMPANIES
# ═══════════════════════════════════════════════════════════════════════════════
print("--- Companies ---")
companies = [
    {
        'id': 'dominos-corp',
        'name': "Domino's Pizza Inc.",
        'type': 'public',
        'ticker': 'DPZ',
        'hq_country': 'US',
        'annual_revenue': 4500000000,
        'violation_count': 8,
        'violation_summary': "Wage theft settlements in multiple states. Franchise model creates accountability gaps — corporate blames franchisees for labor violations. 2022: class action over delivery driver wage theft.",
        'lobbying_annual': 1800000,
        'lobbying_issues': 'minimum wage legislation, franchise regulation, food delivery regulation',
        'description': "World's largest pizza delivery chain by revenue. Public company (NYSE:DPZ). 19,000+ franchise locations globally. Tech-forward delivery model.",
    },
    {
        'id': 'papa-johns-corp',
        'name': "Papa John's International",
        'type': 'pe',
        'ticker': 'PZZA',
        'hq_country': 'US',
        'annual_revenue': 2100000000,
        'violation_count': 15,
        'violation_summary': "Founder John Schnatter ousted 2018 after racial slur controversy. Starboard Value PE acquired significant stake. Multiple franchise labor violations. Class action re: misleading 'better ingredients' claims.",
        'lobbying_annual': 890000,
        'lobbying_issues': 'minimum wage, franchise regulation, food labeling',
        'description': "National pizza chain. Substantially PE-influenced by Starboard Value. Founded 1984 by John Schnatter in Jeffersonville IN. Post-founder controversy brand has struggled for identity.",
    },
]

for co in companies:
    c.execute("""INSERT OR IGNORE INTO companies
        (id, name, type, ticker, hq_country, annual_revenue,
         violation_count, violation_summary, lobbying_annual, lobbying_issues, description)
        VALUES (:id,:name,:type,:ticker,:hq_country,:annual_revenue,
                :violation_count,:violation_summary,:lobbying_annual,:lobbying_issues,:description)""", co)
    print(f"  {'NEW' if c.rowcount else 'skip'}: company {co['id']}")

# ═══════════════════════════════════════════════════════════════════════════════
# 2. NEW BRAND RECORDS — FAST FOOD CHAINS
# ═══════════════════════════════════════════════════════════════════════════════
print("\n--- Fast Food Chain Brands ---")
chain_brands = [
    {
        'id': 'subway',
        'name': 'Subway',
        'slug': 'subway',
        'parent_company_id': 'subway-restaurants',
        'category': 'restaurant',
        'format': 'fast_casual',
        'price_tier': 1,
        'independent': 0,
        'pe_owned': 1,
        'overall_zone': 'red',
        'founded_year': 1965,
        'acquired_year': 2023,
        'headline_finding': "Subway sold to Roark Capital (PE) in 2023 for $9.55B — the largest restaurant acquisition ever. Same PE firm owns Arby's, Buffalo Wild Wings, and Sonic. That footlong funds private equity.",
        'share_text': "Subway is now owned by Roark Capital PE ($9.55B deal, 2023). The 'fresh' sub chain is now a PE portfolio company alongside Arby's and Sonic.",
        'founder_story': "Founded 1965 by 17-year-old Fred DeLuca and family friend Peter Buck in Bridgeport CT. DeLuca borrowed $1,000 to open the first sandwich shop. Grew to the world's largest restaurant chain by location count (37,000+). After DeLuca's death from leukemia in 2015, the founding family sold to Roark Capital PE in 2023 for $9.55 billion — the largest restaurant acquisition in history.",
        'ingredient_drift': 1,
        'ingredient_drift_note': "2014: Subway bread found to contain azodicarbonamide (used in yoga mats) — removed after public pressure. Franchise model creates inconsistent ingredient sourcing. 'Tuna lawsuit' (2021) raised questions about tuna content.",
        'watch_list': 1,
    },
    {
        'id': 'in-n-out',
        'name': 'In-N-Out Burger',
        'slug': 'in-n-out',
        'parent_company_id': 'in-n-out',
        'category': 'restaurant',
        'format': 'fast_casual',
        'price_tier': 1,
        'independent': 0,
        'pe_owned': 0,
        'overall_zone': 'yellow',
        'founded_year': 1948,
        'headline_finding': "In-N-Out is privately owned by the Snyder family — descendants of founders Harry and Esther Snyder. Never been PE-backed. Known for above-average wages and no franchising.",
        'share_text': "In-N-Out is still owned by the Snyder family who founded it in 1948. One of the last major fast food chains that's genuinely family-owned.",
        'founder_story': "Founded 1948 by Harry and Esther Snyder in Baldwin Park CA — California's first drive-through burger stand. Passed to son Rich Snyder (died 1993), then grandson Guy Snyder (died 1999), and now 100% owned by granddaughter Lynsi Snyder. Menu has remained almost unchanged in 75 years. No franchising ever. Pays above-market wages for fast food. The Animal Style secret menu has become Bay Area lore.",
        'ingredient_drift': 0,
        'ingredient_drift_note': None,
        'watch_list': 0,
    },
    {
        'id': 'five-guys',
        'name': 'Five Guys',
        'slug': 'five-guys',
        'parent_company_id': 'five-guys',
        'category': 'restaurant',
        'format': 'fast_casual',
        'price_tier': 2,
        'independent': 0,
        'pe_owned': 0,
        'overall_zone': 'yellow',
        'founded_year': 1986,
        'headline_finding': "Five Guys is privately owned by the Murrell family. Premium pricing ($15+ for a burger) goes to a family business. Has turned down every acquisition offer.",
        'share_text': "Five Guys is still owned by Jerry Murrell and his five sons who founded it in 1986. 100% private, no PE.",
        'founder_story': "Founded 1986 by Jerry Murrell and his five sons (Janie, Matt, Chad, Ben, Tyler) in Arlington VA — literally named for the five boys. Started as a single location with fresh never-frozen beef and free peanuts. Stayed private through 1,700+ locations. Jerry Murrell has turned down every acquisition offer, including from McDonald's. Peanut oil only, fresh-cut fries, no freezers in kitchens.",
        'ingredient_drift': 0,
        'ingredient_drift_note': None,
        'watch_list': 0,
    },
    {
        'id': 'wingstop',
        'name': 'Wingstop',
        'slug': 'wingstop',
        'parent_company_id': 'wingstop-corp',
        'category': 'restaurant',
        'format': 'fast_casual',
        'price_tier': 1,
        'independent': 0,
        'pe_owned': 0,
        'overall_zone': 'yellow',
        'founded_year': 1994,
        'headline_finding': "Wingstop (NASDAQ:WING) is a public company. Despite the neighborhood feel, your wings fund public shareholders. Franchise model — most locations are operator-owned.",
        'share_text': "Wingstop is publicly traded (NASDAQ:WING). Public company, franchise model.",
        'founder_story': "Founded 1994 in Garland TX. Named for the aviation theme (1940s pilot décor). Went public on NASDAQ in 2015. Pure-play wing chain with 2,000+ locations. Franchise model — individual franchisees operate nearly all locations. Rick Ross (rapper) owns multiple franchises.",
        'ingredient_drift': 0,
        'ingredient_drift_note': None,
        'watch_list': 0,
    },
    {
        'id': 'dutch-bros',
        'name': 'Dutch Bros Coffee',
        'slug': 'dutch-bros',
        'parent_company_id': 'dutch-bros',
        'category': 'coffee',
        'format': 'cafe',
        'price_tier': 1,
        'independent': 0,
        'pe_owned': 0,
        'overall_zone': 'yellow',
        'founded_year': 1992,
        'headline_finding': "Dutch Bros (NYSE:BROS) went public in 2021, ending its indie chapter. Founded by Dutch immigrant brothers in a small Oregon town. Now a $10B+ public company with 900+ drive-thru locations.",
        'share_text': "Dutch Bros went public in 2021 (NYSE:BROS). Your cold brew now funds public shareholders — not the brothers who started it.",
        'founder_story': "Founded 1992 by brothers Dane and Travis Boersma in Grants Pass OR — Dutch immigrants who started with a pushcart espresso machine outside a coffee shop. Named their business after their heritage. Travis died of ALS in 2009. Dane honored him by continuing to grow the chain. Went public in September 2021 raising $484M. Known for enthusiastic 'bro' service culture and drive-thru-only model.",
        'ingredient_drift': 0,
        'ingredient_drift_note': None,
        'watch_list': 0,
    },
    {
        'id': 'chick-fil-a',
        'name': 'Chick-fil-A',
        'slug': 'chick-fil-a',
        'parent_company_id': 'chick-fil-a',
        'category': 'restaurant',
        'format': 'fast_casual',
        'price_tier': 1,
        'independent': 0,
        'pe_owned': 0,
        'overall_zone': 'yellow',
        'founded_year': 1946,
        'headline_finding': "Chick-fil-A is privately owned by the Cathy family. Has donated tens of millions to organizations opposing LGBTQ+ rights including Fellowship of Christian Athletes. Closed Sundays by religious conviction.",
        'share_text': "Chick-fil-A is Cathy family-owned and has donated millions to anti-LGBTQ+ groups. Your chicken sandwich funds those contributions.",
        'founder_story': "Founded 1946 by Truett Cathy in Hapeville GA as 'Dwarf Grill'. Rebranded as Chick-fil-A in 1967 after inventing the boneless chicken sandwich. Truett's son Dan Cathy serves as CEO. 100% privately held by the Cathy family with deep Baptist Christian identity. Sunday closures are non-negotiable policy. Known for franchise model where operators must be 'personally compatible' with company values.",
        'ingredient_drift': 0,
        'ingredient_drift_note': None,
        'watch_list': 1,
    },
    {
        'id': 'dominos',
        'name': "Domino's Pizza",
        'slug': 'dominos',
        'parent_company_id': 'dominos-corp',
        'category': 'restaurant',
        'format': 'fast_casual',
        'price_tier': 1,
        'independent': 0,
        'pe_owned': 0,
        'overall_zone': 'yellow',
        'founded_year': 1960,
        'headline_finding': "Domino's (NYSE:DPZ) is publicly traded. 8 wage violations across franchise network. Delivery driver pay has lagged inflation despite record profits. Tech investment ≠ worker investment.",
        'share_text': "Domino's is publicly traded (NYSE:DPZ). Franchise model, 8 wage violations, delivery driver wages lag behind profits.",
        'founder_story': "Founded 1960 by brothers Tom and James Monaghan in Ypsilanti MI. James traded his half for a used VW Beetle. Tom built it into the world's largest pizza delivery company. Sold to Bain Capital in 1998 for $1B, went public in 2004. Famous for the 30-minute delivery guarantee (discontinued 1993 after fatal accident lawsuits). Now operates on a tech-forward franchise model.",
        'ingredient_drift': 0,
        'ingredient_drift_note': None,
        'watch_list': 0,
    },
    {
        'id': 'papa-johns',
        'name': "Papa John's",
        'slug': 'papa-johns',
        'parent_company_id': 'papa-johns-corp',
        'category': 'restaurant',
        'format': 'fast_casual',
        'price_tier': 1,
        'independent': 0,
        'pe_owned': 1,
        'overall_zone': 'red',
        'founded_year': 1984,
        'acquired_year': 2019,
        'headline_finding': "Papa John's founder John Schnatter ousted 2018 after using racial slurs. Starboard Value PE took significant control in 2019. 15 labor violations. The 'better ingredients' brand has had the worst ingredients in its C-suite.",
        'share_text': "Papa John's founder was ousted for racist remarks. Starboard Value PE now controls the brand. 15 violations.",
        'founder_story': "Founded 1984 by John Schnatter ('Papa John') in Jeffersonville IN — he sold his prized 1971 Camaro Z28 to buy pizza equipment and converted a broom closet into a carry-out. Grew to 5,500+ locations. In 2018, Schnatter was caught using racial slurs on a media training call and blaming NFL player protests for sales decline. He resigned. Starboard Value PE acquired a major stake in 2019 and installed new management. The brand has struggled to recover.",
        'ingredient_drift': 1,
        'ingredient_drift_note': "Post-Schnatter era: 'Better Ingredients, Better Pizza' marketing has been deprioritized. PE cost-cutting pressure creates tension with premium positioning. Cheese blend sourcing has shifted.",
        'watch_list': 1,
    },
]

for b in chain_brands:
    c.execute("""INSERT OR IGNORE INTO brands
        (id, name, slug, parent_company_id, category, format,
         price_tier, independent, pe_owned, overall_zone, founded_year, acquired_year,
         headline_finding, share_text, founder_story, ingredient_drift, ingredient_drift_note, watch_list)
        VALUES (:id,:name,:slug,:parent_company_id,:category,:format,
                :price_tier,:independent,:pe_owned,:overall_zone,:founded_year,:acquired_year,
                :headline_finding,:share_text,:founder_story,:ingredient_drift,:ingredient_drift_note,:watch_list)""",
        {**b, 'acquired_year': b.get('acquired_year'), 'ingredient_drift_note': b.get('ingredient_drift_note')})
    print(f"  {'NEW' if c.rowcount else 'skip'}: brand {b['id']}")

# ═══════════════════════════════════════════════════════════════════════════════
# 3. NEW BRAND RECORDS — SF INDEPENDENTS
# ═══════════════════════════════════════════════════════════════════════════════
print("\n--- SF Independent Brands ---")
indie_brands = [
    {
        'id': 'humphry-slocombe',
        'name': 'Humphry Slocombe',
        'slug': 'humphry-slocombe',
        'parent_company_id': None,
        'category': 'restaurant',
        'format': 'fast_casual',
        'price_tier': 2,
        'independent': 1,
        'pe_owned': 0,
        'overall_zone': 'green',
        'founded_year': 2008,
        'headline_finding': "SF indie since 2008. Jake Godby and Sean Vahey's Mission District ice cream shop — Secret Breakfast (bourbon + corn flakes) put them on the map. Still independent, still weird, still SF.",
        'share_text': "Humphry Slocombe is SF indie ice cream since 2008 — Secret Breakfast, local dairy, founder-owned.",
        'founder_story': "Founded 2008 by pastry chef Jake Godby and front-of-house veteran Sean Vahey in the Mission District. Named after two British sitcom characters. Famous for adult flavors: Secret Breakfast (bourbon and corn flakes), Blue Bottle Vietnamese Coffee, Harvey Milk & Honey. Multiple SF locations. Won countless 'Best Ice Cream in SF' awards. Genuinely founder-owned and operated — never took outside investment.",
    },
    {
        'id': 'bi-rite-creamery',
        'name': 'Bi-Rite Creamery',
        'slug': 'bi-rite-creamery',
        'parent_company_id': None,
        'category': 'restaurant',
        'format': 'fast_casual',
        'price_tier': 2,
        'independent': 1,
        'pe_owned': 0,
        'overall_zone': 'green',
        'founded_year': 2006,
        'headline_finding': "Part of the SF-rooted Bi-Rite family. Across from Dolores Park. Salted caramel ice cream that defined a generation of SF food culture. Indie since 2006.",
        'share_text': "Bi-Rite Creamery is SF indie — salted caramel that defined a neighborhood, part of the Bi-Rite family since 2006.",
        'founder_story': "Opened 2006 by Sam Mogannam as the dessert extension of the Bi-Rite Market family at 3692 18th St, across from Dolores Park. Famous for salted caramel, honey lavender, and ricanelas (cinnamon) ice cream. Lines around the block on sunny Sundays. Small-batch production using local dairy from Strauss Family Creamery and other Bay Area farms. Part of the same family business that's anchored the Mission since 1964.",
    },
    {
        'id': 'tartine-bakery',
        'name': 'Tartine Bakery',
        'slug': 'tartine-bakery',
        'parent_company_id': None,
        'category': 'coffee',
        'format': 'cafe',
        'price_tier': 2,
        'independent': 1,
        'pe_owned': 0,
        'overall_zone': 'green',
        'founded_year': 2002,
        'headline_finding': "The ORIGINAL Tartine on 18th St — Chad Robertson and Liz Prueitt's 2002 bakery. Country loaf at 5pm, gone in an hour. Still independent. NOTE: Tartine Manufactory (Alabama St) is PE-backed — separate operation.",
        'share_text': "Tartine Bakery (original, 18th St) is SF indie — Chad Robertson's country loaf changed American bread culture.",
        'founder_story': "Founded 2002 by bakers Chad Robertson and Liz Prueitt at 600 Guerrero St, Mission District. Chad trained in France under master bakers. His country loaf — baked fresh at 5pm daily, sold out within an hour — became one of the most influential breads in American food culture. James Beard Award Outstanding Baker. IMPORTANT: This record covers the original 18th St bakery. Tartine Manufactory (Alabama St) is a separate, PE-backed operation not covered here.",
    },
    {
        'id': 'wise-sons',
        'name': 'Wise Sons Jewish Deli',
        'slug': 'wise-sons',
        'parent_company_id': None,
        'category': 'restaurant',
        'format': 'fast_casual',
        'price_tier': 2,
        'independent': 1,
        'pe_owned': 0,
        'overall_zone': 'green',
        'founded_year': 2011,
        'headline_finding': "SF's beloved Jewish deli since 2011. Evan Bloom and Leo Beckerman's house-cured pastrami and matzo ball soup. Real deli culture on the West Coast. Founder-owned.",
        'share_text': "Wise Sons is SF indie — real Jewish deli since 2011, house-cured pastrami, founder-owned by Evan Bloom and Leo Beckerman.",
        'founder_story': "Founded 2011 by Evan Bloom and Leo Beckerman, childhood friends from the East Bay who wanted to bring authentic Jewish deli culture to SF. Started as a pop-up at the SF Ferry Building. Known for house-cured pastrami, matzo ball soup, latkes, and babka. Multiple SF locations plus Tokyo. One of the only genuine Jewish delis on the West Coast.",
    },
    {
        'id': 'the-interval',
        'name': 'The Interval at Long Now',
        'slug': 'the-interval',
        'parent_company_id': None,
        'category': 'restaurant',
        'format': 'sit_down',
        'price_tier': 2,
        'independent': 1,
        'pe_owned': 0,
        'overall_zone': 'green',
        'founded_year': 2014,
        'headline_finding': "Bar-café inside the Long Now Foundation at Fort Mason. Nonprofit-adjacent. 3,500-book library, 10,000-Year Clock prototype. Probably the most intellectually interesting bar in SF.",
        'share_text': "The Interval is a nonprofit bar-café at Fort Mason — home of the Long Now Foundation. No PE, no shareholders.",
        'founder_story': "Opened 2014 as the physical home of the Long Now Foundation — founded by Stewart Brand, Brian Eno, Danny Hillis, and others — at Fort Mason Center. Part bar, part café, part library with 3,500+ curated books on long-term thinking. Houses working components of the 10,000-Year Clock and a mechanical Orrery. Operated to support the Long Now Foundation's mission of fostering long-term responsibility. No outside investors.",
    },
    {
        'id': '20th-century-cafe',
        'name': '20th Century Café',
        'slug': '20th-century-cafe',
        'parent_company_id': None,
        'category': 'coffee',
        'format': 'cafe',
        'price_tier': 2,
        'independent': 1,
        'pe_owned': 0,
        'overall_zone': 'green',
        'founded_year': 2013,
        'headline_finding': "Hayes Valley gem since 2013. Michelle Polzine's love letter to Viennese café culture — Russian honey cake, prune rugelach, mushroom toast. James Beard Outstanding Baker semifinalist.",
        'share_text': "20th Century Café is SF indie — Michelle Polzine's Eastern European pastry café in Hayes Valley since 2013.",
        'founder_story': "Founded 2013 by pastry chef Michelle Polzine in Hayes Valley, inspired by the grand cafés of Vienna, Prague, and Budapest. Famous for the Russian honey cake (medovik), prune rugelach, poppy seed roll, and savory mushroom toast. James Beard Award Outstanding Baker semifinalist multiple years. Small, intimate space that draws lines for weekend brunch. One of SF's most distinctive and wholly independent neighborhood gems.",
    },
    {
        'id': 'cockscomb-sf',
        'name': 'Cockscomb',
        'slug': 'cockscomb-sf',
        'parent_company_id': None,
        'category': 'restaurant',
        'format': 'sit_down',
        'price_tier': 3,
        'independent': 1,
        'pe_owned': 0,
        'overall_zone': 'green',
        'founded_year': 2014,
        'headline_finding': "SoMa nose-to-tail restaurant from James Beard chef Chris Cosentino. Whole animal butchery, offal-forward menu. Opened 2014. Founder-owned, no outside investment.",
        'share_text': "Cockscomb is Chris Cosentino's SF indie — whole animal, nose-to-tail cooking, founder-owned since 2014.",
        'founder_story': "Opened 2014 by James Beard Award-winning chef Chris Cosentino at 564 4th St in SoMa. Known for offal and whole-animal cooking — named for a cut of meat, not the plant. Menu changes daily based on what's available from local ranches and whole animal butchery. Cosentino is also known for Top Chef Masters. No outside investors — a true chef-owned restaurant in the classic SF tradition.",
    },
]

for b in indie_brands:
    c.execute("""INSERT OR IGNORE INTO brands
        (id, name, slug, parent_company_id, category, format,
         price_tier, independent, pe_owned, overall_zone, founded_year,
         headline_finding, share_text, founder_story)
        VALUES (:id,:name,:slug,:parent_company_id,:category,:format,
                :price_tier,:independent,:pe_owned,:overall_zone,:founded_year,
                :headline_finding,:share_text,:founder_story)""", b)
    print(f"  {'NEW' if c.rowcount else 'skip'}: indie {b['id']}")

# ═══════════════════════════════════════════════════════════════════════════════
# 4. LOCAL_VENDORS — new SF independents (skip wise-sons, already has lv)
# ═══════════════════════════════════════════════════════════════════════════════
print("\n--- Local Vendors ---")
new_vendors = [
    ('humphry-slocombe-lv', 'Humphry Slocombe', 'restaurant', 'fast_casual', 2,
     'Mission District',
     'Iconic SF indie ice cream — Secret Breakfast (bourbon cornflake), salted caramel. Founded 2008.',
     'humphry-slocombe', 1, 16, 12,
     'SF original since 2008. Wild flavors, local dairy. Founded by pastry chef Jake Godby and Sean Vahey.',
     'Local dairy sourcing from Bay Area farms, Strauss Family Creamery.'),
    ('bi-rite-creamery-lv', 'Bi-Rite Creamery', 'restaurant', 'fast_casual', 2,
     'Mission District',
     'Across from Dolores Park — salted caramel ice cream that defined SF food culture. Bi-Rite family.',
     'bi-rite-creamery', 1, 18, 15,
     "Part of the Bi-Rite family feeding the Mission since 1964. Small-batch daily production.",
     'Local and organic dairy from Strauss Family Creamery and Bay Area farms.'),
    ('tartine-bakery-lv', 'Tartine Bakery', 'coffee', 'cafe', 2,
     'Mission District',
     'The original 18th St location. Chad Robertson country loaf baked at 5pm — gone in an hour.',
     'tartine-bakery', 1, 22, 18,
     "Chad Robertson's country loaf changed American bread. Original 18th St only — not PE-backed Tartine Manufactory.",
     'Locally milled flour from Grist & Toll, seasonal produce from Bay Area farms.'),
    ('the-interval-lv', 'The Interval at Long Now', 'restaurant', 'sit_down', 2,
     'Fort Mason',
     'Bar-café at the Long Now Foundation. 3,500-book library, 10,000-year clock prototype. Best bar in SF?',
     'the-interval', 1, 10, 8,
     'Nonprofit-adjacent. Home of the Long Now Foundation — long-term thinking, great cocktails.',
     'Seasonal, local ingredients throughout the menu.'),
    ('20th-century-cafe-lv', '20th Century Café', 'coffee', 'cafe', 2,
     'Hayes Valley',
     'Eastern European pastry café. Russian honey cake, prune rugelach, mushroom toast. James Beard semifinalist.',
     '20th-century-cafe', 1, 11, 9,
     "Michelle Polzine's love letter to Vienna and Prague café culture. Hayes Valley gem since 2013.",
     'Local, seasonal ingredients throughout; butter from Straus Family Creamery.'),
    ('cockscomb-sf-lv', 'Cockscomb', 'restaurant', 'sit_down', 3,
     'SoMa',
     "Chris Cosentino's whole-animal SoMa restaurant. Nose-to-tail, offal-forward, menu changes daily.",
     'cockscomb-sf', 1, 10, 15,
     "James Beard chef Chris Cosentino's founder-owned nose-to-tail restaurant. No outside investors.",
     'Whole animal butchery from local and regional ranches.'),
]

for v in new_vendors:
    vid, name, cat, fmt, tier, hood, note, slug, verified, yrs, jobs, comm, src = v
    c.execute("""INSERT OR IGNORE INTO local_vendors
        (id, name, category, format, price_tier, neighborhood, note, slug,
         verified, years_open, local_jobs, community_note, sourcing_note)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (vid, name, cat, fmt, tier, hood, note, slug, verified, yrs, jobs, comm, src))
    print(f"  {'NEW' if c.rowcount else 'skip'}: vendor {vid}")

# ═══════════════════════════════════════════════════════════════════════════════
# 5. ALIASES — normalized, INSERT OR IGNORE
# ═══════════════════════════════════════════════════════════════════════════════
print("\n--- Aliases ---")
inserted = skipped = 0

def add(alias_raw, brand_id):
    global inserted, skipped
    n = normalize(alias_raw)
    c.execute("INSERT OR IGNORE INTO brand_aliases (alias_text, brand_id, source) VALUES (?,?,'seed_v3')", (n, brand_id))
    if c.rowcount:
        inserted += 1
    else:
        skipped += 1

# ── New fast food chains ──────────────────────────────────────────────────────
add("Subway", "subway")
add("Subway Restaurant", "subway")
add("Subway Sandwiches", "subway")
add("Subway Sandwich", "subway")

add("In-N-Out Burger", "in-n-out")
add("In-N-Out", "in-n-out")
add("In and Out Burger", "in-n-out")
add("InNOut Burger", "in-n-out")

add("Five Guys", "five-guys")
add("Five Guys Burgers and Fries", "five-guys")
add("Five Guys Burgers", "five-guys")
add("Five Guys Burger", "five-guys")

add("Wingstop", "wingstop")
add("Wing Stop", "wingstop")
add("Wingstop Restaurant", "wingstop")
add("Wingstop Wings", "wingstop")

add("Dutch Bros Coffee", "dutch-bros")
add("Dutch Bros", "dutch-bros")
add("Dutch Brothers Coffee", "dutch-bros")
add("Dutch Brothers", "dutch-bros")

add("Chick-fil-A", "chick-fil-a")
add("Chick Fil A", "chick-fil-a")
add("Chickfila", "chick-fil-a")
add("Chick-fil-A Restaurant", "chick-fil-a")

add("Domino's Pizza", "dominos")
add("Dominos Pizza", "dominos")
add("Domino's", "dominos")
add("Dominos", "dominos")

add("Papa John's Pizza", "papa-johns")
add("Papa Johns Pizza", "papa-johns")
add("Papa John's", "papa-johns")
add("Papa Johns", "papa-johns")

# ── Existing chains — enrich to 3+ ───────────────────────────────────────────
add("McDonald's", "mcdonalds")
add("McDonalds", "mcdonalds")
add("McDonald's Restaurant", "mcdonalds")
add("Mickey D's", "mcdonalds")
add("McDonald's Burgers", "mcdonalds")

add("Burger King", "burger-king")
add("BK", "burger-king")
add("Burger King Restaurant", "burger-king")
add("Burger King Grill", "burger-king")

add("Taco Bell", "taco-bell")
add("Taco Bell Restaurant", "taco-bell")
add("Taco Bell Cantina", "taco-bell")
add("Taco Bell Grill", "taco-bell")

add("KFC", "kfc")
add("Kentucky Fried Chicken", "kfc")
add("KFC Restaurant", "kfc")
add("KFC Chicken", "kfc")

add("Wendy's", "wendys")
add("Wendys", "wendys")
add("Wendy's Restaurant", "wendys")
add("Wendy's Old Fashioned Hamburgers", "wendys")

add("Dunkin'", "dunkin")
add("Dunkin Donuts", "dunkin")
add("Dunkin Coffee", "dunkin")
add("Dunkin' Donuts", "dunkin")
add("Dunkin' Coffee", "dunkin")

add("Tim Hortons", "tim-hortons")
add("Tim Horton's", "tim-hortons")
add("Tims", "tim-hortons")
add("Tim Hortons Coffee", "tim-hortons")
add("Tim Horton", "tim-hortons")

# ── Existing SF indie brands — enrich to 3+ ──────────────────────────────────
add("Burma Superstar", "burma-superstar")
add("Burma Super Star", "burma-superstar")
add("Burma Superstar Restaurant", "burma-superstar")
add("Burma Superstar Clement", "burma-superstar")

add("Dandelion Chocolate", "dandelion-chocolate")
add("Dandelion Chocolate Cafe", "dandelion-chocolate")
add("Dandelion Chocolate Factory", "dandelion-chocolate")
add("Dandelion Chocolate SF", "dandelion-chocolate")

add("Equator Coffees", "equator-coffees")
add("Equator Coffee", "equator-coffees")
add("Equator", "equator-coffees")
add("Equator Coffees and Teas", "equator-coffees")

add("Flour + Water", "flour-water-sf")
add("Flour Water", "flour-water-sf")
add("Flour and Water", "flour-water-sf")
add("Flour + Water Restaurant", "flour-water-sf")

add("Lazy Bear", "lazy-bear-sf")
add("Lazy Bear SF", "lazy-bear-sf")
add("Lazy Bear Restaurant", "lazy-bear-sf")
add("Lazy Bear Supper Club", "lazy-bear-sf")

add("Nopa", "nopa-brand")
add("Nopa Restaurant", "nopa-brand")
add("Nopa SF", "nopa-brand")
add("NoPa Kitchen", "nopa-brand")

add("Nopalito", "nopalito-sf")
add("Nopalito Restaurant", "nopalito-sf")
add("Nopalito SF", "nopalito-sf")
add("Nopalito Mexican", "nopalito-sf")

add("Rich Table", "rich-table-sf")
add("Rich Table Restaurant", "rich-table-sf")
add("Rich Table SF", "rich-table-sf")
add("Rich Table Hayes Valley", "rich-table-sf")

add("State Bird Provisions", "state-bird-brand")
add("State Bird", "state-bird-brand")
add("State Bird Provisions SF", "state-bird-brand")
add("State Bird Restaurant", "state-bird-brand")

add("Zuni Cafe", "zuni-cafe-brand")
add("Zuni Café", "zuni-cafe-brand")
add("Zuni Café SF", "zuni-cafe-brand")
add("Zuni", "zuni-cafe-brand")
add("Zuni Cafe SF", "zuni-cafe-brand")

add("Foreign Cinema", "foreign-cinema-brand")
add("Foreign Cinema Restaurant", "foreign-cinema-brand")
add("Foreign Cinema SF", "foreign-cinema-brand")
add("Foreign Cinema Mission", "foreign-cinema-brand")

# ── New SF indie brands ───────────────────────────────────────────────────────
add("Humphry Slocombe", "humphry-slocombe")
add("Humphry Slocombe Ice Cream", "humphry-slocombe")
add("Humphrey Slocombe", "humphry-slocombe")
add("Humphry Slocombe SF", "humphry-slocombe")

add("Bi-Rite Creamery", "bi-rite-creamery")
add("Birite Creamery", "bi-rite-creamery")
add("Bi Rite Creamery", "bi-rite-creamery")
add("Bi-Rite Ice Cream", "bi-rite-creamery")

add("Tartine Bakery", "tartine-bakery")
add("Tartine", "tartine-bakery")
add("Tartine Bakery SF", "tartine-bakery")
add("Tartine Bread", "tartine-bakery")

add("Wise Sons", "wise-sons")
add("Wise Sons Jewish Deli", "wise-sons")
add("Wise Sons Deli", "wise-sons")
add("Wise Sons Delicatessen", "wise-sons")

add("The Interval", "the-interval")
add("The Interval at Long Now", "the-interval")
add("Interval at Long Now", "the-interval")
add("Interval Long Now", "the-interval")

add("20th Century Cafe", "20th-century-cafe")
add("20th Century Café", "20th-century-cafe")
add("Twentieth Century Cafe", "20th-century-cafe")
add("20th Century Café Hayes Valley", "20th-century-cafe")

add("Cockscomb", "cockscomb-sf")
add("Cockscomb SF", "cockscomb-sf")
add("Cockscomb Restaurant", "cockscomb-sf")
add("Cockscomb SoMa", "cockscomb-sf")

conn.commit()
conn.close()
print(f"\n✓ seed_v3 complete: {inserted} aliases inserted, {skipped} skipped (conflicts/dupes)")
print("\nNext: copy DB to main repo, restart Flask, run resolver tests")
