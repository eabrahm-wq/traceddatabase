import sqlite3
import requests
import time
import json
import re
from datetime import datetime

DB_PATH = "/Users/evan/Desktop/Traceddatabase/traced.db"

def slugify(name):
    return re.sub(r'[^a-z0-9]+', '-', name.lower()).strip('-')

def get_companies(conn):
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM companies ORDER BY name")
    return cur.fetchall()

def existing_descriptions(conn):
    cur = conn.cursor()
    cur.execute("SELECT description FROM violations WHERE violation_type='FDA warning letter'")
    return set(row[0] for row in cur.fetchall() if row[0])

def fetch_warning_letters(search_term, field="legal_name"):
    """Search FDA warning letters for a company name."""
    base = "https://api.fda.gov/other/warning_letters.json"
    # Try exact search
    params = {
        "search": f'{field}:"{search_term}"',
        "limit": 100
    }
    try:
        r = requests.get(base, params=params, timeout=15)
        if r.status_code == 200:
            data = r.json()
            return data.get("results", [])
        elif r.status_code == 404:
            return []
        else:
            return []
    except Exception as e:
        print(f"  Error fetching {search_term}: {e}")
        return []

def insert_violation(conn, company_id, year, description, outcome, source_url, fine_amount=None):
    cur = conn.cursor()
    # Generate unique ID
    cur.execute("SELECT COUNT(*) FROM violations")
    count = cur.fetchone()[0]
    vid = f"warn-{count+1:04d}"
    # Ensure unique
    cur.execute("SELECT id FROM violations WHERE id=?", (vid,))
    while cur.fetchone():
        count += 1
        vid = f"warn-{count+1:04d}"
        cur.execute("SELECT id FROM violations WHERE id=?", (vid,))
    
    cur.execute("""
        INSERT INTO violations (id, company_id, violation_type, year, description, outcome, fine_amount, source_url)
        VALUES (?, ?, 'FDA warning letter', ?, ?, ?, ?, ?)
    """, (vid, company_id, year, description, outcome, fine_amount, source_url))
    return vid

def main():
    conn = sqlite3.connect(DB_PATH)
    companies = get_companies(conn)
    existing = existing_descriptions(conn)
    
    inserted = 0
    checked = 0
    errors = 0
    
    # Food-related keywords to filter relevant warning letters
    food_keywords = [
        'food', 'beverage', 'drink', 'snack', 'cereal', 'dairy', 'meat', 'poultry',
        'seafood', 'produce', 'nutrition', 'dietary', 'supplement', 'ingredient',
        'labeling', 'label', 'adulterat', 'sanit', 'contamina', 'CGMP', 'GMP',
        'misbranded', 'allergen', 'haccp', 'listeria', 'salmonella', 'E. coli',
        'pesticide', 'additive', 'preservative', 'color', 'flavor'
    ]
    
    print(f"Starting Pipeline 1 — FDA Warning Letters")
    print(f"Checking {len(companies)} companies...")
    print()
    
    for company_id, company_name in companies:
        checked += 1
        print(f"[{checked}/{len(companies)}] Searching: {company_name}")
        
        # Try multiple name variations
        search_names = [company_name]
        # Add common abbreviations/aliases
        aliases = {
            "Nestlé": ["Nestle", "Nestle USA"],
            "Mondelēz": ["Mondelez", "Mondelez International", "Kraft Foods"],
            "Kraft Heinz": ["Kraft Foods", "Heinz", "H.J. Heinz"],
            "Kellogg's": ["Kellogg", "Kellogg Company"],
            "PepsiCo": ["Pepsi", "Frito-Lay"],
            "Coca-Cola": ["Coca Cola", "The Coca-Cola Company"],
            "General Mills": ["General Mills Inc"],
            "Tyson Foods": ["Tyson", "Tyson Foods Inc"],
            "Hormel Foods": ["Hormel", "Hormel Foods Corporation"],
            "Conagra Brands": ["ConAgra", "ConAgra Foods"],
            "Campbell's": ["Campbell Soup", "Campbell Soup Company"],
            "Unilever": ["Unilever United States", "Unilever US"],
            "Hershey Company": ["Hershey", "The Hershey Company"],
            "J.M. Smucker": ["Smucker", "J.M. Smucker Company"],
            "Danone": ["Danone North America", "Dannon"],
            "JBS USA": ["JBS", "Swift & Company"],
            "Smithfield Foods": ["Smithfield"],
            "Perdue Farms": ["Perdue"],
            "TreeHouse Foods": ["TreeHouse"],
        }
        
        if company_name in aliases:
            search_names.extend(aliases[company_name])
        
        company_inserted = 0
        
        for search_name in search_names:
            for field in ["legal_name", "company_name"]:
                results = fetch_warning_letters(search_name, field)
                time.sleep(0.4)
                
                for letter in results:
                    # Build description from available fields
                    subject = letter.get("subject", "")
                    legal_name = letter.get("legal_name", letter.get("company_name", ""))
                    date_issued = letter.get("date_issued", "")
                    vol_mand = letter.get("voluntary_mandated", "")
                    url = letter.get("url", letter.get("letter_url", ""))
                    
                    # Build description
                    desc = f"Warning letter to {legal_name}: {subject}"
                    if vol_mand:
                        desc += f" ({vol_mand})"
                    
                    # Skip if already exists
                    if desc in existing:
                        continue
                    
                    # Extract year
                    year = None
                    if date_issued:
                        try:
                            year = int(date_issued[:4])
                        except:
                            pass
                    
                    # Check if food-related (filter out pharma/medical/cosmetic)
                    combined = (subject + " " + desc).lower()
                    is_food = any(kw.lower() in combined for kw in food_keywords)
                    
                    # For large food companies, include all warning letters unless clearly pharma
                    pharma_skip = ['drug', 'pharmaceutical', 'medicine', 'biologic', 'medical device']
                    is_pharma = any(kw in combined for kw in pharma_skip)
                    
                    if is_pharma and not is_food:
                        continue
                    
                    source = url if url else "https://www.fda.gov/inspections-compliance-enforcement-and-criminal-investigations/compliance-actions-and-activities/warning-letters"
                    
                    try:
                        insert_violation(conn, company_id, year, desc, "Warning Letter Issued", source)
                        existing.add(desc)
                        inserted += 1
                        company_inserted += 1
                        print(f"  + Inserted: {desc[:80]}...")
                    except Exception as e:
                        errors += 1
                        print(f"  ! Error inserting: {e}")
                
                if results:
                    break  # If we got results on legal_name, don't retry company_name
            
            if company_inserted > 0:
                break  # If we found matches, don't try aliases
        
        time.sleep(0.5)
    
    conn.commit()
    conn.close()
    
    print()
    print("=" * 60)
    print(f"PIPELINE 1 SUMMARY — FDA Warning Letters")
    print(f"  Companies checked: {checked}")
    print(f"  Records inserted:  {inserted}")
    print(f"  Errors:            {errors}")
    print("=" * 60)

if __name__ == "__main__":
    main()
