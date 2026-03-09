# Traced Maps — Claude Code Context

This file is automatically loaded by Claude Code at startup. Keep it up to date.

## What Is This

**Traced Maps** — a Chrome extension that overlays corporate ownership data on Google Maps (and eventually Yelp, DoorDash, OpenTable). Backend is Flask/SQLite.

## Environment

- Mac (ARM), Python 3.9 at `/Library/Frameworks/Python.framework/Versions/3.9/bin/python3` or `/Library/Developer/CommandLineTools/usr/bin/python3`
- Flask app: `~/Desktop/traceddatabase/traced_app.py` — **port 5001** (never 5000)
- Database: `~/Desktop/traceddatabase/traced.db` (80MB, Git LFS tracked)
- Chrome extension: `~/Desktop/traceddatabase/chrome-extension/`
- rapidfuzz 3.13.0 at `/Users/evan/Library/Python/3.9/`
- GitHub: `https://github.com/eabrahm-wq/traceddatabase.git`
- Active branch: `claude/bold-johnson` (PR #1 open against main)

## Critical Variable Names

- DB variable in `traced_app.py` is `DB` (not `DB_PATH`)
- Flask port is **5001**

## Session Startup Checklist

```bash
cd ~/Desktop/traceddatabase
pkill -f traced_app && python3 traced_app.py &
curl http://localhost:5001/api/lookup?name=Blue+Bottle+Coffee  # verify working
curl http://localhost:5001/api/resolver/misses                 # check gaps
git status                                                      # check uncommitted
```

## Git Workflow

- **Always work in the worktree**: `.claude/worktrees/bold-johnson/` (branch: `claude/bold-johnson`)
- **traced.db is Git LFS** — always `git add traced.db` explicitly before commit
- **Never git reset --hard on main** — it wipes LFS files from disk
- After every meaningful DB change: `git add traced.db && git commit -m "..." && git push origin claude/bold-johnson`
- PR #1: `https://github.com/eabrahm-wq/traceddatabase/pull/1`

## Architecture

### Geo-Entity Resolver (`traced_resolver.py`)
- `normalize()` — strips punctuation, location suffixes (SF/San Francisco/etc), legal suffixes (LLC/Inc/Corp/Co./Ltd/Group/Holdings), lowercases, removes possessives
- `resolve()` — 3-pass: (1) exact alias match, (2) rapidfuzz fuzzy ≥88, (3) partial/contains (min 8 chars)
- Logs misses to `resolver_misses` table
- Key: `brand_aliases.alias_text` must be the **normalized** form

### Flask API
- `GET /api/lookup?name=&surface=` — full brand JSON with parent_record
- `GET /api/nearby?category=&price_tier=&format=&limit=` — verified indie local_vendors
- `GET /api/resolver/misses` — unmatched lookups
- All routes: `Access-Control-Allow-Origin: *`

### Chrome Extension (MV3)
- `content/google_maps.js` — v5, full panel UI
- `content/overlay.css` — dark theme
- Panel sections: compact row → teaser → OWNERSHIP CHAIN → ORIGIN/FOUNDER STORY → WHY THIS MATTERS (indie only) → PARENT COMPANY RECORD → INGREDIENT DRIFT → BETTER NEARBY → Actions
- `IGNORE_PATTERNS` filters SF street/neighborhood names
- 600ms debounce on MutationObserver
- In-memory cache per tab (cache bust `&v=3`)
- Reload: `chrome://extensions` → refresh icon (do NOT re-load unpacked)

## Database Schema (Key Tables)

### brands
```
id TEXT PK, name TEXT, slug TEXT, parent_company_id TEXT (FK→companies.id)
category TEXT, format TEXT (cafe/fast_casual/sit_down/market/pharmacy)
price_tier INTEGER (1=$  2=$$  3=$$$  4=$$$$)
independent BOOLEAN, pe_owned BOOLEAN
founded_year, acquired_year, acquisition_price
overall_zone TEXT (green=independent, yellow=public/private chain, red=PE/corporate)
headline_finding TEXT, share_text TEXT, founder_story TEXT
ingredient_drift BOOLEAN, ingredient_drift_note TEXT
watch_list INTEGER
```

### companies
```
id TEXT PK, name TEXT, type TEXT (conglomerate/public/pe/private)
ticker TEXT, hq_country TEXT, annual_revenue INTEGER
violation_count INTEGER, violation_summary TEXT
lobbying_annual INTEGER, lobbying_issues TEXT
description TEXT
```

### brand_aliases
```
alias_text TEXT (normalized!), brand_id TEXT (FK→brands.id), source TEXT
```

### local_vendors
```
id TEXT PK, name TEXT, category TEXT, format TEXT, price_tier INTEGER
neighborhood TEXT, note TEXT, slug TEXT, verified INTEGER (1=active 0=excluded)
years_open INTEGER, local_jobs INTEGER, community_note TEXT, sourcing_note TEXT
```

## DB Current State (as of last seed)
- **149 brands** with category data
- **117 companies** with violation/lobbying data
- **60 verified local_vendors** (Better Nearby pool)
- **301 brand aliases**

## Key Brand → Company Mappings
- `mcdonalds` → `mcdonalds-corp` (42 violations, $7.2M/yr lobbying)
- `burger-king`, `tim-hortons` → `rbi` (3G Capital)
- `taco-bell`, `kfc` → `yum-brands`
- `dunkin` → `inspire-brands` (Roark Capital)
- `panera-bread` → `roark-capital`
- `subway` → `subway-restaurants` (Roark Capital acquired 2023)
- `starbucks` → `starbucks-corp` (26 violations, $4.6M/yr)
- `whole-foods` → `amazon-corp` (31 violations, $21M/yr)
- `safeway` → `albertsons` (Cerberus Capital)
- `trader-joes` → `aldi-group` (Albrecht family, private) — zone=yellow

## zone Rules
- `green` — independent/community-owned, founder still in control
- `yellow` — public company OR private family chain (not PE)
- `red` — PE-backed OR conglomerate-owned

## Useful Commands

```bash
# Test resolver
python3 -c "from traced_resolver import resolve; print(resolve('Blue Bottle Coffee'))"

# Add alias
python3 -c "from traced_resolver import add_alias; add_alias('dutch bros coffee', 'dutch-bros')"

# Check misses
curl http://localhost:5001/api/resolver/misses

# Restart Flask
pkill -f traced_app && sleep 1 && python3 traced_app.py &

# Test lookup
curl "http://localhost:5001/api/lookup?name=McDonalds"
curl "http://localhost:5001/api/lookup?name=In-N-Out+Burger"

# DB quick check
python3 -c "import sqlite3; c=sqlite3.connect('traced.db').cursor(); c.execute('SELECT COUNT(*) FROM brands WHERE category IS NOT NULL'); print(c.fetchone())"
```

## Deployment Status
- **Deferred** — Railway doesn't support Git LFS (84MB traced.db)
- Options: pg dump to Postgres, or Render with persistent disk
- Local dev only for now

## Roadmap (priority order)
1. ✅ Geo-entity resolver
2. ✅ Flask API (lookup + nearby + misses)
3. ✅ Google Maps panel UI (v5 with WHY THIS MATTERS + Better Nearby)
4. ✅ Seed: 100+ SF restaurants, 50+ coffee, all major chains, grocery
5. 🔄 **IN PROGRESS**: Add fast food chains + SF indie brands (see below)
6. ⬜ Yelp surface (`content/yelp.js`)
7. ⬜ Extension popup (`popup.html`)
8. ⬜ Deployment (Render + Postgres)

## Current Task: Brands to Add

### Fast Food Chains (need brand records — companies already exist)
| Brand | Company ID | Zone |
|---|---|---|
| Subway | `subway-restaurants` | red |
| In-N-Out | `in-n-out` | yellow |
| Five Guys | `five-guys` | yellow |
| Wingstop | `wingstop-corp` | yellow |
| Dutch Bros | `dutch-bros` | yellow |
| Chick-fil-A | `chick-fil-a` | yellow |
| Domino's | `dominos-corp` (needs creating) | yellow |
| Papa John's | `papa-johns-corp` (needs creating) | red |

### Companies to Create
- `dominos-corp` — Domino's Pizza Inc. (public NYSE:DPZ)
- `papa-johns-corp` — Papa John's International (Starboard Value PE)

### SF Independents to Add (brand + local_vendor)
- Humphry Slocombe (ice cream, tier 2, fast_casual) — Jake Godby + Sean Vahey, SF 2008
- Bi-Rite Creamery (ice cream, tier 2, fast_casual) — Bi-Rite family, SF 2006
- Tartine Bakery ORIGINAL (cafe, tier 2) — Chad Robertson + Liz Prueitt, SF 2002, NOT Tartine Manufactory
- Wise Sons Jewish Deli (fast_casual, tier 2) — SF 2011
- The Interval at Long Now (cafe/bar, tier 2, sit_down) — Fort Mason, nonprofit
- 20th Century Café (cafe, tier 2) — Michelle Polzine, SF Hayes Valley, Eastern European
- Cockscomb (sit_down, tier 3) — Chris Cosentino, SF SoMa

### Existing Brands Needing More Aliases (≥3 required)
mcdonalds, burger-king, taco-bell, kfc, wendys, dunkin, tim-hortons, burma-superstar, dandelion-chocolate, equator-coffees, flour-water-sf, lazy-bear-sf, nopa-brand, nopalito-sf, rich-table-sf, state-bird-brand, zuni-cafe-brand, foreign-cinema-brand

## Data Quality Rules
- `brand_aliases.alias_text` = always normalized (run through `normalize()`)
- `INSERT OR IGNORE` for all inserts
- Min 3 aliases per brand
- Never use a name string as parent_company_id — always use `companies.id`
- Independents: `independent=1, pe_owned=0, parent_company_id=NULL`
- All independents added to `local_vendors` with `verified=1`
