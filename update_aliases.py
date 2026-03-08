from traced_resolver import get_db, normalize

DB_PATH = "/Users/evan/Desktop/traceddatabase/traced.db"

NEW_ALIASES = [
    # Coffee
    ("blue bottle coffee",           "Blue Bottle Coffee"),
    ("blue bottle",                  "Blue Bottle Coffee"),
    ("peets coffee",                 "Peet's Coffee"),
    ("peets",                        "Peet's Coffee"),
    ("peets coffee tea",             "Peet's Coffee"),
    ("starbucks coffee",             "Starbucks"),
    ("starbucks reserve",            "Starbucks"),
    ("starbucks",                    "Starbucks"),
    ("philz coffee",                 "Philz Coffee"),
    ("philz",                        "Philz Coffee"),
    ("ritual coffee roasters",       "Ritual Coffee Roasters"),
    ("ritual coffee",                "Ritual Coffee Roasters"),
    ("sightglass coffee",            "Sightglass Coffee"),
    ("sightglass",                   "Sightglass Coffee"),

    # Grocery
    ("whole foods market",           "Whole Foods Market"),
    ("whole foods",                  "Whole Foods Market"),
    ("whole foods market inc",       "Whole Foods Market Inc."),
    ("safeway",                      "Safeway Inc."),
    ("safeway store",                "Safeway Inc."),
    ("safeway inc",                  "Safeway Inc."),
    ("trader joes",                  "Trader Joe's"),
    ("trader joes store",            "Trader Joe's"),
    ("trader giotto",                "Trader Giotto's"),
    ("sprouts farmers market",       "Sprouts Farmers Market"),
    ("sprouts",                      "Sprouts Farmers Market"),
    ("costco wholesale",             "Costco"),
    ("costco",                       "Costco"),
    ("kroger",                       "Kroger"),
    ("the kroger co",                "The Kroger Co."),
    ("walmart",                      "Walmart"),
    ("target",                       "Walmart"),  # remove if Target is separate
    ("aldi",                         "Aldi"),
    ("lidl",                         "Lidl"),
    ("heb",                          "H-E-B"),
    ("h e b",                        "H-E-B"),
    ("wegmans",                      "Wegmans"),
    ("publix",                       "Publix"),

    # Pharmacy / Health
    ("cvs pharmacy",                 "CVS"),
    ("cvs",                          "CVS"),
    ("walgreens pharmacy",           "Walgreens"),
    ("walgreens",                    "Walgreens"),

    # Restaurants / Fast food
    ("sweetgreen",                   "Sweetgreen"),
    ("shake shack",                  "Shake Shack"),
    ("chipotle mexican grill",       "Chipotle"),
    ("chipotle",                     "Chipotle"),
    ("mcdonalds",                    "McDonald's"),
    ("panera bread",                 "Panera Bread"),
    ("panera",                       "Panera Bread"),

    # Brands in your DB (CPG crossover for Maps)
    ("annie",                        "Annie's"),
    ("annies homegrown",             "Annie's Homegrown"),
    ("annies",                       "Annie's"),
    ("rxbar",                        "RXBAR"),
    ("clif bar",                     "Clif Bar"),
    ("clif",                         "Clif"),
    ("siete family foods",           "Siete Family Foods"),
    ("siete",                        "Siete"),
    ("oatly",                        "Oatly"),
    ("beyond meat",                  "Beyond Meat"),
    ("impossible",                   "Impossible"),
    ("ben jerrys",                   "Ben & Jerry's"),
    ("ben and jerrys",               "Ben & Jerry's"),
    ("haagen dazs",                  "Haagen Dazs"),
    ("salt straw",                   "Salt & Straw"),
    ("salt and straw",               "Salt & Straw"),
    ("stonyfield",                   "Stonyfield"),
    ("stonyfield organic",           "Stonyfield Organic"),
    ("chobani",                      "Chobani"),
    ("siggis",                       "siggi's"),
    ("siggi",                        "siggi's"),
    ("organic valley",               "Organic Valley"),
    ("tillamook",                    "Tillamook"),
    ("vital farms",                  "Vital Farms"),
    ("good culture",                 "Good Culture"),
    ("noosa",                        "noosa"),
    ("amy kitchen",                  "Amy's Kitchen Inc."),
    ("amys",                         "Amy's"),
    ("amys kitchen",                 "Amy's Kitchen Inc."),
    ("applegate",                    "Applegate"),
    ("applegate naturals",           "Applegate Naturals"),
    ("bob red mill",                 "Bob's Red Mill"),
    ("bobs red mill",                "Bob's Red Mill"),
    ("simple mills",                 "Simple Mills"),
    ("larabar",                      "Larabar"),
    ("rxbar",                        "RXBAR"),
    ("gomacro",                      "GoMacro"),
    ("kind bar",                     "KIND"),
    ("kind",                         "KIND"),
    ("clif bar",                     "Clif Bar"),
    ("lara bar",                     "Larabar"),
    ("health ade",                   "Health-Ade"),
    ("health-ade",                   "Health-Ade"),
    ("olipop",                       "OLIPOP"),
    ("poppi",                        "poppi"),
    ("liquid death",                 "Liquid Death"),
    ("spindrift",                    "spindrift"),
    ("la croix",                     "La Croix"),
    ("lacroix",                      "LaCroix"),
    ("zevia",                        "Zevia"),
    ("celsius",                      "CELSIUS"),
    ("red bull",                     "Red Bull"),
    ("ag1",                          "AG1"),
    ("athletic greens",              "AG1"),
    ("primal kitchen",               "Primal Kitchen"),
    ("chosen foods",                 "Chosen Foods"),
    ("bragg",                        "Bragg"),
    ("365",                          "365 Everyday Value"),
    ("365 everyday value",           "365 Everyday Value"),
    ("365 whole foods",              "365 Whole Foods Market"),
    ("o organics",                   "O Organics"),
    ("open nature",                  "Open Nature"),
    ("kirkland",                     "Kirkland Signature"),
    ("kirkland signature",           "Kirkland Signature"),
    ("great value",                  "Great Value"),
    ("good gather",                  "Good & Gather"),
    ("good and gather",              "Good & Gather"),
]

def update():
    conn = get_db(DB_PATH)
    c = conn.cursor()
    added = 0
    skipped = 0

    for alias_text, brand_name in NEW_ALIASES:
        c.execute("SELECT id FROM brands WHERE lower(name) = lower(?)", (brand_name,))
        row = c.fetchone()
        if not row:
            print(f"  SKIP (not in DB): {brand_name}")
            skipped += 1
            continue
        try:
            c.execute(
                "INSERT OR IGNORE INTO brand_aliases (alias_text, brand_id, source) VALUES (?, ?, 'seed2')",
                (alias_text, row["id"])
            )
            if c.rowcount > 0:
                added += 1
        except Exception as e:
            print(f"  ERROR: {e}")

    conn.commit()
    conn.close()
    print(f"\n✓ Added {added} new aliases, skipped {skipped} (not in DB)")

    # Show total alias count
    conn = get_db(DB_PATH)
    total = conn.execute("SELECT COUNT(*) FROM brand_aliases").fetchone()[0]
    conn.close()
    print(f"✓ Total aliases in DB: {total}")

if __name__ == "__main__":
    update()
