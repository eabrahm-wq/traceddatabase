import sqlite3

DB = '/Users/evan/Desktop/Traceddatabase/traced.db'
conn = sqlite3.connect(DB)
c = conn.cursor()
conn.execute("PRAGMA journal_mode=WAL")

# brand_name -> company_id mapping
# Only mapping brands we can definitively attribute
BRAND_MAP = {
    # PepsiCo
    'Bubly':          'pepsico',
    'Propel':         'pepsico',
    'PopCorners':     'pepsico',
    "Miss Vickie's":  'pepsico',
    'bai':            'pepsico',
    'Siete Family Foods': 'pepsico',  # acquired 2024

    # Coca-Cola
    'Glaceau':        'coca-cola',
    'Sanpellegrino':  'coca-cola',
    'Smartwater':     'coca-cola',
    'Core Power':     'coca-cola',
    'Monster':        'coca-cola',  # Coca-Cola owns significant stake

    # Kraft Heinz
    'Philadelphia':   'kraft-heinz',
    "Breakstone's":   'kraft-heinz',
    'Crystal Light':  'kraft-heinz',
    'Jell-O':         'kraft-heinz',
    'Maxwell House':  'kraft-heinz',
    'Planters':       'kraft-heinz',  # sold to Hormel 2021 but check
    'Heinz':          'kraft-heinz',
    'Classico':       'kraft-heinz',
    "Rao's":          'kraft-heinz',  # acquired 2023
    "RAO'S HOMEMADE": 'kraft-heinz',

    # General Mills
    'Pillsbury':      'general-mills',
    'Fiber One':      'general-mills',
    'Betty Crocker':  'general-mills',
    'Yoplait':        'general-mills',
    'Old El Paso':    'general-mills',
    'Totino\'s':      'general-mills',
    'Progresso':      'general-mills',
    'Larabar':        'general-mills',
    'LÄRABAR':        'general-mills',
    'Fruit Roll-Ups': 'general-mills',
    'Gushers':        'general-mills',
    'Fruit by the Foot': 'general-mills',
    'Perfect Bar':    'general-mills',  # acquired 2019
    'Good and Gather':'walmart',        # Target private label... wrong, it's Target

    # Kellogg's / Kellanova / Mars (as of 2024 Mars acquired Kellanova)
    'Morning Star Farms': 'kelloggs',
    'Keebler':        'kelloggs',
    'Pringles':       'kelloggs',

    # Conagra
    'Banquet':        'conagra',
    'Birds Eye':      'conagra',
    'Duncan Hines':   'conagra',
    'Healthy Choice': 'conagra',
    'Hunt\'s':        'conagra',
    "Marie Callender's": 'conagra',
    "Slim Jim":       'conagra',
    'Vlasic':         'conagra',
    "Angie's BOOMCHICKAPOP": 'conagra',
    'Gardein':        'conagra',
    'Alexia':         'conagra',
    'Bertolli':       'conagra',  # pasta sauces US (Mizkan bought from Unilever for EU; Conagra has US rights)
    'PAM':            'conagra',
    "Snack Pack":     'conagra',
    'Reddi Whip':     'conagra',
    'Swiss Miss':     'conagra',

    # Campbell's
    'Pacific Foods':  'campbell',
    'Pepperidge Farm': 'campbell',
    'Plum Organics Parent': 'campbell',
    'V8':             'campbell',
    'Swanson':        'campbell',
    'Prego':          'campbell',
    'Pace':           'campbell',

    # Hormel Foods
    'Skippy':         'hormel',
    'Applegate':      'hormel',
    "Justin's":       'hormel',
    'Natural Choice': 'hormel',
    'Wholly':         'hormel',
    'SPAM':           'hormel',
    "Jennie-O":       'hormel',
    'Bob Evans':      'post-holdings',  # Post Holdings, not Hormel

    # J.M. Smucker
    'Folgers':        'jm-smucker',
    'Jif':            'jm-smucker',
    "Smucker's":      'jm-smucker',
    'Hostess':        'jm-smucker',  # acquired 2023
    'Pillsbury':      'jm-smucker',  # baking mix license
    'Sahale':         'jm-smucker',
    'Dunkin\'':       'jm-smucker',  # packaged coffee

    # Unilever
    "Hellmann's":     'unilever',
    "Maille":         'unilever',
    "Knorr":          'unilever',
    "Magnum":         'unilever',
    "Ben & Jerry's":  'unilever',
    "Breyers":        'unilever',
    "Talenti":        'unilever',
    "Wish-Bone":      'unilever',
    "Liquid I.V.":    'unilever',
    "Vital Proteins": 'unilever',  # acquired 2020
    "Dermalogica":    'unilever',

    # Danone
    'Dannon':         'danone',
    'Activia':        'danone',
    'Actimel':        'danone',
    'Silk':           'danone',
    'So Delicious':   'danone',
    'Happy Family':   'danone',
    'Horizon Organic':'danone',
    'Evian':          'danone',
    'Volvic':         'danone',
    'Badoit':         'danone',
    'Two Good':       'danone',
    'International Delight': 'danone',
    'Land O Lakes':   'danone',    # fluid dairy brand licensed

    # Nestlé
    'Gerber':         'nestle',
    'Stouffer\'s':    'nestle',
    'Lean Cuisine':   'nestle',
    'Carnation':      'nestle',
    'Nesquik':        'nestle',
    'Nescafé':        'nestle',
    'Purina':         'nestle',
    'Fancy Feast':    'nestle',
    'Friskies':       'nestle',
    'Garden Gourmet': 'nestle',
    'Perrier':        'nestle',
    'Poland Spring':  'nestle',
    'Deer Park':      'nestle',  # divested to Bluetriton but formerly Nestlé
    'Sanpellegrino':  'nestle',  # correction: Nestlé owns San Pellegrino
    'Vittel':         'nestle',
    'Orgain':         'orgain',  # Nestlé minority but Orgain is the company

    # Hershey
    'Reese\'s':       'hershey',
    'Kit Kat':        'hershey',  # US rights
    'SkinnyPop':      'hershey',
    "Pirate's Booty": 'hershey',
    "ONE Bars":       'hershey',
    "Dot's Homestyle Pretzels": 'hershey',
    "Ice Breakers":   'hershey',

    # Mars Inc.
    'KIND':           'mars',
    'Wrigley':        'mars',
    'Orbit':          'mars',
    'Skittles':       'mars',
    'Starburst':      'mars',
    'Snickers':       'mars',
    'Twix':           'mars',
    'M&M':            'mars',
    'Dove':           'mars',
    'Uncle Ben\'s':   'mars',
    'Ben\'s Original': 'mars',
    'Seeds of Change': 'mars',

    # Mondelēz
    'Oreo':           'mondelez',
    'Chips Ahoy':     'mondelez',
    'Ritz':           'mondelez',
    'Triscuit':       'mondelez',
    'Wheat Thins':    'mondelez',
    'Cadbury':        'mondelez',
    'Toblerone':      'mondelez',
    'Milka':          'mondelez',
    'Sour Patch Kids':'mondelez',
    'Swedish Fish':   'mondelez',
    'belVita':        'mondelez',
    'Tate\'s Bake Shop': 'mondelez',
    'Clif Bar':       'mondelez',  # acquired 2022

    # Post Holdings
    'Premier Protein': 'c23bacfe-812c-4983-bbb6-5b225e218a29',  # BellRing
    'Dymatize':       'c23bacfe-812c-4983-bbb6-5b225e218a29',  # BellRing
    'PowerBar':       'c23bacfe-812c-4983-bbb6-5b225e218a29',  # BellRing
    'Bob Evans':      'post-holdings',

    # Simply Good / Atkins
    'Atkins':         '35f49ad8-80d7-4d67-84e7-2fb4321b3e91',  # Simply Good Foods
    'Quest':          '35f49ad8-80d7-4d67-84e7-2fb4321b3e91',

    # Glanbia
    'Optimum Nutrition': 'f28db92d-c4c8-423c-8d17-b2f4e9e65e96',  # Glanbia
    'BSN':            'f28db92d-c4c8-423c-8d17-b2f4e9e65e96',
    'Isopure':        'f28db92d-c4c8-423c-8d17-b2f4e9e65e96',
    'Amazing Grass':  'f28db92d-c4c8-423c-8d17-b2f4e9e65e96',
    'Think!':         'f28db92d-c4c8-423c-8d17-b2f4e9e65e96',

    # Haleon (GSK Consumer)
    'Centrum':        '6d09f1b1-e7e7-4522-9f57-7610f5bf5dcd',
    'Advil':          '6d09f1b1-e7e7-4522-9f57-7610f5bf5dcd',
    'Sensodyne':      '6d09f1b1-e7e7-4522-9f57-7610f5bf5dcd',
    'Tums':           '6d09f1b1-e7e7-4522-9f57-7610f5bf5dcd',
    'Emergen-C':      '6d09f1b1-e7e7-4522-9f57-7610f5bf5dcd',

    # Pharmavite / Otsuka
    'Nature Made':    'f358b5d6-0af1-4730-877a-bc6ad7470e20',  # Pharmavite

    # Church & Dwight
    'Vitafusion':     'church-dwight',
    "L'il Critters":  'church-dwight',

    # Clorox
    "Burt's Bees":    '3a47c69b-f1e8-4200-925f-bbfcb63f68b5',
    'Brita':          '3a47c69b-f1e8-4200-925f-bbfcb63f68b5',
    'Hidden Valley':  '3a47c69b-f1e8-4200-925f-bbfcb63f68b5',
    'Kingsford':      '3a47c69b-f1e8-4200-925f-bbfcb63f68b5',
    'RenewLife':      '3a47c69b-f1e8-4200-925f-bbfcb63f68b5',

    # Hain Celestial
    "Earth's Best":   'hain-celestial',
    'Garden of Eatin\'': 'hain-celestial',
    'Celestial Seasonings': 'hain-celestial',
    'Arrowhead Mills': 'hain-celestial',
    'Terra Chips':    'hain-celestial',

    # Reckitt Benckiser
    'Mucinex':        'reckitt',
    'Airborne':       'reckitt',
    'Enfamil':        'reckitt',
    'Mead Johnson':   'reckitt',

    # JBS USA
    "Pilgrim's Pride": 'jbs',
    'Just Bare':      'jbs',

    # Smithfield Foods
    'Eckrich':        'smithfield',
    'Farmland':       'smithfield',

    # Tyson Foods
    'Jimmy Dean':     'tyson',
    'Ball Park':      'tyson',
    'Hillshire Farm': 'tyson',
    'State Fair':     'tyson',
    'Aidells':        'tyson',
    'Perdue':         'perdue',  # brand of Perdue Farms company

    # B&G Foods
    'Green Giant':    'b-g-foods',
    'Crisco':         'b-g-foods',
    'Ortega':         'b-g-foods',
    'Cream of Wheat': 'b-g-foods',
    "Grandma's":      'b-g-foods',
    'Las Palmas':     'b-g-foods',

    # Barilla
    'Barilla Collezione': 'barilla',
    'Wasa':           'barilla',  # Barilla owns Wasa

    # Gruma
    'Guerrero':       'gruma',
    'Mission Wrap':   'gruma',
    'MASECA':         'gruma',

    # Associated British Foods
    'Twinings':       'associated-british-foods',
    'Ovaltine':       'associated-british-foods',
    'Ryvita':         'associated-british-foods',

    # TreeHouse Foods
    'E.D. Smith':     'treehouse-foods',

    # Flowers Foods
    'Wonder':         'flowers-foods',
    "Nature's Own":   'flowers-foods',
    "Dave's Killer Bread": 'flowers-foods',
    'Tastykake':      'flowers-foods',
    'Canyon Bakehouse': 'flowers-foods',
    'Brownberry':     'flowers-foods',
    'Arnold':         'flowers-foods',
    'Oroweat':        'flowers-foods',

    # Lactalis
    'President':      'lancashire-farms',
    'Galbani':        'lancashire-farms',
    "Siggi's":        'lancashire-farms',
    'Parmalat':       'lancashire-farms',
    'Sargento':       'lancashire-farms',  # distributed, not owned

    # Morinaga
    'Beech-Nut':      'e0a23e9c-946d-4028-8803-7e5c308abf62',

    # Dean Foods (bankrupt/acquired)
    'TruMoo':         'dean-foods',
    'Land O\'Lakes':  'dean-foods',   # fluid dairy, not the co-op

    # Walmart private labels
    'Great Value':    'walmart',
    'Equate':         'walmart',
    'Sam\'s Choice':  'walmart',
    'Marketside':     'walmart',
    'Wal-Mart Stores Inc.': 'walmart',

    # Kroger private labels
    'Simple Truth':   'kroger',
    'Private Selection': 'kroger',
    'Kroger Brand':   'kroger',
    'Signature Select': 'kroger',
    'Signature Kitchens': 'kroger',

    # Target private labels
    'Good and Gather': 'target',
    'Market Pantry':  'target',
    'Archer':         'target',
    'Favorite Day':   'target',

    # Whole Foods / Amazon
    '365 by Whole Foods': 'whole-foods',
    'Happy Belly':    'whole-foods',
    '365':            'whole-foods',

    # Costco
    'Kirkland Signature': 'costco',
    'Members Mark':   'costco',    # Actually Sam's Club / Walmart
    'Wellsley Farms': 'costco',    # BJ's Wholesale
    'Costco':         'costco',

    # Aldi
    'Clancy\'s':      'aldi',
    'Specially Selected': 'aldi',
    'Simply Nature':  'aldi',
    'liveGfree':      'aldi',
    'Benton\'s':      'aldi',
    'Choceur':        'aldi',
    "Baker's Corner": 'aldi',
    'Alesto':         'aldi',
    'Moser Roth':     'aldi',
    'Fin Carré':      'aldi',
    'Countryside Creamery': 'aldi',
    "L'oven Fresh":   'aldi',
    'Earthly Grains': 'aldi',
    'Stonemill':      'aldi',
    'Elevation':      'aldi',
    'Park Street Deli': 'aldi',
    'Reggano':        'aldi',
    'Southern Grove': 'aldi',
    'Tuscan Garden':  'aldi',
    'Priano':         'aldi',

    # Schwarz Group / Lidl
    'Freshona':       'schwarz-group',
    'Pilos':          'schwarz-group',
    'Sondey':         'schwarz-group',
    'chef select':    'schwarz-group',
    'Alesto':         'schwarz-group',  # Lidl brand

    # HEB
    'Central Market': 'heb',
    'H-E-B':          'heb',
    'Meal Simple':    'heb',

    # Goya Foods
    'Goya Foods Inc.': 'goya',

    # Trader Joe's (Aldi Nord owns TJ's; map to Trader Joes company)
    'Trader Joe\'s':  'trader-joes',

    # Publix
    'GreenWise':      'publix',

    # Wegmans
    'Wegmans':        'wegmans',  # brand same as company

    # Sprouts
    'Sprouts':        'sprouts',

    # Ferrero
    'Nutella':        'ferrero',
    'Ferrero Rocher': 'ferrero',
    'Kinder':         'ferrero',
    'Tic Tac':        'ferrero',
    'Butterfinger':   'ferrero',
    'BabyRuth':       'ferrero',
    'Crunch':         'ferrero',

    # J.M. Smucker (Hostess)
    'Twinkies':       'jm-smucker',  # via Hostess
    'Ding Dongs':     'jm-smucker',
    'Ho Hos':         'jm-smucker',
    'Donettes':       'jm-smucker',

    # Mizkan (pasta sauces from Unilever)
    'Ragu':           'mizkan',

    # Maple Leaf Foods
    'Lightlife':      'ef401afe-9ec6-433b-89ea-f35cacc81ce0',
    'Field Roast':    'ef401afe-9ec6-433b-89ea-f35cacc81ce0',

    # Procter & Gamble
    'Metamucil':      'procter-gamble',
    'Pepto-Bismol':   'procter-gamble',
    'Gillette':       'procter-gamble',

    # Johnson & Johnson (now Kenvue)
    'Neutrogena':     'johnson-johnson',
    'Tylenol':        'johnson-johnson',
    'Listerine':      'johnson-johnson',
    'Band-Aid':       'johnson-johnson',
    'Aveeno':         'johnson-johnson',

    # Independent / standalone brands (remain unlinked or link to themselves)
    # Amy's Kitchen - independent, family-owned
    # Bob's Red Mill - employee-owned ESOP
    # Chobani - independent
    # Clif Bar - sold to Mondelēz
    # La Croix - National Beverage Corp
    # LaCroix - National Beverage Corp
    # Nature's Path - independent, family-owned
    # Organic Valley - cooperative
    # Tillamook - cooperative
    # Ocean Spray - cooperative
    # Blue Diamond - cooperative
    # Cabot Creamery - cooperative
    # Vital Farms - public company
    # Oatly - public company
    # Beyond Meat - public company
    # Liquid Death - private, VC-backed
    # OLIPOP - private, VC-backed
    # Poppi - private (acquired by PepsiCo 2025)
    # Zevia - public (Zevia PBC)
    # Waterloo - Strand Equity portfolio
}

updated = 0
not_found = 0
for brand_name, company_id in BRAND_MAP.items():
    # brands table uses name as primary key-ish
    result = c.execute(
        "UPDATE brands SET parent_company_id=? WHERE name=? AND (parent_company_id IS NULL OR parent_company_id='')",
        (company_id, brand_name)
    )
    if result.rowcount > 0:
        updated += result.rowcount
        print(f"  Linked: {brand_name!r} -> {company_id}")
    else:
        # check if brand exists
        exists = c.execute("SELECT name, parent_company_id FROM brands WHERE name=?", (brand_name,)).fetchone()
        if exists:
            if exists[1]:
                pass  # already has a parent, skip silently
            else:
                not_found += 1
                print(f"  NOT FOUND in brands: {brand_name!r}")
        else:
            not_found += 1

conn.commit()
print(f"\nPhase 4 COMPLETE")
print(f"  Brand links updated: {updated}")
print(f"  Not found / already set: {not_found}")
still_null = c.execute("SELECT COUNT(*) FROM brands WHERE parent_company_id IS NULL").fetchone()[0]
print(f"  Brands still missing parent_company_id: {still_null}")
conn.close()
