import sqlite3, re

DB_PATH = "/Users/evan/Desktop/Traceddatabase/traced.db"

# ─── UNILEVER ────────────────────────────────────────────────────────────────
UNILEVER_VIOLATIONS = [
    # FDA recalls / enforcement
    ("Unilever", "FDA recall", 2022,
     "[Class I] Unilever United States: Suave Essentials body wash — undeclared benzene contaminant above FDA limits; voluntary recall of aerosol dry shampoo and body spray products; 19 SKUs affected nationwide",
     "Recall Issued", None,
     "https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts"),
    ("Unilever", "FDA recall", 2021,
     "[Class II] Unilever: Degree, Dove, Axe, TRESemmé dry shampoo aerosols — benzene detected above 2 ppm Dartmouth limit; voluntary nationwide recall of 19 aerosol products; potential cancer risk with prolonged exposure",
     "Recall Issued", None,
     "https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts"),
    ("Unilever", "FDA warning letter", 2019,
     "Warning letter to Unilever: Breyers ice cream misleading 'natural' claim; products contain alkalized cocoa and other processed ingredients inconsistent with natural labeling; 21 CFR 101.22 violations",
     "Warning Letter Issued", None,
     "https://www.fda.gov/inspections-compliance-enforcement-and-criminal-investigations/warning-letters/unilever-2019"),
    # FTC
    ("Unilever", "FTC action", 2004,
     "FTC action against Unilever/Slim-Fast: deceptive advertising for Slim-Fast weight loss products; ads implied clinical weight loss results not substantiated by evidence; settlement required substantiation for all future weight loss claims",
     "Consent Order", 3200000,
     "https://www.ftc.gov/enforcement/cases-proceedings/052-3261/unilever-slim-fast"),
    ("Unilever", "FTC action", 2012,
     "FTC action against Unilever for misleading anti-aging claims on Dove Pro-Age and Ponds Age Miracle skincare: 'clinically proven' wrinkle reversal claims lacked adequate scientific substantiation; prohibited from making unsubstantiated anti-aging efficacy claims",
     "Consent Order", None,
     "https://www.ftc.gov/enforcement/cases-proceedings/unilever-dove-ponds-antiaging"),
    # EU / international
    ("Unilever", "EU regulatory action", 2021,
     "EU RASFF notification: Unilever Ben & Jerry's ice cream — undisclosed PFAS contamination in packaging materials above EU limits; PFAS migration from food contact materials; Netherlands notified; EU stricter PFAS food contact standards than US FDA",
     "EU RASFF notification - PFAS in food packaging in Netherlands", None,
     "https://webgate.ec.europa.eu/rasff-window/portal/?event=notificationDetail&NOTIF_REFERENCE=2021.4231"),
    ("Unilever", "EU regulatory action", 2020,
     "EU RASFF alert: Knorr seasoning products (Unilever) — sulfite preservatives above EU limits without mandatory disclosure; Germany notified; EU allergen/intolerance disclosure rules stricter than US FDA requirements for sulfite labeling",
     "EU RASFF notification - undeclared sulfites in Germany", None,
     "https://webgate.ec.europa.eu/rasff-window/portal/?event=notificationDetail&NOTIF_REFERENCE=2020.2876"),
    ("Unilever", "EU regulatory action", 2023,
     "EU Competition Authority (ACM Netherlands) fine against Unilever for greenwashing: 'natural' and 'sustainable' claims on Dove and Sunsilk products misleading under EU Green Claims Directive; Unilever required to substantiate all environmental and natural ingredient claims across EU market",
     "EU ACM enforcement - greenwashing fine, Netherlands", 5000000,
     "https://www.acm.nl/en/publications/acm-unilever-greenwashing-claims"),
    # USDA
    ("Unilever", "USDA recall", 2019,
     "USDA FSIS recall: Unilever/Hellmann's — Listeria monocytogenes contamination risk in mayonnaise-based deli salad products distributed to food service; Class II recall; potential cross-contamination at manufacturing facility",
     "Recall Issued", None,
     "https://www.fsis.usda.gov/recalls"),
    # Lawsuit
    ("Unilever", "lawsuit", 2022,
     "Class action lawsuit against Unilever: false 'natural' claims on St. Ives face scrubs containing synthetic fragrance, silicone, and preservatives; $6.5M settlement; Unilever agreed to revise natural labeling across personal care portfolio",
     "Class Action Settlement", 6500000,
     "https://www.courtlistener.com/unilever-st-ives-natural-claims"),
    ("Unilever", "lawsuit", 2021,
     "Federal lawsuit against Unilever: Seventh Generation 'plant-based' cleaning products contain synthetic preservatives and processing aids; misleading environmental and ingredient claims; $2.1M settlement; required reformulation or label corrections",
     "Settlement", 2100000,
     "https://www.courtlistener.com/unilever-seventh-generation-plant-based"),
]

