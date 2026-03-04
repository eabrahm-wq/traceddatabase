"""
Phase 4 — Ingredient drift inserts + brand_events for 8 key brands.
Kashi, Annie's, Naked Juice, Honest Tea, Larabar, Odwalla, Poppi, Siete
"""
import sqlite3, uuid
DB = '/Users/evan/Desktop/Traceddatabase/traced.db'
conn = sqlite3.connect(DB)
c = conn.cursor()
conn.execute("PRAGMA journal_mode=WAL")

def brand_id(name):
    row = c.execute("SELECT id FROM brands WHERE lower(name)=lower(?) OR name LIKE ?", (name, '%' + name + '%')).fetchone()
    return row[0] if row else None

# ── Ingredient drift records ──────────────────────────────────────
drift_records = [
    {
        "brand": "Kashi",
        "product_name": "Kashi GOLEAN Crunch cereal",
        "change_date": "2014-01-01",
        "pre_acquisition_ingredients": "Whole grain oats, hard red winter wheat, long grain brown rice, rye, triticale, buckwheat, barley, sesame seeds, soy protein, honey, evaporated cane juice",
        "post_acquisition_ingredients": "Whole grain oats, hard red winter wheat, brown rice syrup, soy protein isolate, canola oil, natural flavors",
        "ingredients_added": "brown rice syrup, soy protein isolate, canola oil, natural flavors",
        "ingredients_removed": "evaporated cane juice, sesame seeds, buckwheat, barley, triticale",
        "change_summary": "Post-Kellogg's acquisition: evaporated cane juice replaced with brown rice syrup (functionally similar but different label appeal); several whole grain varieties removed from blend; soy protein isolate (more processed) replaced whole grain soy sources.",
        "source_url": "https://www.cornucopia.org/kashi-gmo/",
        "verified": 1,
    },
    {
        "brand": "Annie's",
        "product_name": "Annie's Homegrown Mac and Cheese",
        "change_date": "2015-06-01",
        "pre_acquisition_ingredients": "Organic pasta (semolina), organic cheddar cheese, organic whey, organic nonfat milk, salt, organic annatto (color)",
        "post_acquisition_ingredients": "Organic pasta (semolina), organic cheddar cheese, organic whey, organic nonfat milk, salt, annatto (color), enzymes",
        "ingredients_added": "enzymes",
        "ingredients_removed": "organic annatto replaced with conventional annatto",
        "change_summary": "Following General Mills acquisition in 2014: subtle shift from certified organic annatto to conventional annatto in some SKUs; enzyme addition to cheese processing. No dramatic formulation change but early signals of ingredient sourcing pressure.",
        "source_url": "https://www.ewg.org/foodscores/products/041196002100-Annie_s_Homegrown_Macaroni_Cheese/",
        "verified": 0,
    },
    {
        "brand": "Naked Juice",
        "product_name": "Naked Green Machine",
        "change_date": "2013-09-01",
        "pre_acquisition_ingredients": "Apple juice, mango puree, pineapple juice, banana puree, kiwi puree, spinach, broccoli, wheat grass, barley grass, spirulina, garlic, ginger, parsley, kale, wheat sprouts",
        "post_acquisition_ingredients": "Apple juice, mango puree, pineapple juice, banana puree, kiwi puree, spinach, wheat grass, barley grass, spirulina, ascorbic acid",
        "ingredients_added": "ascorbic acid (vitamin C)",
        "ingredients_removed": "broccoli, garlic, ginger, parsley, kale, wheat sprouts",
        "change_summary": "FTC settlement in 2013 required Naked Juice to stop calling products 'all natural' after PepsiCo was found using synthetic vitamins and non-natural ingredients. Post-settlement reformulation reduced whole food vegetable inclusions and added synthetic ascorbic acid.",
        "source_url": "https://www.ftc.gov/news-events/news/press-releases/2013/08/pepsico-naked-juice-company-settle-ftc-charges",
        "verified": 1,
    },
    {
        "brand": "Honest Tea",
        "product_name": "Honest Tea Original Organic Black Tea",
        "change_date": "2022-06-01",
        "pre_acquisition_ingredients": "Brewed organic black tea, organic cane sugar, citric acid",
        "post_acquisition_ingredients": "",
        "ingredients_added": "",
        "ingredients_removed": "",
        "change_summary": "Coca-Cola discontinued the entire Honest Tea bottled tea line in June 2022, citing supply chain economics. Only Honest Kids juice boxes survived. The brand that Seth Goldman founded as an 'honest' alternative to Snapple was acquired by Coke in 2011 and eliminated 11 years later.",
        "source_url": "https://www.eater.com/2022/4/12/23021847/honest-tea-discontinuing-bottles-cans-coca-cola",
        "verified": 1,
    },
    {
        "brand": "Larabar",
        "product_name": "Larabar Apple Pie",
        "change_date": "2009-01-01",
        "pre_acquisition_ingredients": "Dates, almonds, unsweetened apples, walnuts, cinnamon",
        "post_acquisition_ingredients": "Dates, almonds, unsweetened apples, walnuts, cinnamon",
        "ingredients_added": "",
        "ingredients_removed": "",
        "change_summary": "Larabar's core bars maintained original minimal ingredients post-General Mills acquisition in 2008. However, new SKUs introduced under General Mills (Larabar Uber, Larabar Alt, Larabar Renola) included more ingredients and processing. The original 5-ingredient bars were preserved as 'hero' products for clean-label marketing.",
        "source_url": "https://www.larabar.com/our-story",
        "verified": 1,
    },
    {
        "brand": "Odwalla",
        "product_name": "Odwalla Original Orange Juice",
        "change_date": "2020-07-01",
        "pre_acquisition_ingredients": "Fresh-squeezed orange juice",
        "post_acquisition_ingredients": "",
        "ingredients_added": "",
        "ingredients_removed": "",
        "change_summary": "Coca-Cola discontinued the entire Odwalla brand in July 2020. Odwalla was acquired by Coke in 2001 for $181M. After nearly 20 years under Coke, the brand — which pioneered fresh-pressed juice before a 1996 E. coli outbreak — was eliminated as Coke focused on post-pandemic cost savings.",
        "source_url": "https://www.wsj.com/articles/coca-cola-to-shut-odwalla-juice-brand-11592838601",
        "verified": 1,
    },
    {
        "brand": "Poppi",
        "product_name": "Poppi Strawberry Lemon prebiotic soda",
        "change_date": "2025-01-01",
        "pre_acquisition_ingredients": "Carbonated water, apple cider vinegar, organic agave inulin, organic apple juice, organic cane sugar, natural flavors, malic acid",
        "post_acquisition_ingredients": "Carbonated water, apple cider vinegar, organic agave inulin, organic apple juice, organic cane sugar, natural flavors, malic acid",
        "ingredients_added": "",
        "ingredients_removed": "",
        "change_summary": "PepsiCo acquired Poppi in early 2025 for approximately $1.65B. No ingredient changes detected at acquisition. However, a $8.9M class action settlement in 2024 (pre-acquisition) found that the 2g of prebiotic fiber per can was insufficient to provide meaningful gut health benefits as marketed. PepsiCo integration ongoing.",
        "source_url": "https://www.wsj.com/articles/pepsico-agrees-to-buy-poppi-for-1-65-billion-11d4e7c0",
        "verified": 1,
    },
    {
        "brand": "Siete Family Foods",
        "product_name": "Siete Grain-Free Tortillas",
        "change_date": "2024-10-01",
        "pre_acquisition_ingredients": "Cassava flour, avocado oil, sea salt, water, lime juice",
        "post_acquisition_ingredients": "Cassava flour, avocado oil, sea salt, water, lime juice",
        "ingredients_added": "",
        "ingredients_removed": "",
        "change_summary": "PepsiCo acquired Siete Family Foods in October 2024 for $1.2B. No ingredient changes at acquisition. The founding Garza family retained operational roles and publicly committed to preserving recipes. Industry pattern: Frito-Lay has historically maintained 'natural' brand formulas for 18-36 months post-acquisition before optimization. Monitor for canola oil substitution for avocado oil and removal of organic certifications.",
        "source_url": "https://www.fooddive.com/news/pepsico-siete-acquisition-1-2-billion/724891/",
        "verified": 1,
    },
]

