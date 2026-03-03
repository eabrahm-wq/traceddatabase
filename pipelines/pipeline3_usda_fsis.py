import sqlite3
import requests
import json
import re
from datetime import datetime

DB_PATH = "/Users/evan/Desktop/Traceddatabase/traced.db"
FSIS_URL = "https://www.fsis.usda.gov/fsis/api/recall/v/1"
HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

# Key companies to focus on for meat/poultry
KEY_COMPANIES = {
    "tyson": "Tyson Foods",
    "hillshire": "Tyson Foods",
    "jimmy dean": "Tyson Foods",
    "sara lee": "Tyson Foods",
    "ball park": "Tyson Foods",
    "state fair": "Tyson Foods",
    "hormel": "Hormel Foods",
    "jennie-o": "Hormel Foods",
    "jennie o": "Hormel Foods",
    "skippy": "Hormel Foods",
    "spam": "Hormel Foods",
    "natural choice": "Hormel Foods",
    "austin blues": "Hormel Foods",
    "jbs": "JBS USA",
    "swift": "JBS USA",
    "pilgrim's": "JBS USA",
    "pilgrims": "JBS USA",
    "smithfield": "Smithfield Foods",
    "eckrich": "Smithfield Foods",
    "farmland": "Smithfield Foods",
    "john morrell": "Smithfield Foods",
    "kretschmar": "Smithfield Foods",
    "perdue": "Perdue Farms",
    "coleman natural": "Perdue Farms",
    "niman ranch": "Perdue Farms",
    "kraft": "Kraft Heinz",
    "oscar mayer": "Kraft Heinz",
    "planters": "Kraft Heinz",
    "bob evans": "Post Holdings",
    "conagra": "Conagra Brands",
    "banquet": "Conagra Brands",
    "bertolli": "Conagra Brands",
    "campbell": "Campbell's",
    "pepperidge": "Campbell's",
    "swanson": "Campbell's",
    "nestle": "Nestlé",
    "stouffer": "Nestlé",
    "hot pocket": "Nestlé",
    "lean cuisine": "Nestlé",
    "general mills": "General Mills",
    "progresso": "General Mills",
    "pillsbury": "General Mills",
    "gold medal": "General Mills",
    "kellogg": "Kellogg's",
    "morning star": "Kellogg's",
    "morningstar": "Kellogg's",
    "walmart": "Walmart",
    "great value": "Walmart",
    "kroger": "Kroger",
    "costco": "Costco",
    "kirkland": "Costco",
    "whole foods": "Whole Foods (Amazon)",
    "365": "Whole Foods (Amazon)",
    "trader joe": "Trader Joes",
    "aldi": "Aldi",
}

def get_company_id(conn, company_name):
    cur = conn.cursor()
    cur.execute("SELECT id FROM companies WHERE name=?", (company_name,))
    row = cur.fetchone()
    return row[0] if row else None

def existing_recall_numbers(conn):
    cur = conn.cursor()
    cur.execute("SELECT description FROM violations WHERE violation_type='USDA recall'")
    descs = [row[0] for row in cur.fetchall() if row[0]]
    nums = set()
    for d in descs:
        found = re.findall(r'(?:Recall #|FSIS-RC-)\S+', d)
        nums.update(found)
    return nums