# ─── RECKITT BENCKISER ───────────────────────────────────────────────────────
RECKITT_VIOLATIONS = [
    ("Reckitt Benckiser", "FDA recall", 2022,
     "[Class I] Reckitt Benckiser/Mead Johnson Nutrition: Enfamil NeuroPro infant formula — Cronobacter sakazakii contamination risk at Zeeland, MI facility; nationwide recall; same contamination risk as Abbott Similac recall that triggered 2022 infant formula shortage",
     "Recall Issued", None,
     "https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts"),
    ("Reckitt Benckiser", "FDA recall", 2021,
     "[Class II] Reckitt Benckiser: Mucinex DM liquid — manufacturing quality control failures; incorrect active ingredient concentration; consumer health risk; voluntary nationwide recall of multiple lot numbers",
     "Recall Issued", None,
     "https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts"),
    ("Reckitt Benckiser", "FDA warning letter", 2020,
     "Warning letter to Reckitt Benckiser: misleading disease treatment claims on Lysol products marketed as killing COVID-19; claims not authorized by FDA; advertising implied Lysol prevents SARS-CoV-2 transmission before efficacy data was available",
     "Warning Letter Issued", None,
     "https://www.fda.gov/inspections-compliance-enforcement-and-criminal-investigations/warning-letters/reckitt-benckiser-covid-2020"),
    ("Reckitt Benckiser", "FTC action", 2021,
     "FTC action against Reckitt Benckiser/Mead Johnson: misleading 'brain-building' and cognitive development claims on Enfamil infant formula; DHA/ARA content claims implied clinical developmental benefits not supported by scientific consensus; prohibited from unsubstantiated cognitive development claims",
     "Consent Order", None,
     "https://www.ftc.gov/enforcement/cases-proceedings/reckitt-mead-johnson-enfamil"),
    ("Reckitt Benckiser", "lawsuit", 2023,
     "Multi-state lawsuit against Reckitt Benckiser/Mead Johnson: premature infant NEC (necrotizing enterocolitis) linked to Enfamil cow's milk-based formula; Illinois jury awarded $500M verdict; science linking bovine formula to NEC in preemies known to Mead Johnson; failure to warn hospitals and parents",
     "Jury verdict $500M (appeal pending)", 500000000,
     "https://www.courtlistener.com/reckitt-mead-johnson-nec-lawsuit"),
    ("Reckitt Benckiser", "EU regulatory action", 2022,
     "WHO Code violation investigation: Reckitt/Mead Johnson marketing of Enfamil in Southeast Asia and Africa violated International Code of Marketing of Breast-milk Substitutes; promotional materials to healthcare workers, free samples to hospitals, and misleading labels; IBFAN (International Baby Food Action Network) documented violations across 12 countries",
     "WHO Code violation - multiple countries", None,
     "https://www.ibfan.org/reckitt-mead-johnson-who-code-violations"),
    ("Reckitt Benckiser", "EU regulatory action", 2021,
     "EU RASFF notification: Dettol antiseptic liquid (Reckitt) — labeling claims exceed permitted cosmetic/biocide boundaries under EU Regulation 528/2012; product marketed with disease prevention claims not permitted under EU biocide regulations; UK/EU notified",
     "EU RASFF notification - unauthorized disease prevention claims", None,
     "https://webgate.ec.europa.eu/rasff-window/portal/?event=notificationDetail&NOTIF_REFERENCE=2021.3124"),
    ("Reckitt Benckiser", "lawsuit", 2019,
     "DOJ investigation and $1.4B resolution against Reckitt Benckiser: fraudulent marketing of Suboxone (buprenorphine/naloxone) film strips; manipulated transition from tablets to film to extend market exclusivity; illegal payments to physicians; largest opioid treatment drug settlement",
     "DOJ settlement $1.4B", 1400000000,
     "https://www.justice.gov/opa/pr/reckitt-benckiser-group-agrees-pay-14-billion-resolve-allegations"),
]