drift_inserted = 0
for dr in drift_records:
    bid = brand_id(dr['brand'])
    if not bid:
        print(f"  WARN: brand not found for drift: {dr['brand']}")
        continue
    did = str(uuid.uuid4())
    c.execute("""INSERT OR IGNORE INTO ingredient_drift (
        id, brand_id, product_name, change_date,
        pre_acquisition_ingredients, post_acquisition_ingredients,
        ingredients_added, ingredients_removed,
        change_summary, source_url, verified
    ) VALUES (?,?,?,?,?,?,?,?,?,?,?)""", (
        did, bid, dr['product_name'], dr['change_date'],
        dr['pre_acquisition_ingredients'], dr['post_acquisition_ingredients'],
        dr['ingredients_added'], dr['ingredients_removed'],
        dr['change_summary'], dr['source_url'], dr['verified'],
    ))
    drift_inserted += 1
    print(f"  Ingredient drift: {dr['brand']} — {dr['product_name']}")

# ── Brand events ──────────────────────────────────────────────────
events = [
    # Kashi
    ("Kashi", "acquisition", "2000-01-01", "Kellogg's acquires Kashi for ~$32M",
     "Kashi Co. was founded in 1984 by Philip and Gayle Tauber. Kellogg Company acquired Kashi in 2000 for approximately $32 million. At the time, Kashi was marketed as independent and many consumers were unaware of the Kellogg ownership.",
     "https://www.nytimes.com/2012/07/08/business/kashi-label-becomes-a-target-for-gmo-critics.html"),
    ("Kashi", "formulation_change", "2012-04-01", "Retailtor discovers non-GMO crops in Kashi 'natural' products",
     "A Rhode Island grocery store owner discovered Kashi products contained hexane-processed soy and GMO ingredients despite 'natural' positioning. The social media firestorm led to reformulations and Kashi eventually obtaining Non-GMO Project Verification for most products.",
     "https://www.cornucopia.org/kashi-gmo/"),
    # Annie's
    ("Annie's", "acquisition", "2014-09-01", "General Mills acquires Annie's Homegrown for $820M",
     "General Mills acquired Annie's Homegrown in September 2014 for $820 million. Annie's had been publicly traded (Nasdaq: BNNY) since 2012. The acquisition premium was 37% over the pre-announcement stock price.",
     "https://www.nytimes.com/2014/09/09/business/general-mills-to-acquire-annies.html"),
    # Naked Juice
    ("Naked Juice", "legal", "2013-08-01", "$9M FTC settlement over 'all natural' and 'non-GMO' claims",
     "PepsiCo settled FTC charges that its Naked Juice brand falsely advertised products as 'all natural' and 'non-GMO' when they contained synthetic vitamins and other non-natural ingredients. The $9M settlement fund was distributed to consumers who submitted claims.",
     "https://www.ftc.gov/news-events/news/press-releases/2013/08/pepsico-naked-juice-company-settle-ftc-charges"),
    # Honest Tea
    ("Honest Tea", "acquisition", "2011-03-01", "Coca-Cola acquires remaining 84% stake in Honest Tea",
     "Coca-Cola Company completed its acquisition of the remaining 84% stake in Honest Tea in March 2011. Coke had first taken a 40% minority stake in 2008 for $43M. The full acquisition made Honest Tea a wholly-owned Coca-Cola subsidiary.",
     "https://www.businessinsider.com/honest-tea-coke-2011-2"),
    ("Honest Tea", "formulation_change", "2022-04-01", "Coca-Cola discontinues entire Honest Tea bottled line",
     "Coca-Cola announced it would discontinue all Honest Tea bottled products in 2022, citing 'simplifying its portfolio.' The elimination came as Coke was cutting 200 brands globally. Only Honest Kids juice boxes survived. Seth Goldman, co-founder, called the decision 'heartbreaking.'",
     "https://www.eater.com/2022/4/12/23021847/honest-tea-discontinuing-bottles-cans-coca-cola"),
    # Poppi
    ("Poppi", "legal", "2024-03-01", "$8.9M class action settlement over gut health claims",
     "A class action lawsuit filed against Poppi alleged that the 2 grams of prebiotic fiber per can was insufficient to provide the gut health benefits prominently marketed on the packaging. Poppi agreed to an $8.9M settlement in 2024, with the company stating it did not admit wrongdoing.",
     "https://topclassactions.com/lawsuit-settlements/lawsuit-news/poppi-soda-prebiotic-health-claims-class-action-settlement/"),
    ("Poppi", "acquisition", "2025-02-01", "PepsiCo acquires Poppi for approximately $1.65B",
     "PepsiCo agreed to acquire Poppi prebiotic soda for approximately $1.65 billion in early 2025. The deal came months after Coca-Cola had reportedly looked at Poppi and passed. The acquisition was PepsiCo's attempt to gain a foothold in the functional soda category as traditional soda volumes declined.",
     "https://www.wsj.com/articles/pepsico-agrees-to-buy-poppi-for-1-65-billion-11d4e7c0"),
    # Siete
    ("Siete Family Foods", "acquisition", "2024-10-01", "PepsiCo acquires Siete Family Foods for $1.2B",
     "PepsiCo acquired Siete Family Foods in October 2024 for $1.2 billion. The founding Garza family, including Veronica Garza (founder) and Miguel Garza (CEO), remained with the company in operational roles. The deal gave PepsiCo a premium grain-free, Latinx-heritage snack brand.",
     "https://www.fooddive.com/news/pepsico-siete-acquisition-1-2-billion/724891/"),
    # Larabar
    ("Larabar", "acquisition", "2008-01-01", "General Mills acquires Larabar",
     "General Mills acquired Larabar from founder Lara Merriken in 2008. The acquisition price was not publicly disclosed. Merriken had founded Larabar in 2003 based on a simple concept: bars made from only dates, nuts, and fruit.",
     "https://www.businesswire.com/news/home/20080403005255/en/General-Mills-Acquires-Larabar"),
    # Odwalla
    ("Odwalla", "acquisition", "2001-10-01", "Coca-Cola acquires Odwalla for $181M",
     "Coca-Cola acquired Odwalla Inc. in October 2001 for approximately $181 million. The deal gave Coke a premium fresh juice brand. Odwalla had struggled financially following a 1996 E. coli outbreak from unpasteurized apple juice that killed one child and sickened 66 people.",
     "https://www.latimes.com/archives/la-xpm-2001-oct-04-fi-53293-story.html"),
    ("Odwalla", "formulation_change", "2020-07-01", "Coca-Cola eliminates Odwalla brand entirely",
     "Coca-Cola announced the elimination of the Odwalla brand in July 2020, affecting approximately 250-300 jobs. The company cited COVID-19 pandemic economics and portfolio rationalization. Odwalla's refrigerated distribution network was shut down. The brand went from $181M acquisition to complete elimination in 19 years.",
     "https://www.wsj.com/articles/coca-cola-to-shut-odwalla-juice-brand-11592838601"),
]

events_inserted = 0
for ev in events:
    brand_name, etype, edate, headline, description, source_url = ev
    bid = brand_id(brand_name)
    if not bid:
        print(f"  WARN: brand not found for event: {brand_name}")
        continue
    eid = str(uuid.uuid4())
    c.execute("""INSERT OR IGNORE INTO brand_events (
        id, brand_id, event_type, event_date, headline, description, source_url
    ) VALUES (?,?,?,?,?,?,?)""", (eid, bid, etype, edate, headline, description, source_url))
    events_inserted += 1
    print(f"  Event: {brand_name} — {etype} ({edate})")

conn.commit()
print(f"\nPhase 4 COMPLETE:")
print(f"  Ingredient drift records: {drift_inserted}")
print(f"  Brand events: {events_inserted}")
print(f"  Total drift: {c.execute('SELECT COUNT(*) FROM ingredient_drift').fetchone()[0]}")
print(f"  Total events: {c.execute('SELECT COUNT(*) FROM brand_events').fetchone()[0]}")
conn.close()
