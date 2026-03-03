import sqlite3
import requests
import time
import json
import re
from datetime import datetime

DB_PATH = "/Users/evan/Desktop/Traceddatabase/traced.db"
FDA_ENFORCEMENT = "https://api.fda.gov/food/enforcement.json"
FDA_RECALL_URL = "https://www.fda.gov/safety/recalls-market-withdrawals-safety-alerts"

def get_top_brands(conn, limit=100):
    cur = conn.cursor()
    cur.execute("""
        SELECT b.id, b.name, c.id as company_id, c.name as company_name 
        FROM brands b 
        JOIN companies c ON b.parent_company_id = c.id
        ORDER BY b.total_scans DESC NULLS LAST
        LIMIT ?
    """, (limit,))
    return cur.fetchall()

def get_all_companies(conn):
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM companies")
    return cur.fetchall()

def existing_violations(conn):
    """Return set of (company_id, description) tuples for existing FDA recalls."""
    cur = conn.cursor()
    cur.execute("SELECT company_id, description FROM violations WHERE violation_type='FDA recall'")
    return set((row[0], row[1]) for row in cur.fetchall() if row[1])

def existing_recall_numbers(conn):
    """Get existing recall numbers from descriptions to avoid duplicates."""
    cur = conn.cursor()
    cur.execute("SELECT description FROM violations WHERE violation_type='FDA recall'")
    descs = [row[0] for row in cur.fetchall() if row[0]]
    # Extract recall numbers
    numbers = set()
    for d in descs:
        # Look for FDA recall number pattern F-XXXX-YYYY
        nums = re.findall(r'[FZ]-\d{4}-\d{4}', d)
        numbers.update(nums)
    return numbers

def search_enforcement(search_term, field="product_description", classification_filter=None):
    """Search FDA food enforcement by term in a field."""
    params = {
        "search": f'{field}:"{search_term}"',
        "limit": 100
    }
    if classification_filter:
        params["search"] += f'+AND+classification:"{classification_filter}"'
    
    try:
        r = requests.get(FDA_ENFORCEMENT, params=params, timeout=15)
        if r.status_code == 200:
            data = r.json()
            return data.get("results", [])
        elif r.status_code == 404:
            return []
        return []
    except Exception as e:
        print(f"  Error: {e}")
        return []

