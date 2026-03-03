"""
Pipeline: Parse ingredient_snapshots.additives from ingredients_raw
Identifies: artificial colors, preservatives, artificial sweeteners, 
            emulsifiers, flavor enhancers, controversial additives
"""
import sqlite3
import re

ADDITIVE_PATTERNS = {
    # Artificial colors
    'Red 40': r'\bRed\s*40\b',
    'Red 3': r'\bRed\s*3\b',
    'Yellow 5': r'\bYellow\s*5\b',
    'Yellow 6': r'\bYellow\s*6\b',
    'Blue 1': r'\bBlue\s*1\b',
    'Blue 2': r'\bBlue\s*2\b',
    'Green 3': r'\bGreen\s*3\b',
    'Caramel Color': r'\bCaramel\s*Colou?r\b',
    'Titanium Dioxide': r'\bTitanium\s*Dioxide\b',
    'Annatto': r'\bAnnatto\b',

    # Preservatives
    'BHT': r'\bBHT\b',
    'BHA': r'\bBHA\b',
    'TBHQ': r'\bTBHQ\b',
    'Sodium Benzoate': r'\bSodium\s*Benzoate\b',
    'Potassium Sorbate': r'\bPotassium\s*Sorbate\b',
    'Sodium Nitrate': r'\bSodium\s*Nitr(?:ate|ite)\b',
    'Sodium Nitrite': r'\bSodium\s*Nitrite\b',
    'Calcium Propionate': r'\bCalcium\s*Propionate\b',
    'Sulfites': r'\b(?:Sodium|Potassium)\s*(?:Bi)?Sulfit(?:e|es)\b|\bSulfit(?:e|es)\b',

    # Artificial sweeteners
    'Aspartame': r'\bAspartame\b',
    'Sucralose': r'\bSucralose\b',
    'Saccharin': r'\bSaccharin\b',
    'Acesulfame Potassium': r'\bAcesulfame\s*(?:Potassium|K)\b',
    'Stevia': r'\bStevia\b|\bReb(?:audi)?(?:oside)?\s*A\b',
    'Monk Fruit': r'\bMonk\s*Fruit\b',

    # Emulsifiers / stabilizers
    'Carrageenan': r'\bCarrageenan\b',
    'Xanthan Gum': r'\bXanthan\s*Gum\b',
    'Guar Gum': r'\bGuar\s*Gum\b',
    'Soy Lecithin': r'\bSoy\s*Lecithin\b',
    'Sunflower Lecithin': r'\bSunflower\s*Lecithin\b',
    'Carboxymethylcellulose': r'\bCarboxymethylcellulose\b|\bCMC\b',
    'Polysorbate 80': r'\bPolysorbate\s*80\b',
    'DATEM': r'\bDATEM\b',
    'SSL': r'\bSSL\b|\bSodium Stearoyl Lactylate\b',
    'Modified Starch': r'\bModified\s+(?:Corn|Food|Tapioca|Potato)?\s*Starch\b',

    # Flavor enhancers
    'MSG': r'\bMSG\b|\bMonosodium\s*Glutamate\b',
    'Disodium Guanylate': r'\bDisodium\s*Guanylate\b',
    'Disodium Inosinate': r'\bDisodium\s*Inosinate\b',
    'Yeast Extract': r'\bYeast\s*Extract\b',

    # Controversial / flagged
    'High Fructose Corn Syrup': r'\bHigh\s*Fructose\s*Corn\s*Syrup\b|\bHFCS\b',
    'Partially Hydrogenated Oil': r'\bPartially\s*Hydrogenated\b',
    'Brominated Vegetable Oil': r'\bBrominated\s*Vegetable\s*Oil\b|\bBVO\b',
    'Propylene Glycol': r'\bPropylene\s*Glycol\b',
    'Azodicarbonamide': r'\bAzodicarbonamide\b',
    'Potassium Bromate': r'\bPotassium\s*Bromate\b',
    'Artificial Flavor': r'\bArtificial\s*Flav(?:or|our)s?\b',
    'Natural Flavor': r'\bNatural\s*Flav(?:or|our)s?\b',
}

def parse_additives(ingredients_text):
    """Return comma-separated list of detected additives."""
    if not ingredients_text:
        return ''
    found = []
    upper = ingredients_text.upper()
    for name, pattern in ADDITIVE_PATTERNS.items():
        if re.search(pattern, ingredients_text, re.IGNORECASE):
            found.append(name)
    return ', '.join(found)

def main():
    conn = sqlite3.connect('/Users/evan/Desktop/Traceddatabase/traced.db')
    conn.execute("PRAGMA journal_mode=WAL")
    c = conn.cursor()

    # Get all snapshots that need additives parsed
    c.execute("""SELECT id, ingredients_raw FROM ingredient_snapshots 
                 WHERE (additives IS NULL OR additives = '') 
                 AND ingredients_raw IS NOT NULL AND ingredients_raw != ''""")
    rows = c.fetchall()
    
    print(f"Processing {len(rows):,} snapshots...")
    
    updated = 0
    batch = []
    for snap_id, ingredients in rows:
        additives = parse_additives(ingredients)
        if additives:
            batch.append((additives, snap_id))
            updated += 1
        if len(batch) >= 5000:
            conn.executemany("UPDATE ingredient_snapshots SET additives = ? WHERE id = ?", batch)
            conn.commit()
            print(f"  Committed {updated:,}...")
            batch = []

    if batch:
        conn.executemany("UPDATE ingredient_snapshots SET additives = ? WHERE id = ?", batch)
        conn.commit()

    print(f"\nUpdated additives on {updated:,} snapshots")
    
    # Stats on most common additives
    c.execute("""SELECT additives FROM ingredient_snapshots 
                 WHERE additives IS NOT NULL AND additives != ''""")
    from collections import Counter
    counter = Counter()
    for (row,) in c.fetchall():
        for a in row.split(', '):
            if a.strip():
                counter[a.strip()] += 1
    
    print("\nTop 15 additives by frequency:")
    for additive, count in counter.most_common(15):
        print(f"  {additive}: {count:,}")

    # Summary
    c.execute("SELECT COUNT(*) FROM ingredient_snapshots WHERE additives IS NOT NULL AND additives != ''")
    total_with = c.fetchone()[0]
    c.execute("SELECT COUNT(*) FROM ingredient_snapshots")
    total = c.fetchone()[0]
    print(f"\nTotal snapshots with additives flagged: {total_with:,} / {total:,} ({100*total_with/total:.1f}%)")
    
    conn.close()

if __name__ == '__main__':
    main()
