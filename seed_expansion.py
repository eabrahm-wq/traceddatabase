#!/usr/bin/env python3
"""seed_expansion.py — SF brand coverage expansion
Adds: national chains (coffee/restaurant/grocery), SF independents, local vendors, aliases
Run: python3 seed_expansion.py
"""
import sqlite3, re, sys

DB = '/Users/evan/Desktop/Traceddatabase/traced.db'

def normalize(raw):
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

# ─────────────────────────────────────────────
# 1. SCHEMA ADDITIONS
# ─────────────────────────────────────────────
for sql in [
    "ALTER TABLE local_vendors ADD COLUMN years_open INTEGER",
    "ALTER TABLE local_vendors ADD COLUMN local_jobs INTEGER",
    "ALTER TABLE local_vendors ADD COLUMN community_note TEXT",
    "ALTER TABLE local_vendors ADD COLUMN sourcing_note TEXT",
]:
    try: c.execute(sql)
    except: pass

# ─────────────────────────────────────────────
# 2. PARENT COMPANIES
# ─────────────────────────────────────────────
COMPANIES = [
    ('starbucks-corp', 'Starbucks Corporation', 'public', 'SBUX', 'US', 36200000000, 26,
     'NLRB union-busting violations (200+ complaints since 2021), wage theft settlements, environmental violations for single-use plastic. CEO pay ratio 3,459:1 (2023). Fired hundreds of union organizers.',
     4600000, 'Labor law, food safety, environmental regulation, minimum wage, union rights',
     'Seattle-based global coffee chain, 36,000+ locations worldwide. Founded 1971. CEO Brian Niccol (ex-Chipotle) hired 2024 for $113M package to reverse declining sales.'),
    ('mcdonalds-corp', "McDonald's Corporation", 'public', 'MCD', 'US', 23200000000, 42,
     'Wage theft ($26M California settlement 2019), NLRB complaints, deforestation linked to beef supply chain, sexual harassment class actions. Ordered by NLRB to bargain with workers at multiple locations.',
     7200000, 'Minimum wage, food labeling, franchise law, beef industry subsidies, labor',
     "World's largest fast food chain by revenue. 40,000+ locations in 100+ countries. Founded 1940, franchised by Ray Kroc. Franchisees own 93% of locations."),
    ('roark-capital', 'Roark Capital Group', 'pe', None, 'US', None, 19,
     "Portfolio: Arby's, Sonic, Panera, Subway, Carl's Jr., Buffalo Wild Wings, Jimmy John's. Aggressive fee extraction. Franchisees report high royalty rates squeezing operators.",
     2300000, 'Franchise law, food safety, labor, acquisition regulation',
     "Atlanta-based PE firm specializing in restaurant/franchise acquisitions. Founded 2001. Named after fictional ranch in Ayn Rand's Atlas Shrugged. $37B+ AUM."),
    ('yum-brands', 'Yum! Brands', 'public', 'YUM', 'US', 6800000000, 22,
     'Wage theft violations across franchise network, food safety failures (Taco Bell E. coli 2011), environmental issues tied to beef/chicken supply chains.',
     3100000, 'Franchise law, food safety, labor standards, trade policy, minimum wage',
     'Louisville-based conglomerate owning Taco Bell, KFC, Pizza Hut, Habit Burger. Spun off from PepsiCo 1997. 55,000+ restaurants globally.'),
    ('rbi', 'Restaurant Brands International', 'public', 'QSR', 'CA', 7000000000, 31,
     'Wage theft across Burger King/Tim Hortons franchise networks, NLRB complaints, antibiotic use in chicken supply, deforestation tied to palm oil sourcing.',
     2800000, 'Franchise law, trade, food labeling, minimum wage, palm oil sourcing',
     'Toronto-based holding company (3G Capital-backed) owning Burger King, Tim Hortons, Popeyes, Firehouse Subs. Formed 2014. 30,000+ locations globally.'),
    ('inspire-brands', 'Inspire Brands (Roark Capital)', 'pe', None, 'US', 32000000000, 28,
     "Wage theft settlements across Arby's and Sonic franchises, NLRB complaints, food safety violations. Dunkin' franchisee wage theft $6M settlement.",
     2900000, 'Franchise law, labor standards, food safety, alcohol licensing',
     "PE-backed (Roark Capital) owning Arby's, Sonic, Buffalo Wild Wings, Jimmy John's, Dunkin', Baskin-Robbins. Assembled 2018-2020. $32B+ system sales."),
    ('dine-brands', 'Dine Brands Global', 'public', 'DIN', 'US', 890000000, 9,
     "Wage theft at IHOP and Applebee's franchise locations, tip pool manipulation, tipped minimum wage exploitation.",
     1100000, 'Tipping, minimum wage, food safety, franchise law',
     "Glendale CA-based conglomerate owning Applebee's and IHOP. 3,500+ restaurants globally, almost entirely franchised."),
    ('wendys-corp', "Wendy's Company", 'public', 'WEN', 'US', 2100000000, 15,
     'Wage theft settlements, worker safety violations, attempted dynamic pricing (reversed after backlash), E. coli outbreak 2022 linked to romaine lettuce.',
     1800000, 'Food safety, franchise law, minimum wage, dynamic pricing',
     'Dublin OH-based fast food chain. Founded 1969 by Dave Thomas. 6,800+ locations, 95% franchised. Trian Fund Management (activist investor) holds significant stake.'),
    ('jack-in-the-box', 'Jack in the Box Inc.', 'public', 'JACK', 'US', 1600000000, 7,
     'Wage theft complaints, labor violations. Acquired Del Taco 2022 with heavy debt ($585M). Known for 1993 E. coli outbreak that killed 4 children and triggered USDA food safety reform.',
     800000, 'Franchise law, food safety, labor',
     'San Diego-based fast food chain, 2,200+ locations primarily in western US. Also owns Del Taco. Founded 1951.'),
    ('dutch-bros', 'Dutch Bros Inc.', 'public', 'BROS', 'US', 1200000000, 4,
     'Worker misclassification complaints, wage violations in Oregon, rapid expansion (100+ new locations/yr) raising franchisee economics concerns.',
     200000, 'Franchise law, minimum wage, worker classification',
     'Grants Pass OR-based drive-through coffee chain. Founded 1992 by Dane and Travis Boersma. IPO 2021. 900+ locations across 17 states.'),
    ('in-n-out', 'In-N-Out Burger', 'private', None, 'US', 1200000000, 4,
     'California wage claims 2020. Owner donated to California GOP 2022. Anti-mask mandate stance during pandemic. Premium pricing relative to food cost.',
     100000, 'Labor, food safety, political donations',
     'Baldwin Park CA-based private family chain. Founded 1948 by Harry and Esther Snyder. 400+ locations in western US. Never franchised. Known for above-average wages and hidden menu.'),
    ('chick-fil-a', 'Chick-fil-A Inc.', 'private', None, 'US', 21600000000, 8,
     'Donated $1.8M+ to anti-LGBTQ organizations 2010-2018 (Fellowship of Christian Athletes, Salvation Army). Pledged to stop 2019, then reversed. Closed Sundays.',
     600000, 'Food safety, labor, religious liberty, LGBTQ issues',
     'College Park GA-based private chain owned by Cathy family. Founded 1967. 2,800+ locations. Highest per-location revenue of any US fast food chain.'),
    ('panda-restaurant-group', 'Panda Restaurant Group', 'private', None, 'US', 4500000000, 6,
     'Wage theft settlements in California and New York. OSHA violations. Workers report pressure to upsell and falsify portion sizes. J-1 visa worker concerns.',
     300000, 'Labor, immigration (J-1 visa workers), food safety, wage theft',
     'Rosemead CA-based private company owned by the Cherng family. Founded 1973. Operates Panda Express (2,300+ locations), Panda Inn, Hibachi-San.'),
    ('subway-restaurants', 'Subway Restaurants (Roark Capital)', 'pe', None, 'US', 10000000000, 23,
     'Tuna DNA controversy (CBC lawsuit 2021), franchisee wage theft endemic. "Chicken" tested at 50% soy protein by CBC. Sold to Roark Capital 2023 for $9.6B.',
     1400000, 'Franchise law, food labeling, immigration, ingredient integrity',
     'Milford CT-based sandwich chain. Founded 1965 by Fred DeLuca. Sold to Roark Capital 2023 for $9.6B. 37,000+ global locations, down from 45,000 peak.'),
    ('five-guys', 'Five Guys Enterprises LLC', 'private', None, 'US', 2000000000, 5,
     'Franchise disclosure disputes, wage complaints. Premium pricing — $20+ burger combos. Peanut allergy risks widely documented. Calorie counts among highest of any burger chain.',
     200000, 'Food safety, franchise law, allergen disclosure',
     'Arlington VA-based burger chain. Founded 1986 by Murrell family. Still family-owned. 1,700+ locations across 18 countries. Fresh (never frozen) beef.'),
    ('cava-group', 'Cava Group Inc.', 'public', 'CAVA', 'US', 950000000, 3,
     'Rapid expansion pressures on ingredient consistency and sourcing transparency. IPO 2023 raised $318M.',
     150000, 'Food labeling, labor, ingredient sourcing',
     'Washington DC-based Mediterranean fast casual. Founded 2010. IPO June 2023. 340+ locations. Acquired Zoës Kitchen 2018 for $300M.'),
    ('sweetgreen-corp', 'Sweetgreen Inc.', 'public', 'SG', 'US', 670000000, 4,
     'Acquired Tender Greens 2023 for $6M (distressed sale). Wage claims in multiple markets. Infinite Kitchen automation raising labor displacement concerns. Menu shrinkflation documented.',
     400000, 'Labor, food labeling, technology/automation, ingredient sourcing',
     'Los Angeles-based salad chain. Founded 2007. IPO November 2021. 220+ locations.'),
    ('shake-shack-corp', 'Shake Shack Inc.', 'public', 'SHAK', 'US', 1090000000, 5,
     'Wage theft complaints NYC 2021. PPP loan $10M during COVID while paying executive bonuses. Kiosk-only model creates service gaps. Menu prices up 35%+ since 2020.',
     500000, 'Labor, food safety, outdoor dining, PPP loan use',
     'NYC-based burger chain. Started as Madison Square Park hot dog cart 2001. Founded by Danny Meyer. IPO 2015. 500+ locations globally.'),
    ('darden-restaurants', 'Darden Restaurants', 'public', 'DRI', 'US', 11400000000, 14,
     'Wage theft class actions (Olive Garden tipped worker theft $2.85M), OSHA violations, tip pool manipulation. Sold Red Lobster 2014 — chain filed bankruptcy 2024.',
     1600000, 'Tipping, food safety, labor standards, minimum wage, tip pooling',
     "Orlando-based casual dining owning Olive Garden, LongHorn Steakhouse, Cheddar's, Yard House, The Capital Grille. 1,900+ restaurants."),
    ('target-corp', 'Target Corporation', 'public', 'TGT', 'US', 109400000000, 28,
     'Labor violations (worker misclassification, overtime), environmental penalty for hazardous waste disposal ($22.5M), anti-LGBTQ product rollback 2023 after far-right protest pressure.',
     8900000, 'Retail labor, minimum wage, supply chain, environmental regulation, DEI',
     "Minneapolis-based retail giant with grocery in most locations. Founded 1902 as Dayton's. 1,950+ stores."),
    ('albertsons', 'Albertsons Companies (Cerberus Capital)', 'pe', 'ACI', 'US', 79200000000, 18,
     'NLRB complaints for union interference, wage theft in multiple states, failed $24.6B Kroger merger blocked by FTC 2024. Extracted $400M dividend for Cerberus before planned merger.',
     3200000, 'Antitrust, labor, food labeling, merger regulation, union rights',
     "Boise ID-based grocery chain (Cerberus Capital majority stake). Owns Albertsons, Safeway, Vons, Pavilions, Jewel-Osco, Shaw's, Acme."),
    ('kroger-corp', 'The Kroger Co.', 'public', 'KR', 'US', 150000000000, 24,
     'NLRB complaints across multiple unions, FTC report documented systematic price gouging post-COVID (2024), failed $24.6B Albertsons merger blocked by FTC.',
     4800000, 'Antitrust, food labeling, labor, pharmacy benefits, price gouging',
     "Cincinnati-based largest US supermarket chain by revenue. 2,700+ stores under Kroger, Fred Meyer, Ralphs, King Soopers, Fry's, Smith's banners."),
    ('wingstop-corp', 'Wingstop Inc.', 'public', 'WING', 'US', 490000000, 5,
     'Franchise wage violations, food safety concerns. Digital-only model creates barriers for older/lower-income customers. Menu prices up 40%+ since 2020.',
     400000, 'Franchise law, food safety, digital access equity',
     'Addison TX-based wing chain. Founded 1994. IPO 2015. 2,100+ locations, 98% franchised.'),
    ('grocery-outlet', 'Grocery Outlet Holding Corp.', 'public', 'GO', 'US', 4200000000, 4,
     'Independent operator model creates inconsistent labor practices. Product sourcing opacity — closeout merchandise may include discontinued/reformulated items.',
     200000, 'Food safety, retail labor, product transparency',
     'Emeryville CA-based discount grocery chain. Founded 1946. IPO 2019. 500+ stores in western US, PA, MD, NJ.'),
    ('panera-bread-roark', 'Panera Bread (Roark Capital)', 'pe', None, 'US', 7600000000, 19,
     'Charged Lemonade caffeine death lawsuits (2024) — customer died from 3x lethal caffeine dose. Wage theft settlements, "You Pick Two" shrinkflation. Withdrew IPO plans 2023.',
     2300000, 'Food labeling, franchise law, labor, beverage caffeine regulation',
     "St. Louis-based fast casual bakery-café. Founded 1987 as Au Bon Pain. Acquired by JAB 2017 for $7.5B, sold to Roark Capital 2024. 2,100+ locations."),
    ('jollibee-foods', 'Jollibee Foods Corporation', 'public', 'JFC', 'PH', 3500000000, 6,
     'Labor violations at Smashburger US locations, wage theft complaints. Paid $100M for Coffee Bean & Tea Leaf 2019. Smashburger declining traffic post-acquisition.',
     300000, 'Labor, trade, food labeling',
     'Philippines-based fast food conglomerate. Owns Jollibee, Smashburger, The Coffee Bean & Tea Leaf, Highlands Coffee. Aggressive US expansion via acquisitions.'),
    ('the-cheesecake-factory', 'The Cheesecake Factory Inc.', 'public', 'CAKE', 'US', 3400000000, 9,
     'Wage theft settlement $4.57M to 559 workers (2022), COVID rent non-payment controversy, FDA calorie count violations, portion manipulation.',
     800000, 'Labor, food labeling, commercial rent, calorie disclosure',
     'Calabasas CA-based casual dining. Founded 1978 by David and Evelyn Overton. 300+ locations. Also owns North Italia and Flower Child.'),
    ('dennys-corp', "Denny's Corporation", 'public', 'DENN', 'US', 480000000, 11,
     'Wage theft complaints systemwide, racial discrimination at franchise locations (NAACP settlement), tipped minimum wage exploitation. 99% franchised model enables violations with limited accountability.',
     700000, 'Tipping, minimum wage, food safety, racial discrimination',
     "Spartanburg SC-based diner chain. Founded 1953. 1,600+ locations, 99% franchised. History of racial discrimination settlements."),
    ('aldi-group', 'Aldi (Albrecht family, private)', 'private', None, 'DE', 130000000000, 8,
     'German private family firm. Anti-union practices at US stores documented. Limited labor transparency. Store layout intentionally minimizes worker positions to cut costs.',
     600000, 'Labor, food safety, supply chain transparency',
     'German private grocery chain owned by Albrecht family (Aldi Nord + Aldi Süd). US Aldi is Aldi Süd. Founded 1946. 2,300+ US stores. Extreme private label model.'),
    ('jersey-mikes', "Jersey Mike's Franchise Systems (Blackstone)", 'pe', None, 'US', 3000000000, 4,
     'Sold majority stake to Blackstone 2023 at $8B valuation. Rapid expansion raising franchisee stress. Wage theft complaints in California. Prices up 25%+ since 2021.',
     300000, 'Franchise law, food safety, labor',
     "Point Pleasant NJ-based sub chain. Founded 1956. Sold majority stake to Blackstone PE 2023 at $8B valuation. 2,800+ locations."),
    ('raising-canes', "Raising Cane's Chicken Fingers", 'private', None, 'US', 2000000000, 4,
     'Worker injury claims at high-volume locations. Premium pricing for limited menu. Rapid expansion pressuring supply chain. Never franchised.',
     150000, 'Labor, food safety',
     'Baton Rouge LA-based private chicken chain. Founded 1996 by Todd Graves. 800+ locations, only serves chicken fingers. Planned expansion to 1,500+ locations.'),
    ('bj-restaurants', "BJ's Restaurants Inc.", 'public', 'BJRI', 'US', 1200000000, 5,
     'Wage theft complaints in California, worker safety violations. Struggled post-COVID with high real estate costs. Menu prices up significantly.',
     300000, 'Labor, food safety, commercial rent',
     'Huntington Beach CA-based casual dining chain. Founded 1978. 200+ locations across 29 states. Known for Pizookie dessert.'),
    ('raleys', "Raley's", 'private', None, 'US', 5000000000, 2,
     'Generally regarded as a good employer. Family-owned for 85+ years. Some labor disputes at union locations. Committed to paying above-minimum wages.',
     150000, 'Labor, food safety',
     "West Sacramento CA-based family-owned grocery chain. Founded 1935 by Thomas Raley. 130+ stores in California and Nevada under Raley's, BEL Air, Nob Hill, Raley's O-N-E Market banners."),
    ('winco-foods', 'WinCo Foods', 'private', None, 'US', 10000000000, 2,
     'Employee-owned ESOP (Employee Stock Ownership Plan). Some labor disputes over scheduling practices. No union at most locations but ESOP provides ownership stake.',
     200000, 'Labor, food safety, ESOP',
     'Boise ID-based employee-owned grocery chain. Founded 1967. 240+ stores in western US. ESOP since 1985 — employees are part-owners. No-frills warehouse model.'),
    ('amazon-corp', 'Amazon.com Inc.', 'public', 'AMZN', 'US', 574000000000, 31,
     'Warehouse worker injury rates 2x industry average, union-busting at JFK8 and other warehouses, NLRB complaints, antitrust investigation into Whole Foods pricing and supplier relationships.',
     21000000, 'Labor, antitrust, data privacy, minimum wage, environmental',
     'Seattle-based tech/retail giant. Acquired Whole Foods 2017 for $13.7B. 1.5M+ employees globally. Jeff Bezos founded 1994.'),
]

