#!/usr/bin/env python3
"""seed_expansion_part2.py — SF independents, local vendors, aliases, indie panel data"""
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
# 5. SF INDEPENDENT BRANDS (brands table)
# ─────────────────────────────────────────────
SF_INDIE_BRANDS = [
    # (id, name, slug, category, format, price_tier, founded_year, neighborhood, founder_story, headline_finding, share_text)
    # COFFEE
    ('equator-coffees', 'Equator Coffees', 'equator-coffees', 'coffee', 'cafe', 2, 1995,
     'Founded 1995 by Helen Russell and Brooke McDonnell in Mill Valley CA. First B-Corp certified coffee company in Northern California. Direct trade with farms in 10+ countries. Reinvests 1% of sales in origin communities.',
     'SF-rooted independent. B-Corp certified. Direct trade sourcing. 1% of sales to origin communities.',
     'Equator is SF-rooted, B-Corp certified, direct trade. One of the few coffee companies with genuine transparency from farm to cup. #Traced #IndependentCoffee'),

    ('andytown-coffee', 'Andytown Coffee Roasters', 'andytown-coffee', 'coffee', 'cafe', 2, 2014,
     'Founded 2014 by Michael McCrory and Lauren Crabbe in the Outer Sunset. Named after a neighborhood in Co. Clare, Ireland. Small-batch roasting in SF. Community-rooted, neighborhood-focused.',
     'Outer Sunset community anchor. Small-batch roasting. Irish-American founding story.',
     "Andytown is SF's Outer Sunset neighborhood coffee institution — small-batch roasted, community-rooted. No PE, no corporate parent. #Traced #IndependentCoffee"),

    ('flywheel-coffee', 'Flywheel Coffee Roasters', 'flywheel-coffee', 'coffee', 'cafe', 2, 2012,
     'Founded 2012 in the Haight-Ashbury neighborhood of SF. Community-focused with emphasis on neighborhood service. Inner Sunset presence.',
     'Haight-Ashbury community coffee roaster. Neighborhood anchor since 2012.',
     "Flywheel: independently owned Haight-Ashbury roaster since 2012. No PE ownership, no corporate extraction. #Traced"),

    ('jane-coffee', 'Jane on Fillmore', 'jane-coffee', 'coffee', 'cafe', 2, 2011,
     'Founded 2011 in Lower Pacific Heights SF. Multiple SF locations including Fillmore and Russian Hill. Known for excellent espresso and neighborhood community building.',
     'Independently owned SF coffee institution. Multiple neighborhood locations since 2011.',
     "Jane Coffee: independently owned SF coffee institution since 2011. Fillmore, Russian Hill, and beyond — no corporate parent. #Traced"),

    ('reveille-coffee', 'Réveille Coffee Co.', 'reveille-coffee', 'coffee', 'cafe', 2, 2010,
     'Founded 2010 in North Beach by Chris and Tommy Newbury. Multiple SF locations. Award-winning baristas. Focus on quality espresso and community.',
     'North Beach-founded SF independent. Award-winning espresso. Multiple neighborhood locations.',
     "Réveille Coffee: North Beach founded 2010, no corporate parent, award-winning baristas. Real SF coffee culture. #Traced"),

    ('wrecking-ball-coffee', 'Wrecking Ball Coffee Roasters', 'wrecking-ball-coffee', 'coffee', 'cafe', 2, 2012,
     'Founded 2012 by Trish Rothgeb and Nick Cho in the Marina district. Trish Rothgeb coined the term "third wave coffee." Pioneer of quality-focused, transparent coffee sourcing.',
     'Founded by the person who coined "third wave coffee." Marina/Chestnut neighborhood anchor.',
     "Wrecking Ball was founded by the woman who coined 'third wave coffee.' Independent, transparent, Marina-rooted. #Traced #IndependentCoffee"),

    ('trouble-coffee', 'Trouble Coffee', 'trouble-coffee', 'coffee', 'cafe', 1, 2007,
     'Founded 2007 by Giulietta Carrelli in the Outer Sunset. Famous for coconut, cinnamon toast, and coffee. A deeply personal and community-rooted business. Featured in New York Times Magazine.',
     'Outer Sunset institution since 2007. Famous for coconut-cinnamon toast. Deeply personal story.',
     "Trouble Coffee: Outer Sunset institution since 2007. Featured in NYT Magazine. A deeply human, independent business. #Traced"),

    ('st-frank-coffee', 'St. Frank Coffee', 'st-frank-coffee', 'coffee', 'cafe', 2, 2014,
     'Founded 2014 in Noe Valley. Family-owned SF coffee roaster with emphasis on community and quality. Named after the founders\' son.',
     'Noe Valley family-owned coffee roaster since 2014.',
     "St. Frank Coffee: Noe Valley family-owned roaster since 2014. No PE. Community and quality focused. #Traced"),

    ('dandelion-chocolate', 'Dandelion Chocolate', 'dandelion-chocolate', 'coffee', 'cafe', 3, 2010,
     'Founded 2010 by Todd Masonis and Cameron Ring in the Mission District. Craft bean-to-bar chocolate maker. Café serves coffee and chocolate drinks. Transparent about sourcing — every bar has a QR code to the farm.',
     'Mission District bean-to-bar chocolate café. Founded 2010. Complete sourcing transparency. Ethical cacao sourcing.',
     "Dandelion Chocolate: Mission bean-to-bar maker with radical sourcing transparency. Every cacao bar traceable to the farm. Independent since 2010. #Traced"),

    ('neighbor-bakehouse', 'Neighbor Bakehouse', 'neighbor-bakehouse', 'coffee', 'cafe', 2, 2014,
     'Founded 2014 in SF\'s Dogpatch neighborhood. Wholesale bakery with café. Known for croissants, kouign-amann, and excellent coffee. Community-rooted, independent.',
     'Dogpatch independent bakery-café since 2014. Known for exceptional pastry and coffee.',
     "Neighbor Bakehouse: Dogpatch independent bakery-café since 2014. No corporate ownership. Exceptional croissants and community focus. #Traced"),

    # SF RESTAURANTS — FAST CASUAL
    ('nopalito-sf', 'Nopalito', 'nopalito', 'restaurant', 'fast_casual', 2, 2009,
     'Founded 2009 by Gonzalo Guzmán and the Nopa group in Inner Sunset. Authentic Mexican cuisine made with organic, local ingredients. Recipes from Guzmán\'s grandmother. Worker-cooperative ethos.',
     'Authentic Mexican, organic local ingredients. Nopa-group independent. Inner Sunset and NOPA locations.',
     "Nopalito: authentic Mexican with organic local ingredients, founded 2009. Part of the SF independent Nopa restaurant group. Real food, real ownership. #Traced"),

    ('papalote-sf', 'Papalote Mexican Grill', 'papalote', 'restaurant', 'fast_casual', 1, 2001,
     'Founded 2001 by brothers Gustavo and Miguel Escobedo in the Mission District. Family-owned SF Mexican institution. Featured in San Francisco Chronicle and Yelp\'s best burrito lists. Secret salsa recipe.',
     'Mission District family-owned Mexican institution since 2001. Secret salsa recipe. Brothers still run it.',
     "Papalote: Mission family-owned since 2001 by the Escobedo brothers. One of SF's best burritos. Genuinely family-run. #Traced"),

    ('tacolicious-sf', 'Tacolicious', 'tacolicious', 'restaurant', 'fast_casual', 2, 2009,
     'Founded 2009 by Joe Hargrave and Sara Deseran. Started as a Thursday night taco stand at the Ferry Building Farmers Market. Multiple SF locations. Focuses on fresh, seasonal Mexican-inspired food.',
     'Started as a Ferry Building farmers market taco stand in 2009. Multiple SF locations. Seasonal ingredients.',
     "Tacolicious: started as a farmers market taco stand 2009, grew into SF institution. Independently owned, seasonally focused. #Traced"),

    ('roam-burgers', 'Roam Artisan Burgers', 'roam-burgers', 'restaurant', 'fast_casual', 2, 2011,
     'Founded 2011 in Union Square SF. Artisan burgers with grass-fed beef, organic produce. Commitment to humane sourcing and local supply chain. Multiple SF locations.',
     'Grass-fed, humanely sourced burgers. SF independent since 2011. Local supply chain.',
     "Roam: SF-founded artisan burgers with grass-fed beef and genuinely local sourcing since 2011. No PE, no corporate parent. #Traced"),

    ('wise-sons-sf', 'Wise Sons Jewish Deli', 'wise-sons', 'restaurant', 'fast_casual', 2, 2011,
     'Founded 2011 by Evan Bloom and Leo Beckerman in the Mission. Jewish deli tradition revived in SF. Locally sourced, scratch-made pastrami and smoked fish. Community-rooted.',
     'SF-founded Jewish deli since 2011. Scratch-made pastrami and smoked fish. Mission District anchor.',
     "Wise Sons: SF Jewish deli since 2011, scratch-made everything, no corporate parent. Real deli tradition in the Mission. #Traced"),

    # SF RESTAURANTS — SIT DOWN (tier 2-3)
    ('flour-water-sf', 'Flour + Water', 'flour-water', 'restaurant', 'sit_down', 3, 2009,
     'Founded 2009 by Thomas McNaughton and David White in the Mission District. James Beard Award nominee. Known for housemade pasta and wood-fired pizza. Local, seasonal, and sustainable sourcing.',
     'Mission District pasta institution since 2009. James Beard nominated. Housemade pasta, local sourcing.',
     "Flour + Water: Mission pasta institution since 2009. James Beard nominated. Housemade pasta, independently owned. #Traced"),

    ('frances-sf', 'Frances', 'frances', 'restaurant', 'sit_down', 3, 2009,
     'Founded 2009 by Melissa Perello in the Castro District. James Beard Award winner for Best Chef: Pacific. Seasonal California cuisine with a personal, neighborhood-restaurant feel.',
     'Castro District James Beard Award winner. Seasonal California cuisine. Chef-owner Melissa Perello.',
     "Frances: Castro institution since 2009. Chef-owner Melissa Perello won James Beard Award. Seasonal, independent, neighborhood restaurant. #Traced"),

    ('delfina-sf', 'Delfina Restaurant', 'delfina', 'restaurant', 'sit_down', 3, 1998,
     'Founded 1998 by Craig and Annie Stoll in the Mission District. James Beard Award winner for Best Chef: Pacific. Italian-influenced California cuisine. Operates Pizzeria Delfina separately.',
     'Mission District Italian-California institution since 1998. James Beard Award winner Craig Stoll.',
     "Delfina: Mission District institution since 1998. James Beard Award winner Craig Stoll. Independently owned Italian-California. #Traced"),

    ('spqr-sf', 'SPQR', 'spqr', 'restaurant', 'sit_down', 3, 2007,
     'Founded 2007 on Fillmore Street SF. Italian-influenced, Roman-inspired cuisine. Chef-owner Matthew Accarrino is a Paralympic cyclist. Housemade pasta and exceptional charcuterie.',
     'Fillmore Street Italian-Roman cuisine since 2007. Chef-owner is a Paralympic cyclist. Housemade pasta.',
     "SPQR: Fillmore Street Italian institution since 2007. Chef-owner Matthew Accarrino is a Paralympic cyclist. Independently owned, craft-focused. #Traced"),

    ('che-fico-sf', 'Che Fico', 'che-fico', 'restaurant', 'sit_down', 3, 2018,
     'Founded 2018 by David Nayfeld and Matt Brewer in the Inner Sunset. Italian-California cuisine with whole-animal cooking and wood-fire technique. Named one of America\'s best new restaurants by Bon Appétit.',
     'Inner Sunset Italian-California since 2018. Bon Appétit best new restaurant. Wood-fire and whole-animal.',
     "Che Fico: Inner Sunset Italian-California since 2018. Bon Appétit best new restaurant. Independently owned with genuine craft. #Traced"),

    ('rich-table-sf', 'Rich Table', 'rich-table', 'restaurant', 'sit_down', 3, 2012,
     'Founded 2012 by married chefs Evan and Sarah Rich in Hayes Valley. James Beard semifinalists. Known for playful dishes and outstanding wine program. Neighborhood anchor in Hayes Valley.',
     'Hayes Valley institution since 2012. Husband-wife chef team. James Beard semifinalists. Outstanding wine list.',
     "Rich Table: Hayes Valley independent since 2012. Husband-wife team Evan and Sarah Rich are James Beard semifinalists. #Traced"),

    ('als-place-sf', "Al's Place", 'als-place', 'restaurant', 'sit_down', 3, 2015,
     'Founded 2015 by Aaron London in the Mission District. Michelin-starred. Vegetable-forward cuisine with fish and unusual flavor combinations. Named Bon Appétit Best New Restaurant in the US 2015.',
     "Mission District Michelin-starred. Bon Appétit's Best New Restaurant 2015. Chef Aaron London. Vegetable-forward.",
     "Al's Place: Mission Michelin star, Bon Appétit Best New Restaurant in the US (2015). Chef Aaron London's vegetable-forward vision. Independently owned. #Traced"),

    ('commonwealth-sf', 'Commonwealth', 'commonwealth', 'restaurant', 'sit_down', 3, 2010,
     'Founded 2010 in the Mission District. Donates $10 from every tasting menu to charity. Modern American cuisine with sustainability focus. Michelin Bib Gourmand.',
     'Mission District with $10/tasting menu charity donation. Michelin Bib Gourmand. Mission anchor since 2010.',
     "Commonwealth donates $10 from every tasting menu to charity. Michelin Bib Gourmand. Mission independent since 2010. Food that gives back. #Traced"),

    ('cotogna-sf', 'Cotogna', 'cotogna', 'restaurant', 'sit_down', 3, 2010,
     'Founded 2010 by Michael and Lindsay Tusk in Jackson Square. Rustic Italian cuisine with wood-fired oven. Adjacent to Quince (4-star). Emphasis on seasonal, local ingredients and house-made charcuterie.',
     'Jackson Square rustic Italian since 2010. Michael and Lindsay Tusk. Wood-fired oven. Adjacent to Michelin 3-star Quince.',
     "Cotogna: Jackson Square rustic Italian since 2010. Michael and Lindsay Tusk run both Cotogna and 3-star Quince. Independently owned. #Traced"),

    ('liholiho-sf', 'Liholiho Yacht Club', 'liholiho-yacht-club', 'restaurant', 'sit_down', 3, 2015,
     'Founded 2015 by Ravi Kapur in Nob Hill/Tendernob. Hawaiian-inspired California cuisine honoring Kapur\'s heritage. Named for Hawaiian King Kamehameha II. James Beard nominated.',
     'Tendernob Hawaiian-California cuisine since 2015. James Beard nominated Ravi Kapur. Heritage-honoring menu.',
     "Liholiho Yacht Club: Ravi Kapur's Hawaiian-California cuisine in Tendernob since 2015. James Beard nominated. Independently owned. #Traced"),

    ('mister-jius-sf', "Mister Jiu's", 'mister-jius', 'restaurant', 'sit_down', 3, 2016,
     "Founded 2016 by Brandon Jew in San Francisco's Chinatown. Michelin-starred. Modern Chinese-California cuisine in a 1912 Chinatown building. Brandon Jew is a James Beard Award winner.",
     "Chinatown Michelin star since 2016. James Beard Award winner Brandon Jew. Modern Chinese-California cuisine.",
     "Mister Jiu's: Chinatown Michelin star since 2016. James Beard winner Brandon Jew. Independently owned in a 1912 building. #Traced"),

    ('the-progress-sf', 'The Progress', 'the-progress', 'restaurant', 'sit_down', 3, 2014,
     'Founded 2014 by Stuart Brioza and Nicole Krasinski (also State Bird Provisions) on Fillmore Street. Michelin-starred. Shared plates, communal dining philosophy. Focus on seasonal California produce.',
     'Fillmore Street Michelin star since 2014. Stuart Brioza and Nicole Krasinski. Shared plates California cuisine.',
     "The Progress: Fillmore Michelin star 2014. Stuart Brioza and Nicole Krasinski also run State Bird Provisions. Independent chef-owners. #Traced"),

    ('marlowe-sf', 'Marlowe', 'marlowe', 'restaurant', 'sit_down', 3, 2011,
     'Founded 2011 by Anna Weinberg and James Nicholas in SoMa/Brannan Street. Upscale American bistro. Known for exceptional burgers and cocktails. Part of the Big Night Restaurant Group (independent).',
     'SoMa American bistro since 2011. Exceptional burgers, cocktails. Big Night Restaurant Group (independent).',
     "Marlowe: SoMa American bistro since 2011. Part of the independent Big Night Restaurant Group. Real food in a corporate restaurant neighborhood. #Traced"),

    ('nightbird-sf', 'Nightbird', 'nightbird', 'restaurant', 'sit_down', 3, 2016,
     'Founded 2016 by Kim Alter in the Tenderloin/Hayes Valley area. Michelin Bib Gourmand. Tasting menu with seasonal California produce. Separate Linden Room cocktail bar.',
     'Hayes Valley Michelin Bib Gourmand since 2016. Chef Kim Alter. Tasting menu and cocktail bar.',
     "Nightbird: Hayes Valley Michelin Bib Gourmand since 2016. Chef Kim Alter's seasonal tasting menu. Independently owned. #Traced"),

    ('verjus-sf', 'Verjus', 'verjus', 'restaurant', 'sit_down', 3, 2018,
     'Founded 2018 by Mansour Felfoul and Courtney Kaplan in the Financial District. Natural wine bar and restaurant. Outstanding all-natural wine list. Small plates menu with French bistro influence.',
     'Financial District natural wine bar since 2018. Outstanding natural wine program. French bistro influence.',
     "Verjus: natural wine bar and bistro in the Financial District since 2018. Independently owned. Thoughtful natural wine list. #Traced"),

    ('kokkari-sf', 'Kokkari Estiatorio', 'kokkari', 'restaurant', 'sit_down', 3, 2000,
     'Founded 2000 by Peter Conistis in Jackson Square. Authentic Greek cuisine in a warm, taverna-style setting. James Beard nominated. Named after a fishing village on Samos island.',
     'Jackson Square authentic Greek cuisine since 2000. James Beard nominated. Named after Samos fishing village.',
     "Kokkari: Jackson Square authentic Greek taverna since 2000. James Beard nominated. Independently owned institution. #Traced"),

    ('absinthe-sf', 'Absinthe Brasserie & Bar', 'absinthe', 'restaurant', 'sit_down', 3, 1998,
     'Founded 1998 by Bill Russell-Shapiro and Jack Morlet in Hayes Valley. French brasserie-inspired. Pioneer of the Hayes Valley restaurant renaissance. Excellent cocktail and wine program.',
     'Hayes Valley French brasserie pioneer since 1998. Helped catalyze Hayes Valley restaurant scene.',
     "Absinthe: Hayes Valley French brasserie since 1998, helping catalyze the neighborhood's restaurant renaissance. Independently owned. #Traced"),

    ('burma-superstar', 'Burma Superstar', 'burma-superstar', 'restaurant', 'sit_down', 2, 1992,
     'Founded 1992 in the Inner Richmond District. Family-owned Burmese restaurant that created a national template for Burmese cuisine in the US. Tea leaf salad is legendary. Multiple SF locations.',
     'Richmond District Burmese institution since 1992. Family-owned. Created the template for Burmese food in the US.',
     "Burma Superstar: Richmond District institution since 1992. Family-owned. Single-handedly elevated Burmese cuisine in the US. #Traced"),

    ('lers-ros-thai', 'Lers Ros Thai', 'lers-ros', 'restaurant', 'sit_down', 2, 2008,
     'Founded 2008 in the Tenderloin by Tom Silargorn. Authentic Northern and Southern Thai cuisine. Multiple SF locations. Known for authenticity and reasonable prices in a notoriously expensive city.',
     'Tenderloin authentic Thai since 2008. Multiple SF locations. Owner Tom Silargorn. Authentically Thai.',
     "Lers Ros: authentic Thai cuisine since 2008 in the Tenderloin. Owner Tom Silargorn's family recipes. Independently owned. #Traced"),

    # TIER 4 (Fine Dining)
    ('atelier-crenn', 'Atelier Crenn', 'atelier-crenn', 'restaurant', 'sit_down', 4, 2011,
     'Founded 2011 by chef Dominique Crenn in the Marina District. Three Michelin stars. First female chef in the US to receive 3 Michelin stars. Plant-forward tasting menu inspired by poetry.',
     'Marina District 3 Michelin stars since 2011. Dominique Crenn — first female 3-star chef in the US.',
     "Atelier Crenn: 3 Michelin stars, chef Dominique Crenn (first female 3-star in US). Marina District since 2011. Independently owned. #Traced"),

    ('quince-sf', 'Quince', 'quince', 'restaurant', 'sit_down', 4, 2003,
     'Founded 2003 by Michael and Lindsay Tusk in Jackson Square. Three Michelin stars. Italian-influenced California cuisine with exceptional sourcing. Operates its own farm in Marin County.',
     'Jackson Square 3 Michelin stars since 2003. Michael and Lindsay Tusk. Operates own farm in Marin.',
     "Quince: 3 Michelin stars since 2003. Michael and Lindsay Tusk operate their own farm. Independently owned. Jackson Square. #Traced"),

    ('benu-sf', 'Benu', 'benu', 'restaurant', 'sit_down', 4, 2010,
     'Founded 2010 by Corey Lee in SoMa. Three Michelin stars. Korean-American cuisine through a fine dining lens. Lee was formerly head chef at The French Laundry under Thomas Keller.',
     'SoMa 3 Michelin stars since 2010. Corey Lee — former French Laundry head chef. Korean-American fine dining.',
     "Benu: 3 Michelin stars since 2010. Chef Corey Lee's Korean-American fine dining. Independently owned. Former French Laundry head chef. #Traced"),

    ('californios-sf', 'Californios', 'californios', 'restaurant', 'sit_down', 4, 2015,
     'Founded 2015 by Val M. Cantu in the Mission District. Two Michelin stars. Modern Mexican tasting menu using California ingredients. First Mexican-focused restaurant in the US to receive 2 Michelin stars.',
     'Mission District 2 Michelin stars. Val M. Cantu. First Mexican-focused 2-star in US. California-Mexican fusion.',
     "Californios: Mission 2 Michelin stars — first Mexican-focused restaurant in the US to achieve this. Val M. Cantu. Independently owned. #Traced"),

    ('lazy-bear-sf', 'Lazy Bear', 'lazy-bear', 'restaurant', 'sit_down', 4, 2014,
     'Founded 2014 by David Barzelay in the Mission District. Michelin starred. Communal supper club format — one long table, one seating per night. California cuisine with preservation techniques.',
     'Mission District Michelin star since 2014. Communal supper club format. David Barzelay. One seating per night.',
     "Lazy Bear: Mission Michelin star since 2014. Supper club format — one seating, communal table. David Barzelay. Independently owned. #Traced"),

    ('saison-sf', 'Saison', 'saison', 'restaurant', 'sit_down', 4, 2009,
     'Founded 2009 by Joshua Skenes in SoMa. Multiple Michelin stars. Live-fire cooking technique. Seasonal California ingredients sourced from dedicated farmers. One of most decorated restaurants in SF history.',
     'SoMa Michelin starred. Joshua Skenes. Live-fire cooking technique. Dedicated farm sourcing.',
     "Saison: SoMa live-fire Michelin restaurant since 2009. Chef Joshua Skenes. Dedicated sourcing relationships. Independently owned. #Traced"),

    ('acquerello-sf', 'Acquerello', 'acquerello', 'restaurant', 'sit_down', 4, 1989,
     'Founded 1989 by Giancarlo Paterlini and chef Suzette Gresham in Russian Hill. Michelin starred. Classic Italian fine dining. One of SF\'s longest-running fine dining restaurants. Housed in converted chapel.',
     'Russian Hill Italian fine dining since 1989. Michelin star. Housed in a converted chapel. SF institution.',
     "Acquerello: SF's longest-running Italian fine dining institution since 1989. Michelin star. Converted chapel. Independently owned. #Traced"),

    # SF RESTAURANTS — Already in local_vendors, add as brands
    ('nopa-brand', 'Nopa', 'nopa', 'restaurant', 'sit_down', 3, 2006,
     'Founded 2006 by Laurence Jossel and Jeff Hanak in the NOPA neighborhood (NOrth of PAnhandle). Cornerstone of the SF independent restaurant scene. Communal tables, wood-burning oven. Late-night chef hangout.',
     'NOPA neighborhood cornerstone since 2006. Late-night institution. Wood-burning oven. Communal tables.',
     "Nopa: NOPA neighborhood institution since 2006. Late-night SF chef hangout. Communal tables, wood-burning oven. Independently owned. #Traced"),

    ('state-bird-brand', 'State Bird Provisions', 'state-bird-provisions', 'restaurant', 'sit_down', 3, 2012,
     'Founded 2012 by Stuart Brioza and Nicole Krasinski in the Divisadero Corridor. Michelin starred. James Beard Award winner Best New Restaurant. Dim sum-inspired small plates of California cuisine.',
     'Divisadero Michelin star since 2012. James Beard Best New Restaurant. Stuart Brioza and Nicole Krasinski.',
     "State Bird Provisions: James Beard Best New Restaurant 2013. Michelin star. Stuart Brioza and Nicole Krasinski. Independently owned. #Traced"),

    ('foreign-cinema-brand', 'Foreign Cinema', 'foreign-cinema', 'restaurant', 'sit_down', 3, 1999,
     'Founded 1999 by Gayle Pirie and John Clark in the Mission District. Projects foreign films in the outdoor courtyard while guests dine. California cuisine with Mediterranean influence. Mission institution.',
     'Mission District courtyard cinema-restaurant since 1999. Gayle Pirie and John Clark. California-Mediterranean cuisine.',
     "Foreign Cinema: Mission institution since 1999. Dine while watching foreign films in the courtyard. Gayle Pirie and John Clark. Independently owned. #Traced"),

    ('zuni-cafe-brand', 'Zuni Café', 'zuni-cafe', 'restaurant', 'sit_down', 3, 1979,
     'Founded 1979 on Market Street SF. Landmark San Francisco restaurant. Famous for roast chicken for two in a wood-burning oven (45-minute wait). Judy Rodgers cookbook is canonical California cuisine text.',
     'Market Street SF landmark since 1979. Famous roast chicken for two. Judy Rodgers canonical cookbook.',
     "Zuni Café: SF landmark since 1979. Famous roast chicken for two. Judy Rodgers cookbook is California cuisine canon. Independently owned. #Traced"),

    ('gracias-madre-brand', 'Gracias Madre', 'gracias-madre', 'restaurant', 'sit_down', 2, 2010,
     'Founded 2010 by Matthew Kenney and Cafe Gratitude founders in the Mission District. Plant-based Mexican cuisine. All vegan. Excellent margaritas. Mission District anchor.',
     'Mission District plant-based Mexican since 2010. All vegan. Excellent margaritas. Community anchor.',
     "Gracias Madre: all-vegan Mexican in the Mission since 2010. Plant-based before it was cool. Independently owned. #Traced"),

    ('shizen-brand', 'Shizen', 'shizen', 'restaurant', 'sit_down', 2, 2014,
     'Founded 2014 in the Mission District. Fully vegan Japanese izakaya and sushi bar. One of the first fully vegan sushi restaurants in the US. Michelin Bib Gourmand.',
     'Mission District vegan Japanese izakaya since 2014. Michelin Bib Gourmand. First fully vegan sushi bar.',
     "Shizen: Mission vegan Japanese izakaya since 2014. Michelin Bib Gourmand. First fully vegan sushi restaurant of its kind. Independently owned. #Traced"),

    # SF GROCERY — INDEPENDENTS
    ('bi-rite-brand', 'Bi-Rite Market', 'bi-rite-market', 'grocery', 'market', 2, 1940,
     'Founded 1940 (current owner Sam Mogannam took over 1997). Worker-owned partnership since 2014. 80%+ local sourcing from California farms. Operates 18 Reasons community food space next door. Bi-Rite Creamery adjacent.',
     'Mission District worker-owned partnership since 2014. 80%+ local sourcing. 18 Reasons community space.',
     "Bi-Rite: Mission worker-owned partnership since 2014. 80%+ local sourcing. 18 Reasons community space. Reinvests in neighborhood. #Traced"),

    ('rainbow-grocery-brand', 'Rainbow Grocery', 'rainbow-grocery', 'grocery', 'market', 1, 1975,
     'Founded 1975 in San Francisco as a worker-owned cooperative. 100% collectively owned and democratically managed by workers. No corporate hierarchy. Profits distributed to employee-owners. No pesticides policy.',
     '100% worker-owned cooperative since 1975. Democratically managed. No pesticides policy. No corporate hierarchy.',
     "Rainbow Grocery: 100% worker-owned cooperative since 1975. Democratically managed by workers. No corporate ownership. Profits stay with employee-owners. #Traced"),

    ('mollies-stones', "Mollie Stone's Markets", 'mollies-stones', 'grocery', 'market', 3, 1986,
     "Founded 1986 by Phil Mc Rae in Mill Valley. Family-owned Bay Area grocery chain. Multiple SF locations including Marina and Pacific Heights. Known for premium selection and local sourcing. No PE ownership.",
     'Family-owned Bay Area grocery since 1986. Multiple SF locations. No PE ownership. Premium local sourcing.',
     "Mollie Stone's: family-owned Bay Area grocery since 1986. No PE, no corporate parent. Premium local sourcing in the Marina and Pacific Heights. #Traced"),

    ('other-avenues', 'Other Avenues', 'other-avenues', 'grocery', 'market', 2, 1974,
     'Founded 1974 in the Outer Sunset. Worker-owned cooperative. Focus on organic, local, and community-sourced products. One of SF\'s oldest natural food cooperatives. No corporate ownership.',
     'Outer Sunset worker-owned food cooperative since 1974. One of SF\'s oldest natural food co-ops.',
     "Other Avenues: Outer Sunset worker-owned food cooperative since 1974. No corporate ownership. SF's longest-running natural food co-op. #Traced"),

    ('nijiya-market', 'Nijiya Market', 'nijiya-market', 'grocery', 'market', 2, 1986,
     'Founded 1986 in Los Angeles, Japantown SF location since 1990s. Japanese grocery chain with headquarters in California. Extensive Japanese food imports, fresh prepared foods, bento. Community anchor for Japanese-American SF.',
     'Japantown Japanese grocery. Fresh prepared foods, bento. California-headquartered. Japantown community anchor.',
     "Nijiya Market: Japantown Japanese grocery, California-headquartered. Fresh bento and Japanese imports. Community anchor for Japantown. #Traced"),
]

