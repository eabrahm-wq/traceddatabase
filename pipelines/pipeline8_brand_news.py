import sqlite3
import requests
import time
import json
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from urllib.parse import quote

DB_PATH = "/Users/evan/Desktop/Traceddatabase/traced.db"

def get_brands_needing_refresh(conn, days_threshold=90):
    """Get brands with 0 events OR last event older than threshold."""
    cutoff_date = (datetime.now() - timedelta(days=days_threshold)).strftime('%Y-%m-%d')
    cur = conn.cursor()
    cur.execute("""
        SELECT b.id, b.name, c.name as parent_name, 
               COUNT(be.id) as event_count, 
               MAX(be.event_date) as last_event
        FROM brands b
        JOIN companies c ON b.parent_company_id = c.id
        LEFT JOIN brand_events be ON be.brand_id = b.id
        GROUP BY b.id
        HAVING event_count = 0 OR last_event < ? OR last_event IS NULL
        ORDER BY c.name, b.name
    """, (cutoff_date,))
    return cur.fetchall()

def get_existing_headlines(conn):
    cur = conn.cursor()
    cur.execute("SELECT headline FROM brand_events WHERE headline IS NOT NULL")
    return set(row[0] for row in cur.fetchall())

def fetch_google_news_rss(brand_name, query_suffix="recall OR lawsuit OR acquired OR reformulated OR controversy"):
    """Fetch Google News RSS for a brand."""
    query = f'"{brand_name}" {query_suffix}'
    encoded = quote(query)
    url = f"https://news.google.com/rss/search?q={encoded}&hl=en-US&gl=US&ceid=US:en"
    
    headers = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    
    try:
        r = requests.get(url, headers=headers, timeout=15)
        if r.status_code == 200:
            return r.content
        return None
    except Exception as e:
        return None

def parse_rss_items(content, brand_name):
    """Parse RSS feed items."""
    if not content:
        return []
    
    items = []
    try:
        root = ET.fromstring(content)
        channel = root.find('channel')
        if not channel:
            return []
        
        for item in channel.findall('item'):
            title = item.findtext('title', '').strip()
            link = item.findtext('link', '').strip()
            pub_date = item.findtext('pubDate', '').strip()
            description = item.findtext('description', '').strip()
            
            if not title or not link:
                continue
            
            # Parse date
            event_date = None
            if pub_date:
                try:
                    # Try to parse various date formats
                    for fmt in ['%a, %d %b %Y %H:%M:%S %Z', '%a, %d %b %Y %H:%M:%S %z']:
                        try:
                            dt = datetime.strptime(pub_date, fmt)
                            event_date = dt.strftime('%Y-%m-%d')
                            break
                        except:
                            pass
                except:
                    pass
            
            # Clean description (remove HTML tags)
            clean_desc = re.sub(r'<[^>]+>', '', description).strip()
            clean_title = re.sub(r'<[^>]+>', '', title).strip()
            
            items.append({
                'title': clean_title,
                'link': link,
                'date': event_date,
                'description': clean_desc[:500]
            })
    except Exception as e:
        pass
    
    return items

def classify_event(title, description):
    """Classify the event type based on title/description."""
    text = (title + " " + description).lower()
    
    if any(kw in text for kw in ['recall', 'withdrawn', 'contaminate', 'listeria', 'salmonella', 'e. coli', 'allergen']):
        return 'recall'
    elif any(kw in text for kw in ['lawsuit', 'suit', 'court', 'settlement', 'legal action', 'ftc', 'class action', 'fine', 'penalty']):
        return 'violation'
    elif any(kw in text for kw in ['acquired', 'acquisition', 'bought', 'purchase', 'merger', 'sold to', 'takeover']):
        return 'acquisition'
    elif any(kw in text for kw in ['reformulat', 'new recipe', 'ingredients changed', 'updated formula', 'new formula', 'removed', 'added']):
        return 'reformulation'
    elif any(kw in text for kw in ['discontinued', 'ending production', 'shut down', 'closing', 'pulling from shelves']):
        return 'discontinuation'
    elif any(kw in text for kw in ['controversy', 'backlash', 'criticism', 'protest', 'boycott', 'outrage']):
        return 'controversy'
    else:
        return 'news'

def is_noise(title, brand_name):
    """Filter out noise - stock news, unrelated companies, etc."""
    title_lower = title.lower()
    brand_lower = brand_name.lower()
    
    # Skip pure stock/financial news
    financial_keywords = ['stock price', 'shares up', 'shares down', 'earnings per share', 
                         'quarterly results', 'analyst rating', 'target price', 'market cap',
                         'investor', 'dividend', 'IPO', 'trading at']
    if any(kw.lower() in title_lower for kw in financial_keywords):
        return True
    
    # Skip if brand name not clearly in title (false positives)
    if len(brand_lower) > 4 and brand_lower not in title_lower:
        # Check for partial match
        brand_words = brand_lower.split()
        if not any(word in title_lower for word in brand_words if len(word) > 3):
            return True
    
    return False