def get_next_id(conn):
    cur = conn.cursor()
    cur.execute("SELECT id FROM violations WHERE id LIKE 'recl-%' ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    if row:
        try:
            num = int(row[0].replace('recl-', ''))
            return f"recl-{num+1:04d}"
        except:
            pass
    cur.execute("SELECT COUNT(*) FROM violations")
    n = cur.fetchone()[0]
    return f"recl-{n+1:04d}"

def build_description(r):
    firm = r.get("recalling_firm", "")
    product = r.get("product_description", "")[:200]
    reason = r.get("reason_for_recall", "")[:200]
    cls = r.get("classification", "")
    recall_num = r.get("recall_number", "")
    return f"[{cls}] {firm}: {product} — {reason} (Recall #{recall_num})"

def insert_violation(conn, company_id, year, description, fine_amount=None):
    vid = get_next_id(conn)
    cur = conn.cursor()
    cur.execute("SELECT id FROM violations WHERE id=?", (vid,))
    while cur.fetchone():
        n = int(vid.replace("recl-", ""))
        vid = f"recl-{n+1:04d}"
        cur.execute("SELECT id FROM violations WHERE id=?", (vid,))
    
    cur.execute("""
        INSERT INTO violations (id, company_id, violation_type, year, description, outcome, fine_amount, source_url)
        VALUES (?, ?, 'FDA recall', ?, ?, 'Recall Issued', ?, ?)
    """, (vid, company_id, year, description, fine_amount, FDA_RECALL_URL))
    return vid

def main():
    conn = sqlite3.connect(DB_PATH)
    
    brands = get_top_brands(conn, 100)
    companies = get_all_companies(conn)
    existing_viol = existing_violations(conn)
    existing_nums = existing_recall_numbers(conn)
    
    print("Pipeline 2 — FDA Food Enforcement (expanding beyond 235 existing records)")
    print(f"Checking top 100 brands + {len(companies)} companies...")
    print()
    
    inserted = 0
    skipped_dup = 0
    checked = 0
    
    # Search by brand name in product_description
    seen_recall_nums = set(existing_nums)
    
    # Broader company name searches to find Class I and II recalls we're missing
    search_terms = []
    
    # From top brands
    for brand_id, brand_name, company_id, company_name in brands:
        search_terms.append((brand_name, company_id, company_name))
    
    # Also search by company name directly
    company_search_names = {
        "nestle": "Nestlé",
        "pepsico": "PepsiCo",
        "general mills": "General Mills",
        "kraft": "Kraft Heinz",
        "kellogg": "Kellogg's",
        "conagra": "Conagra Brands",
        "campbell": "Campbell's",
        "hershey": "Hershey Company",
        "hormel": "Hormel Foods",
        "tyson": "Tyson Foods",
        "smithfield": "Smithfield Foods",
        "perdue": "Perdue Farms",
        "jbs": "JBS USA",
        "mondelez": "Mondelēz",
        "danone": "Danone",
        "unilever": "Unilever",
        "post holdings": "Post Holdings",
        "hain celestial": "Hain Celestial",
        "flowers foods": "Flowers Foods",
        "treehouse": "TreeHouse Foods",
        "dean foods": "Dean Foods",
        "barilla": "Barilla",
        "goya": "Goya Foods",
        "mars": "Mars Inc.",
        "ferrero": "Ferrero",
        "coca-cola": "Coca-Cola",
        "coca cola": "Coca-Cola",
        "frito-lay": "PepsiCo",
        "quaker": "PepsiCo",
        "tropicana": "PepsiCo",
        "gatorade": "PepsiCo",
    }
    
    # Get company IDs by name
    company_map = {}
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM companies")
    for cid, cname in cur.fetchall():
        company_map[cname] = cid
    
    # Build search term list including company searches
    for search_name, company_name in company_search_names.items():
        cid = company_map.get(company_name)
        if cid:
            search_terms.append((search_name, cid, company_name))
    
    # Process each search term
    processed = set()  # avoid duplicate searches
    
    for search_name, company_id, company_name in search_terms:
        if search_name.lower() in processed:
            continue
        processed.add(search_name.lower())
        checked += 1
        
        results = search_enforcement(search_name, "product_description")
        time.sleep(0.5)
        
        class_filtered = [r for r in results if r.get("classification") in ["Class I", "Class II"]]
        
        if class_filtered:
            print(f"  [{company_name}] '{search_name}': {len(class_filtered)} Class I/II recalls found")
        
        for r in class_filtered:
            recall_num = r.get("recall_number", "")
            if recall_num and recall_num in seen_recall_nums:
                skipped_dup += 1
                continue
            
            desc = build_description(r)
            
            # Check description duplicate  
            key = (company_id, desc[:100])
            if key in existing_viol:
                skipped_dup += 1
                continue
            
            # Extract year
            year = None
            date_str = r.get("recall_initiation_date", "")
            if date_str and len(date_str) >= 4:
                try:
                    year = int(date_str[:4])
                except:
                    pass
            
            try:
                insert_violation(conn, company_id, year, desc)
                existing_viol.add(key)
                if recall_num:
                    seen_recall_nums.add(recall_num)
                inserted += 1
            except Exception as e:
                print(f"  ! Insert error: {e}")
    
    # Also search by recalling_firm for major companies
    firm_searches = [
        ("Nestle", "Nestlé"),
        ("Kraft", "Kraft Heinz"),
        ("Kellogg", "Kellogg's"),
        ("Tyson", "Tyson Foods"),
        ("Hormel", "Hormel Foods"),
        ("ConAgra", "Conagra Brands"),
        ("Campbell", "Campbell's"),
        ("General Mills", "General Mills"),
        ("Hain", "Hain Celestial"),
        ("Flowers", "Flowers Foods"),
        ("Post Holdings", "Post Holdings"),
        ("Dean Foods", "Dean Foods"),
        ("Barilla", "Barilla"),
        ("Goya", "Goya Foods"),
        ("Perdue", "Perdue Farms"),
        ("Smithfield", "Smithfield Foods"),
        ("Danone", "Danone"),
        ("Dannon", "Danone"),
        ("Unilever", "Unilever"),
        ("Ferrero", "Ferrero"),
        ("TreeHouse", "TreeHouse Foods"),
        ("Smucker", "J.M. Smucker"),
        ("Mondelez", "Mondelēz"),
        ("Pepperidge Farm", "Campbell's"),
        ("Birds Eye", "Conagra Brands"),
        ("Healthy Choice", "Conagra Brands"),
        ("Marie Callender", "Conagra Brands"),
        ("Skippy", "Hormel Foods"),
        ("Jennie-O", "Hormel Foods"),
        ("Hillshire", "Tyson Foods"),
        ("Jimmy Dean", "Tyson Foods"),
        ("Ball Park", "Tyson Foods"),
        ("Sara Lee", "Tyson Foods"),
        ("Vlasic", "Conagra Brands"),
        ("Hunt's", "Conagra Brands"),
        ("Swiss Miss", "Conagra Brands"),
        ("Orville", "Conagra Brands"),
        ("PAM", "Conagra Brands"),
        ("Snyder's-Lance", "Campbell's"),
        ("Pepperidge", "Campbell's"),
        ("Annie's", "General Mills"),
        ("Larabar", "General Mills"),
        ("Pillsbury", "General Mills"),
        ("Progresso", "General Mills"),
        ("Old El Paso", "General Mills"),
        ("Cheerios", "General Mills"),
        ("Nature Valley", "General Mills"),
        ("Yoplait", "General Mills"),
        ("Häagen-Dazs", "Nestlé"),
        ("Stouffer", "Nestlé"),
        ("Hot Pockets", "Nestlé"),
        ("DiGiorno", "Nestlé"),
        ("Buitoni", "Nestlé"),
    ]
    
    print(f"\nSearching by recalling_firm field...")
    for firm_name, company_name in firm_searches:
        cid = company_map.get(company_name)
        if not cid:
            continue
        
        if firm_name.lower() in processed:
            continue
        processed.add(firm_name.lower())
        
        results = search_enforcement(firm_name, "recalling_firm")
        time.sleep(0.5)
        
        class_filtered = [r for r in results if r.get("classification") in ["Class I", "Class II"]]
        
        for r in class_filtered:
            recall_num = r.get("recall_number", "")
            if recall_num and recall_num in seen_recall_nums:
                skipped_dup += 1
                continue
            
            desc = build_description(r)
            key = (cid, desc[:100])
            if key in existing_viol:
                skipped_dup += 1
                continue
            
            year = None
            date_str = r.get("recall_initiation_date", "")
            if date_str and len(date_str) >= 4:
                try:
                    year = int(date_str[:4])
                except:
                    pass
            
            try:
                insert_violation(conn, cid, year, desc)
                existing_viol.add(key)
                if recall_num:
                    seen_recall_nums.add(recall_num)
                inserted += 1
                print(f"  + [{company_name}] {year}: {desc[:80]}")
            except Exception as e:
                print(f"  ! Insert error: {e}")
    
    conn.commit()
    
    # Final count
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM violations WHERE violation_type='FDA recall'")
    total = cur.fetchone()[0]
    
    conn.close()
    
    print()
    print("=" * 60)
    print("PIPELINE 2 SUMMARY — FDA Food Enforcement")
    print(f"  Search terms checked:    {checked}")
    print(f"  New records inserted:    {inserted}")
    print(f"  Skipped (duplicates):    {skipped_dup}")
    print(f"  Total FDA recalls in DB: {total}")
    print("=" * 60)

if __name__ == "__main__":
    main()