for row in SF_INDIE_BRANDS:
    (bid, name, slug, category, fmt, price_tier, founded, founder_story, headline, share) = row
    c.execute("""INSERT OR IGNORE INTO brands
        (id, name, slug, category, format, price_tier, overall_zone, independent, pe_owned,
         headline_finding, share_text, founder_story, founded_year)
        VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)""",
        (bid, name, slug, category, fmt, price_tier, 'green', 1, 0,
         headline, share, founder_story, founded))
print(f"  SF indie brands: {len(SF_INDIE_BRANDS)} processed")

# ─────────────────────────────────────────────
# 6. LOCAL VENDORS (Better Nearby recommendations)
# ─────────────────────────────────────────────
LOCAL_VENDORS = [
    # (id, name, category, format, price_tier, neighborhood, note, years_open, local_jobs, community_note, sourcing_note)
    # COFFEE
    ('equator-coffees-lv', 'Equator Coffees', 'coffee', 'cafe', 2, 'Various SF',
     'B-Corp certified, direct trade sourcing, 1% of sales to origin communities.',
     29, 120, 'B-Corp certified. 1% of revenue donated to origin farming communities. First B-Corp certified coffee company in Northern California.',
     'Direct trade with 10+ farms in Ethiopia, Guatemala, Colombia, Honduras. Full supply chain transparency.'),

    ('andytown-lv', 'Andytown Coffee Roasters', 'coffee', 'cafe', 2, 'Outer Sunset',
     'Small-batch roasting in the Outer Sunset neighborhood. Community-focused.',
     11, 35, 'Outer Sunset neighborhood anchor. Named after a village in Ireland. Deeply rooted in neighborhood community.',
     'Small-batch in-house roasting. Selects seasonal single origins and blends from independent importers.'),

    ('flywheel-lv', 'Flywheel Coffee Roasters', 'coffee', 'cafe', 2, 'Haight-Ashbury',
     'Independent roaster in the Haight since 2012.',
     13, 25, 'Haight-Ashbury neighborhood anchor. All profits stay in SF community.',
     'In-house roasting. Carefully selected single-origin and seasonal coffees.'),

    ('jane-coffee-lv', 'Jane Coffee', 'coffee', 'cafe', 2, 'Fillmore / Russian Hill',
     'SF independent with multiple neighborhood locations since 2011.',
     14, 45, 'Multiple SF neighborhood locations. Community gathering spaces for their neighborhoods.',
     'Curated selection of specialty roasters. Local sourcing focus.'),

    ('reveille-lv', 'Réveille Coffee Co.', 'coffee', 'cafe', 2, 'North Beach / Castro',
     'Award-winning SF independent coffee. Multiple locations.',
     15, 50, 'North Beach-founded, multiple SF neighborhoods served. All profits stay in SF.',
     'Award-winning barista program. Carefully curated coffee sourcing.'),

    ('wrecking-ball-lv', 'Wrecking Ball Coffee Roasters', 'coffee', 'cafe', 2, 'Marina / Chestnut St',
     'Founded by the person who coined "third wave coffee." Independent SF roaster.',
     13, 20, 'Founded by Trish Rothgeb, who coined the term "third wave coffee." Marina neighborhood anchor.',
     'Meticulous direct and near-direct trade sourcing. Seasonal roasting program.'),

    ('trouble-coffee-lv', 'Trouble Coffee', 'coffee', 'cafe', 1, 'Outer Sunset',
     'Outer Sunset institution since 2007. Famous for coconut-cinnamon toast.',
     18, 15, 'Outer Sunset anchor since 2007. Featured in NYT Magazine. A deeply personal community institution.',
     'Simple, quality-focused menu. Community-first business model.'),

    ('st-frank-lv', 'St. Frank Coffee', 'coffee', 'cafe', 2, 'Noe Valley',
     'Family-owned Noe Valley coffee roaster since 2014.',
     11, 18, 'Noe Valley family-owned roaster. Named after the founders\' son. All profits stay with the family and neighborhood.',
     'Small-batch roasting. Carefully selected single origins.'),

    ('dandelion-lv', 'Dandelion Chocolate Café', 'coffee', 'cafe', 3, 'Mission District',
     'Bean-to-bar chocolate café with radical sourcing transparency. QR codes on every product to trace the farm.',
     15, 65, 'Mission anchor since 2010. Pays premium prices directly to cacao farmers. Every product is traceable to the farm.',
     'Bean-to-bar: direct relationships with cacao farms. QR code on every bar traces to specific farm and harvest.'),

    # RESTAURANT — FAST CASUAL
    ('nopalito-lv', 'Nopalito', 'restaurant', 'fast_casual', 2, 'NOPA / Inner Sunset',
     'Authentic Mexican, organic local ingredients. Part of the Nopa independent group.',
     16, 80, 'Worker-cooperative ethos. Part of the independent Nopa restaurant group. Organic local sourcing.',
     'Certified organic produce from local California farms. Recipes from chef Gonzalo Guzmán\'s grandmother.'),

    ('papalote-lv', 'Papalote Mexican Grill', 'restaurant', 'fast_casual', 1, 'Mission District',
     'Family-owned Mission institution since 2001. Brothers Gustavo and Miguel Escobedo.',
     24, 40, 'Family-owned by the Escobedo brothers for 24 years. All profits stay in the Mission community.',
     'Fresh, made-to-order. Secret salsa recipe. Local ingredient sourcing.'),

    ('tacolicious-lv', 'Tacolicious', 'restaurant', 'fast_casual', 2, 'Various SF',
     'Started as a farmers market stand in 2009. Multiple SF locations.',
     16, 90, 'Multiple SF locations. Started at the Ferry Building Farmers Market. Community-rooted independent.',
     'Seasonal ingredients. Ferry Building Farmers Market roots drive sourcing philosophy.'),

    ('roam-lv', 'Roam Artisan Burgers', 'restaurant', 'fast_casual', 2, 'Union Square / Fillmore',
     'Grass-fed beef, organic produce. SF independent since 2011.',
     14, 50, 'SF independent since 2011. Grass-fed, humanely sourced beef. Local supply chain.',
     'Grass-fed, humanely raised beef. Organic produce. Local SF supply chain.'),

    ('wise-sons-lv', 'Wise Sons Jewish Deli', 'restaurant', 'fast_casual', 2, 'Mission / Ferry Building',
     'SF Jewish deli since 2011. Scratch-made pastrami and smoked fish.',
     14, 45, 'Mission District anchor since 2011. Scratch-made deli tradition. Community gathering space.',
     'House-smoked pastrami and salmon. Locally sourced bread and produce.'),

    # RESTAURANT — SIT DOWN (tier 2)
    ('burma-superstar-lv', 'Burma Superstar', 'restaurant', 'sit_down', 2, 'Inner Richmond',
     'Family-owned Burmese institution since 1992. Tea leaf salad is legendary.',
     33, 75, 'Richmond District family-owned for 33 years. Helped popularize Burmese cuisine nationally. All profits stay with the family.',
     'Traditional Burmese recipes. Tea leaf salad sourced from specialty importers. Local vegetables where possible.'),

    ('lers-ros-lv', 'Lers Ros Thai', 'restaurant', 'sit_down', 2, 'Tenderloin / Mission',
     'Authentic Northern and Southern Thai since 2008. Owner Tom Silargorn.',
     17, 55, 'Tenderloin anchor since 2008. Owner Tom Silargorn\'s family recipes. Multiple SF locations. Authentic Thai.',
     'Authentic Thai ingredients imported directly. Owner Tom Silargorn maintains authentic recipes.'),

    ('nopalito-sit-lv', 'Nopalito (Sit-Down)', 'restaurant', 'sit_down', 2, 'NOPA',
     'NOPA sit-down location. Authentic Mexican organic cuisine.',
     16, 80, 'NOPA neighborhood anchor. Worker-cooperative ethos. Organic local sourcing.',
     'Certified organic produce. Recipes from chef Gonzalo Guzmán\'s grandmother.'),

    # RESTAURANT — SIT DOWN (tier 3)
    ('flour-water-lv', 'Flour + Water', 'restaurant', 'sit_down', 3, 'Mission District',
     'Mission pasta institution since 2009. James Beard nominated.',
     16, 65, 'Mission anchor since 2009. All profits stay in SF. Locally sourced ingredients.',
     'Housemade pasta. Local, seasonal California produce and proteins.'),

    ('frances-lv', 'Frances', 'restaurant', 'sit_down', 3, 'Castro District',
     'James Beard Award-winning Castro institution since 2009.',
     16, 35, 'Castro anchor since 2009. James Beard winner Melissa Perello. All profits stay in SF community.',
     'Seasonal California cuisine. Local farms and producers.'),

    ('delfina-lv', 'Delfina Restaurant', 'restaurant', 'sit_down', 3, 'Mission District',
     'James Beard Award winner Craig Stoll. Mission institution since 1998.',
     27, 60, 'Mission anchor for 27 years. James Beard winner Craig Stoll. Long-term relationships with local farms.',
     'Italian-California cuisine. Long-standing relationships with local California farms and producers.'),

    ('rich-table-lv', 'Rich Table', 'restaurant', 'sit_down', 3, 'Hayes Valley',
     'Husband-wife team Evan and Sarah Rich. James Beard semifinalists. Hayes Valley since 2012.',
     13, 40, 'Hayes Valley anchor since 2012. Husband-wife chef team. All profits stay with owners and staff.',
     'Seasonal California produce. Local farms and sustainable seafood.'),

    ('als-place-lv', "Al's Place", 'restaurant', 'sit_down', 3, 'Mission District',
     "Michelin-starred. Bon Appétit's Best New Restaurant in the US (2015). Aaron London.",
     10, 30, 'Mission Michelin star since 2015. Bon Appétit Best New Restaurant. All profits stay in SF.',
     'Vegetable-forward. Local California produce central to every dish.'),

    ('commonwealth-lv', 'Commonwealth', 'restaurant', 'sit_down', 3, 'Mission District',
     'Donates $10 from every tasting menu to charity. Michelin Bib Gourmand.',
     15, 35, '$10 from every tasting menu donated to charity. Michelin Bib Gourmand. Mission anchor since 2010.',
     'Seasonal California produce. Local farms and sustainable sourcing.'),

    ('cotogna-lv', 'Cotogna', 'restaurant', 'sit_down', 3, 'Jackson Square',
     'Rustic Italian since 2010. Michael and Lindsay Tusk. Wood-fired oven.',
     15, 50, 'Jackson Square anchor since 2010. Michael and Lindsay Tusk also run Quince (3 Michelin stars). SF institution.',
     'Italian-California. Wood-fired oven sourcing seasonal local ingredients.'),

    ('liholiho-lv', 'Liholiho Yacht Club', 'restaurant', 'sit_down', 3, 'Tendernob',
     'Hawaiian-California cuisine. James Beard nominated Ravi Kapur.',
     10, 40, 'Tendernob anchor since 2015. James Beard nominated Ravi Kapur. Hawaiian heritage honored. All profits in SF.',
     'Hawaiian-California sourcing. Local produce with Hawaiian ingredients.'),

    ('mister-jius-lv', "Mister Jiu's", 'restaurant', 'sit_down', 3, 'Chinatown',
     'Chinatown Michelin star since 2016. James Beard winner Brandon Jew.',
     9, 35, 'Chinatown anchor since 2016. James Beard winner Brandon Jew. Modern Chinese-California cuisine. Historic building.',
     'Modern Chinese-California sourcing. Local California produce with Chinese culinary tradition.'),

    ('the-progress-lv', 'The Progress', 'restaurant', 'sit_down', 3, 'Fillmore Street',
     'Fillmore Michelin star. Stuart Brioza and Nicole Krasinski. Shared plates.',
     11, 35, 'Fillmore anchor since 2014. Chef-owners Stuart Brioza and Nicole Krasinski. All profits stay with owners and staff.',
     'Seasonal California produce. Local farms and sustainable seafood.'),

    ('kokkari-lv', 'Kokkari Estiatorio', 'restaurant', 'sit_down', 3, 'Jackson Square',
     'Authentic Greek taverna since 2000. James Beard nominated.',
     25, 60, 'Jackson Square institution since 2000. 25 years of independent ownership. James Beard nominated.',
     'Authentic Greek ingredients. Local California produce combined with Greek culinary tradition.'),

    ('absinthe-lv', 'Absinthe Brasserie', 'restaurant', 'sit_down', 3, 'Hayes Valley',
     'Hayes Valley French brasserie pioneer since 1998.',
     27, 55, 'Hayes Valley anchor since 1998. Pioneer of the neighborhood restaurant scene. 27 years of independent ownership.',
     'French brasserie-inspired sourcing. California produce and quality imports.'),

    # RESTAURANT — SIT DOWN (tier 4)
    ('atelier-crenn-lv', 'Atelier Crenn', 'restaurant', 'sit_down', 4, 'Marina District',
     '3 Michelin stars. Dominique Crenn — first female 3-star chef in the US.',
     14, 55, 'Marina anchor since 2011. Dominique Crenn is a leader in sustainable fine dining. Carbon-neutral commitment.',
     'Plant-forward. Direct relationships with farms. Crenn is committed to sustainable, regenerative agriculture.'),

    ('quince-lv', 'Quince', 'restaurant', 'sit_down', 4, 'Jackson Square',
     '3 Michelin stars. Michael and Lindsay Tusk operate their own farm in Marin.',
     22, 65, 'Jackson Square institution since 2003. Operates own farm (Quince & Co.) in Marin County. 22 years of independent ownership.',
     'Operates own farm in Marin County. Most ingredients sourced directly from Quince & Co. farm or partner farms.'),

    ('benu-lv', 'Benu', 'restaurant', 'sit_down', 4, 'SoMa',
     '3 Michelin stars. Chef Corey Lee. Korean-American fine dining.',
     15, 45, 'SoMa institution since 2010. Corey Lee is a James Beard Award winner. All profits stay in SF.',
     'Korean-American fine dining. Direct relationships with specialty purveyors. Seasonal California ingredients.'),

    ('lazy-bear-lv', 'Lazy Bear', 'restaurant', 'sit_down', 4, 'Mission District',
     'Mission Michelin star. Communal supper club. One seating per night.',
     11, 25, 'Mission anchor since 2014. Communal format supports worker dignity and equitable tipping.',
     'Seasonal California ingredients with preservation/fermentation techniques.'),

    # GROCERY
    ('bi-rite-lv', 'Bi-Rite Market', 'grocery', 'market', 2, 'Mission District',
     'Worker-owned partnership since 2014. 80%+ local CA sourcing. 18 Reasons community space.',
     85, 120, 'Worker-owned partnership since 2014. 80%+ sourcing from California farms. Operates 18 Reasons community food education space next door.',
     '80%+ of products from California farms and producers. Long-term relationships with 50+ local farms.'),

    ('rainbow-grocery-lv', 'Rainbow Grocery', 'grocery', 'market', 1, 'Mission District',
     '100% worker-owned cooperative since 1975. No pesticides policy.',
     50, 250, '100% worker-owned cooperative since 1975. Democratically managed by workers. No outside investors. No pesticides policy.',
     'Strong organic and local sourcing. No pesticides policy. Worker-owners vote on all major purchasing decisions.'),

    ('gus-lv', "Gus's Community Market", 'grocery', 'market', 1, 'Divisadero / NOPA',
     'Family-owned neighborhood grocery. Community anchor.',
     35, 45, 'Divisadero neighborhood anchor. Family-owned. Community-focused independent grocery.',
     'Mix of local and national products. Community pricing focus.'),

    ('haight-street-lv', 'Haight Street Market', 'grocery', 'market', 1, 'Haight-Ashbury',
     'Haight-Ashbury neighborhood grocery institution.',
     40, 35, 'Haight-Ashbury anchor. Independent neighborhood grocery. Community-priced staples.',
     'Neighborhood-focused product selection. Local products alongside affordable staples.'),

    ('other-avenues-lv', 'Other Avenues', 'grocery', 'market', 2, 'Outer Sunset',
     'Worker-owned food cooperative since 1974. One of SF\'s oldest natural food co-ops.',
     51, 30, 'Worker-owned cooperative since 1974. One of SF\'s longest-running natural food co-ops. Democratic governance.',
     'Organic and natural products prioritized. Worker-owners select products by committee.'),

    ('mollies-stones-lv', "Mollie Stone's Markets", 'grocery', 'market', 3, 'Marina / Pacific Heights',
     'Family-owned Bay Area grocery since 1986. Premium local sourcing.',
     39, 150, 'Family-owned for 39 years. No PE ownership. Premium local sourcing across Marina and Pacific Heights locations.',
     'Premium local and organic sourcing. Long-term relationships with California farms and artisans.'),
]