def get_next_event_id(conn):
    cur = conn.cursor()
    cur.execute("SELECT id FROM brand_events WHERE id LIKE 'be-%' ORDER BY id DESC LIMIT 1")
    row = cur.fetchone()
    if row:
        try:
            n = int(row[0].replace('be-', ''))
            return f"be-{n+1:04d}"
        except:
            pass
    cur.execute("SELECT COUNT(*) FROM brand_events")
    n = cur.fetchone()[0]
    return f"be-{n+1:04d}"

def insert_event(conn, brand_id, event_type, event_date, headline, description, source_url):
    vid = get_next_event_id(conn)
    cur = conn.cursor()
    cur.execute("SELECT id FROM brand_events WHERE id=?", (vid,))
    while cur.fetchone():
        n = int(vid.replace("be-", ""))
        vid = f"be-{n+1:04d}"
        cur.execute("SELECT id FROM brand_events WHERE id=?", (vid,))
    
    cur.execute("""
        INSERT INTO brand_events (id, brand_id, event_type, event_date, headline, description, source_url, verified)
        VALUES (?, ?, ?, ?, ?, ?, ?, 0)
    """, (vid, brand_id, event_type, event_date, headline[:500], description[:1000], source_url))

def main():
    conn = sqlite3.connect(DB_PATH)
    
    brands = get_brands_needing_refresh(conn, days_threshold=90)
    existing_headlines = get_existing_headlines(conn)
    
    print(f"Pipeline 8 — Brand News Refresh")
    print(f"Brands needing refresh (0 events or >90 days old): {len(brands)}")
    print()
    
    inserted = 0
    skipped_dup = 0
    skipped_noise = 0
    brands_checked = 0
    brands_with_news = 0
    
    # Limit to top priority brands - first 80 to avoid too many requests
    priority_brands = brands[:80]
    
    for brand_id, brand_name, parent_name, event_count, last_event in priority_brands:
        brands_checked += 1
        
        # Fetch news RSS
        rss_content = fetch_google_news_rss(brand_name)
        time.sleep(1.2)  # Rate limit: stay under Google's limits
        
        if not rss_content:
            continue
        
        items = parse_rss_items(rss_content, brand_name)
        
        if not items:
            continue
        
        brand_inserted = 0
        for item in items[:15]:  # Limit per brand
            title = item['title']
            link = item['link']
            date = item['date']
            desc = item['description']
            
            # Skip noise
            if is_noise(title, brand_name):
                skipped_noise += 1
                continue
            
            # Must have a source URL
            if not link:
                continue
            
            # Skip duplicates by headline
            if title in existing_headlines:
                skipped_dup += 1
                continue
            
            # Also check partial match to avoid near-duplicates
            title_words = set(title.lower().split())
            is_dup = False
            for existing in existing_headlines:
                existing_words = set(existing.lower().split())
                overlap = len(title_words & existing_words)
                if overlap > len(title_words) * 0.8 and len(title_words) > 5:
                    is_dup = True
                    break
            
            if is_dup:
                skipped_dup += 1
                continue
            
            # Classify event
            event_type = classify_event(title, desc)
            
            # Use current year if no date found
            if not date:
                date = "2024-01-01"  # Default to recent
            
            try:
                insert_event(conn, brand_id, event_type, date, title, desc, link)
                existing_headlines.add(title)
                inserted += 1
                brand_inserted += 1
            except Exception as e:
                pass
        
        if brand_inserted > 0:
            brands_with_news += 1
            print(f"  [{parent_name}] {brand_name}: +{brand_inserted} events")
    
    conn.commit()
    
    # Final count
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) FROM brand_events")
    total_events = cur.fetchone()[0]
    
    conn.close()
    
    print()
    print("=" * 60)
    print("PIPELINE 8 SUMMARY — Brand News Refresh")
    print(f"  Brands checked:          {brands_checked}")
    print(f"  Brands with new events:  {brands_with_news}")
    print(f"  New events inserted:     {inserted}")
    print(f"  Skipped (duplicates):    {skipped_dup}")
    print(f"  Skipped (noise/stock):   {skipped_noise}")
    print(f"  Total brand events in DB: {total_events}")
    print("=" * 60)

if __name__ == "__main__":
    main()
