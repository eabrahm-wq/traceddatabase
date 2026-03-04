import sqlite3, uuid, json, re

DB = '/Users/evan/Desktop/Traceddatabase/traced.db'
conn = sqlite3.connect(DB)
c = conn.cursor()
conn.execute("PRAGMA journal_mode=WAL")

# ── Fix remaining Phase 2 ownership updates ──
remaining_updates = [
    ("private_conglomerate", "Trader Joe's is a privately-held US grocery chain owned by Aldi Nord (German Albrecht family). Despite its friendly, independent-seeming branding, it is part of one of the world's largest retail conglomerates.", '%Trader%Joe%'),
    ("public_conglomerate", "Target Corporation is a US mass-market retailer carrying food, household, and wellness brands alongside general merchandise.", '%Target%'),
    ("public_conglomerate", "Costco Wholesale is a US membership warehouse retailer known for bulk goods and its Kirkland Signature private label.", '%Costco%'),
    ("public_conglomerate", "Albertsons Companies is a US supermarket chain operating Safeway, Jewel-Osco, Vons, and other banners.", '%Albertsons%'),
    ("public_conglomerate", "Ahold Delhaize is a Dutch-Belgian retail conglomerate operating Stop & Shop, Giant, Food Lion, and Peapod.", '%Ahold%'),
]
for otype, desc, name_like in remaining_updates:
    c.execute("UPDATE companies SET ownership_type=?, description=? WHERE name LIKE ? AND (ownership_type IS NULL OR ownership_type='')", (otype, desc, name_like))
    print(f"Updated {name_like}: {c.rowcount} rows")

# ── Insert new companies (schema has no slug column; use name as uniqueness check) ──
new_companies = [
    ('Simply Good Foods', 'public_conglomerate', 2017, 0, None, 0, 'Simply Good Foods Company is a Nasdaq-listed holding company that owns Quest Nutrition and Atkins Nutritionals. It was created specifically to consolidate premium nutrition brands.'),
    ('BellRing Brands', 'public_conglomerate', 2019, 0, None, 0, 'BellRing Brands is a publicly traded company (NYSE: BRBR) spun off from Post Holdings. It owns Premier Protein, Dymatize, and PowerBar.'),
    ('Hain Celestial', 'public_conglomerate', 1993, 0, None, 0, "Hain Celestial Group is a Nasdaq-listed natural and organic products company. It owns Earth's Best, Garden of Eatin', Celestial Seasonings, and dozens of other \"natural\" brands."),
    ('Post Holdings', 'public_conglomerate', 1895, 0, None, 0, 'Post Holdings is a NYSE-listed consumer packaged goods holding company. It owns Post cereals, Bob Evans, Michael Foods, and spun off BellRing Brands in 2019.'),
    ('Glanbia', 'public_conglomerate', 1997, 0, None, 0, "Glanbia plc is an Irish global nutrition group that owns Optimum Nutrition, BSN, Think!, Isopure, and Amazing Grass through its Glanbia Performance Nutrition division."),
    ('KKR', 'pe_firm', 1976, 0, 'KKR', 0, "KKR & Co. is one of the world's largest private equity firms with $500B+ AUM. In food/consumer, it owns Magic Leap, Panera, and held RBF and other brands. KKR typically holds portfolio companies 5-7 years before exit."),
    ('TPG Capital', 'pe_firm', 1992, 0, 'TPG Capital', 0, 'TPG Capital is a major global PE firm that has owned Schiff Nutrition, Safeway, and various food/supplement brands. Known for aggressive cost-cutting post-acquisition.'),
    ('Clorox', 'public_conglomerate', 1913, 0, None, 0, "The Clorox Company is a NYSE-listed consumer goods manufacturer known for bleach, but also owns Burt's Bees, Brita, Hidden Valley, KC Masterpiece, Kingsford, and RenewLife supplements."),
    ('Pharmavite', 'subsidiary', 1971, 0, None, 0, 'Pharmavite LLC is the maker of Nature Made vitamins and supplements. It is a wholly-owned subsidiary of Otsuka Holdings of Japan. Nature Made is the #1 selling vitamin brand in the US.'),
    ('Haleon', 'public_conglomerate', 2022, 0, None, 0, 'Haleon plc (formerly GSK Consumer Healthcare) is a London-listed consumer health company spun off from GlaxoSmithKline in 2022. It owns Centrum, Advil, Sensodyne, Chapstick, Tums, and Emergen-C.'),
    ('Maple Leaf Foods', 'public_conglomerate', 1927, 0, None, 0, 'Maple Leaf Foods is a Canadian meat and plant-based protein company listed on the Toronto Stock Exchange. It owns Lightlife Foods and Field Roast through its Greenleaf Foods subsidiary.'),
    ('Otsuka Holdings', 'public_conglomerate', 1964, 0, None, 0, 'Otsuka Holdings is a Japanese pharmaceutical and consumer products conglomerate listed on the Tokyo Stock Exchange. It owns Pharmavite (Nature Made vitamins) in the US.'),
    ('Morinaga', 'public_conglomerate', 1899, 0, None, 0, 'Morinaga & Co. is a Japanese confectionery and food company. In the US, it owns Beech-Nut Nutrition, a baby food brand, which it acquired in 2013.'),
    ('Hero Group', 'private_conglomerate', 1886, 0, None, 0, "Hero Group is a Swiss family-owned food company founded in 1886. It owns Beech-Nut's former operations in some markets and holds the Fruit-eze brand. Known for fruit spreads and baby nutrition."),
    ('Plum Organics Parent', 'public_conglomerate', 1869, 0, None, 0, 'Campbell Soup Company subsidiary responsible for Plum Organics baby food brand, acquired in 2013 for approximately $249 million.'),
]

for row in new_companies:
    name, otype, fy, fl, pe, nacq, desc = row
    exists = c.execute("SELECT id FROM companies WHERE name=?", (name,)).fetchone()
    if exists:
        print(f"  SKIP existing: {name}")
        continue
    cid = str(uuid.uuid4())
    c.execute("""INSERT INTO companies (id, name, ownership_type, founded_year, founder_led, pe_firm, num_acquisitions, description)
                 VALUES (?,?,?,?,?,?,?,?)""",
              (cid, name, otype, fy, fl, pe, nacq, desc))
    print(f"  Inserted: {name}")

conn.commit()
print("\nPhase 2 COMPLETE")
print("Total companies:", c.execute("SELECT COUNT(*) FROM companies").fetchone()[0])
conn.close()
