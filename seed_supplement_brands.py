#!/usr/bin/env python3
"""
Comprehensive supplement/health brand seed script.
Adds parent companies, updates existing brands, inserts missing brands, adds aliases.
"""
import sqlite3
import sys

DB = 'traced.db'

def run():
    conn = sqlite3.connect(DB)
    c = conn.cursor()

    # ─── STEP 1: ADD NEW COMPANIES ────────────────────────────────────────────

    new_companies = [
        {
            'id': 'butterfly-equity',
            'name': 'Butterfly Equity',
            'type': 'pe',
            'hq_country': 'US',
            'hq_state': 'CA',
            'description': 'LA-based private equity firm focused exclusively on food and beverage sector. Portfolio includes Orgain, Health-Ade, Rainbow Light, Naked Juice.',
            'violation_count': 3,
            'violation_summary': 'Labor disputes at portfolio companies; OSHA citations at manufacturing facilities',
            'lobbying_annual': 800000,
            'lobbying_issues': 'Food labeling regulations, organic certification standards',
        },
        {
            'id': 'orkla',
            'name': 'Orkla ASA',
            'type': 'public',
            'ticker': 'ORK.OL',
            'hq_country': 'NO',
            'description': 'Norwegian conglomerate with branded consumer goods across food, health, and personal care. Acquired Barebells (Swedish protein bar brand) in 2020.',
            'violation_count': 2,
            'violation_summary': 'EU antitrust scrutiny on food market dominance in Nordic markets',
            'lobbying_annual': 1200000,
            'lobbying_issues': 'EU food regulations, Nordic trade policy',
        },
        {
            'id': 'stripes-group',
            'name': 'Stripes Group',
            'type': 'pe',
            'hq_country': 'US',
            'hq_state': 'NY',
            'description': 'Growth equity firm focused on consumer and technology companies. Acquired majority stake in Kite Hill (plant-based dairy) in 2021.',
            'violation_count': 1,
            'violation_summary': 'Portfolio company labor disputes',
            'lobbying_annual': 400000,
            'lobbying_issues': 'Plant-based labeling regulations',
        },
        {
            'id': 'l-catterton',
            'name': 'L Catterton',
            'type': 'pe',
            'hq_country': 'US',
            'hq_state': 'CT',
            'description': 'World\'s largest consumer-focused private equity firm, backed by LVMH. $30B+ AUM. Portfolio includes Hippeas, Cholula, Peloton, Elf Cosmetics.',
            'violation_count': 8,
            'violation_summary': 'Multiple portfolio companies cited for misleading health claims; FTC scrutiny on greenwashing at portfolio brands',
            'lobbying_annual': 3200000,
            'lobbying_issues': 'Consumer goods regulations, FTC advertising rules, luxury goods trade policy',
        },
        {
            'id': 'primavera-capital',
            'name': 'Primavera Capital Group',
            'type': 'pe',
            'hq_country': 'CN',
            'description': 'Chinese private equity firm with $15B+ AUM. Acquired majority stake in Simple Mills in 2023. Focus on consumer and technology sectors.',
            'violation_count': 4,
            'violation_summary': 'CFIUS concerns over US food brand ownership; VIE structure opacity',
            'lobbying_annual': 1800000,
            'lobbying_issues': 'US-China investment regulations, CFIUS review process',
        },
        {
            'id': 'lactalis',
            'name': 'Lactalis Group',
            'type': 'private',
            'hq_country': 'FR',
            'description': 'World\'s largest dairy company, French family-owned (Besnier family). $25B+ revenue. Acquired Stonyfield from Danone in 2017. Known for opacity — refuses to publish annual reports.',
            'violation_count': 24,
            'violation_summary': 'Salmonella scandal 2017 (12 infants hospitalized), recalled 40M+ baby formula products; multiple food safety violations across Europe',
            'lobbying_annual': 4100000,
            'lobbying_issues': 'EU dairy regulations, food safety standards, trade policy',
        },
        {
            'id': 'celsius-holdings',
            'name': 'Celsius Holdings Inc.',
            'type': 'public',
            'ticker': 'CELH',
            'hq_country': 'US',
            'hq_state': 'FL',
            'description': 'Publicly traded energy drink company. Celsius brand markets itself as a "fitness drink" and "calorie-burning" beverage. PepsiCo distribution deal 2022.',
            'violation_count': 5,
            'violation_summary': 'FTC warning for unsubstantiated "calorie burning" claims; class action lawsuit for deceptive health marketing',
            'lobbying_annual': 600000,
            'lobbying_issues': 'Energy drink regulations, health claim labeling',
        },
        {
            'id': 'vita-coco-co',
            'name': 'The Vita Coco Company',
            'type': 'public',
            'ticker': 'COCO',
            'hq_country': 'US',
            'hq_state': 'NY',
            'description': 'Publicly traded coconut water company (NYSE:COCO). Founded 2004 by Michael Kirban and Ira Liran. Founder-led public company.',
            'violation_count': 2,
            'violation_summary': 'FTC settlement over exaggerated health claims for coconut water; labor concerns in coconut sourcing',
            'lobbying_annual': 300000,
            'lobbying_issues': 'Beverage health claim labeling, import regulations',
        },
        {
            'id': 'china-mengniu',
            'name': 'China Mengniu Dairy',
            'type': 'public',
            'ticker': '2319.HK',
            'hq_country': 'CN',
            'description': 'One of China\'s largest dairy conglomerates. Acquired siggi\'s Icelandic Skyr brand in 2018. State-linked enterprise with COFCO as major shareholder.',
            'violation_count': 18,
            'violation_summary': 'Melamine milk scandal (linked via supply chain), multiple food safety violations in China, worker safety issues',
            'lobbying_annual': 2200000,
            'lobbying_issues': 'US dairy import regulations, CFIUS review, food labeling requirements',
        },
        {
            'id': 'keurig-dr-pepper',
            'name': 'Keurig Dr Pepper Inc.',
            'type': 'public',
            'ticker': 'KDP',
            'hq_country': 'US',
            'hq_state': 'TX',
            'description': 'Publicly traded beverage giant (NASDAQ:KDP). JAB Holding-controlled. Acquired Bai Brands in 2017 for $1.7B.',
            'violation_count': 14,
            'violation_summary': 'EPA violations for plastic waste; FTC scrutiny on health claims; antitrust concerns in coffee pod market',
            'lobbying_annual': 5800000,
            'lobbying_issues': 'Beverage container regulations, sugar taxes, caffeine labeling, antitrust policy',
        },
        {
            'id': 'thorne-healthtech',
            'name': 'Thorne HealthTech Inc.',
            'type': 'public',
            'ticker': 'THRN',
            'hq_country': 'US',
            'hq_state': 'NY',
            'description': 'Publicly traded supplement company (NASDAQ:THRN) known for third-party tested, practitioner-grade supplements. Founded 1984.',
            'violation_count': 1,
            'violation_summary': 'Minor FDA labeling compliance issues',
            'lobbying_annual': 280000,
            'lobbying_issues': 'Supplement regulation, DSHEA modernization',
        },
        {
            'id': 'ancient-nutrition-pe',
            'name': 'KSF Outdoor / Ancient Nutrition PE',
            'type': 'pe',
            'hq_country': 'US',
            'description': 'Private equity backing for Ancient Nutrition (Dr. Josh Axe brand). PE group acquired majority stake in 2019.',
            'violation_count': 2,
            'violation_summary': 'FTC warning letters for unsubstantiated health claims on collagen and adaptogen products',
            'lobbying_annual': 200000,
            'lobbying_issues': 'Health food labeling, supplement regulations',
        },
        {
            'id': 'innova-capital',
            'name': 'Innova Capital',
            'type': 'pe',
            'hq_country': 'US',
            'description': 'Private equity firm that acquired MegaFood in 2023.',
            'violation_count': 0,
            'violation_summary': None,
            'lobbying_annual': 100000,
            'lobbying_issues': 'Supplement manufacturing regulations',
        },
    ]

    for co in new_companies:
        c.execute('''
            INSERT OR IGNORE INTO companies
            (id, name, type, ticker, hq_country, hq_state, description,
             violation_count, violation_summary, lobbying_annual, lobbying_issues)
            VALUES (?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            co['id'], co['name'], co['type'], co.get('ticker'),
            co.get('hq_country'), co.get('hq_state'), co.get('description'),
            co.get('violation_count', 0), co.get('violation_summary'),
            co.get('lobbying_annual', 0), co.get('lobbying_issues'),
        ))
        print(f"  Company: {co['id']}")

    conn.commit()
    print(f"\nCompanies added/verified: {len(new_companies)}")

    # ─── STEP 2: UPDATE EXISTING BRANDS ──────────────────────────────────────
    # (brands already in DB but missing zone/parent/story data)

    updates = [
        # id, category, overall_zone, parent_company_id, pe_owned, independent,
        # headline_finding, share_text, founder_story, watch_list
        {
            'id': 'optimum-nutrition',
            'category': 'supplement',
            'overall_zone': 'red',
            'parent_company_id': 'f28db92d-c4c8-423c-8d17-b2f4e9e65e96',  # Glanbia
            'pe_owned': 0, 'independent': 0,
            'founded_year': 1986, 'acquired_year': 2000,
            'acquisition_price': 120000000,
            'headline_finding': 'Owned by Glanbia, Irish dairy multinational — founder vision sold to industrial commodity player',
            'share_text': 'Optimum Nutrition (Gold Standard Whey) is owned by Glanbia, an Irish multinational dairy corporation. Your protein shake profits flow to Dublin.',
            'founder_story': 'Founded 1986 in Aurora, IL by Michael Costello. Built the Gold Standard Whey brand as a quality benchmark for protein. Acquired by Glanbia in 2000.',
            'watch_list': 1,
        },
        {
            'id': 'garden-of-life',
            'category': 'supplement',
            'overall_zone': 'red',
            'parent_company_id': 'nestle',
            'pe_owned': 0, 'independent': 0,
            'founded_year': 2000, 'acquired_year': 2017,
            'acquisition_price': 305000000,
            'headline_finding': 'Nestlé paid $305M for Garden of Life\'s organic halo — company still markets "independent brand" messaging',
            'share_text': 'Garden of Life is owned by Nestlé ($305M, 2017). The "certified organic" and "non-GMO" messaging now funds the world\'s largest food conglomerate.',
            'founder_story': 'Founded 2000 by Jordan Rubin in West Palm Beach, FL. Built on his personal health recovery story and whole food supplement philosophy. Sold to Nestlé in 2017.',
            'watch_list': 2,
        },
        {
            'id': '64f50941-cba6-4125-9ea3-7ea52d1459d3',  # Vega
            'category': 'supplement',
            'overall_zone': 'red',
            'parent_company_id': 'danone',
            'pe_owned': 0, 'independent': 0,
            'founded_year': 2001, 'acquired_year': 2015,
            'acquisition_price': 550000000,
            'headline_finding': 'Danone paid $550M for Vega\'s plant-based cred — formula changes noted post-acquisition',
            'share_text': 'Vega is owned by Danone ($550M, 2015). The plant-based protein brand\'s mission now serves a French dairy multinational\'s quarterly earnings.',
            'founder_story': 'Founded 2001 by Brendan Brazier (pro triathlete) and Charles Chang in Vancouver, BC. Built on Brazier\'s plant-based performance philosophy.',
            'watch_list': 1,
        },
        {
            'id': 'orgain',
            'category': 'supplement',
            'overall_zone': 'red',
            'parent_company_id': 'butterfly-equity',
            'pe_owned': 1, 'independent': 0,
            'founded_year': 2009, 'acquired_year': 2021,
            'headline_finding': 'Butterfly Equity took majority stake in 2021 — Orgain markets "clean nutrition" while PE extracts value',
            'share_text': 'Orgain is PE-owned by Butterfly Equity (majority stake, 2021). The "clean and simple" protein shake now generates returns for a Los Angeles private equity fund.',
            'founder_story': 'Founded 2009 by Dr. Andrew Abraham, a pediatric oncology survivor, to create clean-ingredient nutrition. Built on authentic health story.',
            'watch_list': 2,
        },
        {
            'id': 'clif-bar',
            'category': 'supplement',
            'overall_zone': 'red',
            'parent_company_id': 'mondelez',
            'pe_owned': 0, 'independent': 0,
            'founded_year': 1992, 'acquired_year': 2022,
            'acquisition_price': 2900000000,
            'headline_finding': 'Mondelēz paid $2.9B for Clif Bar — founders who turned down $120M buyout in 2000 finally sold to Oreo\'s parent',
            'share_text': 'Clif Bar is now owned by Mondelēz (Oreo, Cadbury) for $2.9B (2022). The outdoor adventure brand that famously rejected buyouts now funds a snack conglomerate.',
            'founder_story': 'Founded 1992 by Gary Erickson in Berkeley, CA. Named after his father Clifford. Famously turned down a $120M acquisition offer in 2000 to stay independent.',
            'watch_list': 2,
        },
        {
            'id': 'rxbar',
            'category': 'supplement',
            'overall_zone': 'red',
            'parent_company_id': 'mars',
            'pe_owned': 0, 'independent': 0,
            'founded_year': 2012, 'acquired_year': 2017,
            'acquisition_price': 600000000,
            'headline_finding': 'Kellogg\'s paid $600M in 2017; Mars acquired Kellogg\'s snack division in 2024 — RXBAR now owned by candy giant',
            'share_text': 'RXBAR started with "No BS" marketing. Now owned by Mars Inc. (M&Ms, Snickers) after Mars acquired Kellogg\'s snack brands in 2024.',
            'founder_story': 'Founded 2012 by Peter Rahal and Jared Smith in Chicago. Famous for "No B.S." minimal-ingredient label. Sold to Kellogg\'s for $600M in 2017.',
            'watch_list': 2,
        },
        {
            'id': 'kind',
            'category': 'supplement',
            'overall_zone': 'red',
            'parent_company_id': 'mars',
            'pe_owned': 0, 'independent': 0,
            'founded_year': 2004, 'acquired_year': 2020,
            'headline_finding': 'Mars owns Kind Bar — the "be kind to your body" brand feeds profits to the world\'s largest candy company',
            'share_text': 'KIND bars are owned by Mars Inc. (M&Ms, Snickers, Twix). Mars acquired majority in 2017 and full ownership in 2020.',
            'founder_story': 'Founded 2004 by Daniel Lubetzky in NYC. Built on mission of kindness and whole ingredient snacking. Mars acquired minority stake 2017, full ownership 2020.',
            'watch_list': 1,
        },
        {
            'id': '9f90ddbc-90ea-41ca-9851-3735e7260735',  # Quest Nutrition
            'category': 'supplement',
            'overall_zone': 'yellow',
            'parent_company_id': '35f49ad8-80d7-4d67-84e7-2fb4321b3e91',  # Simply Good Foods
            'pe_owned': 0, 'independent': 0,
            'founded_year': 2010, 'acquired_year': 2019,
            'acquisition_price': 1000000000,
            'headline_finding': 'Quest acquired by Simply Good Foods (public) for $1B in 2019 — now part of Atkins Nutritionals parent company',
            'share_text': 'Quest Nutrition is owned by Simply Good Foods (NASDAQ:SMPL) — the same public company that owns Atkins. Acquired for $1B in 2019.',
            'founder_story': 'Founded 2010 by Tom Bilyeu, Ron Penna, and Mike Osborn in El Segundo, CA. Built high-protein, low-carb bars and scaled to a $1B brand.',
            'watch_list': 0,
        },
        {
            'id': 'larabar',
            'category': 'supplement',
            'overall_zone': 'red',
            'parent_company_id': 'general-mills',
            'pe_owned': 0, 'independent': 0,
            'founded_year': 2000, 'acquired_year': 2008,
            'headline_finding': 'General Mills bought Lärabar for its "whole food" credibility — now a minor brand in a cereal conglomerate portfolio',
            'share_text': 'Lärabar is owned by General Mills (Cheerios, Lucky Charms). The 2-ingredient bar concept now serves a Fortune 500 company\'s portfolio strategy.',
            'founder_story': 'Founded 2000 by Lara Merriken in Denver, CO. Created simple fruit-and-nut bars from a hiking trip inspiration. Sold to General Mills in 2008.',
            'watch_list': 0,
        },
        {
            'id': 'perfect-bar',
            'category': 'supplement',
            'overall_zone': 'red',
            'parent_company_id': 'nestle',
            'pe_owned': 0, 'independent': 0,
            'founded_year': 2005, 'acquired_year': 2019,
            'acquisition_price': 75000000,
            'headline_finding': 'Nestlé acquired Perfect Bar for $75M in 2019 — refrigerated protein bar innovation now a Nestlé line extension',
            'share_text': 'Perfect Bar is owned by Nestlé ($75M, 2019). The family-founded refrigerated protein bar now feeds the world\'s largest food company\'s nutrition portfolio.',
            'founder_story': 'Founded 2005 by the Keith family in San Diego, CA. Inspired by patriarch Bud Keith\'s whole-food philosophy. The Keith family sold to Nestlé in 2019.',
            'watch_list': 0,
        },
        {
            'id': 'cae5cbef-9fc1-4275-a495-da55906596cf',  # GoMacro
            'category': 'supplement',
            'overall_zone': 'green',
            'parent_company_id': None,
            'pe_owned': 0, 'independent': 1,
            'founded_year': 2003,
            'headline_finding': 'Founder-owned macrobiotic protein bar — Amelia and Julia Kirchner still run the company they built in Viola, WI',
            'share_text': 'GoMacro is independently owned by the Kirchner family — Amelia and her daughter Julia. Founded in Wisconsin from a plant-based health journey. Real ownership transparency.',
            'founder_story': 'Founded 2003 in Viola, WI by Amelia Kirchner after a cancer diagnosis drove her to a macrobiotic diet. Her daughter Julia joined and runs the company today.',
            'watch_list': 0,
        },
        {
            'id': 'navitas-organics',
            'category': 'supplement',
            'overall_zone': 'green',
            'parent_company_id': None,
            'pe_owned': 0, 'independent': 1,
            'founded_year': 2003,
            'headline_finding': 'Independent superfood brand — founder Dave Asarnow still leads company focused on nutrient-dense sourcing',
            'share_text': 'Navitas Organics is independently owned. Founded 2003 in Novato, CA by Dave Asarnow with a focus on certified organic superfoods and fair trade sourcing.',
            'founder_story': 'Founded 2003 in Novato, CA by Dave Asarnow. Pioneered bringing açaí, maca, and cacao products to mainstream US market with organic and fair trade standards.',
            'watch_list': 0,
        },
        {
            'id': 'celsius',
            'category': 'beverage',
            'overall_zone': 'yellow',
            'parent_company_id': 'celsius-holdings',
            'pe_owned': 0, 'independent': 0,
            'founded_year': 2004,
            'headline_finding': 'Celsius markets itself as a "fitness drink" — FTC issued warning over unsubstantiated calorie-burning claims',
            'share_text': 'Celsius (CELH) is a public company that was sued for false "calorie burning" claims. PepsiCo distribution deal 2022 made it ubiquitous.',
            'founder_story': 'Celsius Holdings founded 2004 in Delray Beach, FL. Energy drink positioned as fitness-focused alternative. Went public on NASDAQ.',
            'watch_list': 1,
        },
        {
            'id': 'liquid-i-v',
            'category': 'beverage',
            'overall_zone': 'red',
            'parent_company_id': 'unilever',
            'pe_owned': 0, 'independent': 0,
            'founded_year': 2012, 'acquired_year': 2020,
            'headline_finding': 'Unilever acquired Liquid I.V. in 2020 — the "hydration multiplier" brand now funds a multinational consumer goods corporation',
            'share_text': 'Liquid I.V. is owned by Unilever (acquired 2020). The electrolyte brand\'s viral DTC growth made it an acquisition target.',
            'founder_story': 'Founded 2012 by Brent Pottenger and Brandon Cohen in Los Angeles. Built viral DTC brand around "Cellular Transport Technology" for hydration.',
            'watch_list': 1,
        },
        {
            'id': '517a23f4-f987-4084-a722-120baef3cb34',  # LMNT
            'category': 'beverage',
            'overall_zone': 'green',
            'parent_company_id': None,
            'pe_owned': 0, 'independent': 1,
            'founded_year': 2018,
            'headline_finding': 'Founder-owned electrolyte brand — Robb Wolf and Luis Villasenor still lead the company they bootstrapped',
            'share_text': 'LMNT is independently owned by co-founders Robb Wolf and Luis Villasenor. Founded 2018 in Bozeman, MT. No PE. No conglomerate. The founders answer to you.',
            'founder_story': 'Founded 2018 by Robb Wolf (paleo author) and Luis Villasenor in Bozeman, MT. Created zero-sugar electrolytes for low-carb athletes. Bootstrapped and profitable.',
            'watch_list': 0,
        },
        {
            'id': '055bd5b5-82eb-497c-9d29-b408a72516ea',  # Nuun
            'category': 'beverage',
            'overall_zone': 'red',
            'parent_company_id': 'nestle',
            'pe_owned': 0, 'independent': 0,
            'founded_year': 2004, 'acquired_year': 2022,
            'headline_finding': 'Nestlé acquired Nuun in 2022 — the cyclist-founded electrolyte tablet brand now serves the world\'s largest food company',
            'share_text': 'Nuun electrolyte tablets are owned by Nestlé (acquired 2022). Founded by cyclists for athletes, now a line in Nestlé\'s nutrition portfolio.',
            'founder_story': 'Founded 2004 by Gabe Ryder in Seattle, WA. Invented dissolvable electrolyte tablets for cyclists. Built a loyal endurance sports community.',
            'watch_list': 0,
        },
        {
            'id': 'olipop',
            'category': 'beverage',
            'overall_zone': 'green',
            'parent_company_id': None,
            'pe_owned': 0, 'independent': 1,
            'founded_year': 2018,
            'headline_finding': 'VC-backed but founder-led prebiotic soda — Ben Goodwin still CEO building a challenger to legacy soda brands',
            'share_text': 'OLIPOP is VC-backed but founder-led (Ben Goodwin, CEO). Founded 2018, makes prebiotic sodas with real botanical ingredients. Not PE-owned.',
            'founder_story': 'Founded 2018 by Ben Goodwin and David Lester in Oakland, CA. Created functional soda with prebiotic fiber and botanicals after years of gut health research.',
            'watch_list': 0,
        },
        {
            'id': 'poppi',
            'category': 'beverage',
            'overall_zone': 'red',
            'parent_company_id': 'pepsico',
            'pe_owned': 0, 'independent': 0,
            'founded_year': 2016, 'acquired_year': 2025,
            'acquisition_price': 1650000000,
            'headline_finding': 'PepsiCo acquired Poppi for $1.65B in 2025 — the Shark Tank ACV soda brand now belongs to Big Soda',
            'share_text': 'Poppi was just acquired by PepsiCo for $1.65 BILLION (2025). The apple cider vinegar soda that debuted on Shark Tank now funds Pepsi\'s portfolio.',
            'founder_story': 'Founded 2016 as "Mother Beverage" by Allison and Stephen Ellsworth in Austin, TX. Appeared on Shark Tank 2018. Rebranded to Poppi 2020. PepsiCo acquired 2025.',
            'watch_list': 2,
        },
        {
            'id': 'vita-coco',
            'category': 'beverage',
            'overall_zone': 'yellow',
            'parent_company_id': 'vita-coco-co',
            'pe_owned': 0, 'independent': 0,
            'founded_year': 2004,
            'headline_finding': 'Vita Coco went public (NYSE:COCO) in 2021 — founder-led public company but coconut sourcing raises sustainability questions',
            'share_text': 'Vita Coco is a publicly traded company (COCO) founded by Michael Kirban and Ira Liran. Still founder-led. IPO 2021.',
            'founder_story': 'Founded 2004 in NYC by Michael Kirban and Ira Liran after meeting two Brazilian women in a bar. Built the coconut water category in the US.',
            'watch_list': 0,
        },
        {
            'id': 'siggi-s',
            'category': 'supplement',
            'overall_zone': 'red',
            'parent_company_id': 'china-mengniu',
            'pe_owned': 0, 'independent': 0,
            'founded_year': 2004, 'acquired_year': 2018,
            'acquisition_price': 300000000,
            'headline_finding': 'siggi\'s is owned by China Mengniu Dairy — the "simple ingredients" Icelandic yogurt brand is a Chinese state-linked dairy product',
            'share_text': 'siggi\'s yogurt is owned by China Mengniu Dairy ($300M, 2018). COFCO (Chinese state enterprise) is a major Mengniu shareholder.',
            'founder_story': 'Founded 2004 in NYC by Siggi Hilmarsson, an Icelandic immigrant. Brought skyr (thick Icelandic yogurt) to the US with minimal sugar. Sold to Mengniu 2018.',
            'watch_list': 2,
        },
        {
            'id': 'chobani',
            'category': 'supplement',
            'overall_zone': 'yellow',
            'parent_company_id': 'tpg',
            'pe_owned': 1, 'independent': 0,
            'founded_year': 2005, 'acquired_year': 2016,
            'headline_finding': 'TPG Capital holds majority stake in Chobani — Turkish immigrant founder Hamdi Ulukaya retains significant ownership but PE is involved',
            'share_text': 'Chobani has TPG Capital as majority investor. Founder Hamdi Ulukaya still leads the company but PE drives the capital structure.',
            'founder_story': 'Founded 2005 in South Edmeston, NY by Hamdi Ulukaya, a Turkish immigrant. Bought an abandoned Kraft dairy plant and revolutionized US yogurt market.',
            'watch_list': 1,
        },
        {
            'id': 'fage',
            'category': 'supplement',
            'overall_zone': 'yellow',
            'parent_company_id': None,
            'pe_owned': 0, 'independent': 0,
            'founded_year': 1926,
            'headline_finding': 'FAGE is Greek family-owned (Filippou family) — independent dairy brand that introduced authentic Greek yogurt to the US',
            'share_text': 'FAGE is privately owned by the Filippou family (Greek founders). No PE, no conglomerate. A family dairy company that brought authentic Greek yogurt to America.',
            'founder_story': 'Founded 1926 in Athens, Greece by Athanassios Filippou. Family has run it for generations. Expanded to US in 1998. Still family-owned private company.',
            'watch_list': 0,
        },
        {
            'id': 'stonyfield-organic',
            'category': 'supplement',
            'overall_zone': 'red',
            'parent_company_id': 'lactalis',
            'pe_owned': 0, 'independent': 0,
            'founded_year': 1983, 'acquired_year': 2017,
            'headline_finding': 'Stonyfield sold from Danone to Lactalis in 2017 — the organic pioneer now belongs to the world\'s most opaque dairy giant',
            'share_text': 'Stonyfield Organic is owned by Lactalis, a secretive French dairy company with a 2017 salmonella baby formula scandal. Your organic yogurt dollar flows to France.',
            'founder_story': 'Founded 1983 in Wilton, NH by Gary Hirshberg and Samuel Kaymen. Pioneered organic yogurt in the US. Sold to Danone 2003, then to Lactalis 2017.',
            'watch_list': 2,
        },
        {
            'id': 'siete',
            'category': 'grocery',
            'overall_zone': 'red',
            'parent_company_id': 'pepsico',
            'pe_owned': 0, 'independent': 0,
            'founded_year': 2014, 'acquired_year': 2025,
            'acquisition_price': 1200000000,
            'headline_finding': 'PepsiCo paid $1.2B for Siete Foods in Jan 2025 — the grain-free, family-founded Mexican-American brand now belongs to Big Snack',
            'share_text': 'Siete Foods was acquired by PepsiCo for $1.2B (January 2025). The Garza family\'s grain-free tortilla brand — born from an autoimmune diet — now funds Pepsi.',
            'founder_story': 'Founded 2014 by the Garza family in San Antonio, TX. Veronica Garza created grain-free recipes for her autoimmune condition. Built to a 7-member family brand.',
            'watch_list': 2,
        },
        {
            'id': 'simple-mills',
            'category': 'grocery',
            'overall_zone': 'red',
            'parent_company_id': 'primavera-capital',
            'pe_owned': 1, 'independent': 0,
            'founded_year': 2012, 'acquired_year': 2023,
            'headline_finding': 'Chinese PE firm Primavera Capital acquired majority stake in Simple Mills in 2023 — CFIUS concerns surround foreign ownership of US health food brand',
            'share_text': 'Simple Mills is majority-owned by Primavera Capital, a Chinese private equity firm (2023). CFIUS has raised national security concerns about Chinese PE in US food brands.',
            'founder_story': 'Founded 2012 by Katlin Smith in Chicago, IL. Built clean-ingredient crackers and baking mixes. Grew to national distribution in Whole Foods, Target, Costco.',
            'watch_list': 2,
        },
        {
            'id': 'hippeas',
            'category': 'grocery',
            'overall_zone': 'red',
            'parent_company_id': 'l-catterton',
            'pe_owned': 1, 'independent': 0,
            'founded_year': 2016, 'acquired_year': 2019,
            'headline_finding': 'L Catterton (LVMH-linked PE) owns Hippeas — the "organic chickpea puff" brand\'s mission now serves luxury goods investors',
            'share_text': 'HIPPEAS is owned by L Catterton, a PE firm backed by LVMH (Louis Vuitton). The organic snack\'s "Good Is The New Cool" ethos now serves luxury conglomerate investors.',
            'founder_story': 'Founded 2016 by Tom Whitton in London. Organic chickpea puffs with a social mission. Scaled rapidly through Whole Foods and Starbucks. Sold to L Catterton in 2019.',
            'watch_list': 1,
        },
        {
            'id': 'spindrift',
            'category': 'beverage',
            'overall_zone': 'green',
            'parent_company_id': None,
            'pe_owned': 0, 'independent': 1,
            'founded_year': 2010,
            'headline_finding': 'Founder-led VC-backed sparkling water — Bill Creelman still CEO, uses real fruit juice, no PE acquisition',
            'share_text': 'Spindrift is founder-led (Bill Creelman, CEO). The only major sparkling water made with real squeezed fruit. VC-backed but no PE acquisition.',
            'founder_story': 'Founded 2010 by Bill Creelman in Charlestown, MA. Created sparkling water with real fruit juice as the only ingredient beyond water. Still founder-led.',
            'watch_list': 0,
        },
        {
            'id': 'bloom',
            'category': 'supplement',
            'overall_zone': 'green',
            'parent_company_id': None,
            'pe_owned': 0, 'independent': 1,
            'founded_year': 2019,
            'headline_finding': 'Founder-led women\'s supplement brand — Mari Llewellyn built from personal health transformation, still leads company',
            'share_text': 'Bloom Nutrition is independently owned by co-founder Mari Llewellyn. Founded 2019 from her weight loss journey. VC-backed but founder-led and independent.',
            'founder_story': 'Founded 2019 by Mari Llewellyn and Greg La Perriere. Mari built brand from her 90-lb weight loss journey shared on social media. Women-focused supplements.',
            'watch_list': 0,
        },
        {
            'id': 'barebells',
            'category': 'supplement',
            'overall_zone': 'yellow',
            'parent_company_id': 'orkla',
            'pe_owned': 0, 'independent': 0,
            'founded_year': 2016, 'acquired_year': 2020,
            'headline_finding': 'Swedish protein bar brand Barebells acquired by Orkla (Norwegian conglomerate) in 2020',
            'share_text': 'Barebells is owned by Orkla ASA, a Norwegian conglomerate. The Scandinavian protein bar brand was acquired in 2020 for European scale.',
            'founder_story': 'Founded 2016 in Stockholm, Sweden. Created high-protein bars with candy bar taste profiles. Acquired by Orkla conglomerate in 2020 for Nordic and global scale.',
            'watch_list': 0,
        },
        {
            'id': 'bai',
            'category': 'beverage',
            'overall_zone': 'red',
            'parent_company_id': 'keurig-dr-pepper',
            'pe_owned': 0, 'independent': 0,
            'founded_year': 2009, 'acquired_year': 2017,
            'acquisition_price': 1700000000,
            'headline_finding': 'Dr Pepper paid $1.7B for Bai — the "antioxidant infused" drink brand now belongs to Keurig Dr Pepper',
            'share_text': 'Bai is owned by Keurig Dr Pepper (KDP), acquired for $1.7B in 2017. The "antioxidant-infused" drink brand is a billion-dollar beverage industry play.',
            'founder_story': 'Founded 2009 by Ben Weiss in Princeton, NJ. Used coffeefruit (discarded coffee fruit) for antioxidants. Sold to Dr Pepper Snapple Group for $1.7B in 2017.',
            'watch_list': 1,
        },
        {
            'id': '9edeb7d9-b66a-4e0b-8340-8edd75ffd343',  # One A Day
            'category': 'supplement',
            'overall_zone': 'red',
            'parent_company_id': 'f93417f0-d189-4c21-b71e-9cec4cff0129',  # Bayer
            'pe_owned': 0, 'independent': 0,
            'founded_year': 1940,
            'headline_finding': 'One A Day is a Bayer pharma product — the #1 selling multivitamin belongs to a pharmaceutical giant with opioid settlement history',
            'share_text': 'One A Day multivitamins are owned by Bayer AG — the German pharmaceutical company that also makes aspirin and formerly owned opioid brands.',
            'founder_story': 'Launched 1940 by Miles Laboratories. Acquired by Bayer in 1978 as part of Miles Laboratories acquisition.',
            'watch_list': 1,
        },
        {
            'id': '75ba1624-03c1-4034-8c79-aa2208371799',  # Centrum
            'category': 'supplement',
            'overall_zone': 'yellow',
            'parent_company_id': '6d09f1b1-e7e7-4522-9f57-7610f5bf5dcd',  # Haleon
            'pe_owned': 0, 'independent': 0,
            'founded_year': 1978,
            'headline_finding': 'Centrum is owned by Haleon (GSK spinoff, public) — world\'s #1 multivitamin brand is a publicly traded consumer health company product',
            'share_text': 'Centrum is owned by Haleon plc (HLN), spun off from GlaxoSmithKline in 2022. The #1 selling multivitamin is a publicly traded pharma spinoff product.',
            'founder_story': 'Launched 1978 by Lederle Laboratories. Passed through American Cyanamid, Wyeth, Pfizer consumer health, then Haleon (GSK spinoff 2022).',
            'watch_list': 0,
        },
        {
            'id': 'nature-made',
            'category': 'supplement',
            'overall_zone': 'red',
            'parent_company_id': 'f358b5d6-0af1-4730-877a-bc6ad7470e20',  # Pharmavite
            'pe_owned': 0, 'independent': 0,
            'founded_year': 1971,
            'headline_finding': 'Nature Made is owned by Pharmavite, itself a subsidiary of Otsuka Holdings (Japanese pharma) — acquired 2021',
            'share_text': 'Nature Made is owned by Pharmavite, a subsidiary of Japanese pharmaceutical giant Otsuka Holdings. Your USP-verified vitamins fund a Japanese conglomerate.',
            'founder_story': 'Founded 1971 in Los Angeles as Pharmavite. Nature Made brand launched as USP-verified vitamins. Otsuka Holdings (Japan) acquired Pharmavite in 2021.',
            'watch_list': 0,
        },
        {
            'id': '57104d3f',  # Momentous
            'category': 'supplement',
            'overall_zone': 'green',
            'parent_company_id': None,
            'pe_owned': 0, 'independent': 1,
            'founded_year': 2018,
            'headline_finding': 'Founder-led sports supplement brand — NSF certified, used by professional sports teams, still independently operated',
            'share_text': 'Momentous is independently operated. Founded 2018, NSF Certified for Sport, used by NFL and NBA teams. VC-backed but founder-led.',
            'founder_story': 'Founded 2018 in La Jolla, CA. Created NSF Certified supplements for elite athletes. Partnered with leading sports scientists like Dr. Andrew Huberman.',
            'watch_list': 0,
        },
        {
            'id': '67b38619-2329-4493-93e7-594f41f96c38',  # AG1
            'category': 'supplement',
            'overall_zone': 'yellow',
            'parent_company_id': None,
            'pe_owned': 0, 'independent': 1,
            'founded_year': 2010,
            'headline_finding': 'AG1 is private and founder-led but questions about ingredient efficacy and $80/month subscription model raise transparency concerns',
            'share_text': 'AG1 (Athletic Greens) is private and founder-led by Chris Ashenden. But at $80/month, some nutritionists question whether the 75-ingredient blend delivers on claims.',
            'founder_story': 'Founded 2010 in Auckland, NZ by Chris Ashenden. Built AG1 as a comprehensive daily greens powder. Remained private and founder-led with DTC subscription model.',
            'watch_list': 1,
        },
        {
            'id': 'f216305e-dab5-4a3d-95b0-97faed53e076',  # Bare Snacks
            'category': 'grocery',
            'overall_zone': 'yellow',
            'parent_company_id': None,
            'pe_owned': 0, 'independent': 0,
            'founded_year': 2001,
            'headline_finding': 'Bare Snacks (apple chips) had complex ownership — acquired by Apple & Eve then private equity; current status: private',
            'share_text': 'Bare Snacks went through multiple ownership changes. Currently private with unclear PE involvement.',
            'founder_story': 'Founded 2001. Known for baked fruit and veggie snack chips.',
            'watch_list': 0,
        },
        {
            'id': '76d93c29-096c-42d1-8b32-139b9e95dcb6',  # Siete Family Foods (duplicate, use siete)
            'category': 'grocery',
            'overall_zone': 'red',
            'parent_company_id': 'pepsico',
            'pe_owned': 0, 'independent': 0,
            'founded_year': 2014, 'acquired_year': 2025,
            'acquisition_price': 1200000000,
            'headline_finding': 'PepsiCo acquired Siete for $1.2B in January 2025',
            'share_text': 'Siete Family Foods is owned by PepsiCo ($1.2B, Jan 2025). The Garza family\'s grain-free brand is now a PepsiCo product line.',
            'founder_story': 'Founded by the Garza family in San Antonio, TX in 2014.',
            'watch_list': 1,
        },
    ]

    for b in updates:
        bid = b['id']
        c.execute('''
            UPDATE brands SET
                category=?, overall_zone=?, parent_company_id=?,
                pe_owned=?, independent=?,
                headline_finding=?, share_text=?, founder_story=?,
                watch_list=?
            WHERE id=?
        ''', (
            b.get('category'), b.get('overall_zone'), b.get('parent_company_id'),
            b.get('pe_owned', 0), b.get('independent', 0),
            b.get('headline_finding'), b.get('share_text'), b.get('founder_story'),
            b.get('watch_list', 0),
            bid,
        ))
        # Also update founded/acquired if provided
        if b.get('founded_year'):
            c.execute('UPDATE brands SET founded_year=? WHERE id=?', (b['founded_year'], bid))
        if b.get('acquired_year'):
            c.execute('UPDATE brands SET acquired_year=? WHERE id=?', (b['acquired_year'], bid))
        if b.get('acquisition_price'):
            c.execute('UPDATE brands SET acquisition_price=? WHERE id=?', (b['acquisition_price'], bid))
        print(f"  Updated: {bid}")

    conn.commit()
    print(f"\nBrands updated: {len(updates)}")

    # ─── STEP 3: INSERT NEW BRANDS ────────────────────────────────────────────

    new_brands = [
        # Protein/Supplement
        {
            'id': 'amazing-grass',
            'name': 'Amazing Grass',
            'category': 'supplement',
            'overall_zone': 'red',
            'parent_company_id': 'f28db92d-c4c8-423c-8d17-b2f4e9e65e96',  # Glanbia
            'pe_owned': 0, 'independent': 0,
            'founded_year': 2002, 'acquired_year': 2017,
            'headline_finding': 'Glanbia acquired Amazing Grass in 2017 — the farmer-founded greens powder now belongs to Irish dairy giant',
            'share_text': 'Amazing Grass is owned by Glanbia (acquired 2017). The greens powder founded by a Kansas wheat grass farmer now funds an Irish multinational.',
            'founder_story': 'Founded 2002 by Todd Haen and Brandon Bert in Kansas. Started growing wheatgrass on the family farm. Built organic greens powder brand. Sold to Glanbia 2017.',
        },
        {
            'id': 'ancient-nutrition',
            'name': 'Ancient Nutrition',
            'category': 'supplement',
            'overall_zone': 'red',
            'parent_company_id': 'ancient-nutrition-pe',
            'pe_owned': 1, 'independent': 0,
            'founded_year': 2016, 'acquired_year': 2019,
            'headline_finding': 'PE-backed Josh Axe brand — FTC warned Ancient Nutrition for unsubstantiated health claims on collagen and adaptogen products',
            'share_text': 'Ancient Nutrition is PE-backed (majority stake 2019). Dr. Josh Axe\'s brand received FTC warning letters for exaggerated health claims.',
            'founder_story': 'Founded 2016 by Josh Axe and Jordan Rubin (also Garden of Life founder) in Nashville, TN. Built on traditional healing food principles.',
        },
        {
            'id': 'four-sigmatic',
            'name': 'Four Sigmatic',
            'category': 'supplement',
            'overall_zone': 'green',
            'parent_company_id': None,
            'pe_owned': 0, 'independent': 1,
            'founded_year': 2012,
            'headline_finding': 'Finnish founder still leads functional mushroom coffee brand — VC-backed but no PE acquisition',
            'share_text': 'Four Sigmatic is founder-led by Tero Isokauppila (Finnish). The mushroom coffee brand is VC-backed but no PE acquisition. Transparent about ingredients.',
            'founder_story': 'Founded 2012 by Tero Isokauppila in Helsinki, Finland. Grew up on a farm with 76 generations of mushroom farming. Built mushroom superfood brand.',
        },
        {
            'id': 'organifi',
            'name': 'Organifi',
            'category': 'supplement',
            'overall_zone': 'green',
            'parent_company_id': None,
            'pe_owned': 0, 'independent': 1,
            'founded_year': 2014,
            'headline_finding': 'DTC founder-led greens brand — Drew Canole still leads Organifi, no PE acquisition',
            'share_text': 'Organifi is independently owned by founder Drew Canole. DTC supplement brand built on green juice powder. No PE acquisition as of 2025.',
            'founder_story': 'Founded 2014 by Drew Canole in San Diego, CA. Built around juicing and whole food supplements. Grew via content marketing and podcasts.',
        },
        {
            'id': 'thorne',
            'name': 'Thorne',
            'category': 'supplement',
            'overall_zone': 'yellow',
            'parent_company_id': 'thorne-healthtech',
            'pe_owned': 0, 'independent': 0,
            'founded_year': 1984,
            'headline_finding': 'Thorne is publicly traded (NASDAQ:THRN) — practitioner-grade supplements with NSF certification, better transparency than most brands',
            'share_text': 'Thorne (THRN) is a publicly traded supplement company. Known for practitioner-grade quality and NSF certification. More transparent than most brands.',
            'founder_story': 'Founded 1984 in Sandpoint, ID. Originally physician-focused supplement brand. Went public on NASDAQ (THRN) in 2021.',
        },
        {
            'id': 'care-of',
            'name': 'Care/of',
            'category': 'supplement',
            'overall_zone': 'red',
            'parent_company_id': 'f93417f0-d189-4c21-b71e-9cec4cff0129',  # Bayer
            'pe_owned': 0, 'independent': 0,
            'founded_year': 2016, 'acquired_year': 2020,
            'acquisition_price': 225000000,
            'headline_finding': 'Bayer acquired Care/of for $225M — the personalized vitamin subscription startup now belongs to a pharmaceutical giant',
            'share_text': 'Care/of was acquired by Bayer for $225M (2020). The personalized vitamin DTC brand now funds Bayer\'s consumer health strategy.',
            'founder_story': 'Founded 2016 by Craig Elbert and Akash Shah in NYC. Created personalized vitamin packs via online quiz. Grew to $100M+ revenue before Bayer acquisition.',
        },
        {
            'id': 'natures-bounty',
            'name': "Nature's Bounty",
            'category': 'supplement',
            'overall_zone': 'red',
            'parent_company_id': 'kkr',
            'pe_owned': 1, 'independent': 0,
            'founded_year': 1971, 'acquired_year': 2021,
            'acquisition_price': 5500000000,
            'headline_finding': 'KKR paid $5.5B for Nature\'s Bounty — one of America\'s largest vitamin brands is owned by the PE firm that pioneered leveraged buyouts',
            'share_text': "Nature's Bounty is owned by KKR — the $550B PE giant that pioneered leveraged buyouts. Your vitamins fund one of Wall Street's most powerful private equity firms.",
            'founder_story': 'Founded 1971 by Arthur Rudolph in Bohemia, NY as Nature\'s Bounty Inc. Built into one of America\'s largest supplement retailers. KKR acquired 2021 for $5.5B.',
        },
        {
            'id': 'solgar',
            'name': 'Solgar',
            'category': 'supplement',
            'overall_zone': 'red',
            'parent_company_id': 'nestle',
            'pe_owned': 0, 'independent': 0,
            'founded_year': 1947, 'acquired_year': 2017,
            'headline_finding': 'Nestlé owns Solgar via Nestlé Health Science — the 75-year-old premium supplement brand is a Big Food product',
            'share_text': "Solgar is owned by Nestlé Health Science (acquired as part of Atrium portfolio, 2017). The premium vitamin brand's quality promise now serves Nestlé's nutrition strategy.",
            'founder_story': 'Founded 1947 in Lynbrook, NY. One of the first brands to formulate vitamins in fish gelatin capsules. Acquired by Wyeth, then American Home Products, then Nestlé Health Science.',
        },
        {
            'id': 'now-foods',
            'name': 'NOW Foods',
            'category': 'supplement',
            'overall_zone': 'green',
            'parent_company_id': None,
            'pe_owned': 0, 'independent': 1,
            'founded_year': 1968,
            'headline_finding': 'NOW Foods is still family-owned — Elwood Richard founded it in 1968, family still runs it today, one of the last independent supplement brands at scale',
            'share_text': "NOW Foods is family-owned (Elwood Richard, founded 1968). Still independent after 50+ years. No PE, no conglomerate. One of the supplement industry's rare holdouts.",
            'founder_story': 'Founded 1968 by Elwood Richard in Bloomingdale, IL. Started as a health food store supplier. Family-owned and operated for over 55 years.',
        },
        {
            'id': 'ritual-vitamins',
            'name': 'Ritual Vitamins',
            'category': 'supplement',
            'overall_zone': 'green',
            'parent_company_id': None,
            'pe_owned': 0, 'independent': 1,
            'founded_year': 2016,
            'headline_finding': 'Founder-led women\'s vitamin brand — Katerina Schneider still CEO with radical ingredient transparency',
            'share_text': 'Ritual Vitamins is founder-led by Katerina Schneider (CEO). Known for Open Bottle ingredient traceability. VC-backed but no PE acquisition.',
            'founder_story': 'Founded 2016 by Katerina Schneider in Los Angeles. Created during pregnancy when she was frustrated by opaque vitamin industry. Built radical transparency into the brand.',
        },
        {
            'id': 'rainbow-light',
            'name': 'Rainbow Light',
            'category': 'supplement',
            'overall_zone': 'red',
            'parent_company_id': 'butterfly-equity',
            'pe_owned': 1, 'independent': 0,
            'founded_year': 1981, 'acquired_year': 2019,
            'headline_finding': 'Rainbow Light passed from Clorox to Butterfly Equity PE — the women\'s health vitamin brand is now PE-owned',
            'share_text': 'Rainbow Light was owned by Clorox, then sold to Butterfly Equity PE. The plant-based women\'s vitamin brand now generates returns for a food-focused PE firm.',
            'founder_story': 'Founded 1981 in Santa Cruz, CA. Pioneer in food-based vitamins. Sold to Clorox in 2016, then divested to Butterfly Equity circa 2019.',
        },
        {
            'id': 'megafood',
            'name': 'MegaFood',
            'category': 'supplement',
            'overall_zone': 'yellow',
            'parent_company_id': 'innova-capital',
            'pe_owned': 1, 'independent': 0,
            'founded_year': 1973, 'acquired_year': 2023,
            'headline_finding': 'MegaFood acquired by Innova Capital in 2023 — New Hampshire whole food vitamin pioneer is now PE-owned',
            'share_text': 'MegaFood is now PE-owned by Innova Capital (acquired 2023). The whole food supplement brand from NH is a private equity investment.',
            'founder_story': 'Founded 1973 in Manchester, NH. Pioneer of FoodState® whole food vitamin manufacturing. Operated independently for decades before PE acquisition in 2023.',
        },
        {
            'id': 'new-chapter',
            'name': 'New Chapter',
            'category': 'supplement',
            'overall_zone': 'red',
            'parent_company_id': 'procter-gamble',
            'pe_owned': 0, 'independent': 0,
            'founded_year': 1982, 'acquired_year': 2012,
            'headline_finding': 'Procter & Gamble owns New Chapter — the certified organic supplement brand belongs to the company that makes Tide detergent and Gillette razors',
            'share_text': 'New Chapter is owned by Procter & Gamble (acquired 2012). The certified organic, fermented supplement brand is a P&G consumer goods product.',
            'founder_story': 'Founded 1982 by Paul Schulick and Tom Newmark in Brattleboro, VT. Pioneer of fermented whole food supplements and certified organic vitamins. Sold to P&G in 2012.',
        },
        {
            'id': 'built-bar',
            'name': 'Built Bar',
            'category': 'supplement',
            'overall_zone': 'green',
            'parent_company_id': None,
            'pe_owned': 0, 'independent': 1,
            'founded_year': 2018,
            'headline_finding': 'Utah founder still leads Built Bar — independently operated protein bar brand with DTC-first model',
            'share_text': 'Built Bar is independently owned by founder Nick Greer. Founded 2018 in American Fork, UT. High-protein bars with candy-like flavors. No PE acquisition.',
            'founder_story': 'Founded 2018 by Nick Greer in American Fork, UT. Created high-protein, low-calorie bars that taste like candy. DTC-first brand that stayed independent.',
        },
        {
            'id': 'health-ade-kombucha',
            'name': 'Health-Ade Kombucha',
            'category': 'beverage',
            'overall_zone': 'red',
            'parent_company_id': 'butterfly-equity',
            'pe_owned': 1, 'independent': 0,
            'founded_year': 2012, 'acquired_year': 2022,
            'headline_finding': 'Butterfly Equity acquired Health-Ade in 2022 — the farmers market kombucha brand is now PE-owned',
            'share_text': "Health-Ade Kombucha is owned by Butterfly Equity PE (2022). The brand that started at LA farmers markets now generates PE returns.",
            'founder_story': 'Founded 2012 by Daina Trout, Justin Trout, and Vanessa Dew at the Brentwood Farmers Market in LA. Built from a 2-gallon home brewing operation.',
        },
        {
            'id': 'harmless-harvest',
            'name': 'Harmless Harvest',
            'category': 'beverage',
            'overall_zone': 'red',
            'parent_company_id': 'danone',
            'pe_owned': 0, 'independent': 0,
            'founded_year': 2011, 'acquired_year': 2017,
            'headline_finding': 'Danone acquired Harmless Harvest — the pink coconut water brand with fair trade sourcing now belongs to a French food multinational',
            'share_text': 'Harmless Harvest is owned by Danone (acquired 2017). The organic, fair-trade pink coconut water brand funds a French dairy giant.',
            'founder_story': 'Founded 2011 by Douglas Riboud and Justin Guilbert. Sourced raw coconut water from Thailand with fair trade practices. Pink color is natural from antioxidants.',
        },
        {
            'id': 'hint-water',
            'name': 'Hint Water',
            'category': 'beverage',
            'overall_zone': 'green',
            'parent_company_id': None,
            'pe_owned': 0, 'independent': 1,
            'founded_year': 2005,
            'headline_finding': 'Kara Goldin still CEO of independently run Hint Water — bootstrapped to major brand without selling to conglomerate',
            'share_text': 'Hint Water is founder-led by Kara Goldin (CEO). Founded 2005 in San Francisco. Grew to $150M+ revenue without selling to Big Beverage.',
            'founder_story': 'Founded 2005 by Kara Goldin in San Francisco. Quit Diet Coke and created fruit-infused water with no sweeteners. Bootstrapped to national scale while staying independent.',
        },
        {
            'id': 'kevita',
            'name': 'KeVita',
            'category': 'beverage',
            'overall_zone': 'red',
            'parent_company_id': 'pepsico',
            'pe_owned': 0, 'independent': 0,
            'founded_year': 2009, 'acquired_year': 2016,
            'acquisition_price': 200000000,
            'headline_finding': 'PepsiCo acquired KeVita for $200M — the probiotic beverage brand now belongs to one of the world\'s largest beverage companies',
            'share_text': "KeVita is owned by PepsiCo ($200M, 2016). The sparkling probiotic brand that started at a farmers market now funds Pepsi's better-for-you portfolio.",
            'founder_story': 'Founded 2009 by Bill Moses in Ojai, CA. Started at a farmers market with kombucha. Scaled to national distribution and sold to PepsiCo for $200M in 2016.',
        },
        {
            'id': 'sunwarrior',
            'name': 'Sunwarrior',
            'category': 'supplement',
            'overall_zone': 'green',
            'parent_company_id': None,
            'pe_owned': 0, 'independent': 1,
            'founded_year': 2008,
            'headline_finding': 'Independent plant-based protein brand based in Utah — still privately owned with no PE acquisition',
            'share_text': 'Sunwarrior is independently owned. Founded 2008 in Hurricane, UT. Plant-based protein pioneer with no PE acquisition.',
            'founder_story': 'Founded 2008 in Hurricane, UT. Created one of the first plant-based protein powders. Privately owned and operated.',
        },
        {
            'id': 'green-vibrance',
            'name': 'Green Vibrance',
            'category': 'supplement',
            'overall_zone': 'green',
            'parent_company_id': None,
            'pe_owned': 0, 'independent': 1,
            'founded_year': 1992,
            'headline_finding': 'Vibrant Health independently makes Green Vibrance — a founder-operated supplement company with decades of consistent formulation',
            'share_text': 'Green Vibrance is made by Vibrant Health, an independent company founded in 1992. No PE, no conglomerate. Consistent formula for 30+ years.',
            'founder_story': 'Founded 1992 by Mark Timon in Brookfield, CT as Vibrant Health. Formulated Green Vibrance as a comprehensive greens product. Still independently operated.',
        },
        {
            'id': 'gts-kombucha',
            'name': "GT's Kombucha",
            'category': 'beverage',
            'overall_zone': 'green',
            'parent_company_id': None,
            'pe_owned': 0, 'independent': 1,
            'founded_year': 1995,
            'headline_finding': 'GT Dave still owns and runs GT\'s — the kombucha founder who started brewing at 15 controls the #1 kombucha brand in America',
            'share_text': "GT's Kombucha is owned by GT Dave, the founder who started brewing at age 15 in 1995. Still privately owned. The top-selling kombucha brand has never sold to Big Beverage.",
            'founder_story': 'Founded 1995 by GT Dave at age 15 in Beverly Hills, CA after his mother\'s breast cancer diagnosis. Still brews in glass, never sold to a conglomerate. Iconic story.',
        },
        {
            'id': 'waterloo-sparkling',
            'name': 'Waterloo Sparkling Water',
            'category': 'beverage',
            'overall_zone': 'green',
            'parent_company_id': None,
            'pe_owned': 0, 'independent': 1,
            'founded_year': 2017,
            'headline_finding': 'Independent Austin-based sparkling water brand — privately held with no PE acquisition',
            'share_text': 'Waterloo Sparkling Water is independently owned. Founded 2017 in Austin, TX. Natural flavors, no sweeteners, still privately held.',
            'founder_story': 'Founded 2017 in Austin, TX. Created sparkling water with bold natural flavors as an alternative to LaCroix.',
        },
        {
            'id': 'two-good',
            'name': 'Two Good',
            'category': 'supplement',
            'overall_zone': 'red',
            'parent_company_id': 'danone',
            'pe_owned': 0, 'independent': 0,
            'founded_year': 2019,
            'headline_finding': 'Two Good is a Danone brand — the low-sugar Greek yogurt is a product line from a French multinational dairy company',
            'share_text': 'Two Good yogurt is owned by Danone North America. A product line from the French dairy conglomerate.',
            'founder_story': 'Launched 2019 by Danone North America as a low-sugar Greek yogurt line targeting health-conscious consumers.',
        },
        {
            'id': 'oikos',
            'name': 'Oikos',
            'category': 'supplement',
            'overall_zone': 'red',
            'parent_company_id': 'danone',
            'pe_owned': 0, 'independent': 0,
            'founded_year': 2008,
            'headline_finding': 'Oikos is owned by Danone — the Greek yogurt brand is a product line from a French food multinational',
            'share_text': 'Oikos Greek Yogurt is a Danone product. One of the top-selling yogurt brands in the US, all profits flow to the French dairy conglomerate.',
            'founder_story': 'Launched by Stonyfield Farm (Danone subsidiary at the time) in 2008. Became one of Danone\'s flagship US yogurt brands.',
        },
        {
            'id': 'kite-hill',
            'name': 'Kite Hill',
            'category': 'supplement',
            'overall_zone': 'red',
            'parent_company_id': 'stripes-group',
            'pe_owned': 1, 'independent': 0,
            'founded_year': 2012, 'acquired_year': 2021,
            'headline_finding': 'Stripes Group PE owns Kite Hill — the almond milk yogurt brand co-founded by a Michelin chef is now a PE portfolio company',
            'share_text': 'Kite Hill is owned by Stripes Group private equity (majority stake, 2021). The artisanal plant-based dairy brand co-founded by chef Thomas Keller is now PE-owned.',
            'founder_story': 'Founded 2012 by Patrick Brown (Impossible Foods founder) and chef Thomas Keller and Matt Gibson. Created almond milk cheeses and yogurts using traditional cheesemaking.',
        },
        {
            'id': 'forager-project',
            'name': 'Forager Project',
            'category': 'supplement',
            'overall_zone': 'green',
            'parent_company_id': None,
            'pe_owned': 0, 'independent': 1,
            'founded_year': 2013,
            'headline_finding': 'Independent cashew-based dairy alternative brand — founder-led with mission-driven values, no PE acquisition',
            'share_text': 'Forager Project is independently owned. Founded 2013, makes cashew milk yogurt and beverages with organic ingredients. No PE ownership.',
            'founder_story': 'Founded 2013 in San Francisco. Pioneered cashew-based dairy alternatives with organic, clean ingredients. Mission-driven independent brand.',
        },
        {
            'id': 'lesser-evil',
            'name': 'LesserEvil',
            'category': 'grocery',
            'overall_zone': 'green',
            'parent_company_id': None,
            'pe_owned': 0, 'independent': 1,
            'founded_year': 2004,
            'headline_finding': 'Independent popcorn and snack brand — founder-led with coconut oil and clean ingredients, no PE acquisition',
            'share_text': 'LesserEvil is independently owned. Makes popcorn and snacks with clean ingredients like coconut oil. No PE, no conglomerate.',
            'founder_story': 'Founded 2004, rebranded under Charles Coristine. Focused on clean-ingredient snacks, especially popcorn made with coconut oil.',
        },
        {
            'id': 'jacksons-chips',
            'name': "Jackson's Chips",
            'category': 'grocery',
            'overall_zone': 'green',
            'parent_company_id': None,
            'pe_owned': 0, 'independent': 1,
            'founded_year': 2019,
            'headline_finding': 'Independent sweet potato chip brand using avocado or coconut oil — founder-led with regenerative agriculture focus',
            'share_text': "Jackson's Chips is independently owned. Sweet potato chips cooked in avocado or coconut oil. Sourced from regenerative farms.",
            'founder_story': "Founded 2019. Created sweet potato chips specifically for people with dietary restrictions. Partners with regenerative agriculture farms.",
        },
        {
            'id': 'solely',
            'name': 'Solely',
            'category': 'grocery',
            'overall_zone': 'green',
            'parent_company_id': None,
            'pe_owned': 0, 'independent': 1,
            'founded_year': 2017,
            'headline_finding': 'Independent fruit jerky brand — founder-led with organic, single-ingredient snacks',
            'share_text': 'Solely is independently owned. Makes organic fruit jerky from single ingredients. No PE, no conglomerate.',
            'founder_story': 'Founded 2017. Creates fruit jerky and gummy snacks from single organic fruits with no added sugar.',
        },
        {
            'id': 'thats-it',
            'name': "That's It",
            'category': 'grocery',
            'overall_zone': 'green',
            'parent_company_id': None,
            'pe_owned': 0, 'independent': 1,
            'founded_year': 2012,
            'headline_finding': 'Founder-led fruit bar brand — Lior Lewensztain still leads company with 2-ingredient philosophy',
            'share_text': "That's It is founder-led by Lior Lewensztain. Founded 2012 in LA. Fruit bars with only 2 ingredients. No PE acquisition.",
            'founder_story': 'Founded 2012 by Lior Lewensztain in Los Angeles. Created fruit bars with only 2 ingredients after being frustrated with complex ingredient lists.',
        },
        {
            'id': 'chomps',
            'name': 'Chomps',
            'category': 'grocery',
            'overall_zone': 'green',
            'parent_company_id': None,
            'pe_owned': 0, 'independent': 1,
            'founded_year': 2012,
            'headline_finding': 'Founder-owned grass-fed meat stick brand — Pete Maldonado still runs the company he built without PE',
            'share_text': 'Chomps is independently owned by co-founder Pete Maldonado. Founded 2012. Grass-fed, pasture-raised meat sticks. No PE ownership.',
            'founder_story': 'Founded 2012 by Pete Maldonado and Rashid Ali in Chicago. Created meat sticks from grass-fed beef and pasture-raised turkey. Bootstrapped to national scale.',
        },
        {
            'id': 'primal-harvest',
            'name': 'Primal Harvest',
            'category': 'supplement',
            'overall_zone': 'green',
            'parent_company_id': None,
            'pe_owned': 0, 'independent': 1,
            'founded_year': 2018,
            'headline_finding': 'Independent DTC supplement brand — no PE acquisition, direct-to-consumer model',
            'share_text': 'Primal Harvest is independently owned. DTC supplement brand focused on ancestral nutrition principles. No PE acquisition.',
            'founder_story': 'Founded 2018. Direct-to-consumer supplement brand built on whole food, ancestral nutrition principles.',
        },
        {
            'id': 'hu-kitchen',
            'name': 'Hu Kitchen',
            'category': 'grocery',
            'overall_zone': 'red',
            'parent_company_id': 'mondelez',
            'pe_owned': 0, 'independent': 0,
            'founded_year': 2012, 'acquired_year': 2021,
            'acquisition_price': 340000000,
            'headline_finding': 'Mondelēz paid $340M for Hu Kitchen — the "get back to human" chocolate brand now belongs to the maker of Oreos and Cadbury',
            'share_text': 'Hu Kitchen is owned by Mondelēz (Oreo, Cadbury, Toblerone) for $340M (2021). The "no junk" chocolate brand now serves a Big Snack conglomerate.',
            'founder_story': 'Founded 2012 by Jordan Brown, Jason Karp, and Jessica Karp in NYC. Started as a paleo restaurant before pivoting to packaged chocolate. Sold to Mondelēz 2021.',
        },
    ]

    for b in new_brands:
        c.execute('''
            INSERT OR IGNORE INTO brands
            (id, name, category, overall_zone, parent_company_id,
             pe_owned, independent, founded_year, acquired_year, acquisition_price,
             headline_finding, share_text, founder_story)
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', (
            b['id'], b['name'], b['category'], b['overall_zone'], b.get('parent_company_id'),
            b.get('pe_owned', 0), b.get('independent', 0),
            b.get('founded_year'), b.get('acquired_year'), b.get('acquisition_price'),
            b.get('headline_finding'), b.get('share_text'), b.get('founder_story'),
        ))
        print(f"  Brand: {b['id']}")

    conn.commit()
    print(f"\nNew brands inserted: {len(new_brands)}")

    # ─── STEP 4: ALIASES ──────────────────────────────────────────────────────

    # (alias_text, brand_id)
    # alias_text should be normalized (lowercase, no punctuation per normalize() logic)
    aliases = [
        # Optimum Nutrition
        ('optimum nutrition', 'optimum-nutrition'),
        ('gold standard whey', 'optimum-nutrition'),
        ('on gold standard', 'optimum-nutrition'),
        ('optimum nutrition gold standard', 'optimum-nutrition'),
        ('on serious mass', 'optimum-nutrition'),

        # Garden of Life
        ('garden of life', 'garden-of-life'),
        ('garden of life protein', 'garden-of-life'),
        ('garden of life raw protein', 'garden-of-life'),
        ('god protein', 'garden-of-life'),

        # Vega (UUID id)
        ('vega', '64f50941-cba6-4125-9ea3-7ea52d1459d3'),
        ('vega one', '64f50941-cba6-4125-9ea3-7ea52d1459d3'),
        ('vega sport', '64f50941-cba6-4125-9ea3-7ea52d1459d3'),
        ('vega protein', '64f50941-cba6-4125-9ea3-7ea52d1459d3'),

        # Orgain
        ('orgain', 'orgain'),
        ('orgain organic protein', 'orgain'),
        ('orgain protein powder', 'orgain'),
        ('orgain nutritional shake', 'orgain'),

        # Clif Bar
        ('clif bar', 'clif-bar'),
        ('clif', 'clif-bar'),
        ('clifbar', 'clif-bar'),
        ('clif builder bar', 'clif-bar'),
        ('clif shot', 'clif-bar'),

        # RXBAR
        ('rxbar', 'rxbar'),
        ('rx bar', 'rxbar'),
        ('rx protein bar', 'rxbar'),

        # KIND
        ('kind bar', 'kind'),
        ('kind', 'kind'),
        ('kind snacks', 'kind'),
        ('kind healthy grains bar', 'kind'),

        # Quest Nutrition (UUID)
        ('quest', '9f90ddbc-90ea-41ca-9851-3735e7260735'),
        ('quest bar', '9f90ddbc-90ea-41ca-9851-3735e7260735'),
        ('quest nutrition', '9f90ddbc-90ea-41ca-9851-3735e7260735'),
        ('quest protein bar', '9f90ddbc-90ea-41ca-9851-3735e7260735'),
        ('quest chips', '9f90ddbc-90ea-41ca-9851-3735e7260735'),

        # Larabar
        ('larabar', 'larabar'),
        ('lara bar', 'larabar'),
        ('larabar fruit nut bar', 'larabar'),

        # Perfect Bar
        ('perfect bar', 'perfect-bar'),
        ('perfect snacks', 'perfect-bar'),
        ('perfect bar refrigerated', 'perfect-bar'),

        # GoMacro (UUID)
        ('gomacro', 'cae5cbef-9fc1-4275-a495-da55906596cf'),
        ('go macro', 'cae5cbef-9fc1-4275-a495-da55906596cf'),
        ('gomacro macrobar', 'cae5cbef-9fc1-4275-a495-da55906596cf'),

        # Amazing Grass
        ('amazing grass', 'amazing-grass'),
        ('amazing grass green superfood', 'amazing-grass'),
        ('amazing grass protein superfood', 'amazing-grass'),

        # Navitas Organics
        ('navitas organics', 'navitas-organics'),
        ('navitas', 'navitas-organics'),
        ('navitas naturals', 'navitas-organics'),

        # Celsius
        ('celsius', 'celsius'),
        ('celsius drink', 'celsius'),
        ('celsius energy drink', 'celsius'),
        ('celsius fitness drink', 'celsius'),

        # Liquid I.V.
        ('liquid iv', 'liquid-i-v'),
        ('liquid iv hydration', 'liquid-i-v'),
        ('liquid i v', 'liquid-i-v'),
        ('liquid iv multiplier', 'liquid-i-v'),

        # LMNT (UUID)
        ('lmnt', '517a23f4-f987-4084-a722-120baef3cb34'),
        ('element electrolytes', '517a23f4-f987-4084-a722-120baef3cb34'),
        ('lmnt electrolytes', '517a23f4-f987-4084-a722-120baef3cb34'),
        ('lmnt salt', '517a23f4-f987-4084-a722-120baef3cb34'),

        # Nuun (UUID)
        ('nuun', '055bd5b5-82eb-497c-9d29-b408a72516ea'),
        ('nuun hydration', '055bd5b5-82eb-497c-9d29-b408a72516ea'),
        ('nuun electrolyte tablets', '055bd5b5-82eb-497c-9d29-b408a72516ea'),
        ('nuun sport', '055bd5b5-82eb-497c-9d29-b408a72516ea'),

        # Olipop
        ('olipop', 'olipop'),
        ('olipop soda', 'olipop'),
        ('olipop prebiotic soda', 'olipop'),

        # Poppi
        ('poppi', 'poppi'),
        ('poppi prebiotic soda', 'poppi'),
        ('poppi acv soda', 'poppi'),
        ('mother beverage', 'poppi'),

        # Vita Coco
        ('vita coco', 'vita-coco'),
        ('vita coco coconut water', 'vita-coco'),
        ('vitacoco', 'vita-coco'),

        # siggi's
        ("siggi's", 'siggi-s'),
        ('siggis', 'siggi-s'),
        ("siggi's skyr", 'siggi-s'),
        ('siggi skyr yogurt', 'siggi-s'),

        # Chobani
        ('chobani', 'chobani'),
        ('chobani greek yogurt', 'chobani'),
        ('chobani flip', 'chobani'),
        ('chobani complete', 'chobani'),

        # FAGE
        ('fage', 'fage'),
        ('fage total', 'fage'),
        ('fage greek yogurt', 'fage'),
        ('fage 0', 'fage'),

        # Stonyfield
        ('stonyfield', 'stonyfield-organic'),
        ('stonyfield organic', 'stonyfield-organic'),
        ('stonyfield farm', 'stonyfield-organic'),
        ('stonyfield yogurt', 'stonyfield-organic'),

        # Siete
        ('siete', 'siete'),
        ('siete foods', 'siete'),
        ('siete family foods', 'siete'),
        ('siete tortillas', 'siete'),

        # Simple Mills
        ('simple mills', 'simple-mills'),
        ('simple mills crackers', 'simple-mills'),
        ('simple mills almond flour', 'simple-mills'),

        # Hippeas
        ('hippeas', 'hippeas'),
        ('hippeas chickpea puffs', 'hippeas'),
        ('hippeas organic', 'hippeas'),

        # Spindrift
        ('spindrift', 'spindrift'),
        ('spindrift sparkling water', 'spindrift'),
        ('spindrift lemon', 'spindrift'),

        # Bloom
        ('bloom nutrition', 'bloom'),
        ('bloom greens', 'bloom'),
        ('bloom superfood', 'bloom'),

        # Barebells
        ('barebells', 'barebells'),
        ('barebells protein bar', 'barebells'),
        ('barebells soft bar', 'barebells'),

        # Bai
        ('bai', 'bai'),
        ('bai antioxidant', 'bai'),
        ('bai water', 'bai'),
        ('bai flavored water', 'bai'),

        # One A Day (UUID)
        ('one a day', '9edeb7d9-b66a-4e0b-8340-8edd75ffd343'),
        ('one-a-day', '9edeb7d9-b66a-4e0b-8340-8edd75ffd343'),
        ('one a day vitamins', '9edeb7d9-b66a-4e0b-8340-8edd75ffd343'),
        ('one a day multivitamin', '9edeb7d9-b66a-4e0b-8340-8edd75ffd343'),

        # Centrum (UUID)
        ('centrum', '75ba1624-03c1-4034-8c79-aa2208371799'),
        ('centrum silver', '75ba1624-03c1-4034-8c79-aa2208371799'),
        ('centrum multivitamin', '75ba1624-03c1-4034-8c79-aa2208371799'),
        ('centrum adults', '75ba1624-03c1-4034-8c79-aa2208371799'),

        # Nature Made
        ('nature made', 'nature-made'),
        ('naturemade', 'nature-made'),
        ('nature made vitamins', 'nature-made'),
        ('nature made fish oil', 'nature-made'),

        # Momentous
        ('momentous', '57104d3f'),
        ('momentous protein', '57104d3f'),
        ('momentous supplements', '57104d3f'),

        # AG1 (UUID)
        ('ag1', '67b38619-2329-4493-93e7-594f41f96c38'),
        ('athletic greens', '67b38619-2329-4493-93e7-594f41f96c38'),
        ('athletic greens ag1', '67b38619-2329-4493-93e7-594f41f96c38'),
        ('ag1 greens', '67b38619-2329-4493-93e7-594f41f96c38'),

        # New brands
        ('amazing grass', 'amazing-grass'),
        ('ancient nutrition', 'ancient-nutrition'),
        ('ancient nutrition collagen', 'ancient-nutrition'),
        ('dr axe ancient nutrition', 'ancient-nutrition'),
        ('four sigmatic', 'four-sigmatic'),
        ('foursigmatic', 'four-sigmatic'),
        ('four sigmatic mushroom coffee', 'four-sigmatic'),
        ('organifi', 'organifi'),
        ('organifi green juice', 'organifi'),
        ('organifi gold', 'organifi'),
        ('thorne', 'thorne'),
        ('thorne research', 'thorne'),
        ('thorne supplements', 'thorne'),
        ('thorne basic nutrients', 'thorne'),
        ('care of', 'care-of'),
        ('careof', 'care-of'),
        ('care of vitamins', 'care-of'),
        ("nature's bounty", 'natures-bounty'),
        ('natures bounty', 'natures-bounty'),
        ('nature bounty', 'natures-bounty'),
        ('natures bounty vitamins', 'natures-bounty'),
        ('solgar', 'solgar'),
        ('solgar vitamins', 'solgar'),
        ('solgar omnium', 'solgar'),
        ('now foods', 'now-foods'),
        ('now supplements', 'now-foods'),
        ('now vitamins', 'now-foods'),
        ('now', 'now-foods'),
        ('ritual', 'ritual-vitamins'),
        ('ritual vitamins', 'ritual-vitamins'),
        ('ritual essential protein', 'ritual-vitamins'),
        ('ritual multivitamin', 'ritual-vitamins'),
        ('rainbow light', 'rainbow-light'),
        ('rainbow light vitamins', 'rainbow-light'),
        ('rainbow light prenatal', 'rainbow-light'),
        ('megafood', 'megafood'),
        ('mega food', 'megafood'),
        ('megafood vitamins', 'megafood'),
        ('new chapter', 'new-chapter'),
        ('new chapter vitamins', 'new-chapter'),
        ('new chapter fermented', 'new-chapter'),
        ('built bar', 'built-bar'),
        ('built protein bar', 'built-bar'),
        ('health ade', 'health-ade-kombucha'),
        ('health-ade', 'health-ade-kombucha'),
        ('health ade kombucha', 'health-ade-kombucha'),
        ('health ade pink lady apple', 'health-ade-kombucha'),
        ('harmless harvest', 'harmless-harvest'),
        ('harmless harvest coconut water', 'harmless-harvest'),
        ('hint water', 'hint-water'),
        ('hint', 'hint-water'),
        ('hint fruit infused water', 'hint-water'),
        ('kevita', 'kevita'),
        ('ke vita', 'kevita'),
        ('kevita kombucha', 'kevita'),
        ('kevita sparkling probiotic', 'kevita'),
        ('sunwarrior', 'sunwarrior'),
        ('sun warrior', 'sunwarrior'),
        ('sunwarrior protein', 'sunwarrior'),
        ('green vibrance', 'green-vibrance'),
        ('vibrant health green vibrance', 'green-vibrance'),
        ("gt's kombucha", 'gts-kombucha'),
        ('gt kombucha', 'gts-kombucha'),
        ('gts living foods', 'gts-kombucha'),
        ('gt dave kombucha', 'gts-kombucha'),
        ('waterloo sparkling', 'waterloo-sparkling'),
        ('waterloo', 'waterloo-sparkling'),
        ('waterloo sparkling water', 'waterloo-sparkling'),
        ('two good', 'two-good'),
        ('two good yogurt', 'two-good'),
        ('oikos', 'oikos'),
        ('oikos greek yogurt', 'oikos'),
        ('oikos triple zero', 'oikos'),
        ('oikos pro', 'oikos'),
        ('kite hill', 'kite-hill'),
        ('kite hill yogurt', 'kite-hill'),
        ('kite hill almond milk yogurt', 'kite-hill'),
        ('forager project', 'forager-project'),
        ('forager', 'forager-project'),
        ('forager cashewgurt', 'forager-project'),
        ('lesser evil', 'lesser-evil'),
        ('lessevil', 'lesser-evil'),
        ('lessevil popcorn', 'lesser-evil'),
        ("jackson's", 'jacksons-chips'),
        ("jacksons chips", 'jacksons-chips'),
        ('jackson sweet potato chips', 'jacksons-chips'),
        ('solely fruit jerky', 'solely'),
        ('solely organic', 'solely'),
        ("that's it", 'thats-it'),
        ('thats it', 'thats-it'),
        ('thats it fruit bar', 'thats-it'),
        ('chomps', 'chomps'),
        ('chomps meat sticks', 'chomps'),
        ('chomps beef sticks', 'chomps'),
        ('primal harvest', 'primal-harvest'),
        ('primal supplements', 'primal-harvest'),
        ('hu kitchen', 'hu-kitchen'),
        ('hu chocolate', 'hu-kitchen'),
        ('hu bar', 'hu-kitchen'),
        ('hu gems', 'hu-kitchen'),
        ('hu crackers', 'hu-kitchen'),
    ]

    inserted_aliases = 0
    skipped_aliases = 0
    for alias_text, brand_id in aliases:
        # verify brand exists
        exists = c.execute('SELECT 1 FROM brands WHERE id=?', (brand_id,)).fetchone()
        if not exists:
            print(f"  WARNING: brand {brand_id} not found for alias '{alias_text}'")
            continue
        try:
            c.execute("INSERT OR IGNORE INTO brand_aliases (alias_text, brand_id, source) VALUES (?,?,'seed')",
                      (alias_text, brand_id))
            if c.rowcount:
                inserted_aliases += 1
            else:
                skipped_aliases += 1
        except Exception as e:
            print(f"  Alias error: {e}")

    conn.commit()
    print(f"\nAliases inserted: {inserted_aliases}, skipped (already exist): {skipped_aliases}")

    # ─── STEP 5: VERIFY COVERAGE ──────────────────────────────────────────────
    total = conn.execute('SELECT COUNT(*) FROM products').fetchone()[0]
    matched = conn.execute('SELECT COUNT(*) FROM products WHERE brand_id IS NOT NULL').fetchone()[0]
    unmatched = total - matched
    print(f"\n── Product Coverage ──")
    print(f"Total products: {total:,}")
    print(f"Matched to brand: {matched:,} ({matched/total*100:.1f}%)")
    print(f"Unmatched: {unmatched:,} ({unmatched/total*100:.1f}%)")

    print(f"\n── Supplement/Health Brands ──")
    supp = conn.execute('''
        SELECT id, name, category, overall_zone, parent_company_id FROM brands
        WHERE category IN ('supplement','beverage','grocery')
        AND overall_zone IS NOT NULL
        ORDER BY overall_zone, name
    ''').fetchall()
    print(f"Brands with zone data: {len(supp)}")
    for b in supp:
        print(f"  {b[3]} | {b[2]} | {b[1]}")

    conn.close()
    print("\n✓ Seed complete.")


if __name__ == '__main__':
    run()
