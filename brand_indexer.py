#!/usr/bin/env python3
"""
brand_indexer.py — TracedHealth brand research pipeline
Queries Wikidata, Google News, FDA, Open Food Facts.
Synthesizes with Claude API (falls back to minimal profile).
Saves to brand_drafts table + ./drafts/<slug>.draft.json
"""

import argparse
import json
import os
import re
import sqlite3
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from pathlib import Path
from urllib.parse import quote_plus, urlencode
from urllib.request import urlopen, Request
from urllib.error import HTTPError, URLError

ANTHROPIC_AVAILABLE = False
try:
    import anthropic
    ANTHROPIC_AVAILABLE = True
except ImportError:
    pass

DB_PATH = os.path.join(os.path.dirname(__file__), 'traced.db')
DRAFTS_DIR = os.path.join(os.path.dirname(__file__), 'drafts')


# ── DB ────────────────────────────────────────────────────────────────────────

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS brand_drafts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            slug TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            profile_json TEXT,
            review_status TEXT DEFAULT 'draft',
            created_at TEXT,
            reviewed_at TEXT,
            reviewer_notes TEXT
        )
    ''')
    conn.commit()
    conn.close()
    print('[db] brand_drafts table ready')


# ── SLUG ──────────────────────────────────────────────────────────────────────

def to_slug(name):
    s = name.lower().strip()
    s = re.sub(r'[^a-z0-9]+', '-', s)
    s = s.strip('-')
    return s


# ── WIKIDATA ──────────────────────────────────────────────────────────────────

def _wd_get(url):
    req = Request(url, headers={'User-Agent': 'TracedHealthIndexer/1.0'})
    with urlopen(req, timeout=10) as r:
        return json.loads(r.read().decode())


def fetch_wikidata(brand_name):
    result = {'parent_company': None, 'founded_year': None, 'country': None, 'qid': None}
    try:
        # 1. search for QID
        search_url = (
            'https://www.wikidata.org/w/api.php?action=wbsearchentities'
            '&search=' + quote_plus(brand_name) +
            '&language=en&limit=3&format=json'
        )
        data = _wd_get(search_url)
        if not data.get('search'):
            return result
        qid = data['search'][0]['id']
        result['qid'] = qid

        # 2. fetch entity claims
        entity_url = 'https://www.wikidata.org/wiki/Special:EntityData/' + qid + '.json'
        entity = _wd_get(entity_url)
        claims = entity.get('entities', {}).get(qid, {}).get('claims', {})

        # P749 = parent organization, P127 = owned by
        for prop in ('P749', 'P127'):
            if prop in claims:
                try:
                    parent_qid = claims[prop][0]['mainsnak']['datavalue']['value']['id']
                    parent_url = 'https://www.wikidata.org/wiki/Special:EntityData/' + parent_qid + '.json'
                    parent_entity = _wd_get(parent_url)
                    parent_labels = parent_entity.get('entities', {}).get(parent_qid, {}).get('labels', {})
                    result['parent_company'] = parent_labels.get('en', {}).get('value')
                    break
                except (KeyError, IndexError):
                    pass

        # P571 = inception (founding year)
        if 'P571' in claims:
            try:
                time_str = claims['P571'][0]['mainsnak']['datavalue']['value']['time']
                year_match = re.search(r'\+(\d{4})', time_str)
                if year_match:
                    result['founded_year'] = int(year_match.group(1))
            except (KeyError, IndexError):
                pass

        # P17 = country
        if 'P17' in claims:
            try:
                country_qid = claims['P17'][0]['mainsnak']['datavalue']['value']['id']
                country_url = 'https://www.wikidata.org/wiki/Special:EntityData/' + country_qid + '.json'
                country_entity = _wd_get(country_url)
                country_labels = country_entity.get('entities', {}).get(country_qid, {}).get('labels', {})
                result['country'] = country_labels.get('en', {}).get('value')
            except (KeyError, IndexError):
                pass

    except Exception as e:
        print(f'  [wikidata] error: {e}')

    return result


# ── GOOGLE NEWS RSS ───────────────────────────────────────────────────────────

def fetch_news(brand_name, max_items=8):
    headlines = []
    try:
        q = quote_plus('"' + brand_name + '"')
        url = f'https://news.google.com/rss/search?q={q}&hl=en-US&gl=US&ceid=US:en'
        req = Request(url, headers={'User-Agent': 'TracedHealthIndexer/1.0'})
        with urlopen(req, timeout=10) as r:
            raw = r.read()
        try:
            root = ET.fromstring(raw)
            items = root.findall('.//item')
            for item in items[:max_items]:
                title = item.findtext('title', '')
                pub = item.findtext('pubDate', '')
                source_el = item.find('{https://news.google.com/rss}source')
                source = source_el.text if source_el is not None else ''
                if title:
                    headlines.append({'title': title, 'pub_date': pub, 'source': source})
        except ET.ParseError:
            # fallback: regex
            for m in re.finditer(r'<title><!\[CDATA\[(.*?)\]\]>', raw.decode('utf-8', errors='replace')):
                headlines.append({'title': m.group(1), 'pub_date': '', 'source': ''})
                if len(headlines) >= max_items:
                    break
    except Exception as e:
        print(f'  [news] error: {e}')
    return headlines


# ── FDA ───────────────────────────────────────────────────────────────────────

def fetch_fda(brand_name):
    recalls = []
    try:
        q = quote_plus(f'recalling_firm:"{brand_name}"')
        url = f'https://api.fda.gov/food/enforcement.json?search={q}&limit=5'
        req = Request(url, headers={'User-Agent': 'TracedHealthIndexer/1.0'})
        try:
            with urlopen(req, timeout=10) as r:
                data = json.loads(r.read().decode())
            for result in data.get('results', []):
                recalls.append({
                    'reason': result.get('reason_for_recall', ''),
                    'date': result.get('recall_initiation_date', ''),
                    'classification': result.get('classification', ''),
                    'product': result.get('product_description', '')
                })
        except HTTPError as e:
            if e.code != 404:
                print(f'  [fda] HTTP {e.code}')
    except Exception as e:
        print(f'  [fda] error: {e}')
    return recalls


# ── OPEN FOOD FACTS ───────────────────────────────────────────────────────────

def fetch_off(brand_name, max_products=5):
    products = []
    try:
        params = urlencode({
            'action': 'process',
            'brands': brand_name,
            'json': '1',
            'page_size': max_products,
            'fields': 'product_name,brands,ingredients_text,additives_tags,nova_group,nutriscore_grade,labels_tags'
        })
        url = f'https://world.openfoodfacts.org/cgi/search.pl?{params}'
        req = Request(url, headers={'User-Agent': 'TracedHealthIndexer/1.0'})
        with urlopen(req, timeout=15) as r:
            data = json.loads(r.read().decode())
        for p in data.get('products', [])[:max_products]:
            products.append({
                'name': p.get('product_name', ''),
                'ingredients': (p.get('ingredients_text') or '')[:300],
                'additives': p.get('additives_tags', [])[:10],
                'nova_group': p.get('nova_group'),
                'nutriscore': p.get('nutriscore_grade'),
                'labels': [l.replace('en:', '') for l in (p.get('labels_tags') or [])[:5]]
            })
    except Exception as e:
        print(f'  [off] error: {e}')
    return products


# ── RESEARCH SUMMARY ──────────────────────────────────────────────────────────

def build_research_summary(brand_name, wiki, news, fda, off):
    lines = [f'Brand: {brand_name}']

    if wiki.get('parent_company'):
        lines.append(f'Parent company (Wikidata): {wiki["parent_company"]}')
    if wiki.get('founded_year'):
        lines.append(f'Founded: {wiki["founded_year"]}')
    if wiki.get('country'):
        lines.append(f'Country: {wiki["country"]}')

    if news:
        lines.append('\nRecent news headlines:')
        for h in news[:5]:
            src = f' [{h["source"]}]' if h.get('source') else ''
            lines.append(f'- {h["title"]}{src}')

    if fda:
        lines.append(f'\nFDA recalls ({len(fda)} found):')
        for r in fda[:3]:
            lines.append(f'- {r["date"]}: {r["reason"][:120]} [{r["classification"]}]')
    else:
        lines.append('\nFDA recalls: none found')

    if off:
        lines.append(f'\nOpen Food Facts products ({len(off)} found):')
        for p in off[:3]:
            name = p.get('name', 'unknown')
            nova = f'NOVA {p["nova_group"]}' if p.get('nova_group') else ''
            nutri = f'Nutriscore {p["nutriscore"].upper()}' if p.get('nutriscore') else ''
            add_count = len(p.get('additives', []))
            parts = [x for x in [nova, nutri, f'{add_count} additives' if add_count else ''] if x]
            lines.append(f'- {name}: {", ".join(parts)}')

    return '\n'.join(lines)


# ── CLAUDE SYNTHESIS ──────────────────────────────────────────────────────────

SYNTHESIS_PROMPT = '''You are a factual research analyst for a consumer health transparency platform.
Given raw research data about a brand, produce a structured JSON profile.
Be objective and factual. No marketing language. No scores or verdicts.
If data is insufficient for a field, use null.