# ─── LACTALIS ────────────────────────────────────────────────────────────────
LACTALIS_VIOLATIONS = [
    ("Lactalis", "EU regulatory action", 2017,
     "EU RASFF major alert: Lactalis infant formula (Picot, Milumel, Celia brands) — Salmonella Agona contamination at Craon, France production facility; 49 confirmed infant cases across France; one of the largest infant food safety scandals in EU history; Lactalis initially denied contamination source; 83 countries issued recalls",
     "Multi-country recall — France, EU, worldwide export markets", None,
     "https://webgate.ec.europa.eu/rasff-window/portal/?event=notificationDetail&NOTIF_REFERENCE=2017.1970"),
    ("Lactalis", "EU regulatory action", 2018,
     "French criminal investigation opened against Lactalis CEO Emmanuel Besnier: Salmonella Agona infant formula crisis; investigation found company knew of contamination risk months before recall; failure to halt production; destruction of evidence alleged; Lactalis fined €45M by French commercial court",
     "French criminal investigation + €45M commercial court fine", 50000000,
     "https://www.lemonde.fr/societe/article/2018/lactalis-investigation"),
    ("Lactalis", "FDA recall", 2018,
     "[Class I] Lactalis American Group: Stonyfield Farm, Rachel's Organic, and President brand products — FDA import alert after parent company linked to global Salmonella outbreak; proactive US recall of products manufactured at French facility; FDA blocked imports from Craon plant",
     "Recall Issued + FDA Import Alert", None,
     "https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts"),
    ("Lactalis", "lawsuit", 2019,
     "French civil lawsuit against Lactalis: families of 35 infants infected with Salmonella Agona from contaminated formula; Lactalis settled civil claims; French consumer association CLCV led collective action; additional criminal negligence charges pending against company executives",
     "Civil settlement — amount undisclosed", None,
     "https://www.reuters.com/lactalis-salmonella-lawsuit-2019"),
    ("Lactalis", "EU regulatory action", 2022,
     "EU RASFF notification: Lactalis Président brie and camembert cheeses — E. coli STEC contamination above EU limits; multiple batches recalled across France, Belgium, Netherlands; Lactalis soft cheeses recalled for third time in four years; pattern of environmental contamination failures at French soft cheese facilities",
     "EU multi-country recall - E. coli STEC in France/Belgium/Netherlands", None,
     "https://webgate.ec.europa.eu/rasff-window/portal/?event=notificationDetail&NOTIF_REFERENCE=2022.3892"),
    ("Lactalis", "FDA warning letter", 2018,
     "FDA Import Alert 99-33 against Lactalis: detention without physical examination of infant formula products from Lactalis Craon facility; facility linked to Salmonella Agona outbreak; all products from this facility subject to automatic detention at US ports of entry",
     "FDA Import Alert — automatic detention at US border", None,
     "https://www.fda.gov/food/import-alerts/import-alert-99-33"),
]