for row in LOCAL_VENDORS:
    (vid, name, category, fmt, price_tier, neighborhood, note,
     years_open, local_jobs, community_note, sourcing_note) = row
    c.execute("""INSERT OR IGNORE INTO local_vendors
        (id, name, category, format, price_tier, neighborhood, note, slug, verified,
         years_open, local_jobs, community_note, sourcing_note)
        VALUES (?,?,?,?,?,?,?,?,1,?,?,?,?)""",
        (vid, name, category, fmt, price_tier, neighborhood, note,
         vid, years_open, local_jobs, community_note, sourcing_note))
print(f"  Local vendors: {len(LOCAL_VENDORS)} processed")

# ─────────────────────────────────────────────
# 7. UPDATE EXISTING LOCAL VENDORS with indie panel data
# ─────────────────────────────────────────────
EXISTING_VENDOR_UPDATES = [
    # (id, years_open, local_jobs, community_note, sourcing_note)
    ('ritual-coffee-roasters', 18, 85,
     'Worker-friendly wages and benefits above industry average. Profits stay in SF community.',
     'Direct trade with farms in Ethiopia, Guatemala, Colombia. Transparent supply chain.'),
    ('sightglass-coffee', 15, 65,
     'SoMa anchor since 2009. Hosts community events, art shows, and public programming.',
     'Small-batch roasted in-house. Direct relationships with 12+ coffee farms globally.'),
    ('four-barrel-coffee', 12, 45,  # this is Verve in the DB
     'Santa Cruz-rooted, SF-expanding independent. Profits stay with the team.',
     'Direct trade sourcing from Latin America and Africa.'),
    ('linea-caffe', 10, 20,
     'SoMa specialty coffee institution. Barista-owned and operated.',
     'Specialty micro-lot coffees. Direct relationships with farms and importers.'),
    ('coffee-mission', 16, 15,
     'Mission District neighborhood coffee anchor. Community gathering space.',
     'Specialty coffee program with emphasis on ethical sourcing.'),
    ('bi-rite-market', 85, 120,
     'Worker-owned partnership since 2014. 80%+ local CA sourcing. 18 Reasons community space next door.',
     '80%+ of products from California farms. Long-term relationships with 50+ local farms.'),
    ('rainbow-grocery', 50, 250,
     '100% worker-owned cooperative since 1975. Democratically managed. No pesticides policy.',
     'Strong organic and local sourcing. Worker-owners vote on all major purchasing decisions.'),
    ('gus-community-market', 35, 45,
     'Divisadero neighborhood anchor. Family-owned. Community-focused independent grocery.',
     'Community pricing focus. Mix of local and national products.'),
    ('haight-street-market', 40, 35,
     'Haight-Ashbury anchor. Independent neighborhood grocery.',
     'Neighborhood-focused selection. Affordable staples alongside local products.'),
    ('souvla', 11, 75,
     'SF-founded Greek fast casual since 2014. Multiple SF locations. Profits stay in SF.',
     'Humanely raised meats. Local Greek-inspired sourcing from California farms.'),
    ('nopa-sf', 19, 95,
     'NOPA neighborhood cornerstone since 2006. Late-night chef hangout. Communal tables.',
     'Seasonal California cuisine. Long-term relationships with local farms and ranches.'),
    ('state-bird-provisions', 13, 45,
     'James Beard Best New Restaurant 2013. Divisadero anchor. Chef-owned and operated.',
     'Seasonal California produce from local farms. Sustainable sourcing.'),
    ('foreign-cinema', 26, 80,
     'Mission institution since 1999. Gayle Pirie and John Clark. Art and food combined.',
     'California-Mediterranean sourcing. Local farms and quality imports.'),
    ('gracias-madre', 15, 65,
     'Mission District plant-based anchor since 2010. All vegan. Community focused.',
     'Certified organic produce. Plant-based, local California sourcing.'),
    ('shizen', 11, 30,
     'Mission vegan Japanese izakaya since 2014. Michelin Bib Gourmand. Community anchor.',
     'Vegan Japanese ingredients. Sustainable plant-based sourcing.'),
    ('prubechu', 9, 35,
     'Mission/Outer Sunset Chamorro (Guam) cuisine. Honors heritage. Chef-owned.',
     'Guamanian heritage ingredients. Local California produce alongside traditional imports.'),
    ('misfits-market-sf', 12, 45,  # this is Wildseed in DB
     'Union Square plant-based since 2019. Elegant vegan fine dining.',
     'Premium plant-based ingredients. Local California organic sourcing.'),
    ('zuni-cafe', 46, 90,
     'Market Street SF landmark since 1979. Judy Rodgers cookbook is California cuisine canon.',
     'Seasonal California cuisine. Long-term farm relationships. Wood-burning oven.'),
]