Return ONLY valid JSON (no markdown fences, no commentary) with this exact structure:
{
  "name": "Brand Name",
  "slug": "brand-name",
  "category": "supplements|food|beverage|personal-care|other",
  "parent_company": null or "Company Name",
  "founded_year": null or 1234,
  "hq_country": null or "Country",
  "ownership_notes": "brief factual note about ownership structure",
  "product_summary": "1-2 sentence objective description of what the brand makes",
  "ingredient_notes": "factual notes on ingredient patterns observed, or null",
  "regulatory_history": "factual summary of any FDA actions, or 'No FDA enforcement actions found'",
  "recent_news_summary": "brief factual summary of recent coverage, or null",
  "key_findings": ["finding 1", "finding 2"],
  "data_sources": ["wikidata", "google_news", "fda", "open_food_facts"],
  "research_completeness": "full|partial|minimal"
}

Research data:
'''


def synthesize_with_claude(brand_name, research_text):
    if not ANTHROPIC_AVAILABLE:
        return None
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print('  [claude] ANTHROPIC_API_KEY not set, using fallback')
        return None
    try:
        client = anthropic.Anthropic(api_key=api_key)
        msg = client.messages.create(
            model='claude-haiku-4-5-20251001',
            max_tokens=1600,
            messages=[{'role': 'user', 'content': SYNTHESIS_PROMPT + research_text}]
        )
        text = msg.content[0].text.strip()
        # strip markdown fences if present
        text = re.sub(r'^```(?:json)?\s*', '', text)
        text = re.sub(r'\s*```$', '', text)
        profile = json.loads(text)
        return profile
    except Exception as e:
        print(f'  [claude] synthesis error: {e}')
        return None


def fallback_profile(brand_name, slug, wiki, fda):
    return {
        'name': brand_name,
        'slug': slug,
        'category': 'other',
        'parent_company': wiki.get('parent_company'),
        'founded_year': wiki.get('founded_year'),
        'hq_country': wiki.get('country'),
        'ownership_notes': None,
        'product_summary': None,
        'ingredient_notes': None,
        'regulatory_history': f'{len(fda)} FDA enforcement action(s) found' if fda else 'No FDA enforcement actions found',
        'recent_news_summary': None,
        'key_findings': [],
        'data_sources': ['wikidata', 'google_news', 'fda', 'open_food_facts'],
        'research_completeness': 'minimal'
    }


# ── PROCESS BRAND ─────────────────────────────────────────────────────────────

def process_brand(brand_name, output_dir, force=False):
    slug = to_slug(brand_name)
    draft_path = os.path.join(output_dir, slug + '.draft.json')

    if os.path.exists(draft_path) and not force:
        print(f'[skip] {brand_name} — draft exists ({draft_path})')
        return slug, None

    print(f'\n[index] {brand_name} (slug: {slug})')

    print('  fetching wikidata...')
    wiki = fetch_wikidata(brand_name)
    print(f'    parent={wiki["parent_company"]} founded={wiki["founded_year"]} country={wiki["country"]}')

    print('  fetching news...')
    news = fetch_news(brand_name)
    print(f'    {len(news)} headlines')

    print('  fetching FDA...')
    fda = fetch_fda(brand_name)
    print(f'    {len(fda)} recalls')

    print('  fetching Open Food Facts...')
    off = fetch_off(brand_name)
    print(f'    {len(off)} products')

    research_text = build_research_summary(brand_name, wiki, news, fda, off)

    print('  synthesizing with Claude...')
    profile = synthesize_with_claude(brand_name, research_text)
    if profile is None:
        print('  using fallback profile')
        profile = fallback_profile(brand_name, slug, wiki, fda)

    # ensure slug is consistent
    profile['slug'] = slug
    profile['name'] = brand_name

    # attach raw research for human review
    draft = {
        'profile': profile,
        'raw': {
            'wikidata': wiki,
            'news': news,
            'fda': fda,
            'open_food_facts': off,
            'research_text': research_text
        },
        'indexed_at': datetime.utcnow().isoformat() + 'Z'
    }

    os.makedirs(output_dir, exist_ok=True)
    with open(draft_path, 'w') as f:
        json.dump(draft, f, indent=2)
    print(f'  saved draft → {draft_path}')

    # save to DB
    conn = get_conn()
    c = conn.cursor()
    c.execute('''
        INSERT INTO brand_drafts (slug, name, profile_json, review_status, created_at)
        VALUES (?, ?, ?, 'draft', ?)
        ON CONFLICT(slug) DO UPDATE SET
            profile_json=excluded.profile_json,
            created_at=excluded.created_at,
            review_status='draft'
    ''', (slug, brand_name, json.dumps(profile), datetime.utcnow().isoformat()))
    conn.commit()
    conn.close()
    print(f'  saved to DB (review_status=draft)')

    return slug, profile


# ── MAIN ──────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description='TracedHealth brand indexer')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--brand', help='Single brand name to index')
    group.add_argument('--list', dest='list_file', help='Path to file with one brand per line')
    parser.add_argument('--output', default=DRAFTS_DIR, help='Output directory for draft JSON files')
    parser.add_argument('--delay', type=float, default=4.0, help='Seconds between brands (default 4)')
    parser.add_argument('--force', action='store_true', help='Re-index even if draft already exists')

    args = parser.parse_args()

    init_db()
    os.makedirs(args.output, exist_ok=True)

    brands = []
    if args.brand:
        brands = [args.brand]
    else:
        with open(args.list_file) as f:
            brands = [line.strip() for line in f if line.strip() and not line.startswith('#')]

    print(f'\n=== TracedHealth Brand Indexer ===')
    print(f'Brands to index: {len(brands)}')
    print(f'Output: {args.output}')
    print(f'Claude available: {ANTHROPIC_AVAILABLE}')
    print(f'API key set: {bool(os.environ.get("ANTHROPIC_API_KEY"))}')
    print()

    results = []
    for i, brand_name in enumerate(brands):
        slug, profile = process_brand(brand_name, args.output, force=args.force)
        results.append({'brand': brand_name, 'slug': slug, 'ok': profile is not None})
        if i < len(brands) - 1:
            time.sleep(args.delay)

    print(f'\n=== Done ===')
    print(f'Processed: {len(results)}')
    ok = sum(1 for r in results if r['ok'])
    skipped = sum(1 for r in results if not r['ok'])
    print(f'Indexed: {ok}  Skipped (already exist): {skipped}')
    for r in results:
        status = 'OK' if r['ok'] else 'SKIPPED'
        print(f'  [{status}] {r["brand"]} → {r["slug"]}')


if __name__ == '__main__':
    main()