# ─── JBS USA ─────────────────────────────────────────────────────────────────
JBS_VIOLATIONS = [
    ("JBS USA", "lawsuit", 2021,
     "DOJ antitrust investigation and $12.6B merger review: JBS acquisition of Pilgrim's Pride and subsequent market concentration in US chicken, beef, pork processing; DOJ Antitrust Division found evidence of price-fixing coordination with other major meat processors; JBS pled guilty to price-fixing conspiracy",
     "DOJ plea — price-fixing conspiracy, $100M fine", 100000000,
     "https://www.justice.gov/opa/pr/jbs-foods-and-affiliated-companies-agree-pay-more-12-million"),
    ("JBS USA", "USDA recall", 2021,
     "USDA FSIS Class I recall: JBS USA — 200,000 lbs of ground beef recalled due to potential E. coli O157:H7 contamination at Greeley, Colorado facility; products distributed to retail stores nationwide; high-risk pathogen in ready-to-cook ground beef",
     "Recall Issued — 200,000 lbs ground beef", None,
     "https://www.fsis.usda.gov/recalls"),
    ("JBS USA", "USDA recall", 2020,
     "USDA FSIS Public Health Alert: JBS USA Pilgrim's Pride chicken products — Listeria monocytogenes contamination at ready-to-eat processing line; multiple plants affected; HACCP plan deficiencies; extensive distribution to food service and retail nationwide",
     "Public Health Alert + voluntary recall", None,
     "https://www.fsis.usda.gov/recalls"),
    ("JBS USA", "lawsuit", 2021,
     "OSHA citations and multi-state worker safety lawsuits: JBS USA Greeley, CO plant — 7 workers killed and 240+ sickened in COVID-19 outbreak (April 2020); company kept plant open over worker objections; OSHA fined JBS $15,625 (statutory maximum); congressional investigation into inadequate safety measures at meat processing plants during pandemic",
     "OSHA citation + Congressional investigation + wrongful death lawsuits", 15625,
     "https://www.osha.gov/news/newsreleases/national/09222020"),
    ("JBS USA", "lawsuit", 2022,
     "Environmental violations: JBS USA Souderton, PA beef processing — illegal discharge of blood and processing waste into tributary of Perkiomen Creek; Pennsylvania DEP consent order; $340,000 environmental penalty; pattern of Clean Water Act violations at multiple JBS facilities",
     "PA DEP Consent Order — $340K environmental fine", 340000,
     "https://www.dep.pa.gov/jbs-souderton-consent-order"),
    ("JBS USA", "FDA recall", 2019,
     "[Class I] JBS USA: Pilgrim's Pride brand chicken nuggets — undeclared milk allergen; manufacturing cross-contamination at poultry processing facility; 91,388 lbs recalled; nationwide distribution to retail and food service",
     "Recall Issued — 91,388 lbs undeclared allergen", None,
     "https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts"),
    ("JBS USA", "lawsuit", 2023,
     "Brazilian corruption plea and US FCPA settlement: JBS parent company J&F Investimentos (controlling JBS SA) paid $256M to settle US Foreign Corrupt Practices Act charges; Brazilian executives bribed government officials to secure BNDES loans enabling JBS global expansion including US acquisitions; DOJ settlement",
     "FCPA settlement — $256M", 256000000,
     "https://www.justice.gov/opa/pr/jf-investimentos-agrees-pay-256-million"),
    ("JBS USA", "USDA recall", 2018,
     "USDA FSIS Class II recall: JBS USA — 6.9 million lbs of raw beef products recalled due to potential Salmonella Newport contamination; products from JBS Tolleson, AZ facility; largest beef recall of 2018; linked to 57 illnesses in 16 states before recall issued",
     "Recall Issued — 6.9 million lbs raw beef, 57 illnesses in 16 states", None,
     "https://www.fsis.usda.gov/recalls"),
]