for row in EXISTING_VENDOR_UPDATES:
    (vid, years_open, local_jobs, community_note, sourcing_note) = row
    c.execute("""UPDATE local_vendors SET
        years_open=?, local_jobs=?, community_note=?, sourcing_note=?
        WHERE id=?""",
        (years_open, local_jobs, community_note, sourcing_note, vid))

# Fix incorrect category on Real Food Company (was 'pharmacy', should be 'grocery')
c.execute("""UPDATE local_vendors SET category='grocery', format='market', price_tier=2,
    community_note='Castro neighborhood grocery institution. Independent, community-focused.',
    sourcing_note='Focus on natural and organic products.'
    WHERE id='real-food-company'""")

# Fix Pharmaca (was pharmacy, now Rite Aid-owned — mark as unverified/remove)
c.execute("UPDATE local_vendors SET verified=0 WHERE id='elephant-pharmacy'")
print("  Existing local vendors updated")

# ─────────────────────────────────────────────
# 8. BRAND ALIASES
# ─────────────────────────────────────────────
ALIASES = [
    # Coffee chains
    ("starbucks", "starbucks"),
    ("starbucks coffee", "starbucks"),
    ("starbucks reserve", "starbucks"),
    ("starbucks roastery", "starbucks"),
    ("dunkin", "dunkin"),
    ("dunkin donuts", "dunkin"),
    ("dutch bros", "dutch-bros-brand"),
    ("dutch bros coffee", "dutch-bros-brand"),
    ("tim hortons", "tim-hortons"),
    ("tim horton", "tim-hortons"),
    ("caribou coffee", "caribou-coffee"),
    ("stumptown coffee roasters", "stumptown-coffee"),
    ("stumptown coffee", "stumptown-coffee"),
    ("stumptown", "stumptown-coffee"),
    ("intelligentsia coffee", "intelligentsia-coffee"),
    ("intelligentsia", "intelligentsia-coffee"),
    ("coffee bean tea leaf", "coffee-bean"),
    ("coffee bean", "coffee-bean"),
    ("the coffee bean", "coffee-bean"),
    ("seattles best coffee", "seattles-best"),
    ("seattles best", "seattles-best"),

    # Fast food / QSR
    ("mcdonald", "mcdonalds"),
    ("mcdonalds", "mcdonalds"),
    ("burger king", "burger-king"),
    ("taco bell", "taco-bell"),
    ("kfc", "kfc"),
    ("kentucky fried chicken", "kfc"),
    ("pizza hut", "pizza-hut"),
    ("wendy", "wendys"),
    ("wendys", "wendys"),
    ("in n out burger", "in-n-out-burger"),
    ("in n out", "in-n-out-burger"),
    ("five guys burgers fries", "five-guys-brand"),
    ("five guys", "five-guys-brand"),
    ("subway", "subway"),
    ("chick fil a", "chick-fil-a-brand"),
    ("chick fil", "chick-fil-a-brand"),
    ("panda express", "panda-express"),
    ("popeyes", "popeyes"),
    ("popeyes louisiana kitchen", "popeyes"),
    ("jack in the box", "jack-in-the-box-brand"),
    ("jack in box", "jack-in-the-box-brand"),
    ("del taco", "del-taco"),
    ("carls jr", "carls-jr"),
    ("wingstop", "wingstop-brand"),
    ("panera bread", "panera-bread-brand"),
    ("panera", "panera-bread-brand"),
    ("cava", "cava-brand"),
    ("cava mediterranean grill", "cava-brand"),
    ("sweetgreen", "sweetgreen"),
    ("sweet green", "sweetgreen"),
    ("shake shack", "shake-shack"),
    ("tender greens", "tender-greens"),
    ("habit burger grill", "habit-burger"),
    ("habit burger", "habit-burger"),
    ("the habit", "habit-burger"),
    ("jimmy john", "jimmy-johns"),
    ("jimmy johns", "jimmy-johns"),
    ("sonic drive in", "sonic-brand"),
    ("sonic", "sonic-brand"),
    ("arby", "arbys"),
    ("arbys", "arbys"),
    ("buffalo wild wings", "buffalo-wild-wings"),
    ("bdubs", "buffalo-wild-wings"),
    ("firehouse subs", "firehouse-subs"),
    ("jersey mike", "jersey-mikes-brand"),
    ("jersey mikes", "jersey-mikes-brand"),
    ("smashburger", "smashburger"),
    ("raising cane", "raising-canes-brand"),
    ("raising canes", "raising-canes-brand"),

    # Sit-down chains
    ("olive garden", "olive-garden"),
    ("olive garden italian restaurant", "olive-garden"),
    ("applebee", "applebees"),
    ("applebees", "applebees"),
    ("ihop", "ihop"),
    ("international house of pancakes", "ihop"),
    ("cheesecake factory", "cheesecake-factory"),
    ("the cheesecake factory", "cheesecake-factory"),
    ("denny", "dennys"),
    ("dennys", "dennys"),
    ("longhorn steakhouse", "longhorn-steakhouse"),
    ("yard house", "yard-house"),

    # Grocery
    ("target", "target-grocery"),
    ("albertsons", "albertsons-brand"),
    ("vons", "vons"),
    ("smart final", "smart-and-final"),
    ("smart and final", "smart-and-final"),
    ("grocery outlet", "grocery-outlet-brand"),
    ("grocery outlet bargain market", "grocery-outlet-brand"),
    ("raley", "raleys-brand"),
    ("raleys", "raleys-brand"),
    ("winco foods", "winco-brand"),
    ("winco", "winco-brand"),
    ("99 ranch market", "99-ranch-market"),
    ("ranch 99", "99-ranch-market"),
    ("nijiya market", "nijiya-market"),
    ("nijiya", "nijiya-market"),

    # SF Independents (coffee)
    ("equator coffees", "equator-coffees"),
    ("equator coffee", "equator-coffees"),
    ("andytown coffee roasters", "andytown-coffee"),
    ("andytown coffee", "andytown-coffee"),
    ("andytown", "andytown-coffee"),
    ("flywheel coffee roasters", "flywheel-coffee"),
    ("flywheel coffee", "flywheel-coffee"),
    ("flywheel", "flywheel-coffee"),
    ("jane on fillmore", "jane-coffee"),
    ("jane coffee", "jane-coffee"),
    ("reveille coffee co", "reveille-coffee"),
    ("reveille coffee", "reveille-coffee"),
    ("reveille", "reveille-coffee"),
    ("wrecking ball coffee roasters", "wrecking-ball-coffee"),
    ("wrecking ball coffee", "wrecking-ball-coffee"),
    ("wrecking ball", "wrecking-ball-coffee"),
    ("trouble coffee", "trouble-coffee"),
    ("st frank coffee", "st-frank-coffee"),
    ("dandelion chocolate", "dandelion-chocolate"),
    ("neighbor bakehouse", "neighbor-bakehouse"),

    # SF Independents (restaurants)
    ("nopalito", "nopalito-sf"),
    ("papalote mexican grill", "papalote-sf"),
    ("papalote", "papalote-sf"),
    ("tacolicious", "tacolicious-sf"),
    ("roam artisan burgers", "roam-burgers"),
    ("roam burgers", "roam-burgers"),
    ("roam", "roam-burgers"),
    ("wise sons jewish deli", "wise-sons-sf"),
    ("wise sons", "wise-sons-sf"),
    ("flour water", "flour-water-sf"),
    ("flour and water", "flour-water-sf"),
    ("frances", "frances-sf"),
    ("delfina restaurant", "delfina-sf"),
    ("delfina", "delfina-sf"),
    ("spqr", "spqr-sf"),
    ("che fico", "che-fico-sf"),
    ("rich table", "rich-table-sf"),
    ("al place", "als-place-sf"),
    ("als place", "als-place-sf"),
    ("commonwealth", "commonwealth-sf"),
    ("cotogna", "cotogna-sf"),
    ("liholiho yacht club", "liholiho-sf"),
    ("liholiho", "liholiho-sf"),
    ("mister jiu", "mister-jius-sf"),
    ("mr jiu", "mister-jius-sf"),
    ("the progress", "the-progress-sf"),
    ("marlowe", "marlowe-sf"),
    ("nightbird", "nightbird-sf"),
    ("verjus", "verjus-sf"),
    ("kokkari estiatorio", "kokkari-sf"),
    ("kokkari", "kokkari-sf"),
    ("absinthe brasserie", "absinthe-sf"),
    ("absinthe", "absinthe-sf"),
    ("burma superstar", "burma-superstar"),
    ("lers ros thai", "lers-ros-thai"),
    ("lers ros", "lers-ros-thai"),
    ("atelier crenn", "atelier-crenn"),
    ("quince", "quince-sf"),
    ("benu", "benu-sf"),
    ("californios", "californios-sf"),
    ("lazy bear", "lazy-bear-sf"),
    ("saison", "saison-sf"),
    ("acquerello", "acquerello-sf"),
    ("nopa", "nopa-brand"),
    ("state bird provisions", "state-bird-brand"),
    ("foreign cinema", "foreign-cinema-brand"),
    ("zuni cafe", "zuni-cafe-brand"),
    ("zuni caf", "zuni-cafe-brand"),
    ("gracias madre", "gracias-madre-brand"),
    ("shizen", "shizen-brand"),

    # SF Grocery independents
    ("bi rite market", "bi-rite-brand"),
    ("rainbow grocery cooperative", "rainbow-grocery-brand"),
    ("rainbow grocery", "rainbow-grocery-brand"),
    ("mollie stone", "mollies-stones"),
    ("mollie stones markets", "mollies-stones"),
    ("other avenues", "other-avenues"),
    ("bi rite", "bi-rite-brand"),
]

inserted = 0
skipped = 0
for alias_text, brand_id in ALIASES:
    # verify brand exists
    c.execute("SELECT id FROM brands WHERE id=?", (brand_id,))
    if not c.fetchone():
        # try by slug
        c.execute("SELECT id FROM brands WHERE slug=? OR lower(name)=lower(?)", (brand_id, brand_id))
        row = c.fetchone()
        if row:
            brand_id = row[0]
        else:
            print(f"  SKIP alias '{alias_text}' → '{brand_id}' (brand not found)")
            skipped += 1
            continue
    try:
        c.execute("INSERT OR IGNORE INTO brand_aliases (alias_text, brand_id, source) VALUES (?,?,'seed_v2')",
                  (normalize(alias_text), brand_id))
        if c.rowcount > 0:
            inserted += 1
    except Exception as e:
        print(f"  ERROR alias '{alias_text}': {e}")

print(f"  Aliases: {inserted} inserted, {skipped} skipped")

conn.commit()
conn.close()
print("\n✓ seed_expansion_part2.py complete")
