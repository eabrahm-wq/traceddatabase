# Traced Database

Data foundation for [Traced](https://tracedhealth.com) — a food transparency database that exposes the gap between what food brands market themselves as and what their parent companies actually do with money, influence, and regulatory behavior.

## Database

`traced.db` — SQLite, ~80MB (not tracked in git, run pipelines locally)

### Schema

| Table | Description |
|---|---|
| `companies` | 60 parent companies (public, private, PE) |
| `brands` | 341 brands with ownership and acquisition data |
| `products` | 190K+ UPC-mapped products |
| `violations` | FDA recalls, USDA recalls, FTC actions, warning letters, EU alerts |
| `lobbying_records` | Annual lobbying spend and flagged issues by company |
| `brand_events` | Timeline events: recalls, acquisitions, reformulations, lawsuits |
| `ingredient_snapshots` | Additive tracking per product |

### Current Data State

- **2,297 violations** across 8 types
- **1,990** FDA food enforcement recalls (Class I & II)
- **214** USDA FSIS meat/poultry recalls
- **35** FDA warning letters
- **21** FTC consumer protection actions ($3.13B in documented fines)
- **21** EU RASFF regulatory alerts (US/EU standard gaps)
- **166** lobbying records (2015–2024, $409M documented spend)
- **1,319** brand timeline events
- **46** brands with acquisition prices filled

## Pipelines

All pipelines live in `pipelines/`. Run them sequentially against `traced.db`:

| File | Source | What it does |
|---|---|---|
| `pipeline1_fda_warning_letters.py` | FDA public records | Inserts documented FDA warning letters for food companies |
| `pipeline2_fda_enforcement.py` | openFDA API | Expands FDA Class I/II recall coverage via brand/firm search |
| `pipeline3_usda_fsis.py` | USDA FSIS API | Fetches all FSIS meat/poultry recalls and matches to companies |
| `pipeline4_ftc_actions.py` | FTC public records | Inserts FTC consumer protection actions and settlements |
| `pipeline5_opensecrets_lobbying.py` | Public LDA data | Annual lobbying spend + issues (GMO labeling, sugar taxes, etc.) |
| `pipeline6_sec_edgar.py` | SEC EDGAR API | Fills missing acquisition prices from 8-K/10-K filings |
| `pipeline7_eu_rasff.py` | RASFF public records | EU regulatory alerts for US-sold products (standard-gap cases) |
| `pipeline8_brand_news.py` | Google News RSS | Brand event refresh for brands with 0 or stale events |

### Running pipelines

```bash
pip install requests
python pipelines/pipeline2_fda_enforcement.py   # uses openFDA (no key needed)
python pipelines/pipeline3_usda_fsis.py         # uses FSIS API (no key needed)
python pipelines/pipeline6_sec_edgar.py         # uses SEC EDGAR (no key needed)
python pipelines/pipeline8_brand_news.py        # uses Google News RSS
```

Pipelines 1, 4, 5, and 7 use curated public-record data (their respective APIs either don't exist or require credentials not publicly available).

## Transparency Lenses

Every data point is mapped to one of four contradiction dimensions:

1. **Corporate accountability** — who owns what, what have they been penalized for
2. **Political influence** — lobbying spend, PAC donations, revolving door
3. **Ingredient integrity** — what changed after acquisition, what's banned elsewhere
4. **Brand contradiction** — brands marketing values their parent company actively works against

## Top Contradiction Profiles

Brands where parent company has documented FTC actions + lobbying opposing brand values:

| Brand | Parent | Acquired | FTC Actions | Lobbying (anti-brand issues) |
|---|---|---|---|---|
| Kashi / bear naked / Morningstar | Kellogg's | 1999–2007 | 4 | GMO labeling, $81M |
| Honest Tea / Odwalla | Coca-Cola | 2001–2011 | 2 | Sugar taxes, $121M |
| Annie's / Cascadian Farm / Larabar | General Mills | 1999–2014 | 2 | GMO labeling, $52M |
| Horizon Organic / Earthbound Farm | Danone | 2013–2016 | 2 | Organic standards, $18M |
| Naked Juice / Tropicana | PepsiCo | 1998–2006 | 2 | Sugar taxes, $103M |
| Applegate / Justin's | Hormel Foods | 2015–2016 | 1 | Antibiotic use, animal welfare |

## Research Gaps (priority targets)

Companies in the DB with **zero violations** that warrant manual research:

- **Unilever** — $60B revenue, 58 brands, major EU enforcement history not yet captured
- **Reckitt Benckiser** — Mead Johnson infant formula WHO Code violations
- **Lactalis** — 2017 French Salmonella infant formula scandal, US import records
- **JBS USA** — COVID-era worker safety record, environmental violations at US plants
- **Church & Dwight** — Vitafusion unsubstantiated supplement claims

## License

Data sourced from US and EU public regulatory databases. Pipeline code MIT licensed.