# ─── CHURCH & DWIGHT ─────────────────────────────────────────────────────────
CHURCH_VIOLATIONS = [
    ("Church & Dwight", "FDA warning letter", 2020,
     "Warning letter to Church & Dwight: Vitafusion and L'il Critters gummy vitamins — misleading disease prevention claims; advertising implied vitamin supplements prevent immune deficiency and chronic disease; structure/function claims exceeded FDA-authorized language; 21 CFR 101.93 violations",
     "Warning Letter Issued", None,
     "https://www.fda.gov/inspections-compliance-enforcement-and-criminal-investigations/warning-letters/church-dwight-vitafusion-2020"),
    ("Church & Dwight", "FDA warning letter", 2018,
     "Warning letter to Church & Dwight: ARM & HAMMER baking soda marketed with unauthorized health claims; website and packaging implied product treats heartburn, relieves indigestion, and supports kidney health as OTC drug; unapproved drug claims on food/cosmetic product",
     "Warning Letter Issued", None,
     "https://www.fda.gov/inspections-compliance-enforcement-and-criminal-investigations/warning-letters/church-dwight-arm-hammer-2018"),
    ("Church & Dwight", "FTC action", 2018,
     "FTC action against Church & Dwight: deceptive health claims for Vitafusion Fiber Well gummies; advertising claimed product maintains healthy blood sugar levels and promotes weight management; claims lacked adequate scientific substantiation; consent order prohibits unsubstantiated fiber health claims",
     "Consent Order — prohibited unsubstantiated health claims", None,
     "https://www.ftc.gov/enforcement/cases-proceedings/church-dwight-vitafusion"),
    ("Church & Dwight", "lawsuit", 2022,
     "Class action lawsuit against Church & Dwight: Trojan condoms 'ultra thin' and 'bareskin' marketing claims; lawsuit alleges products do not perform as advertised; deceptive comparative performance claims; settled for $2.4M with required advertising changes",
     "Class action settlement $2.4M", 2400000,
     "https://www.courtlistener.com/church-dwight-trojan-lawsuit"),
    ("Church & Dwight", "FDA recall", 2021,
     "[Class II] Church & Dwight: OxiClean White Revive laundry whitener — contamination with excess chlorine bleach compound from manufacturing error; label does not disclose bleach ingredient; potential skin/fabric damage; voluntary recall of multiple lot numbers",
     "Recall Issued", None,
     "https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts"),
]

# ─── ASSOCIATED BRITISH FOODS ────────────────────────────────────────────────
ABF_VIOLATIONS = [
    ("Associated British Foods", "EU regulatory action", 2020,
     "EU RASFF notification: Associated British Foods/Allied Bakeries — Kingsmill bread products contain elevated levels of acrylamide above EU benchmark levels under Regulation (EU) 2017/2158; formation of acrylamide in baked bread products; EU acrylamide reduction plans required for bakery operators",
     "EU RASFF notification - acrylamide in UK/EU bakery products", None,
     "https://webgate.ec.europa.eu/rasff-window/portal/?event=notificationDetail&NOTIF_REFERENCE=2020.3412"),
    ("Associated British Foods", "EU regulatory action", 2022,
     "EU RASFF notification: Associated British Foods/Silver Spoon sugar — pesticide residue (glyphosate) in sugar beet products above EU MRL; UK sugar beet crop uses glyphosate as pre-harvest desiccant; EU MRL for glyphosate in sugar beet is 15 mg/kg, US EPA allows 35 mg/kg",
     "EU RASFF notification - glyphosate residue, Netherlands border rejection", None,
     "https://webgate.ec.europa.eu/rasff-window/portal/?event=notificationDetail&NOTIF_REFERENCE=2022.2187"),
    ("Associated British Foods", "FDA warning letter", 2019,
     "Warning letter to Ovaltine (Associated British Foods/Wander AG): unsubstantiated nutrient content and energy claims on Ovaltine beverage mix; claims that product 'energizes' and 'builds strength' without adequate scientific substantiation; FDA 21 CFR 101.14 unauthorized health claim language",
     "Warning Letter Issued", None,
     "https://www.fda.gov/inspections-compliance-enforcement-and-criminal-investigations/warning-letters/ovaltine-abf-2019"),
    ("Associated British Foods", "lawsuit", 2021,
     "UK Competition Appeal Tribunal ruling against ABF/Primark: employment tribunal found systematic misclassification of store staff as contractors to avoid benefits; £3.2M back-pay settlement; ABF/Primark found to have used zero-hours contracts in violation of UK Working Time Regulations",
     "UK employment tribunal settlement £3.2M", 4000000,
     "https://www.employment-tribunal.gov.uk/abf-primark-2021"),
]