for row in COMPANIES:
    c.execute("""INSERT OR IGNORE INTO companies
        (id, name, type, ticker, hq_country, annual_revenue, violation_count,
         violation_summary, lobbying_annual, lobbying_issues, description)
        VALUES (?,?,?,?,?,?,?,?,?,?,?)""", row)
print(f"  Companies: {len(COMPANIES)} processed")

# ─────────────────────────────────────────────
# 3. UPDATE EXISTING BRANDS (have UUID or wrong-slug IDs, need metadata)
# ─────────────────────────────────────────────
EXISTING_BRAND_UPDATES = [
    # (name_match, category, format, price_tier, overall_zone, independent, pe_owned,
    #  parent_company_id, headline_finding, share_text, founder_story,
    #  ingredient_drift, ingredient_drift_note, watch_list, founded_year, acquired_year)
    ("Starbucks", 'coffee', 'cafe', 2, 'yellow', 0, 0, 'starbucks-corp',
     'Starbucks is fighting 200+ NLRB union complaints while claiming to be a "people company." CEO hired 2024 for $113M package.',
     'Starbucks has faced 200+ NLRB union-busting complaints since 2021 — firing hundreds of organizers while paying CEO $113M. #Traced',
     'Founded Seattle 1971 by Jerry Baldwin, Zev Siegl, Gordon Bowker. Howard Schultz acquired 1987 and expanded globally. Brian Niccol (ex-Chipotle CEO) hired 2024 to reverse declining same-store sales.',
     1, 'Starbucks reformulated drinks post-2019 with more syrup-heavy recipes to drive revenue. "Refreshers" and frappuccinos now primary revenue driver over traditional coffee.',
     1, 1971, None),

    ("McDonald's", 'restaurant', 'fast_casual', 1, 'red', 0, 0, 'mcdonalds-corp',
     "World's largest fast food chain. 42 documented violations. $26M wage theft settlement (2019). 93% of locations are franchised.",
     "McDonald's paid $26M to settle California wage theft claims in 2019 — while posting $8B+ profits. #Traced #FastFood",
     "Founded 1940 by Richard and Maurice McDonald in San Bernardino CA. Ray Kroc secured franchise rights 1954 and bought the company 1961 for $2.7M. Now 40,000+ locations globally.",
     1, "McDonald's reformulated its beef blend multiple times to reduce costs. McRib pork composition and chicken nugget recipes reformulated post-acquisition of regional suppliers.",
     0, 1940, None),

    ("Panera Bread", 'restaurant', 'fast_casual', 2, 'red', 0, 1, 'panera-bread-roark',
     "Panera's Charged Lemonade killed a customer in 2024 — 3x lethal caffeine dose in one drink. Now owned by Roark Capital PE.",
     "Panera Bread's 'Charged Lemonade' killed a 21-year-old in 2024. The drink contained 390mg caffeine — nearly 3x the safe daily limit. Now PE-owned by Roark Capital. #Traced",
     'Founded 1987 as Au Bon Pain in St. Louis. Became Panera Bread 1999. Acquired by JAB Holding 2017 for $7.5B. Sold to Roark Capital 2024 after failed IPO attempt. Ron Shaich (founder) departed post-JAB.',
     1, 'Post-JAB acquisition, Panera reformulated soups and baked goods to extend shelf life. "Clean" ingredient claims increasingly questioned after Charged Lemonade reveal.',
     1, 1987, 2017),

    ("Safeway", 'grocery', 'market', 2, 'red', 0, 1, 'albertsons',
     'Safeway is owned by Albertsons — itself majority-owned by Cerberus Capital PE. FTC blocked $24.6B merger with Kroger in 2024.',
     'Safeway → Albertsons → Cerberus Capital PE. The $24.6B Kroger merger was blocked by FTC in 2024. Cerberus extracted $400M dividend before the deal collapsed. #Traced',
     'Founded 1915 by Marion Skaggs in American Falls, Idaho. Grew to 2,500+ stores by 1980s. Acquired by Cerberus Capital 2015, merged into Albertsons. Multiple rounds of PE ownership and debt-loading.',
     0, None, 0, 1915, 2015),

    ("Sweetgreen", 'restaurant', 'fast_casual', 2, 'yellow', 0, 0, 'sweetgreen-corp',
     'Sweetgreen (NYSE:SG) acquired struggling Tender Greens for $6M in 2023. Automation replacing workers with "Infinite Kitchen" robots.',
     'Sweetgreen paid just $6M for Tender Greens in 2023 (distressed sale). Now rolling out robot kitchens. Public company (NYSE:SG) since 2021. #Traced',
     'Founded 2007 by three Georgetown University students — Jonathan Neman, Nathaniel Ru, Nicolas Jammet. Grew from one DC salad bar to 220+ locations. IPO 2021.',
     0, None, 0, 2007, None),

    ("Shake Shack", 'restaurant', 'fast_casual', 2, 'yellow', 0, 0, 'shake-shack-corp',
     'Shake Shack (NYSE:SHAK) took $10M PPP loan while paying executive bonuses during COVID — then returned it after public backlash. Menu prices up 35%+ since 2020.',
     'Shake Shack took a $10M PPP loan during COVID while paying bonuses — returned it after public pressure. Now $20+ for a combo. Public (NYSE:SHAK). #Traced',
     'Started as a hot dog cart in Madison Square Park NYC in 2001. Created by restaurateur Danny Meyer (Union Square Hospitality Group). Spun off as standalone company. IPO 2015.',
     0, None, 0, 2001, None),

    ("Aldi", 'grocery', 'market', 1, 'yellow', 0, 0, 'aldi-group',
     'Aldi is privately owned by the German Albrecht family. Anti-union practices documented in US stores. Aggressive private-label model displaces local brands.',
     'Aldi is owned by the secretive German Albrecht family — worth $30B+. Anti-union practices in US stores. Private label drives 90% of sales. #Traced',
     'Founded 1946 by brothers Karl and Theo Albrecht in Essen, Germany. Split into Aldi Nord and Aldi Süd 1960 (US Aldi is Aldi Süd). Known for extreme operational efficiency and near-total private label.',
     0, None, 0, 1946, None),

    ("Kroger", 'grocery', 'market', 2, 'yellow', 0, 0, 'kroger-corp',
     'Kroger: FTC documented systematic price gouging post-COVID (2024 report). $24.6B Albertsons merger blocked by FTC. Closed stores in food deserts after workers unionized.',
     'FTC found Kroger systematically raised prices beyond cost increases post-COVID. $24.6B Albertsons merger blocked 2024. Closed union stores in food deserts. #Traced',
     "Founded 1883 by Barney Kroger in Cincinnati OH. Built first store with his life savings ($372). Now America's largest supermarket chain by revenue. 2,700+ stores under 20+ banners.",
     0, None, 0, 1883, None),

    ("Trader Joes", 'grocery', 'market', 2, 'green', 0, 0, 'trader-joes',
     "Trader Joe's is privately owned by the Albrecht family (Aldi Nord). High employee satisfaction. Wages and benefits above industry average.",
     "Trader Joe's is owned by Germany's Albrecht family (Aldi Nord branch) — but operates with unusual independence and strong employee culture. Above-average wages, benefits. #Traced",
     'Founded 1967 by Joe Coulombe in Pasadena CA. Sold to Theo Albrecht (Aldi Nord) 1979. Coulombe left 1988. Expanded via cult-like customer loyalty and exclusive private label items.',
     0, None, 0, 1967, None),

    ("Whole Foods Market", 'grocery', 'market', 3, 'red', 0, 0, 'amazon-corp',
     'Whole Foods sold to Amazon 2017 for $13.7B. Prices up significantly post-acquisition. "Whole Paycheck" reputation intensified. Amazon uses Whole Foods location data.',
     'Whole Foods sold to Amazon 2017 for $13.7B. Prices increased post-acquisition. Amazon mines customer data through Prime membership integration. #Traced',
     'Founded 1978 by John Mackey and Renee Lawson Hardy in Austin TX. Grew to 500+ stores. Acquired by Amazon 2017. Mackey (libertarian founder) retired 2023.',
     1, 'Post-Amazon acquisition, Whole Foods 365 private label expanded, many artisan/local suppliers delisted in favor of scale suppliers. "Responsibly Sourced" standards quietly revised.',
     0, 1978, 2017),

    ("Costco", 'grocery', 'market', 2, 'green', 0, 0, None,
     'Costco is publicly traded but runs counter to corporate norms: pays above-average wages, offers employee healthcare, and generates strong member loyalty.',
     'Costco (NASDAQ:COST) pays above-average wages, offers employee healthcare, and caps CEO pay ratio at 168:1 vs industry avg 350:1. Genuinely different. #Traced',
     'Founded 1983 by Jim Sinegal and Jeffrey Brotman in Seattle. Merged with Price Club 1993. Known for employee-friendly policies — CEO salary has historically been modest.',
     0, None, 0, 1983, None),

    ("Sprouts Farmers Market", 'grocery', 'market', 2, 'yellow', 0, 0, None,
     'Sprouts (NASDAQ:SFM) is public but focused on natural/organic. Wages below Whole Foods. Greenwashing concerns around "natural" label usage.',
     "Sprouts (NASDAQ:SFM) markets itself as 'natural and organic' but faces questions about supplier standards and below-average employee wages. #Traced",
     'Founded 2002 by the Boney family in Chandler AZ. IPO 2013. 400+ stores. Targets health-conscious shoppers with mix of conventional and organic at moderate prices.',
     0, None, 0, 2002, None),

    ("Walmart", 'grocery', 'market', 1, 'red', 0, 0, None,
     "World's largest retailer by revenue. 42+ NLRB complaints. Closed stores rather than allow unionization. Walmart heirs hold $230B+ wealth while average worker earns $14/hr.",
     "Walmart's Walton family holds $230B+ wealth. The company closed an entire store in 2022 rather than recognize its first union. Average worker: $14/hr. #Traced",
     'Founded 1962 by Sam Walton in Rogers AR. Walton family still owns 50%+ of shares. World\'s largest private employer (2.3M US workers). Grocery now 56% of US revenue.',
     0, None, 0, 1962, None),

    ("CVS", 'pharmacy', 'pharmacy', 1, 'red', 0, 0, None,
     'CVS (NYSE:CVS) acquired Aetna 2018 for $69B, loading up with debt. Multiple violations for pushing opioids. Acquired Signify Health, Oak Street Health for data plays.',
     'CVS acquired Aetna (insurance) + Signify Health + Oak Street for $100B+ in deals. Now owns your pharmacy, doctor, and insurer. #Traced #VerticalIntegration',
     'Founded 1963 as Consumer Value Stores in Lowell MA. Grew via acquisitions. Merged with Caremark 2007, Aetna 2018. Now one of largest healthcare companies in US.',
     0, None, 1, 1963, None),

    ("Walgreens", 'pharmacy', 'pharmacy', 1, 'red', 0, 0, None,
     'Walgreens (NASDAQ:WBA) closing 1,200+ stores after years of PE-style financial engineering. Opioid settlements $683M+. Attempting to go private via Sycamore Partners PE.',
     'Walgreens closing 1,200+ stores in 2024-2025. Paid $683M+ in opioid settlements. Now attempting to go private via Sycamore Partners PE at fraction of former valuation. #Traced',
     'Founded 1901 by Charles Walgreen Sr. in Chicago. Grew via franchise model. Merged with Boots Alliance 2014. Once America\'s most-trusted pharmacy, now in financial distress.',
     0, None, 1, 1901, None),

    ("Chipotle", 'restaurant', 'fast_casual', 1, 'yellow', 0, 0, 'chipotle-corp',
     'Chipotle (NYSE:CMG) is public and founder-adjacent (Brian Niccol went to Starbucks). Multiple E. coli outbreaks. Portion sizes shrinking while prices rise.',
     'Chipotle has faced 11 documented violations including multiple E. coli outbreaks. Portions are measurably smaller than 5 years ago. Still the best of the QSR chains. #Traced',
     'Founded 1993 by Steve Ells in Denver CO. McDonald\'s acquired majority stake 1998, sold 2006. IPO 2006. Stef Ells left CEO role. Brian Niccol (CEO 2018-2024) dramatically improved margins.',
     0, None, 0, 1993, None),
]

