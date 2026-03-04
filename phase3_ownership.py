import sqlite3

DB = '/Users/evan/Desktop/Traceddatabase/traced.db'
conn = sqlite3.connect(DB)
c = conn.cursor()
conn.execute("PRAGMA journal_mode=WAL")

ownership_data = [
    ("3G Capital",           "pe_firm",            "3G Capital is a Brazilian-American private equity and hedge fund founded by Jorge Paulo Lemann, Marcel Telles, and Carlos Alberto Sicupira. It controls AB InBev, Restaurant Brands International (Burger King, Tim Hortons), and co-owned Kraft Heinz with Berkshire Hathaway. Known for zero-based budgeting and aggressive cost-cutting."),
    ("AbbVie",               "public_conglomerate", "AbbVie is a NYSE-listed biopharmaceutical company spun off from Abbott Laboratories in 2013. In consumer health, it is the parent of Allergan Aesthetics. Primarily a pharma company, it has limited food/supplement brand exposure."),
    ("Advent International", "pe_firm",             "Advent International is a global private equity firm with $88B+ AUM. It has owned Cobham, Aimia, and various consumer brands. In food/health, it held minority stakes in supplement companies."),
    ("Aldi",                 "private_conglomerate", "Aldi is a German discount supermarket chain split into two separate companies: Aldi Nord (owns Trader Joe's in the US) and Aldi Sud (operates Aldi US stores). Both are privately held by members of the Albrecht family. Combined, they are one of the world's largest grocery retailers."),
    ("Associated British Foods", "public_conglomerate", "Associated British Foods (ABF) is a London-listed diversified food, ingredients, and retail group. It owns Primark, Allied Bakeries, Twinings, Ovaltine, Ryvita, Kingsmill, and AB Sugar. Founded by the Weston family and still majority-family-controlled."),
    ("B&G Foods",            "public_conglomerate", "B&G Foods is a NYSE-listed food holding company that acquires 'heritage' and shelf-stable grocery brands. It owns Green Giant (US retail), Crisco, Clabber Girl, Ortega, Cream of Wheat, and dozens more."),
    ("Bain Capital",         "pe_firm",             "Bain Capital is a global private equity and alternative assets firm with $165B+ AUM, founded in 1984. In food/consumer, it has owned Dunkin' Brands, Bombardier Recreational Products, and held various consumer goods companies."),
    ("Barilla",              "private_conglomerate", "Barilla Group is an Italian privately held food company and the world's largest pasta manufacturer. It also owns Mulino Bianco, Harry's bread, Harrys America, Wasa crispbread, and Filiz pasta. Revenue ~$4.5B. Still controlled by the Barilla family."),
    ("Blackstone",           "pe_firm",             "Blackstone is the world's largest alternative asset manager with $1T+ AUM. In food/consumer, it has owned Bumble Bee Foods, Refresco (beverage co-packer), and various food service companies. Notorious for aggressive leverage strategies."),
    ("Campbell's",           "public_conglomerate", "Campbell Soup Company is a NYSE-listed food manufacturer. It owns Campbell's soups, Pepperidge Farm, Goldfish, Snyder's-Lance, Lance, Cape Cod, Kettle Brand, Pacific Foods, and Plum Organics. Revenue ~$9.4B."),
    ("Church & Dwight",      "public_conglomerate", "Church & Dwight is a NYSE-listed consumer packaged goods company. Beyond Arm & Hammer baking soda, it owns Vitafusion gummies, L'il Critters children's vitamins, Floss, Nair, and OxiClean. A major stealth supplement player."),
    ("Coca-Cola",            "public_conglomerate", "The Coca-Cola Company is a NYSE-listed global beverage giant with $46B+ revenue. It owns 500+ brands including Sprite, Fanta, Dasani, Smartwater, Powerade, Minute Maid, Simply, Fairlife, and acquired Honest Tea (later discontinued). Spent $121M+ lobbying against sugar taxes."),
    ("Conagra Brands",       "public_conglomerate", "Conagra Brands is a NYSE-listed packaged food company. It owns Birds Eye, Duncan Hines, Healthy Choice, Marie Callender's, Slim Jim, Vlasic, Hunt's, Orville Redenbacher's, Angie's BOOMCHICKAPOP, and Gardein plant-based foods. Revenue ~$12B."),
    ("Danone",               "public_conglomerate", "Danone is a Paris-listed multinational food company with $30B+ revenue. It owns Dannon/Danone yogurt, Evian, Volvic, Badoit, Activia, Actimel, Silk plant-based, So Delicious, Happy Family, and Horizon Organic. Has B Corp certification at company level despite lobbying activities."),
    ("Dean Foods",           "public_conglomerate", "Dean Foods was a publicly traded US dairy company that filed for bankruptcy in 2019 and was acquired by Dairy Farmers of America in 2020. At its peak it was the largest US dairy processor, owning Land O'Lakes fluid dairy, TruMoo, and 50+ regional dairy brands."),
    ("Ferrero",              "private_conglomerate", "Ferrero Group is an Italian privately held confectionery company founded by Pietro Ferrero. It owns Nutella, Ferrero Rocher, Kinder, Tic Tac, and acquired Nestle's US confectionery business (Butterfingers, Crunch, BabyRuth) and Fannie May. Revenue ~$17B. Still family-controlled."),
    ("Flowers Foods",        "public_conglomerate", "Flowers Foods is a NYSE-listed baked goods company. It owns Wonder Bread, Nature's Own, Dave's Killer Bread, Tastykake, and Canyon Bakehouse. Revenue ~$4.8B."),
    ("General Mills",        "public_conglomerate", "General Mills is a NYSE-listed food company with $20B+ revenue. It owns Cheerios, Wheaties, Yoplait, Haagen-Dazs, Betty Crocker, Pillsbury, Annie's, Cascadian Farm, Muir Glen, and Nature Valley. Spent $52M+ lobbying against GMO labeling."),
    ("Goya Foods",           "private_conglomerate", "Goya Foods is the largest Hispanic-owned food company in the US, privately held by the Unanue family. Founded 1936. It sells 2,500+ products across Latin American, Caribbean, and Spanish cuisines. Revenue ~$1.8B."),
    ("Gruma",                "public_conglomerate", "Gruma SAB de CV is a Mexican publicly listed food company (BMV: GRUMAB) and the world's largest tortilla manufacturer. It owns Mission Foods, MASECA masa flour, and Guerrero. Revenue ~$4B. Controlled by the Gonzalez family."),
    ("HEB",                  "private_conglomerate", "H-E-B (H.E. Butt Grocery Company) is a privately held Texas supermarket chain founded in 1905. It is one of the largest private companies in the US with ~$43B revenue. Known for its Central Market upscale banner and strong regional brand loyalty."),
    ("Hain Celestial",       "public_conglomerate", "Hain Celestial Group is a Nasdaq-listed natural and organic products company. It owns Earth's Best, Garden of Eatin', Celestial Seasonings, Arrowhead Mills, Terra Chips, and dozens of other 'natural' brands. Revenue ~$1.7B."),
    ("Hershey Company",      "public_conglomerate", "The Hershey Company is a NYSE-listed confectionery and snack company with $11B+ revenue. It owns Reese's, Kit Kat (US), SkinnyPop, Pirate's Booty, One Bars protein bars, Dot's Pretzels, and Amplify Snack Brands. ~80% voting control held by Hershey Trust."),
    ("Hormel Foods",         "public_conglomerate", "Hormel Foods is a NYSE-listed food company with $12B+ revenue. It owns Spam, Skippy, Applegate Farms, Justin's, Wholly Guacamole, Natural Choice, and Jennie-O. One of the more acquisitive mid-tier food conglomerates."),
    ("J.M. Smucker",         "public_conglomerate", "The J.M. Smucker Company is a NYSE-listed food holding company. It owns Smucker's jams, Jif peanut butter, Folgers coffee, Dunkin' packaged coffee, Meow Mix, Milk-Bone, and acquired Hostess Brands in 2023. Revenue ~$9B."),
    ("JBS USA",              "public_conglomerate", "JBS USA is the US subsidiary of JBS S.A. (Brazil), the world's largest meat processing company. It owns Pilgrim's Pride, Swift, Certified Angus Beef license, and Planters (acquired from Hormel). JBS S.A. paid $3.2B in corruption settlements (Brazil's Lava Jato scandal) in 2017."),
    ("Johnson & Johnson",    "public_conglomerate", "Johnson & Johnson is a NYSE-listed diversified healthcare conglomerate. In consumer health (now spun off as Kenvue in 2023), it owned Neutrogena, Tylenol, Listerine, Band-Aid, and Aveeno. The consumer segment had $15B+ revenue pre-spinoff."),
    ("KKR",                  "pe_firm",             "KKR & Co. is one of the world's largest private equity firms with $500B+ AUM. In food/consumer, it has owned Panera Bread, US Foods, Del Monte Foods, and held various food and supplement brands. KKR typically holds portfolio companies 5-7 years before exit."),
    ("Kellogg's",            "public_conglomerate", "Kellogg Company (rebranded as Kellanova after 2023 WK Kellogg split) is a NYSE-listed food company. It owns Pringles, Cheez-It, Pop-Tarts, Eggo, MorningStar Farms, Kashi, Bear Naked, and RXBar. Mars Inc. acquired Kellanova in 2024 for $36B. Spent $81M+ lobbying against GMO labeling."),
    ("Kraft Heinz",          "public_conglomerate", "Kraft Heinz Company is a Nasdaq-listed food giant with $26B+ revenue, formed by 3G Capital and Berkshire Hathaway's 2015 merger of Kraft Foods and H.J. Heinz. It owns Kraft, Heinz, Oscar Mayer, Jell-O, Velveeta, Philadelphia, and Primal Kitchen. Known for extreme cost-cutting post-merger."),
    ("Kroger",               "public_conglomerate", "The Kroger Co. is a NYSE-listed supermarket chain and the largest US grocery retailer by revenue (~$150B). It owns Simple Truth, Private Selection, and many store-brand supplements and foods. Operates under King Soopers, Ralphs, Fred Meyer, Harris Teeter, and other banners."),
    ("Lactalis",             "private_conglomerate", "Lactalis Group is a French privately held dairy company and the world's largest dairy company by revenue (~$28B). It owns President, Galbani, Siggi's, Stonyfield Farm (partially), Parmalat, and Sargento (distribution). Controlled by the Besnier family."),
    ("Mars Inc.",            "private_conglomerate", "Mars Inc. is a privately held American multinational with $47B+ revenue, owned by the Mars family. It owns M&Ms, Snickers, Dove, Twix, Orbit gum, Pedigree, Whiskas, Kind bars (acquired 2021), Wrigley, and acquired Kellanova (Pringles, Cheez-It) in 2024 for $36B. One of the largest food companies in the world."),
    ("Mizkan",               "private_conglomerate", "Mizkan Group is a Japanese privately held food company founded in 1804. In the US, it owns Ragu pasta sauce, Bertolli pasta sauce, and various vinegar/condiment brands after acquiring them from Unilever. Revenue ~$2B."),
    ("Mondelēz",             "public_conglomerate", "Mondelēz International is a Nasdaq-listed snacking giant spun off from Kraft Foods in 2012. It owns Oreo, Chips Ahoy!, Ritz, Triscuit, Wheat Thins, Cadbury, Toblerone, Milka, Sour Patch Kids, Swedish Fish, and belVita. Revenue ~$36B."),
    ("Nestlé",               "public_conglomerate", "Nestlé S.A. is a Swiss publicly listed company and the world's largest food company by revenue (~$95B). It owns Nespresso, Nescafé, KitKat (global ex-US), Milo, Nesquik, Stouffer's, Lean Cuisine, Gerber, Carnation, Purina, Vittel, Perrier, and Garden Gourmet plant-based. Faces ongoing criticism for water extraction practices and infant formula marketing."),
    ("Orgain",               "private_conglomerate", "Orgain is a privately held organic nutrition brand founded by Dr. Andrew Abraham in 2009. It makes organic protein shakes, powders, and bars. Nestlé took a significant minority stake in 2021, valuing the company at ~$2B. Revenue ~$500M."),
    ("PepsiCo",              "public_conglomerate", "PepsiCo is a Nasdaq-listed beverage and food conglomerate with $91B+ revenue. It owns Pepsi, Frito-Lay (Lay's, Doritos, Cheetos), Quaker Oats, Gatorade, Tropicana (divested 2021), Naked Juice, Aquafina, Bubly, and SodaStream. Spent $103M+ lobbying against sugar taxes and food labeling."),
    ("Perdue Farms",         "private_conglomerate", "Perdue Farms is a privately held American poultry company founded in 1920. It is the 4th largest US poultry producer. It owns Perdue chicken, Niman Ranch (premium natural meats), Coleman Natural, and Draper Valley Farms."),
    ("Post Holdings",        "public_conglomerate", "Post Holdings is a NYSE-listed consumer packaged goods holding company. It owns Post cereals, Bob Evans, Michael Foods, Attune Foods, and spun off BellRing Brands (Premier Protein, Dymatize) in 2019. Revenue ~$6B."),
    ("Procter & Gamble",     "public_conglomerate", "Procter & Gamble is a NYSE-listed consumer goods giant with $82B+ revenue. While primarily a household/personal care company (Tide, Pampers, Gillette), it exited most food categories decades ago. It retains Metamucil and Pepto-Bismol in health/wellness."),
    ("Publix",               "private_conglomerate", "Publix Super Markets is a Florida-based employee-owned supermarket chain and the largest employee-owned company in the US. Revenue ~$55B. It operates its own GreenWise organic store brand and various private label supplements."),
    ("Reckitt Benckiser",    "public_conglomerate", "Reckitt plc (formerly Reckitt Benckiser) is a UK-listed consumer health and hygiene company with £14B+ revenue. In nutrition, it owns Mead Johnson (Enfamil infant formula), and in health it owns Mucinex, Airborne, Digestive Advantage, and Durex. The Enfamil division faced congressional scrutiny over NEC lawsuits in 2024."),
    ("Schwarz Group",        "private_conglomerate", "Schwarz Group is a German privately held retail conglomerate and Europe's largest retailer by revenue (~€155B). It owns Lidl discount supermarkets and Kaufland hypermarkets, which sell store-brand food and supplement products in Europe and increasingly in the US."),
    ("Siete Family Foods",   "private_conglomerate", "Siete Family Foods is a Texas-based privately held food company founded by the Garza family in 2014. It makes grain-free Mexican-American foods (tortillas, chips, salsas, seasonings). Acquired by PepsiCo in 2024 for $1.2B."),
    ("Simple Mills",         "private_conglomerate", "Simple Mills is a Chicago-based food company founded in 2012 making almond flour-based crackers, cookies, and baking mixes. It has PE backing from Permira (took minority stake in 2021). Revenue ~$200M+."),
    ("Smithfield Foods",     "public_conglomerate", "Smithfield Foods is the world's largest pork processor and hog producer, headquartered in Virginia. It was acquired by Hong Kong-listed WH Group (formerly Shuanghui International) in 2013 for $7.1B — the largest Chinese acquisition of a US company at the time. It owns Eckrich, Nathan's Famous (license), Farmland, and Armor."),
    ("Sprouts Farmers Market","public_conglomerate","Sprouts Farmers Market is a Nasdaq-listed specialty grocery chain focused on natural and organic products. Revenue ~$7B. It sells its own Sprouts brand private label products including vitamins and supplements."),
    ("Strand Equity",        "pe_firm",             "Strand Equity is a consumer-focused private equity firm that invested in brands like Oat Haus and Waterloo Sparkling Water. A smaller PE player focused on emerging natural/better-for-you consumer brands."),
    ("TPG Capital",          "pe_firm",             "TPG Capital is a major global PE firm with $224B+ AUM that has owned Schiff Nutrition, Safeway, and various food/supplement brands. Known for aggressive cost-cutting post-acquisition."),
    ("TreeHouse Foods",      "public_conglomerate", "TreeHouse Foods is a NYSE-listed private label food and beverage manufacturer. It makes store-brand products for retailers under their own labels, including cereals, soups, sauces, and beverages. Revenue ~$3.5B."),
    ("Tyson Foods",          "public_conglomerate", "Tyson Foods is a NYSE-listed food company and the world's second-largest processor and marketer of chicken, beef, and pork. Revenue ~$53B. It owns Jimmy Dean, Ball Park, Hillshire Farm, State Fair, and Aidells. Has faced repeated Chesapeake Bay and Clean Water Act violations."),
    ("Unilever",             "public_conglomerate", "Unilever plc is a UK-listed consumer goods company with €60B+ revenue. In food/nutrition, it owns Hellmann's, Ben & Jerry's, Breyers, Talenti, Magnum, Knorr, and Maille. It sold Skippy to Hormel and divested various brands. Has B Corp targets but faces greenwashing criticism."),
    ("Walmart",              "public_conglomerate", "Walmart Inc. is a NYSE-listed retail conglomerate and the world's largest company by revenue ($650B+). Its Sam's Choice and Great Value store brands cover thousands of food products. The world's largest food retailer by volume, with enormous supplier leverage."),
    ("Wegmans",              "private_conglomerate", "Wegmans Food Markets is a privately held, family-owned US supermarket chain headquartered in Rochester, NY. Founded 1916. Revenue ~$12B. Known for its Wegmans store brand, high quality standards, and employee culture. Regularly ranked among best employers in America."),
    ("Whole Foods (Amazon)", "public_conglomerate", "Whole Foods Market was a publicly traded natural/organic supermarket chain acquired by Amazon in 2017 for $13.7B. It now operates as an Amazon subsidiary, selling 365 by Whole Foods Market private label products. The acquisition marked a major shift in how the natural food industry is perceived."),
]

updated = 0
skipped = 0
for name, otype, desc in ownership_data:
    result = c.execute(
        "UPDATE companies SET ownership_type=?, description=? WHERE name=? AND (ownership_type IS NULL OR ownership_type='')",
        (otype, desc, name)
    )
    if result.rowcount > 0:
        updated += result.rowcount
        print(f"  Updated: {name} -> {otype}")
    else:
        skipped += 1
        # Check if it exists with data already
        row = c.execute("SELECT name, ownership_type FROM companies WHERE name=?", (name,)).fetchone()
        if row:
            print(f"  SKIP (already set): {name} = {row[1]}")
        else:
            print(f"  NOT FOUND: {name}")

conn.commit()
print(f"\nPhase 3 COMPLETE — Updated: {updated}, Skipped: {skipped}")

# Verify
null_count = c.execute("SELECT COUNT(*) FROM companies WHERE ownership_type IS NULL OR ownership_type=''").fetchone()[0]
print(f"Companies still missing ownership_type: {null_count}")
conn.close()
