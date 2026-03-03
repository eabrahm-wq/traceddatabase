# Traced Database

Data foundation for [Traced](https://tracedhealth.com) — a food transparency database that exposes the gap between what food brands market themselves as and what their parent companies actually do with money, influence, and regulatory behavior.

## Database

`traced.db` — SQLite, ~80MB (not tracked in git, run pipelines locally)

### Schema

| Table | Description |
|---|---|
| `companies` | 60 parent companies (public, private, PE) |
| `brands` | 865 brands with ownership, acquisition data, and contradiction scores |
| `products` | 190K+ UPC-mapped products |
| `violations` | FDA recalls, USDA recalls, FTC actions, warning letters, EU alerts |
| `lobbying_records` | Annual lobbying spend and flagged issues by company |
| `brand_events` | Timeline events: recalls, acquisitions, reformulations, lawsuits |
| `ingredient_snapshots` | Additive tracking per product (101K+ records, 60% with parsed additives) |

### Current Data State

- **2,339 violations** across 10 types
- **1,997** FDA food enforcement recalls (Class I & II)
- **218** USDA FSIS meat/poultry recalls
- **41** FDA warning letters
- **25** FTC consumer protection actions
- **31** EU RASFF regulatory alerts (US/EU standard gaps)
- **218** lobbying records (2012–2024, $481M documented spend)
- **1,319** brand timeline events
- **101,767** ingredient snapshots — 61,044 with additives parsed
- **245** brands with contradiction score ≥ 50

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
| `pipeline9_fill_gaps.py` | Curated public records | Violations for zero-coverage companies (Unilever, Reckitt, Lactalis, JBS, etc.) |
| `pipeline10_lobbying_gaps.py` | Public LDA data | Lobbying records for gap companies |
| `pipeline11_ingredient_snapshots.py` | Regex / ingredient text | Parses additives from ingredients_raw (BHT, Red 40, HFCS, etc.) |
| `pipeline12_contradiction_scores.py` | Derived | Scores each brand 0–100 on corporate contradiction |

### Running pipelines

```bash
pip install requests
python pipelines/pipeline2_fda_enforcement.py   # uses openFDA (no key needed)
python pipelines/pipeline3_usda_fsis.py         # uses FSIS API (no key needed)
python pipelines/pipeline6_sec_edgar.py         # uses SEC EDGAR (no key needed)
python pipelines/pipeline8_brand_news.py        # uses Google News RSS
python pipelines/pipeline11_ingredient_snapshots.py  # local only, no API
python pipelines/pipeline12_contradiction_scores.py  # local only, derived data
```

Pipelines 1, 4, 5, 7, 9, and 10 use curated public-record data (their respective APIs either don't exist or require credentials not publicly available).

### Summary script

```bash
python scripts/summary.py
```

Prints counts, violation breakdown, top contradiction brands, most common additives, and companies by violation count.

## Transparency Lenses

Every data point is mapped to one of four contradiction dimensions:

1. **Corporate accountability** — who owns what, what have they been penalized for
2. **Political influence** — lobbying spend, PAC donations, revolving door
3. **Ingredient integrity** — what changed after acquisition, what's banned elsewhere
4. **Brand contradiction** — brands marketing values their parent company actively works against

## Contradiction Score

Each brand gets a score from 0–100:

| Signal | Points |
|---|---|
| Acquired by major food conglomerate | +20 |
| Parent FTC actions (5 pts each, max 25) | up to +25 |
| Parent lobbied on issues contradicting brand values | +20 |
| Parent total lobbying spend > $50M | +10 |
| Parent Class I recalls (5 pts each, max 15) | up to +15 |
| Brand markets itself as natural/organic/clean | +10 |
| Post-acquisition controversy/reformulation events | up to +5 |

## Top Contradiction Profiles

Brands where parent company has documented FTC actions + lobbying opposing brand values:

| Brand | Parent | Score | Key Contradiction |
|---|---|---|---|
| bear naked | Kellogg's | 95 | Natural/organic brand, parent lobbied against GMO labeling ($81M) |
| Naked Juice / Naked | PepsiCo | 90 | "Natural" claims, parent lobbied against sugar taxes ($103M) |
| Morningstar Farms | Kellogg's | 90 | Plant-based positioning, parent lobbied against food labeling |
| Honest Tea | Coca-Cola | 90 | Mission-driven brand, parent lobbied against sugar taxes ($121M) |
| Kashi | Kellogg's | 85 | Whole grain/natural, parent fought GMO disclosure |
| Horizon Organic | Danone | 80 | Organic dairy, parent lobbied against organic standards |
| Cascadian Farm | General Mills | 80 | Organic, parent lobbied against GMO labeling ($52M) |
| Naked Juice | PepsiCo | 90 | "Nothing to hide" branding, parent fought sugar tax legislation |

## Research Gaps

All previously zero-violation companies have now been filled. Next research priorities:

- **Nestlé** — deepen EU enforcement coverage (PFAS in bottled water, plastics)
- **Tyson Foods** — expand Chesapeake Bay / water quality violations
- **Abbott Nutrition** — 2022 Similac infant formula contamination crisis
- **Perrigo** — infant formula recall history

## License

Data sourced from US and EU public regulatory databases. Pipeline code MIT licensed.