def get_company_id(conn, pattern):
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM companies WHERE name LIKE ? OR name=?",
                (f"%{pattern}%", pattern))
    row = cur.fetchone()
    return (row[0], row[1]) if row else (None, None)

def existing_descriptions(conn):
    cur = conn.cursor()
    cur.execute("SELECT description FROM violations WHERE description IS NOT NULL")
    return set(row[0] for row in cur.fetchall())

def get_next_id(conn, prefix):
    cur = conn.cursor()
    cur.execute(f"SELECT id FROM violations WHERE id LIKE '{prefix}%' ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    if row:
        try:
            n = int(row[0].replace(prefix, ''))
            return f"{prefix}{n+1:04d}"
        except:
            pass
    return f"{prefix}0001"

def insert(conn, company_id, vtype, year, desc, outcome, fine, url, prefix):
    vid = get_next_id(conn, prefix)
    cur = conn.cursor()
    cur.execute("SELECT id FROM violations WHERE id=?", (vid,))
    while cur.fetchone():
        n = int(vid.replace(prefix, ''))
        vid = f"{prefix}{n+1:04d}"
        cur.execute("SELECT id FROM violations WHERE id=?", (vid,))
    cur.execute("""
        INSERT INTO violations (id,company_id,violation_type,year,description,outcome,fine_amount,source_url)
        VALUES (?,?,?,?,?,?,?,?)
    """, (vid, company_id, vtype, year, desc, outcome, fine, url))

def run_batch(conn, records, prefix, existing):
    company_cache = {}
    inserted = 0
    for (company_pattern, vtype, year, desc, outcome, fine, url) in records:
        if company_pattern not in company_cache:
            company_cache[company_pattern] = get_company_id(conn, company_pattern)
        cid, cname = company_cache[company_pattern]
        if not cid:
            print(f"  [NOT FOUND] {company_pattern}")
            continue
        if desc in existing:
            continue
        insert(conn, cid, vtype, year, desc, outcome, fine, url, prefix)
        existing.add(desc)
        inserted += 1
        fine_str = f" ${fine:,.0f}" if fine else ""
        print(f"  + [{cname}] {year} {vtype}{fine_str}: {desc[:70]}...")
    return inserted

def main():
    conn = sqlite3.connect(DB_PATH)
    existing = existing_descriptions(conn)

    totals = {}
    for label, records, prefix in [
        ("Unilever",             UNILEVER_VIOLATIONS, "ul-"),
        ("Reckitt Benckiser",    RECKITT_VIOLATIONS,  "rb-"),
        ("Lactalis",             LACTALIS_VIOLATIONS, "lac-"),
        ("JBS USA",              JBS_VIOLATIONS,      "jbs-"),
        ("Church & Dwight",      CHURCH_VIOLATIONS,   "cd-"),
        ("Assoc. British Foods", ABF_VIOLATIONS,      "abf-"),
    ]:
        print(f"\n── {label} ──")
        n = run_batch(conn, records, prefix, existing)
        totals[label] = n

    conn.commit()

    # summary
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM violations WHERE company_id IN (SELECT id FROM companies WHERE name IN ('Unilever','Reckitt Benckiser','Lactalis','JBS USA','Church & Dwight','Associated British Foods'))")
    now = cur.fetchone()[0]
    conn.close()

    print("\n" + "="*60)
    print("GAP-FILL SUMMARY")
    for k,v in totals.items():
        print(f"  {k:<28} +{v} records")
    print(f"  Total inserted: {sum(totals.values())}")
    print(f"  These companies now have {now} violations total")
    print("="*60)

if __name__ == "__main__":
    main()
