import sqlite3, uuid
conn = sqlite3.connect('traced.db')
c = conn.cursor()

# Add Bayer company
bayer_id = str(uuid.uuid4())
c.execute("""INSERT OR IGNORE INTO companies (id, name, ownership_type, founded_year, description)
             VALUES (?, 'Bayer AG', 'public_conglomerate', 1863,
             'Bayer AG is a German multinational pharmaceutical and biotechnology company. Through its 2018 Monsanto acquisition, Bayer became the world largest producer of glyphosate herbicide (Roundup). Bayer paid $10B+ to settle Roundup cancer lawsuits.')""",
            (bayer_id,))
print(f'Bayer insert: {c.rowcount}')

# Get Bayer id
row = c.execute("SELECT id FROM companies WHERE name='Bayer AG'").fetchone()
if row:
    bayer_id = row[0]
    c.execute("UPDATE brands SET parent_company_id=? WHERE lower(name)='one a day'", (bayer_id,))
    print(f'One A Day linked to Bayer: {c.rowcount}')

# Link Nuun to Nestle
nestle = c.execute("SELECT id FROM companies WHERE name LIKE '%Nestle%' OR name LIKE '%Nestl%' LIMIT 1").fetchone()
if nestle:
    c.execute("UPDATE brands SET parent_company_id=? WHERE lower(name)='nuun'", (nestle[0],))
    print(f'Nuun linked to Nestle: {c.rowcount}')

# Check remaining brands that should have parents but don't
# Brands inserted in phase 3 that need parent links
link_fixes = [
    ('Quest Nutrition', 'Simply Good'),
    ('Happy Baby', 'Danone'),
    ('Plum Organics', 'Campbell'),
    ('Lightlife', 'Maple Leaf'),
    ('Sweet Earth', 'Nestle'),
    ('Nuun', 'Nestle'),
    ('Bare Snacks', 'PepsiCo'),
    ('Siete Family Foods', 'PepsiCo'),
    ('Vega', 'Danone'),
    ('Centrum', 'Haleon'),
    ('Emergen-C', 'Haleon'),
    ('Airborne', 'Haleon'),
    ('Nature Made', 'Pharmavite'),
    ('Vital Proteins', 'Nestle'),
    ('Liquid I.V.', 'Unilever'),
    ('Garden of Life', 'Nestle'),
    ('Orgain', 'Nestle'),
    ('Muscle Milk', 'Hormel'),
    ('Premier Protein', 'BellRing'),
    ('Optimum Nutrition', 'Glanbia'),
    ('Gerber', 'Nestle'),
    ('Beech-Nut', 'Morinaga'),
    ("Earth's Best", 'Hain Celestial'),
    ('Gardein', 'Conagra'),
    ('Perfect Bar', 'Mondelez'),
]

for brand_name, company_like in link_fixes:
    company = c.execute("SELECT id FROM companies WHERE name LIKE ?", ('%' + company_like + '%',)).fetchone()
    if not company:
        print(f"  WARN: company not found for {brand_name}: {company_like}")
        continue
    brand = c.execute("SELECT id, parent_company_id FROM brands WHERE lower(name)=lower(?)", (brand_name,)).fetchone()
    if not brand:
        print(f"  WARN: brand not found: {brand_name}")
        continue
    if brand[1] is None:
        c.execute("UPDATE brands SET parent_company_id=? WHERE lower(name)=lower(?)", (company[0], brand_name))
        print(f"  Linked {brand_name} -> {company_like}: {c.rowcount}")
    else:
        print(f"  Already linked: {brand_name}")

conn.commit()
print("Done fixing parent links")
conn.close()