def get_next_id(conn):
    cur = conn.cursor()
    cur.execute("SELECT id FROM violations WHERE id LIKE 'usda-%' ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    if row:
        try:
            n = int(row[0].replace('usda-', ''))
            return f"usda-{n+1:04d}"
        except:
            pass
    return "usda-0001"

def main():
    conn = sqlite3.connect(DB_PATH)
    company_id_cache = {}
    
    # Pre-build company ID cache
    cur = conn.cursor()
    cur.execute("SELECT id, name FROM companies")
    for cid, cname in cur.fetchall():
        company_id_cache[cname] = cid
    
    existing_nums = existing_recall_numbers(conn)
    
    print("Pipeline 3 — USDA FSIS Recalls")
    print(f"Fetching all FSIS recalls from API...")
    
    try:
        r = requests.get(FSIS_URL, headers=HEADERS, timeout=60)
        if r.status_code != 200:
            print(f"  ERROR: Status {r.status_code}")
            return
        recalls = r.json()
        print(f"  Fetched {len(recalls)} total USDA FSIS recalls")
    except Exception as e:
        print(f"  ERROR fetching: {e}")
        return
    
    inserted = 0
    skipped_dup = 0
    skipped_no_match = 0
    company_hits = {}
    
    for recall in recalls:
        title = recall.get("field_title", "")
        establishment = recall.get("field_establishment", "")
        recall_type = recall.get("field_recall_type", "")
        risk_level = recall.get("field_risk_level", "")
        classification = recall.get("field_recall_classification", "")
        recall_date = recall.get("field_recall_date", "")
        recall_number = recall.get("field_recall_number", "")
        reason = recall.get("field_recall_reason", "")
        summary = recall.get("field_summary", "")
        url = recall.get("field_recall_url", "")
        qty = recall.get("field_qty_recovered", "")
        product_items = recall.get("field_product_items", "")
        
        # Determine year
        year = None
        if recall_date:
            try:
                year = int(recall_date[:4])
            except:
                pass
        if not year and recall.get("field_year"):
            try:
                year = int(recall.get("field_year"))
            except:
                pass
        
        # Match to company
        combined = (title + " " + establishment + " " + summary + " " + product_items).lower()
        
        matched_company = None
        matched_company_id = None
        
        for keyword, comp_name in KEY_COMPANIES.items():
            if keyword in combined:
                cid = company_id_cache.get(comp_name)
                if cid:
                    matched_company = comp_name
                    matched_company_id = cid
                    break
        
        if not matched_company_id:
            skipped_no_match += 1
            continue
        
        # Check duplicate
        recall_num_tag = f"Recall #{recall_number}" if recall_number else ""
        if recall_num_tag and recall_num_tag in existing_nums:
            skipped_dup += 1
            continue
        
        # Build description
        # Clean up summary/reason
        clean_reason = re.sub(r'\s+', ' ', reason).strip() if reason else ""
        clean_title = re.sub(r'\s+', ' ', title).strip()
        
        desc_parts = [f"{establishment}: {clean_title}"]
        if clean_reason:
            desc_parts.append(f"Reason: {clean_reason[:200]}")
        if qty:
            desc_parts.append(f"Pounds recalled: {qty}")
        if classification:
            desc_parts.append(f"Class: {classification}")
        if recall_number:
            desc_parts.append(f"Recall #{recall_number}")
        
        desc = " — ".join(desc_parts)
        
        # Get or create ID
        vid = get_next_id(conn)
        cur = conn.cursor()
        cur.execute("SELECT id FROM violations WHERE id=?", (vid,))
        while cur.fetchone():
            n = int(vid.replace("usda-", ""))
            vid = f"usda-{n+1:04d}"
            cur.execute("SELECT id FROM violations WHERE id=?", (vid,))
        
        source = url if url else "https://www.fsis.usda.gov/recalls"
        
        cur.execute("""
            INSERT INTO violations (id, company_id, violation_type, year, description, outcome, fine_amount, source_url)
            VALUES (?, ?, 'USDA recall', ?, ?, 'Recall Issued', NULL, ?)
        """, (vid, matched_company_id, year, desc[:1000], source))
        
        if recall_num_tag:
            existing_nums.add(recall_num_tag)
        inserted += 1
        company_hits[matched_company] = company_hits.get(matched_company, 0) + 1
    
    conn.commit()
    
    print()
    print("Recalls by company:")
    for company, count in sorted(company_hits.items(), key=lambda x: -x[1]):
        print(f"  {company}: {count}")
    
    print()
    print("=" * 60)
    print("PIPELINE 3 SUMMARY — USDA FSIS Recalls")
    print(f"  Total FSIS recalls fetched:    {len(recalls)}")
    print(f"  Matched & inserted:            {inserted}")
    print(f"  Skipped (no company match):    {skipped_no_match}")
    print(f"  Skipped (duplicates):          {skipped_dup}")
    print("=" * 60)
    
    conn.close()

if __name__ == "__main__":
    main()
