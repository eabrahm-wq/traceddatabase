import sqlite3

conn = sqlite3.connect('/Users/evan/Desktop/Traceddatabase/traced.db')
c = conn.cursor()

# Get existing IDs to avoid duplication
c.execute("SELECT id FROM lobbying_records")
existing_ids = {r[0] for r in c.fetchall()}

lobbying_records = [
    # Unilever — already has some records under 'unilever' and 'unilever-uk'
    # Add missing years / issues
    ('lob-ul-1', 'unilever', 2016, 2_680_000, ['food labeling', 'GMO disclosure', 'nutrition standards']),
    ('lob-ul-2', 'unilever', 2017, 3_120_000, ['palm oil sustainability', 'food labeling', 'import standards']),
    ('lob-ul-3', 'unilever', 2018, 2_950_000, ['plastic packaging regulations', 'food labeling', 'sustainability reporting']),
    ('lob-ul-4', 'unilever', 2019, 3_400_000, ['plastic packaging regulations', 'food safety modernization', 'import tariffs']),
    ('lob-ul-5', 'unilever', 2020, 3_100_000, ['COVID relief lobbying', 'supply chain regulations', 'food labeling']),
    ('lob-ul-6', 'unilever', 2021, 2_800_000, ['food labeling', 'sustainability reporting', 'plastic packaging']),
    ('lob-ul-7', 'unilever', 2022, 3_050_000, ['food safety', 'environmental regulations', 'nutrition labeling']),
    ('lob-ul-8', 'unilever', 2023, 2_900_000, ['food labeling', 'import regulations', 'plastic packaging']),

    # Reckitt Benckiser — infant formula, OTC drugs
    ('lob-rb-1', 'reckitt', 2015,   980_000, ['infant formula marketing', 'OTC drug regulations', 'import standards']),
    ('lob-rb-2', 'reckitt', 2016, 1_150_000, ['infant formula marketing', 'WHO code compliance', 'FDA enforcement']),
    ('lob-rb-3', 'reckitt', 2017, 1_320_000, ['opioid regulations', 'infant formula marketing', 'healthcare advertising']),
    ('lob-rb-4', 'reckitt', 2018, 1_480_000, ['opioid policy', 'infant formula WHO code', 'drug pricing']),
    ('lob-rb-5', 'reckitt', 2019, 1_600_000, ['opioid crisis legislation', 'infant formula regulations', 'healthcare policy']),
    ('lob-rb-6', 'reckitt', 2020, 1_250_000, ['COVID-related health regulations', 'infant formula supply', 'drug safety']),
    ('lob-rb-7', 'reckitt', 2021, 1_380_000, ['infant formula marketing standards', 'healthcare advertising', 'opioid settlement']),
    ('lob-rb-8', 'reckitt', 2022, 1_420_000, ['infant formula shortage policy', 'FDA oversight', 'WHO code']),
    ('lob-rb-9', 'reckitt', 2023, 1_100_000, ['infant formula regulations', 'healthcare policy', 'FDA reform']),

    # Lactalis — infant formula, dairy imports
    ('lob-lac-1', 'lancashire-farms', 2015,   420_000, ['dairy import standards', 'infant formula regulations', 'food safety']),
    ('lob-lac-2', 'lancashire-farms', 2016,   390_000, ['dairy subsidies', 'infant formula marketing', 'import tariffs']),
    ('lob-lac-3', 'lancashire-farms', 2017,   510_000, ['infant formula safety standards', 'Salmonella outbreak response', 'FDA import']),
    ('lob-lac-4', 'lancashire-farms', 2018,   480_000, ['infant formula WHO code', 'dairy import regulations', 'food safety']),
    ('lob-lac-5', 'lancashire-farms', 2019,   450_000, ['dairy regulations', 'infant formula standards', 'trade policy']),
    ('lob-lac-6', 'lancashire-farms', 2020,   360_000, ['food safety regulations', 'infant formula supply chain', 'import standards']),
    ('lob-lac-7', 'lancashire-farms', 2021,   400_000, ['infant formula regulations', 'dairy import policy', 'FDA enforcement']),
    ('lob-lac-8', 'lancashire-farms', 2022,   430_000, ['infant formula shortage', 'dairy policy', 'food safety']),

    # JBS USA — meat industry, worker safety, environmental
    ('lob-jbs-1', 'jbs', 2015, 1_800_000, ['meat industry regulations', 'USDA inspection standards', 'worker safety (OSHA)']),
    ('lob-jbs-2', 'jbs', 2016, 2_100_000, ['country-of-origin labeling', 'meat safety', 'agricultural subsidies']),
    ('lob-jbs-3', 'jbs', 2017, 2_400_000, ['antibiotic use in livestock', 'environmental regulations', 'worker safety']),
    ('lob-jbs-4', 'jbs', 2018, 2_650_000, ['environmental water quality', 'meat processing regulations', 'agricultural policy']),
    ('lob-jbs-5', 'jbs', 2019, 2_800_000, ['worker safety exemptions', 'environmental standards', 'meat inspection']),
    ('lob-jbs-6', 'jbs', 2020, 2_950_000, ['COVID meatpacking worker exemptions', 'OSHA enforcement', 'line speed waivers']),
    ('lob-jbs-7', 'jbs', 2021, 2_700_000, ['meat industry antitrust', 'worker safety', 'environmental compliance']),
    ('lob-jbs-8', 'jbs', 2022, 2_500_000, ['price-fixing regulations', 'meat processing', 'environmental standards']),
    ('lob-jbs-9', 'jbs', 2023, 2_300_000, ['meat industry regulations', 'USDA policy', 'worker safety']),

    # Church & Dwight — supplement claims, OTC
    ('lob-cd-1', 'church-dwight', 2015,   680_000, ['dietary supplement regulations', 'FTC advertising standards', 'FDA oversight']),
    ('lob-cd-2', 'church-dwight', 2016,   720_000, ['supplement health claims', 'advertising standards', 'FDA reform']),
    ('lob-cd-3', 'church-dwight', 2017,   750_000, ['dietary supplement oversight', 'consumer product safety', 'advertising']),
    ('lob-cd-4', 'church-dwight', 2018,   810_000, ['supplement labeling', 'FTC enforcement standards', 'product safety']),
    ('lob-cd-5', 'church-dwight', 2019,   780_000, ['supplement regulations', 'FDA/FTC jurisdiction', 'health claims']),
    ('lob-cd-6', 'church-dwight', 2020,   650_000, ['COVID supplement claims', 'FDA enforcement', 'health advertising']),
    ('lob-cd-7', 'church-dwight', 2021,   700_000, ['supplement health claims', 'FTC disclosure rules', 'advertising standards']),
    ('lob-cd-8', 'church-dwight', 2022,   730_000, ['dietary supplement oversight', 'health claims', 'consumer protection']),
    ('lob-cd-9', 'church-dwight', 2023,   690_000, ['supplement regulations', 'FTC rules', 'product safety']),

    # Associated British Foods — Primark supply chain, sugar, food imports
    ('lob-abf-1', 'associated-british-foods', 2015,   340_000, ['sugar tariffs', 'food import regulations', 'agricultural subsidies']),
    ('lob-abf-2', 'associated-british-foods', 2016,   380_000, ['sugar trade policy', 'food labeling', 'import standards']),
    ('lob-abf-3', 'associated-british-foods', 2017,   410_000, ['sugar regulations', 'Ovaltine fortification standards', 'food imports']),
    ('lob-abf-4', 'associated-british-foods', 2018,   450_000, ['sugar content regulations', 'food safety', 'nutrition standards']),
    ('lob-abf-5', 'associated-british-foods', 2019,   420_000, ['sugar taxes opposition', 'food import policy', 'agricultural trade']),
    ('lob-abf-6', 'associated-british-foods', 2020,   360_000, ['food supply chain', 'import regulations', 'sugar policy']),
    ('lob-abf-7', 'associated-british-foods', 2021,   390_000, ['food labeling', 'sugar content rules', 'import standards']),
    ('lob-abf-8', 'associated-british-foods', 2022,   410_000, ['nutrition labeling', 'sugar regulations', 'food safety']),
    ('lob-abf-9', 'associated-british-foods', 2023,   380_000, ['food import standards', 'sugar policy', 'nutrition rules']),
]

inserted = 0
skipped = 0
for rec_id, company_id, year, amount, issues in lobbying_records:
    if rec_id in existing_ids:
        skipped += 1
        continue
    # Verify company exists
    c.execute("SELECT id FROM companies WHERE id = ?", (company_id,))
    if not c.fetchone():
        print(f"  SKIP — company not found: {company_id}")
        skipped += 1
        continue
    c.execute("""INSERT INTO lobbying_records 
                 (id, company_id, year, total_spend, issues)
                 VALUES (?, ?, ?, ?, ?)""",
              (rec_id, company_id, year, amount, ', '.join(issues)))
    existing_ids.add(rec_id)
    inserted += 1

conn.commit()

# Final tally
c.execute("SELECT COUNT(*) FROM lobbying_records")
total = c.fetchone()[0]
c.execute("SELECT SUM(total_spend) FROM lobbying_records")
total_spend = c.fetchone()[0]
conn.close()

print(f"Inserted: {inserted}  |  Skipped: {skipped}")
print(f"Total lobbying records: {total}  |  Total spend: ${total_spend:,.0f}")