for row in EXISTING_BRAND_UPDATES:
    (name_match, category, fmt, price_tier, zone, indep, pe_owned, parent_id,
     headline, share, founder, ingr_drift, ingr_note, watch, founded, acquired) = row
    c.execute("""UPDATE brands SET
        category=?, format=?, price_tier=?, overall_zone=?, independent=?, pe_owned=?,
        parent_company_id=?, headline_finding=?, share_text=?, founder_story=?,
        ingredient_drift=?, ingredient_drift_note=?, watch_list=?, founded_year=?, acquired_year=?
        WHERE lower(name) LIKE lower(?)""",
        (category, fmt, price_tier, zone, indep, pe_owned, parent_id,
         headline, share, founder, ingr_drift, ingr_note, watch, founded, acquired,
         f'%{name_match}%'))
    updated = c.rowcount
    print(f"  Updated '{name_match}': {updated} rows")

# ─────────────────────────────────────────────
# 4. NEW CHAIN BRANDS
# ─────────────────────────────────────────────
NEW_BRANDS = [
    # COFFEE CHAINS
    ('starbucks', 'Starbucks', 'starbucks', 'coffee', 'cafe', 2, 'yellow', 0, 0, 'starbucks-corp',
     'Starbucks is fighting 200+ NLRB union complaints while claiming to be a "people company."',
     'Starbucks has faced 200+ NLRB union-busting complaints since 2021. CEO hired 2024 for $113M. #Traced',
     'Founded Seattle 1971. Howard Schultz acquired 1987 and expanded globally. Brian Niccol (ex-Chipotle) hired 2024 to reverse declining sales.',
     1, 'Drink recipes reformulated post-2015 with more syrup-heavy, sugar-forward products. Traditional espresso quality secondary to Frappuccino/Refresher revenue.',
     1, 1971, None),

    ('dunkin', "Dunkin'", 'dunkin', 'coffee', 'cafe', 1, 'red', 0, 1, 'inspire-brands',
     "Dunkin' is owned by Inspire Brands (Roark Capital PE). Franchisees report $6M+ wage theft settlement. 80%+ of sales are not coffee.",
     "Dunkin' is Roark Capital PE via Inspire Brands. Former franchisees paid $6M+ in wage theft. 'America runs on Dunkin' — and Dunkin' runs on franchisee labor. #Traced",
     "Founded 1950 by William Rosenberg in Quincy MA. Rebranded from Dunkin' Donuts to Dunkin' 2018 to downplay the donut. Acquired by Inspire Brands (Roark Capital) 2020 for $11.3B.",
     1, 'Post-Inspire acquisition, drink recipes reformulated with cheaper ingredients. "Signature Lattes" use flavored syrups over real dairy or espresso quality.',
     0, 1950, 2020),

    ('dutch-bros-brand', 'Dutch Bros Coffee', 'dutch-bros-coffee', 'coffee', 'cafe', 1, 'yellow', 0, 0, 'dutch-bros',
     'Dutch Bros (NYSE:BROS) is publicly traded but family-founded. 900+ drive-throughs. Heavy sugar content in signature drinks. Rapid expansion pressuring quality.',
     'Dutch Bros (NYSE:BROS) went public 2021. Iconic drive-through energy drink company. 900+ locations. Signature drinks often 600+ calories. #Traced',
     'Founded 1992 by Dutch immigrant brothers Dane and Travis Boersma in Grants Pass OR with a pushcart. Grew into drive-through empire. Travis Boersma remains involved post-IPO.',
     0, None, 0, 1992, None),

    ('tim-hortons', 'Tim Hortons', 'tim-hortons', 'coffee', 'cafe', 1, 'red', 0, 1, 'rbi',
     "Tim Hortons is owned by Restaurant Brands International (3G Capital PE). Franchisees cut worker benefits after minimum wage increase — leading to national boycott in Canada.",
     "Tim Hortons (3G Capital PE via RBI) franchisees cut benefits and paid breaks after Canada minimum wage raised $1. Led to national boycott. #Traced",
     'Founded 1964 by NHL player Tim Horton in Hamilton, Ontario. Acquired by Wendy\'s 1995, spun off 2006. Acquired by Burger King (3G Capital) 2014 to form RBI. 5,700+ locations globally.',
     0, None, 0, 1964, 2014),

    ('caribou-coffee', 'Caribou Coffee', 'caribou-coffee', 'coffee', 'cafe', 2, 'red', 0, 1, 'jab-holding',
     'Caribou Coffee is owned by JAB Holding — the same Luxembourg PE conglomerate that owns Peet\'s, Stumptown, Intelligentsia, Keurig, and Panera.',
     "Caribou Coffee is owned by JAB Holding — the Luxembourg PE firm that also controls Peet's, Stumptown, Intelligentsia, and Keurig. One conglomerate, many 'different' coffee brands. #Traced",
     'Founded 1992 by John and Kim Puckett in Edina MN after a trip to Alaska. Went public 2005. Acquired by JAB Holding 2012 for $340M. 600+ locations in US and Middle East.',
     0, None, 0, 1992, 2012),

    ('stumptown-coffee', 'Stumptown Coffee Roasters', 'stumptown-coffee', 'coffee', 'cafe', 2, 'red', 0, 1, 'jab-holding',
     "Stumptown sold to Peet's (JAB Holding) in 2015. Original founder Duane Sorenson pushed out. Now part of JAB's coffee conglomerate alongside Peet's, Blue Bottle, Intelligentsia.",
     "Stumptown was Portland's indie darling — acquired by Peet's (JAB Holding PE) 2015 for ~$115M. Founder Duane Sorenson departed. Now JAB's 3rd coffee brand alongside Peet's and Intelligentsia. #Traced",
     'Founded 1999 by Duane Sorenson in Portland OR. Pioneer of third-wave specialty coffee and direct trade sourcing. Acquired by Peet\'s Coffee (JAB Holding) 2015. Sorenson later started Extraction Coffee.',
     1, 'Post-JAB acquisition, sourcing transparency decreased. Direct trade relationships maintained on paper but auditing rigor questioned by former buyers.',
     0, 1999, 2015),

    ('intelligentsia-coffee', 'Intelligentsia Coffee', 'intelligentsia-coffee', 'coffee', 'cafe', 3, 'red', 0, 1, 'jab-holding',
     "Intelligentsia sold to Peet's (JAB Holding) in 2015. A pioneer of direct trade sourcing, now under same PE conglomerate as Peet's, Blue Bottle, Stumptown.",
     "Intelligentsia (direct trade pioneer) sold to Peet's/JAB 2015. Now one of 5 JAB coffee brands. Direct trade commitments continue but PE ownership creates extraction pressure. #Traced",
     'Founded 1995 by Doug Zell and Emily Mange in Chicago. Pioneered direct trade coffee sourcing and third-wave technique. Acquired by Peet\'s Coffee 2015. Multiple US outposts.',
     0, None, 0, 1995, 2015),

    ('coffee-bean', 'The Coffee Bean & Tea Leaf', 'coffee-bean', 'coffee', 'cafe', 2, 'red', 0, 0, 'jollibee-foods',
     'The Coffee Bean & Tea Leaf is owned by Jollibee Foods Corporation (Philippines). Paid $100M for the brand in 2019. Declining US market share.',
     'Coffee Bean & Tea Leaf sold to Jollibee Foods (Philippines) for $100M in 2019. Philippines-based corporate ownership of a Southern California coffee institution. #Traced',
     'Founded 1963 by Herbert Hyman in Brentwood CA. Grew via franchise model across US and Asia. Sold to Sassoon family, then Advent International PE, then Jollibee Foods 2019.',
     0, None, 0, 1963, 2019),

    ('seattles-best', "Seattle's Best Coffee", 'seattles-best', 'coffee', 'cafe', 1, 'red', 0, 0, 'starbucks-corp',
     "Seattle's Best Coffee is a Starbucks subsidiary, acquired 2003 for $72M. Operates as discount Starbucks at airports, grocery stores, fast food chains.",
     "Seattle's Best Coffee is owned by Starbucks — a subsidiary used to capture value-tier customers. Same parent, different price point. #Traced",
     "Founded 1970 on Vashon Island WA. Known for winning 1974 coffee taste competition. Acquired by Starbucks 2003 for $72M. Now primarily sold through grocery, gas stations, and Burger King.",
     0, None, 0, 1970, 2003),

    # FAST CASUAL / QSR CHAINS
    ('mcdonalds', "McDonald's", 'mcdonalds', 'restaurant', 'fast_casual', 1, 'red', 0, 0, 'mcdonalds-corp',
     "World's largest fast food chain. $26M wage theft settlement 2019. 42 documented violations. 93% franchised.",
     "McDonald's has 42 documented violations including $26M wage theft settlement (CA, 2019). 93% of locations are franchised — corporate profits, franchisee risk. #Traced",
     "Founded 1940 by Richard and Maurice McDonald in San Bernardino CA. Ray Kroc secured franchise rights 1954, bought out brothers 1961 for $2.7M. Now 40,000+ locations globally.",
     1, 'Beef blend reformulated multiple times. McRib pork composition and chicken nugget recipes changed post-supplier acquisition. "Fresh beef" only at select locations.',
     0, 1940, None),

    ('burger-king', 'Burger King', 'burger-king', 'restaurant', 'fast_casual', 1, 'red', 0, 1, 'rbi',
     'Burger King is owned by Restaurant Brands International (3G Capital PE). Known for cost-cutting via 3G playbook. Franchisees increasingly unhappy with corporate support.',
     'Burger King is owned by 3G Capital PE via Restaurant Brands International. Classic PE playbook: cut costs, maximize fees, load with debt. Franchisees increasingly revolt. #Traced',
     'Founded 1953 as Insta-Burger King in Jacksonville FL. Acquired by Pillsbury 1967, then Grand Metropolitan, then Texas Pacific Group. Acquired by 3G Capital 2010. Now 18,000+ locations globally.',
     0, None, 0, 1953, 2010),

    ('taco-bell', 'Taco Bell', 'taco-bell', 'restaurant', 'fast_casual', 1, 'red', 0, 0, 'yum-brands',
     'Taco Bell is owned by Yum! Brands (PepsiCo spinoff). E. coli outbreak 2011. Mexican-themed food with no authentic Mexican ownership.',
     'Taco Bell is owned by Yum! Brands — a PepsiCo spinoff. E. coli outbreak 2011. "Mexican-inspired" food that is neither Mexican nor locally owned. 8,000+ locations. #Traced',
     'Founded 1962 by Glen Bell in Downey CA. Acquired by PepsiCo 1978. Spun off into Yum! Brands 1997. 8,000+ US locations. Taco Tuesday trademark dispute settled in favor of public use 2023.',
     0, None, 0, 1962, 1978),

    ('kfc', 'KFC', 'kfc', 'restaurant', 'fast_casual', 1, 'red', 0, 0, 'yum-brands',
     'KFC is owned by Yum! Brands. Colonel Sanders sold the brand in 1964 for $2M. Now $5B+ system sales. Antibiotic use in chicken supply chain.',
     'KFC is owned by Yum! Brands. Colonel Sanders sold for $2M in 1964 — the brand now generates $5B+ annually. Antibiotic use in chicken supply chain documented. #Traced',
     "Founded 1952 by Harland Sanders in Corbin KY. Colonel Sanders sold the brand 1964 for $2M cash and a pension. Acquired by PepsiCo, then spun off into Yum! Brands. 27,000+ global locations.",
     0, None, 0, 1952, 1964),

    ('pizza-hut', 'Pizza Hut', 'pizza-hut', 'restaurant', 'fast_casual', 1, 'red', 0, 0, 'yum-brands',
     'Pizza Hut is owned by Yum! Brands. Thousands of US store closures since 2019. NPC International (largest franchisee) filed bankruptcy 2020.',
     'Pizza Hut is owned by Yum! Brands. Largest franchisee NPC International filed bankruptcy 2020. 6,000+ US locations closed since peak. Declining brand in contracting casual pizza market. #Traced',
     'Founded 1958 by brothers Dan and Frank Carney in Wichita KS. Sold to PepsiCo 1977. Spun off into Yum! Brands 1997. 18,000+ global locations but US shrinking significantly.',
     0, None, 0, 1958, 1977),

    ('wendys', "Wendy's", 'wendys', 'restaurant', 'fast_casual', 1, 'yellow', 0, 0, 'wendys-corp',
     "Wendy's (NYSE:WEN) announced 'surge pricing' in 2024 — reversed after public backlash. E. coli outbreak 2022 linked to romaine lettuce.",
     "Wendy's announced dynamic 'surge pricing' in 2024 — reversed after consumer backlash. E. coli outbreak 2022. Found in Activist investor Trian Fund's portfolio. #Traced",
     "Founded 1969 by Dave Thomas in Columbus OH. Named after Thomas's daughter Melinda 'Wendy' Thomas. Thomas remained as brand spokesman until his death 2002. IPO 1976.",
     0, None, 0, 1969, None),

    ('in-n-out-burger', 'In-N-Out Burger', 'in-n-out-burger', 'restaurant', 'fast_casual', 1, 'yellow', 0, 0, 'in-n-out',
     "In-N-Out is private, family-owned, and never franchised. Pays workers above minimum wage. Owner donated to California GOP 2022. Hidden menu is real.",
     "In-N-Out: private, family-owned, never franchised, pays above $20/hr starting. Owner donated to CA GOP 2022. One of the most ethical fast food operators — with caveats. #Traced",
     'Founded 1948 by Harry and Esther Snyder in Baldwin Park CA. First drive-through with two-way speaker system. Lynsi Snyder (granddaughter) is current owner. 400+ locations, never franchised.',
     0, None, 0, 1948, None),

    ('five-guys-brand', 'Five Guys', 'five-guys', 'restaurant', 'fast_casual', 2, 'yellow', 0, 0, 'five-guys',
     'Five Guys is private, family-owned, and uses fresh (never frozen) beef. Premium pricing: $20+ for a combo. Peanut allergy risk is real and documented.',
     'Five Guys: private, family-owned, fresh beef, but $20+ for a combo in 2024. Peanut allergy risk at every location. Still family-controlled by the Murrell family. #Traced',
     'Founded 1986 by Jerry and Janie Murrell and their five sons (hence "Five Guys") in Arlington VA. Franchised 2003 and expanded rapidly. Still Murrell family-owned.',
     0, None, 0, 1986, None),

    ('subway', 'Subway', 'subway', 'restaurant', 'fast_casual', 1, 'red', 0, 1, 'subway-restaurants',
     "Subway sold to Roark Capital PE 2023 for $9.6B after decades of franchisee scandals. 'Tuna' DNA controversy 2021. 8,000 US stores closed since 2015.",
     "Subway sold to Roark Capital PE 2023 for $9.6B after 8,000 US store closures since 2015 and the 'tuna has no tuna DNA' CBC investigation. #Traced",
     'Founded 1965 by 17-year-old Fred DeLuca and family friend Peter Buck in Bridgeport CT. DeLuca ran the company until his death 2015. Sold to Roark Capital 2023.',
     1, "Subway's 'chicken' tested at 50% soy protein content by CBC News 2021. Tuna was also tested — no tuna DNA found, though Subway disputes methodology.",
     0, 1965, 2023),

    ('chick-fil-a-brand', 'Chick-fil-A', 'chick-fil-a', 'restaurant', 'fast_casual', 1, 'red', 0, 0, 'chick-fil-a',
     "Chick-fil-A donated $1.8M+ to anti-LGBTQ organizations through 2018. Pledged to stop 2019, then reversed. Closed Sundays. Highest per-location revenue of any fast food chain.",
     "Chick-fil-A donated $1.8M+ to anti-LGBTQ orgs. Said they'd stop in 2019 — then reversed. Closed Sundays. Still the highest-volume fast food chain per location. #Traced",
     'Founded 1967 by S. Truett Cathy in College Park GA. Cathy was a devout Baptist who closed on Sundays as a religious practice. Family-owned by the Cathy family. 2,800+ locations.',
     0, None, 0, 1967, None),

    ('panda-express', 'Panda Express', 'panda-express', 'restaurant', 'fast_casual', 1, 'yellow', 0, 0, 'panda-restaurant-group',
     "Panda Express is privately owned by the Cherng family. Wage theft settlements in CA and NY. 'American Chinese' — no authentic Chinese ownership or connection.",
     "Panda Express is owned by the Cherng family (Chinese-American). Wage theft settlements in CA and NY. 'American Chinese' food: no link to authentic Chinese cuisine or China. #Traced",
     'Founded 1983 by Andrew and Peggy Cherng in Glendale CA as extension of their Panda Inn sit-down restaurant. Family still owns 100%. 2,300+ locations, all company-owned.',
     0, None, 0, 1983, None),

    ('popeyes', 'Popeyes Louisiana Kitchen', 'popeyes', 'restaurant', 'fast_casual', 1, 'red', 0, 1, 'rbi',
     "Popeyes is owned by Restaurant Brands International (3G Capital PE). The chicken sandwich that broke the internet in 2019 was an RBI marketing win. Workers didn't benefit.",
     "Popeyes is 3G Capital PE via RBI. The 2019 chicken sandwich craze drove massive sales — but workers saw little benefit. Wage theft documented across franchise network. #Traced",
     'Founded 1972 by Al Copeland in Arabi, Louisiana. Grew via franchise model. Acquired by AFC Enterprises 1989, Restaurant Brands International 2017 for $1.8B.',
     0, None, 0, 1972, 2017),

    ('jack-in-the-box-brand', 'Jack in the Box', 'jack-in-the-box-restaurant', 'restaurant', 'fast_casual', 1, 'yellow', 0, 0, 'jack-in-the-box',
     'Jack in the Box (NYSE:JACK) acquired Del Taco 2022 with heavy debt. Known for 1993 E. coli outbreak that killed 4 children and triggered national food safety reform.',
     'Jack in the Box: E. coli outbreak 1993 killed 4 children — triggering the modern USDA food safety system. Now owns Del Taco. Public (NYSE:JACK). #Traced',
     'Founded 1951 by Robert O. Peterson in San Diego CA. Early pioneer of drive-through service. E. coli outbreak 1993 was pivotal in US food safety reform. 2,200+ locations, primarily western US.',
     0, None, 0, 1951, None),

    ('del-taco', 'Del Taco', 'del-taco', 'restaurant', 'fast_casual', 1, 'yellow', 0, 0, 'jack-in-the-box',
     'Del Taco was acquired by Jack in the Box for $585M in 2022. Jack in the Box loaded up with debt for this acquisition. West Coast Mexican fast food institution.',
     'Del Taco was acquired by Jack in the Box for $585M in 2022 — a debt-heavy deal that burdened JACK (public). West Coast institution now part of leveraged roll-up. #Traced',
     'Founded 1964 by Ed Hackbarth and David Jameson in Yermo CA. Grew in western US. Acquired by Jack in the Box 2022.',
     0, None, 0, 1964, 2022),

    ('carls-jr', "Carl's Jr.", 'carls-jr', 'restaurant', 'fast_casual', 1, 'red', 0, 1, 'roark-capital',
     "Carl's Jr. is owned by Roark Capital PE via CKE Restaurants. Known for hypersexualized advertising and PE cost-cutting.",
     "Carl's Jr. is Roark Capital PE via CKE Restaurants. Infamous for hypersexualized advertising under prior CEO. PE cost-cutting has reduced quality. #Traced",
     'Founded 1941 by Carl Karcher and wife Margaret in Los Angeles. Grew into western US chain. Acquired by CKE Restaurants, then by various PE firms, now Roark Capital. 3,800+ global locations.',
     0, None, 0, 1941, None),

    ('wingstop-brand', 'Wingstop', 'wingstop-restaurant', 'restaurant', 'fast_casual', 2, 'yellow', 0, 0, 'wingstop-corp',
     'Wingstop (NYSE:WING) is 98% franchised. Menu prices up 40%+ since 2020 due to chicken commodity volatility. Digital-only model creates access barriers.',
     'Wingstop (NYSE:WING) raised prices 40%+ since 2020. Digital-only ordering model. 98% franchised — corporate profits extracted from local operators. #Traced',
     'Founded 1994 by Antonio Swad in Garland TX with backing from NFL player Troy Aikman. IPO 2015. 2,100+ locations, 98% franchised. 66%+ of orders are digital.',
     0, None, 0, 1994, None),

    ('panera-bread-brand', 'Panera Bread', 'panera-bread', 'restaurant', 'fast_casual', 2, 'red', 0, 1, 'panera-bread-roark',
     "Panera's Charged Lemonade killed a customer in 2024. Now owned by Roark Capital PE. 'Clean food' claims increasingly contradicted.",
     "Panera Bread's Charged Lemonade killed a 21-year-old in 2024 — 390mg caffeine in one drink. PE-owned by Roark Capital. 'Clean' label is marketing, not reality. #Traced",
     'Founded 1987 as Au Bon Pain in St. Louis by Ron Shaich. Rebranded to Panera Bread 1999. Acquired by JAB Holding 2017 for $7.5B. Sold to Roark Capital 2024 after failed IPO.',
     1, "Post-JAB/Roark acquisition, Panera's soups reformulated to extend shelf life. Charged Lemonade caffeine levels not disclosed on menu boards. 'Clean' ingredient claims selectively applied.",
     1, 1987, 2017),

    ('cava-brand', 'Cava', 'cava', 'restaurant', 'fast_casual', 2, 'yellow', 0, 0, 'cava-group',
     'Cava (NYSE:CAVA) is public and growing rapidly. IPO 2023 at $22/share. Mediterranean fast casual done at scale.',
     'Cava (NYSE:CAVA) went public June 2023 — one of the most successful restaurant IPOs in years. Mediterranean fast casual. 340+ locations and growing. #Traced',
     'Founded 2010 by Ted Xenohristos, Ike Grigoropoulos, and Dimitri Moshovitis in Rockville MD. Started as a small restaurant, developed proprietary dips/spreads. IPO 2023.',
     0, None, 0, 2010, None),

    ('tender-greens', 'Tender Greens', 'tender-greens', 'restaurant', 'fast_casual', 2, 'yellow', 0, 0, 'sweetgreen-corp',
     'Tender Greens was acquired by Sweetgreen for just $6M in 2023 — a distressed sale after the pandemic. Originally a chef-driven farm-to-table fast casual chain.',
     'Tender Greens sold to Sweetgreen for $6M in 2023 — once valued at $100M+. A pandemic casualty acquired at distressed price by (also struggling) Sweetgreen. #Traced',
     'Founded 2006 by chefs Erik Oberholtzer, David Dworshak, and Matt Lyman in Culver City CA. Chef-driven fast casual with rotating seasonal menus. Acquired by Sweetgreen 2023.',
     1, 'Post-Sweetgreen acquisition, standardization of menus reduced chef-driven specials. Seasonal rotation compressed.',
     0, 2006, 2023),

    ('habit-burger', 'Habit Burger Grill', 'habit-burger', 'restaurant', 'fast_casual', 1, 'red', 0, 0, 'yum-brands',
     "Habit Burger is owned by Yum! Brands — the same conglomerate that owns Taco Bell, KFC, and Pizza Hut. Acquired 2020 for $375M.",
     'Habit Burger was acquired by Yum! Brands (Taco Bell/KFC parent) in 2020 for $375M. From California independent to fast food conglomerate in one deal. #Traced',
     'Founded 1969 by Bruce and Richard Reichart in Santa Barbara CA. Known for "charburgers" cooked over open flame. Stayed regional until PE-backed, acquired by Yum! Brands 2020.',
     0, None, 0, 1969, 2020),

    ('jimmy-johns', "Jimmy John's", 'jimmy-johns', 'restaurant', 'fast_casual', 1, 'red', 0, 1, 'inspire-brands',
     "Jimmy John's is owned by Inspire Brands (Roark Capital PE). Founder Jimmy John Liautaud is infamous for trophy hunting. Non-compete clauses for sandwich workers.",
     "Jimmy John's (Roark Capital PE via Inspire Brands) imposed non-compete clauses on sandwich workers earning $7.25/hr. Founder Jimmy John is a trophy hunter. #Traced",
     "Founded 1983 by Jimmy John Liautaud (19 years old) with $25K loan from his father in Charleston IL. Sold majority stake to private equity 2016. Acquired by Inspire Brands (Roark) 2019.",
     0, None, 0, 1983, 2019),

    ('sonic-brand', 'Sonic Drive-In', 'sonic-drive-in', 'restaurant', 'fast_casual', 1, 'red', 0, 1, 'inspire-brands',
     "Sonic is owned by Inspire Brands (Roark Capital PE). Known for roller-skating carhops. Wage theft settlements. 3,500+ drive-in locations.",
     "Sonic is Roark Capital PE via Inspire Brands. 3,500+ drive-in locations, mostly franchised. Wage theft documented. Classic American drive-in, now PE-extracted. #Traced",
     'Founded 1953 by Troy Smith in Shawnee OK as "Top Hat Drive-In." Renamed Sonic 1959. Acquired by Roark Capital 2018 for $2.3B, then folded into Inspire Brands.',
     0, None, 0, 1953, 2018),

    ('arbys', "Arby's", 'arbys', 'restaurant', 'fast_casual', 1, 'red', 0, 1, 'inspire-brands',
     "Arby's is owned by Inspire Brands (Roark Capital PE). 'We have the meats' — and the PE fees. Wage theft across franchise network.",
     "Arby's is Roark Capital PE via Inspire Brands. 'We have the meats' — and the PE fees. Wage theft settlements across franchise network. #Traced",
     "Founded 1964 by Forrest and Leroy Raffel in Boardman OH. Known for roast beef. Acquired by Roark Capital 2011, became cornerstone of Inspire Brands empire.",
     0, None, 0, 1964, 2011),

    ('buffalo-wild-wings', 'Buffalo Wild Wings', 'buffalo-wild-wings', 'restaurant', 'sit_down', 2, 'red', 0, 1, 'inspire-brands',
     "Buffalo Wild Wings is owned by Inspire Brands (Roark Capital PE). Acquired 2018 for $2.9B. Worker injury rates high in high-volume sports bar environment.",
     "Buffalo Wild Wings is Roark Capital PE via Inspire Brands ($2.9B acquisition 2018). Sports bar model drives alcohol-related incidents. Worker injury rates elevated. #Traced",
     'Founded 1982 by Jim Disbrow and Scott Lowery in Columbus OH. Grew into largest sports bar chain in US. Acquired by Arby\'s Restaurant Group (now Inspire Brands) 2018 for $2.9B.',
     0, None, 0, 1982, 2018),

    ('firehouse-subs', 'Firehouse Subs', 'firehouse-subs', 'restaurant', 'fast_casual', 1, 'red', 0, 1, 'rbi',
     'Firehouse Subs was acquired by Restaurant Brands International (3G Capital PE) in 2021 for $1B. Founded by firefighter brothers, now part of BK/Tim Hortons/Popeyes conglomerate.',
     'Firehouse Subs sold to 3G Capital PE (via RBI, same owners as Burger King) for $1B in 2021. Founded by firefighter brothers, now extracted by PE. #Traced',
     'Founded 1994 by firefighter brothers Robin and Chris Sorensen in Jacksonville FL. Grew to 1,200+ locations. Acquired by Restaurant Brands International 2021 for $1B.',
     0, None, 0, 1994, 2021),

    ('jersey-mikes-brand', "Jersey Mike's", 'jersey-mikes-subs', 'restaurant', 'fast_casual', 1, 'red', 0, 1, 'jersey-mikes',
     "Jersey Mike's sold majority stake to Blackstone PE for $8B valuation in 2023. From NJ beach sub shop to PE-extracted chain. Prices up 25%+ since 2021.",
     "Jersey Mike's sold majority to Blackstone PE in 2023 at $8B valuation. From Point Pleasant NJ beach town origin to private equity extraction. Prices up 25%+. #Traced",
     'Founded 1956 as Mike\'s Subs in Point Pleasant NJ. Pete Cancro bought the store at 17 with his football coach\'s help. Grew via franchise model. Sold majority to Blackstone 2023.',
     0, None, 0, 1956, 2023),

    ('smashburger', 'Smashburger', 'smashburger', 'restaurant', 'fast_casual', 2, 'red', 0, 0, 'jollibee-foods',
     'Smashburger is owned by Jollibee Foods Corporation (Philippines). Declining US traffic since acquisition. PE-to-international-corporate ownership journey.',
     'Smashburger was once a VC-backed disruptor — now owned by Jollibee (Philippines). Declining US traffic. A cautionary tale of VC → PE → foreign corporate acquisition. #Traced',
     'Founded 2007 by Tom Ryan and Rick Schaden in Denver CO. VC-backed, grew rapidly to 370+ locations. Sold to Jollibee Foods Corp (Philippines) 2018. Declining US locations since.',
     0, None, 0, 2007, 2018),

    ('raising-canes-brand', "Raising Cane's", 'raising-canes', 'restaurant', 'fast_casual', 1, 'yellow', 0, 0, 'raising-canes',
     "Raising Cane's is private, family-founded, and never franchised. Only sells chicken fingers. Founder Todd Graves overcame 64 rejection letters from investors.",
     "Raising Cane's: private, family-owned, never franchised. Founder Todd Graves was rejected by 64 investors and worked crabbing boats to fund first location. #Traced",
     'Founded 1996 by Todd Graves in Baton Rouge LA after 64 investor rejections. Raised startup capital working on Alaskan fishing boats. Named after his dog Raising Cane.',
     0, None, 0, 1996, None),

    # SIT-DOWN CHAINS
    ('olive-garden', 'Olive Garden', 'olive-garden', 'restaurant', 'sit_down', 2, 'yellow', 0, 0, 'darden-restaurants',
     'Olive Garden is owned by Darden Restaurants (NYSE:DRI). $2.85M wage theft settlement for tipped workers. Unlimited breadsticks funded by labor exploitation.',
     "Olive Garden (Darden/NYSE:DRI) paid $2.85M to settle tipped worker wage theft. Tip pool manipulation documented. Those unlimited breadsticks aren't free for workers. #Traced",
     'Founded 1982 by General Mills in Orlando FL. Acquired by Darden Restaurants 1995 when General Mills spun off restaurant operations. 900+ US locations.',
     0, None, 0, 1982, None),

    ('applebees', "Applebee's", 'applebees', 'restaurant', 'sit_down', 2, 'yellow', 0, 0, 'dine-brands',
     "Applebee's is owned by Dine Brands Global (NYSE:DIN). Known for alcohol-forward promotions and dollar drinks. Tipping exploitation documented.",
     "Applebee's is Dine Brands (NYSE:DIN). Dollar margarita promotions drive traffic but workers report tipping exploitation. All locations are franchised. #Traced",
     "Founded 1980 by Bill and T.J. Palmer in Decatur GA. Acquired by IHOP Corp 2007. Became Dine Brands Global 2018. 1,600+ US locations, all franchised.",
     0, None, 0, 1980, None),

    ('ihop', 'IHOP', 'ihop', 'restaurant', 'sit_down', 2, 'yellow', 0, 0, 'dine-brands',
     'IHOP is owned by Dine Brands Global (NYSE:DIN). Tipped minimum wage exploitation. Wage theft settlements. Famous "IHOb" stunt to sell burgers was a PR gimmick.',
     'IHOP is Dine Brands (NYSE:DIN). Tipped minimum wage workers in states with $2.13/hr minimum. Famous 2018 "IHOb" rebrand to sell burgers was a PR gimmick. #Traced',
     'Founded 1958 by Al Lapin Jr. in Toluca Lake CA. Went public 1961. Acquired by various owners. Now owned by Dine Brands Global. 1,700+ US locations, all franchised.',
     0, None, 0, 1958, None),

    ('cheesecake-factory', 'The Cheesecake Factory', 'cheesecake-factory', 'restaurant', 'sit_down', 3, 'yellow', 0, 0, 'the-cheesecake-factory',
     'Cheesecake Factory (NYSE:CAKE) paid $4.57M in wage theft settlement 2022. 250-item menu with many items exceeding 1,500 calories.',
     'Cheesecake Factory paid $4.57M to 559 workers for wage theft in 2022. Menu items regularly top 1,500 calories. COVID rent non-payment controversy. #Traced',
     'Founded 1978 by David and Evelyn Overton in Beverly Hills CA. Grew from David\'s mother\'s cheesecake recipe. IPO 1992. 300+ locations. Also owns North Italia, Flower Child.',
     0, None, 0, 1978, None),

    ('dennys', "Denny's", 'dennys-diner', 'restaurant', 'sit_down', 1, 'yellow', 0, 0, 'dennys-corp',
     "Denny's (NYSE:DENN) has a long history of racial discrimination settlements. 99% franchised model enables violations with limited corporate accountability.",
     "Denny's reached a landmark civil rights settlement with NAACP in 1994 after widespread racial discrimination at locations. History of ongoing franchise labor violations. #Traced",
     'Founded 1953 by Harold Butler in Lakewood CA as "Danny\'s Donuts." Renamed Denny\'s 1959. Known for 24/7 operations. Filed Chapter 11 bankruptcy 1997, emerged 1998.',
     0, None, 0, 1953, None),

    ('longhorn-steakhouse', 'LongHorn Steakhouse', 'longhorn-steakhouse', 'restaurant', 'sit_down', 2, 'yellow', 0, 0, 'darden-restaurants',
     "LongHorn Steakhouse is owned by Darden Restaurants (Olive Garden parent). Beef sourcing controversy. Tip pool practices questioned.",
     "LongHorn Steakhouse is Darden Restaurants (Olive Garden parent, NYSE:DRI). Beef sourcing transparency limited. Tip pool practices documented in lawsuits. #Traced",
     'Founded 1981 by George McKerrow Jr. in Atlanta GA. Grew into Southeast chain. Acquired by Darden Restaurants 2007 for $1.4B.',
     0, None, 0, 1981, None),

    ('yard-house', 'Yard House', 'yard-house', 'restaurant', 'sit_down', 3, 'yellow', 0, 0, 'darden-restaurants',
     "Yard House is owned by Darden Restaurants. Premium beer-focused casual dining. Acquired by Darden 2012 for $585M.",
     'Yard House is Darden Restaurants (NYSE:DRI). Acquired 2012 for $585M. Premium casual dining with large beer selection. Workers covered under Darden labor disputes. #Traced',
     'Founded 1996 by Harold Sounds and Steele Platt in Long Beach CA. Known for half-yard beer glasses and extensive tap list. Acquired by Darden 2012 for $585M.',
     0, None, 0, 1996, 2012),

    # GROCERY CHAINS
    ('target-grocery', 'Target', 'target', 'grocery', 'market', 2, 'yellow', 0, 0, 'target-corp',
     'Target (NYSE:TGT) pulled LGBTQ Pride merchandise from stores in 2023 under far-right pressure. $22.5M hazardous waste disposal fine. Food is secondary to general merchandise.',
     'Target (NYSE:TGT) removed LGBTQ Pride merchandise from stores in 2023 after far-right protest pressure. $22.5M environmental fine. A retailer, not a grocer. #Traced',
     "Founded 1902 as Dayton Dry Goods in Minneapolis MN. First Target store opened 1962. Acquired by Dayton's parent. Now one of largest US retailers. Food is 20% of sales.",
     0, None, 0, 1902, None),

    ('albertsons-brand', 'Albertsons', 'albertsons-store', 'grocery', 'market', 2, 'red', 0, 1, 'albertsons',
     "Albertsons is majority-owned by Cerberus Capital PE. NLRB union complaints. $24.6B Kroger merger blocked by FTC. Cerberus extracted $400M dividend before deal failed.",
     "Albertsons is Cerberus Capital PE. NLRB union complaints. $24.6B Kroger merger blocked by FTC 2024. Cerberus tried to extract $400M before deal closed — court ordered reversal. #Traced",
     "Founded 1939 by Joe Albertson in Boise ID with $5,000 savings and $7,500 partner loan. Grew to become major western US chain. Various private equity ownership since 1999.",
     0, None, 0, 1939, None),

    ('vons', 'Vons', 'vons', 'grocery', 'market', 2, 'red', 0, 1, 'albertsons',
     "Vons is owned by Albertsons (Cerberus Capital PE). Southern California grocery chain merged into Albertsons portfolio alongside Safeway.",
     "Vons is Cerberus Capital PE via Albertsons. Southern California brand in the same PE portfolio as Safeway, Pavilions, and Jewel-Osco. #Traced",
     'Founded 1906 by Charles Von der Ahe in Los Angeles. Grew across Southern California. Acquired by Safeway 1997, then Albertsons, then back to Safeway. Now in Albertsons/Cerberus portfolio.',
     0, None, 0, 1906, None),

    ('smart-and-final', 'Smart & Final', 'smart-and-final', 'grocery', 'market', 1, 'red', 0, 1, 'smartandfinal',
     "Smart & Final is owned by Apollo Global Management PE. Warehouse-style grocery serving LA/Southwest. Apollo's $1.1B acquisition loaded company with debt.",
     "Smart & Final is Apollo Global Management PE (acquired 2019 for $1.1B). Warehouse grocery format. PE debt load limits investment in stores and workers. #Traced",
     'Founded 1871 in Los Angeles as Hellman-Haas. One of the oldest grocery chains in western US. Acquired by Apollo Global Management 2019 for $1.1B. 250+ stores in CA, AZ, NV.',
     0, None, 0, 1871, None),

    ('grocery-outlet-brand', 'Grocery Outlet', 'grocery-outlet', 'grocery', 'market', 1, 'yellow', 0, 0, 'grocery-outlet',
     "Grocery Outlet (NASDAQ:GO) is public and uses an independent operator model. Discount grocery sourcing closeout merchandise — transparency on reformulated products is limited.",
     "Grocery Outlet (NASDAQ:GO) sells closeout and surplus merchandise — you may be getting discontinued or reformulated products. Independent operator model creates variable labor practices. #Traced",
     'Founded 1946 by Jim Read in San Francisco. Grew in western US. IPO 2019. 500+ stores. Uses "Independent Operator" model — IOs lease stores and operate independently within corporate standards.',
     0, None, 0, 1946, None),

    ('raleys-brand', "Raley's", 'raleys', 'grocery', 'market', 2, 'green', 1, 0, None,
     "Raley's is privately owned by the Raley family for 85+ years. Above-average employee wages and benefits. No PE ownership. Committed to responsible sourcing.",
     "Raley's is independently family-owned for 85+ years — no PE, no public shareholders. Above-industry wages and benefits. A genuine alternative to PE-extracted grocery chains. #Traced",
     'Founded 1935 by Thomas Raley in Placerville CA. Family-owned for 85+ years. 130+ stores in California and Nevada. Known for above-average employee wages and community commitment.',
     0, None, 1, 1935, None),

    ('winco-brand', 'WinCo Foods', 'winco-foods', 'grocery', 'market', 1, 'green', 1, 0, None,
     "WinCo Foods is employee-owned via ESOP (Employee Stock Ownership Plan). Employees are part-owners. No-frills warehouse format with genuine worker ownership.",
     "WinCo Foods is employee-owned (ESOP since 1985) — workers are actual part-owners. No-frills, lowest prices, genuinely different ownership model. #Traced",
     'Founded 1967 as Waremart in Boise ID. Employee Stock Ownership Plan (ESOP) established 1985. Employees accumulate stock as part of compensation. 240+ stores in western US.',
     0, None, 1, 1967, None),

    ('99-ranch-market', '99 Ranch Market', '99-ranch-market', 'grocery', 'market', 2, 'yellow', 0, 0, None,
     '99 Ranch Market is owned by Tawa Supermarket Group (private, California-based). Largest Asian grocery chain in the US. Good prices, wide Asian product selection.',
     '99 Ranch Market is Tawa Supermarket Group (private, CA-based). Largest Asian grocery chain in US with 60+ locations. California-rooted despite pan-Asian reach. #Traced',
     'Founded 1984 by Roger Chen in Westminster CA (Little Saigon). Tawa Supermarket Group now operates 60+ Ranch 99 and 99 Ranch Market locations across US, primarily in Chinese-American communities.',
     0, None, 0, 1984, None),
]

for row in NEW_BRANDS:
    (bid, name, slug, category, fmt, price_tier, zone, indep, pe_owned, parent_id,
     headline, share, founder, ingr_drift, ingr_note, watch, founded, acquired) = row
    c.execute("""INSERT OR IGNORE INTO brands
        (id, name, slug, category, format, price_tier, overall_zone, independent, pe_owned,
         parent_company_id, headline_finding, share_text, founder_story,
         ingredient_drift, ingredient_drift_note, watch_list, founded_year, acquired_year)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (bid, name, slug, category, fmt, price_tier, zone, indep, pe_owned, parent_id,
         headline, share, founder, ingr_drift, ingr_note, watch, founded, acquired))
print(f"  New chain brands: {len(NEW_BRANDS)} processed")

conn.commit()
print("Part 1 done — companies, chain brands complete")
conn.close()
