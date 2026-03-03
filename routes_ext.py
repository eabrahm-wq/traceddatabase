"""
routes_ext.py — Extended routes for Traced
Registers: /contradiction, /transparency, /brand/<slug>, /scan,
           /share/text/<slug>, /share/card/<slug>, /api/docs,
           /widget/<slug>, /embed.js, /api/brands, /api/companies, /api/stats
"""
import json, os, re, sqlite3
from flask import request, jsonify, Response

BASE = os.path.dirname(os.path.abspath(__file__))
DB   = os.path.join(BASE, 'traced.db')

BG    = '#0a0906'
AMBER = '#d4952a'
RED   = '#c44444'
GREEN = '#3a8a5a'
INK   = '#f0ead8'
MUTED = 'rgba(240,234,216,0.4)'
SURF  = '#121009'
BDR   = 'rgba(255,255,255,0.06)'
B2    = 'rgba(255,255,255,0.12)'

FONTS = (
    "<link href='https://fonts.googleapis.com/css2?"
    "family=Bebas+Neue&family=DM+Mono:wght@300;400;500"
    "&family=Playfair+Display:ital,wght@0,700;1,400&display=swap' rel='stylesheet'>"
)
BASE_CSS = (
    ":root{--bg:#0a0906;--surface:#121009;--s2:#1a1710;"
    "--border:rgba(255,255,255,0.06);--b2:rgba(255,255,255,0.12);"
    "--ink:#f0ead8;--muted:rgba(240,234,216,0.4);"
    "--amber:#d4952a;--alt:rgba(212,149,42,0.12);"
    "--red:#c44444;--rlt:rgba(196,68,68,0.1);"
    "--green:#3a8a5a;--glt:rgba(58,138,90,0.1)}"
    "*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}"
    "body{background:var(--bg);color:var(--ink);font-family:'DM Mono',monospace;min-height:100vh}"
    "nav{border-bottom:1px solid var(--b2);padding:16px 40px;display:flex;"
    "align-items:center;justify-content:space-between;position:sticky;top:0;"
    "background:var(--bg);z-index:100}"
    ".logo{font-family:'Bebas Neue',sans-serif;font-size:24px;letter-spacing:.1em;"
    "color:var(--amber);text-decoration:none}"
    "a{color:var(--amber);text-decoration:none}"
    "a:hover{text-decoration:underline;text-underline-offset:3px}"
    "h1{font-family:'Playfair Display',serif;font-weight:700;line-height:1.2}"
    "em{font-style:italic}"
)

NAV_LINKS = (
    "<div style='display:flex;gap:20px;font-size:10px;letter-spacing:.08em'>"
    "<a href='/contradiction' style='color:" + MUTED + "'>CONTRADICTION INDEX</a>"
    "<a href='/transparency' style='color:" + MUTED + "'>CLEAN BRANDS</a>"
    "<a href='/scan' style='color:" + MUTED + "'>SCAN</a>"
    "</div>"
)

def page_head(title, desc='', slug=''):
    og_img = ('https://tracedhealth.com/share/card/' + slug) if slug else ''
    parts = [
        "<!DOCTYPE html><html lang='en'><head>",
        "<meta charset='UTF-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1.0'>",
        "<title>" + title + "</title>",
        "<meta name='description' content='" + desc.replace("'", "&#39;") + "'>",
        "<meta property='og:title' content='" + title + "'>",
        "<meta property='og:description' content='" + desc.replace("'", "&#39;") + "'>",
        "<meta property='og:site_name' content='Traced'>",
    ]
    if og_img:
        parts += [
            "<meta property='og:image' content='" + og_img + "'>",
            "<meta name='twitter:card' content='summary_large_image'>",
            "<meta name='twitter:image' content='" + og_img + "'>",
        ]
    parts += [
        FONTS,
        "<style>" + BASE_CSS + "</style>",
        "</head><body>",
        "<nav><a class='logo' href='/'>TRACED</a>" + NAV_LINKS + "</nav>",
    ]
    return ''.join(parts)

def score_color(score):
    if score >= 70: return RED
    if score >= 40: return AMBER
    return GREEN

def score_label(score):
    if score >= 70: return 'HIGH CONTRADICTION'
    if score >= 40: return 'MODERATE'
    return 'LOW'

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def load_json(fname):
    path = os.path.join(BASE, fname)
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return {}

def full_brand_data(slug):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "SELECT b.id,b.name,b.slug,b.acquired_year,b.acquisition_price,b.independent,"
        "b.total_scans,b.founded_year,b.contradiction_score,"
        "co.name as co_name,co.type as co_type,co.hq_country,co.annual_revenue,co.id as co_id"
        " FROM brands b LEFT JOIN companies co ON b.parent_company_id=co.id"
        " WHERE b.slug=? OR lower(b.name)=lower(?)"
        " ORDER BY b.total_scans DESC NULLS LAST LIMIT 1",
        (slug, slug))
    brand = c.fetchone()
    if not brand:
        conn.close(); return None
    p = dict(brand)
    co_id = p.get('co_id')
    if co_id:
        c.execute("SELECT name FROM brands WHERE parent_company_id=? AND id!=? ORDER BY total_scans DESC NULLS LAST LIMIT 10", (co_id, p['id']))
        p['siblings'] = [r['name'] for r in c.fetchall()]
        c.execute("SELECT violation_type,year,description,outcome,fine_amount FROM violations WHERE company_id=? AND violation_type!='FDA recall' ORDER BY year DESC", (co_id,))
        p['violations'] = [dict(r) for r in c.fetchall()]
        c.execute("SELECT COUNT(*) FROM violations WHERE company_id=? AND violation_type='FDA recall'", (co_id,))
        p['recall_count'] = c.fetchone()[0]
        c.execute("SELECT year,total_spend,issues FROM lobbying_records WHERE company_id=? ORDER BY year DESC LIMIT 5", (co_id,))
        rows = [dict(r) for r in c.fetchall()]
        p['lobbying'] = rows
        p['lobbying_total'] = sum(r['total_spend'] for r in rows)
        p['lobbying_issues'] = []
        for r in rows:
            for issue in (r['issues'] or '').split(','):
                issue = issue.strip()
                if issue and issue not in p['lobbying_issues']:
                    p['lobbying_issues'].append(issue)
        c.execute("SELECT SUM(fine_amount) FROM violations WHERE company_id=? AND fine_amount IS NOT NULL", (co_id,))
        p['fines_total'] = c.fetchone()[0] or 0
    else:
        p['siblings'] = []; p['violations'] = []; p['recall_count'] = 0
        p['lobbying'] = []; p['lobbying_total'] = 0; p['lobbying_issues'] = []; p['fines_total'] = 0
    c.execute("SELECT event_type,event_date,headline,description,source_url FROM brand_events WHERE brand_id=? ORDER BY event_date DESC", (p['id'],))
    p['events'] = [dict(r) for r in c.fetchall()]
    c.execute("SELECT p.name,s.additives FROM products p JOIN ingredient_snapshots s ON s.product_id=p.id WHERE p.brand_id=? AND s.additives!='' ORDER BY length(s.additives) DESC LIMIT 8", (p['id'],))
    p['products'] = [dict(r) for r in c.fetchall()]
    c.execute("SELECT COUNT(*) FROM products WHERE brand_id=?", (p['id'],))
    p['product_count'] = c.fetchone()[0]
    conn.close()
    return p


def register(app):

    # ── /contradiction ───────────────────────────────────────────
    @app.route('/contradiction')
    def contradiction_index():
        data = load_json('contradiction_index.json')
        brands = data.get('brands', [])
        rows = ''
        for b in brands:
            sc = b['contradiction_score']
            col = score_color(sc)
            lbl = score_label(sc)
            bslug = b.get('slug', '')
            reasons_html = ''.join('<li style="margin-bottom:4px">' + r + '</li>' for r in b.get('top_reasons', [])[:3])
            fines_str = ('$' + str(round(b['parent_fines_total'] / 1e6)) + 'M fines') if b.get('parent_fines_total', 0) > 1e6 else ''
            lobby_str = ('$' + str(round(b['parent_lobbying_total'] / 1e6)) + 'M lobbying') if b.get('parent_lobbying_total', 0) > 1e5 else ''
            meta_pills = ''.join(
                "<span style='font-size:9px;background:rgba(255,255,255,0.06);border-radius:20px;padding:2px 8px;color:" + MUTED + "'>" + s + "</span>"
                for s in [fines_str, lobby_str] if s
            )
            acq_text = ('Acquired ' + str(b['acquired_year'])) if b.get('acquired_year') else ''
            acq_span = ("<span style='font-size:9px;color:" + MUTED + "'>" + acq_text + "</span>") if acq_text else ''
            rows += (
                "<div style='border:1px solid " + BDR + ";border-radius:12px;padding:20px 24px;margin-bottom:10px;"
                "display:grid;grid-template-columns:40px 1fr auto;gap:20px;align-items:start'>"
                "<div style='font-family:Bebas Neue,sans-serif;font-size:32px;color:" + MUTED + ";line-height:1'>" + str(b['rank']) + "</div>"
                "<div>"
                "<div style='display:flex;align-items:center;gap:10px;margin-bottom:6px'>"
                "<a href='/brand/" + bslug + "' style='font-family:Bebas Neue,sans-serif;font-size:24px;letter-spacing:.04em;color:" + INK + "'>" + b['brand'] + "</a>"
                "<span style='font-size:9px;color:" + AMBER + ";background:rgba(212,149,42,.1);padding:2px 8px;border-radius:4px'>" + b['parent'] + "</span>"
                + acq_span +
                "</div>"
                "<div style='font-size:11px;color:rgba(240,234,216,.75);line-height:1.6;margin-bottom:8px'>" + b.get('headline_finding', '') + "</div>"
                "<ul style='font-size:10px;color:" + MUTED + ";line-height:1.7;padding-left:16px;margin-bottom:8px'>" + reasons_html + "</ul>"
                "<div style='display:flex;gap:8px;flex-wrap:wrap'>" + meta_pills + "</div>"
                "</div>"
                "<div style='text-align:right'>"
                "<div style='font-family:Bebas Neue,sans-serif;font-size:48px;color:" + col + ";line-height:1'>" + str(sc) + "</div>"
                "<div style='font-size:8px;letter-spacing:.1em;color:" + col + "'>" + lbl + "</div>"
                "<div style='background:rgba(255,255,255,0.06);border-radius:4px;height:4px;width:60px;margin-top:8px;overflow:hidden'>"
                "<div style='height:4px;border-radius:4px;background:" + col + ";width:" + str(sc) + "%'></div></div>"
                "</div></div>"
            )

        methodology = (
            "<div style='border:1px solid " + BDR + ";border-radius:12px;padding:24px;margin-top:32px;max-width:800px;margin-left:auto;margin-right:auto'>"
            "<div style='font-size:9px;letter-spacing:.14em;text-transform:uppercase;color:" + AMBER + ";margin-bottom:12px'>Methodology</div>"
            "<div style='font-size:11px;color:" + MUTED + ";line-height:1.8'>"
            "The Contradiction Index scores brands 0-100 based on the gap between their positioning and their parent company's documented behavior. "
            "Signals include: brand acquired (+15), natural/organic branding (+20), parent FTC deceptive labeling action (+25), "
            "parent lobbied against GMO labeling (+20), nutrition labeling (+15), sugar/soda tax (+10), animal welfare (+20), "
            "10+ FDA recalls (+10), USDA recall (+10), EU regulatory action (+10), total fines &gt;$100M (+15), lobbying spend &gt;$50M (+10)."
            "</div></div>"
        )
        share_btn = (
            "<div style='text-align:center;margin:24px 0'>"
            "<button onclick=\"navigator.clipboard.writeText(window.location.href).then(()=>{this.textContent='Copied!'})\" "
            "style='background:" + AMBER + ";border:none;border-radius:8px;padding:10px 20px;"
            "font-family:DM Mono,monospace;font-size:10px;letter-spacing:.1em;text-transform:uppercase;"
            "color:#000;cursor:pointer'>Share This Page</button></div>"
        )
        return (
            page_head('The Contradiction Index — Traced', 'Brands that say one thing while their parent companies do another.')
            + "<div style='max-width:900px;margin:0 auto;padding:40px 40px 80px'>"
            "<div style='text-align:center;margin-bottom:40px'>"
            "<h1 style='font-size:clamp(24px,4vw,42px);margin-bottom:12px'>"
            "The <em style='color:" + AMBER + "'>Contradiction</em> Index</h1>"
            "<p style='font-size:12px;color:" + MUTED + ";max-width:500px;margin:0 auto;line-height:1.7'>"
            "Brands that market themselves as natural, honest, or clean — while their parent companies lobby against labeling reform, "
            "rack up FDA violations, and pay hundreds of millions in fines.</p>"
            + share_btn + "</div>"
            + rows + methodology
            + "</div></body></html>"
        )

    # ── /transparency ────────────────────────────────────────────
    @app.route('/transparency')
    def transparency_index():
        data = load_json('transparency_index.json')
        brands = data.get('brands', [])
        rows = ''
        for b in brands:
            sc = b['transparency_score']
            bslug = b.get('slug', b['brand'].lower().replace(' ', '-'))
            founded = (' est. ' + str(b['founded_year'])) if b.get('founded_year') else ''
            prod_str = (str(b['product_count']) + ' products') if b.get('product_count') else ''
            scan_str = (str(b['scan_count']) + ' scans') if b.get('scan_count') else ''
            meta_parts = [s for s in [b.get('category', ''), prod_str, scan_str] if s]
            rows += (
                "<div style='border:1px solid " + BDR + ";border-radius:12px;padding:20px 24px;margin-bottom:10px;"
                "display:grid;grid-template-columns:40px 1fr auto;gap:20px;align-items:start'>"
                "<div style='font-family:Bebas Neue,sans-serif;font-size:32px;color:" + MUTED + ";line-height:1'>" + str(b['rank']) + "</div>"
                "<div>"
                "<div style='display:flex;align-items:center;gap:10px;margin-bottom:6px'>"
                "<a href='/brand/" + bslug + "' style='font-family:Bebas Neue,sans-serif;font-size:24px;letter-spacing:.04em;color:" + INK + "'>" + b['brand'] + "</a>"
                "<span style='font-size:9px;color:" + GREEN + ";background:rgba(58,138,90,.12);padding:2px 8px;border-radius:4px'>INDEPENDENT</span>"
                + ("<span style='font-size:9px;color:" + MUTED + "'>" + founded.strip() + "</span>" if founded else "")
                + "</div>"
                "<div style='font-size:11px;color:rgba(240,234,216,.75);line-height:1.6;margin-bottom:8px'>" + b.get('why', '') + "</div>"
                "<div style='font-size:9px;color:" + MUTED + "'>" + ' · '.join(meta_parts) + "</div>"
                "</div>"
                "<div style='text-align:right'>"
                "<div style='font-family:Bebas Neue,sans-serif;font-size:48px;color:" + GREEN + ";line-height:1'>" + str(sc) + "</div>"
                "<div style='font-size:8px;letter-spacing:.1em;color:" + GREEN + "'>CLEAN</div>"
                "<div style='background:rgba(255,255,255,0.06);border-radius:4px;height:4px;width:60px;margin-top:8px;overflow:hidden'>"
                "<div style='height:4px;border-radius:4px;background:" + GREEN + ";width:" + str(sc) + "%'></div></div>"
                "</div></div>"
            )
        return (
            page_head('Clean Brand Index — Traced', 'Independent brands doing it right.')
            + "<div style='max-width:900px;margin:0 auto;padding:40px 40px 80px'>"
            "<div style='text-align:center;margin-bottom:40px'>"
            "<h1 style='font-size:clamp(24px,4vw,42px);margin-bottom:12px'>"
            "Brands <em style='color:" + GREEN + "'>Doing It Right</em></h1>"
            "<p style='font-size:12px;color:" + MUTED + ";max-width:500px;margin:0 auto;line-height:1.7'>"
            "Independent, founder-led brands with clean ingredient profiles and no conglomerate ownership chains.</p></div>"
            + rows + "</div></body></html>"
        )

    # ── /brand/<slug> ────────────────────────────────────────────
    @app.route('/brand/<slug>')
    def brand_investigation(slug):
        from traced_app import brand_profile, render_profile, CSS, get_stats
        p = brand_profile(slug)
        if not p:
            conn = get_db()
            c2 = conn.cursor()
            c2.execute("SELECT name FROM brands WHERE slug=? LIMIT 1", (slug,))
            row = c2.fetchone()
            conn.close()
            if row:
                p = brand_profile(row['name'])
        if not p:
            return (
                page_head('Brand Not Found — Traced')
                + "<div style='text-align:center;padding:80px;color:" + MUTED + ";font-size:13px'>"
                "Brand not found. <a href='/'>Search brands</a></div></body></html>"
            ), 404

        bslug = p.get('slug') or slug
        brand_name = p['name']
        parent_name = p.get('co_name') or 'Unknown'
        acq_year = p.get('acquired_year') or '?'
        recall_count = p.get('recall_count', 0)
        fines = p.get('fines_total', 0)
        lobby_issues = p.get('lobbying_issues', [])
        lobby_total = p.get('lobbying_total', 0)
        sc = p.get('contradiction_score', 0)

        og_desc = brand_name + ' is owned by ' + parent_name + '. Contradiction score: ' + str(sc) + '/100.'

        jsonld = json.dumps({
            "@context": "https://schema.org",
            "@type": "Organization",
            "name": brand_name,
            "description": og_desc,
            "url": "https://tracedhealth.com/brand/" + bslug,
            "parentOrganization": {"@type": "Organization", "name": parent_name},
        })

        # Share JS (no backslashes inside strings)
        text_parts = [brand_name + " on @TracedHealth:"]
        if p.get('co_name'):
            text_parts.append("Owned by " + parent_name + (" since " + str(acq_year) if p.get('acquired_year') else ""))
        if lobby_issues:
            text_parts.append(parent_name + " spent $" + str(round(lobby_total / 1e6, 1)) + "M lobbying on " + lobby_issues[0])
        elif fines > 1e6:
            text_parts.append("$" + str(round(fines / 1e6, 1)) + "M in documented fines")
        if recall_count > 0:
            text_parts.append(str(recall_count) + " FDA recalls")
        text_parts.append("tracedhealth.com/brand/" + bslug)
        share_text_str = "\\n".join(text_parts)[:280]

        share_bar = (
            "<div style='display:flex;gap:8px;flex-wrap:wrap;margin:16px 40px 0'>"
            "<button id='copy-btn' onclick='copyLink()' style='background:" + SURF + ";border:1px solid " + B2 + ";"
            "border-radius:8px;padding:8px 14px;font-family:DM Mono,monospace;font-size:10px;letter-spacing:.08em;"
            "text-transform:uppercase;color:" + INK + ";cursor:pointer'>Copy Link</button>"
            "<button id='share-text-btn' onclick='shareText()' style='background:" + SURF + ";border:1px solid " + B2 + ";"
            "border-radius:8px;padding:8px 14px;font-family:DM Mono,monospace;font-size:10px;letter-spacing:.08em;"
            "text-transform:uppercase;color:" + INK + ";cursor:pointer'>Share via Text</button>"
            "<a href='https://twitter.com/intent/tweet?text=" + brand_name + " — Traced&url=https://tracedhealth.com/brand/" + bslug + "'"
            " target='_blank' style='background:" + SURF + ";border:1px solid " + B2 + ";border-radius:8px;padding:8px 14px;"
            "font-family:DM Mono,monospace;font-size:10px;letter-spacing:.08em;text-transform:uppercase;color:" + INK + "'>Share on X</a>"
            "</div>"
        )

        embed_code = (
            "<div style='border:1px solid " + BDR + ";border-radius:12px;padding:20px;margin:24px 40px'>"
            "<div style='font-size:9px;letter-spacing:.14em;text-transform:uppercase;color:" + AMBER + ";margin-bottom:10px'>Embed This Card</div>"
            "<textarea onclick='this.select()' readonly style='width:100%;background:#111;border:1px solid " + BDR + ";"
            "border-radius:6px;padding:10px;font-family:DM Mono,monospace;font-size:10px;color:" + MUTED + ";resize:none;height:48px'>"
            "&lt;script src=\"https://tracedhealth.com/embed.js\" data-brand=\"" + bslug + "\"&gt;&lt;/script&gt;"
            "</textarea>"
            "<div style='font-size:10px;color:" + MUTED + ";margin-top:6px'>Paste in any webpage to embed the Traced widget</div>"
            "</div>"
        )

        cite = (
            "<div style='border:1px solid " + BDR + ";border-radius:12px;padding:20px;margin:0 40px 80px'>"
            "<div style='font-size:9px;letter-spacing:.14em;text-transform:uppercase;color:" + AMBER + ";margin-bottom:10px'>Cite This Page</div>"
            "<div style='font-size:10px;color:" + MUTED + ";line-height:1.8'>"
            "Traced. \"" + brand_name + " — Brand Investigation.\" TracedHealth.com. "
            "https://tracedhealth.com/brand/" + bslug + ". Accessed 2026."
            "</div></div>"
        )

        share_js = (
            "function copyLink(){"
            "navigator.clipboard.writeText('https://tracedhealth.com/brand/" + bslug + "')"
            ".then(function(){var b=document.getElementById('copy-btn');b.textContent='Copied!';setTimeout(function(){b.textContent='Copy Link'},2000)})}"
            "function shareText(){"
            "var t='" + share_text_str.replace("'", "\\'") + "';"
            "navigator.clipboard.writeText(t)"
            ".then(function(){var b=document.getElementById('share-text-btn');b.textContent='Copied!';setTimeout(function(){b.textContent='Share via Text'},2000)})}"
        )

        profile_html = render_profile(p)

        return (
            "<!DOCTYPE html><html lang='en'><head>"
            "<meta charset='UTF-8'>"
            "<meta name='viewport' content='width=device-width,initial-scale=1.0'>"
            "<title>" + brand_name + " — Traced Brand Investigation</title>"
            "<meta name='description' content='" + og_desc.replace("'", "&#39;") + "'>"
            "<meta property='og:title' content='" + brand_name + " — Traced'>"
            "<meta property='og:description' content='" + og_desc.replace("'", "&#39;") + "'>"
            "<meta property='og:image' content='https://tracedhealth.com/share/card/" + bslug + "'>"
            "<meta property='og:type' content='article'>"
            "<meta name='twitter:card' content='summary_large_image'>"
            "<meta name='twitter:title' content='" + brand_name + " — Traced'>"
            "<meta name='twitter:image' content='https://tracedhealth.com/share/card/" + bslug + "'>"
            + FONTS
            + "<style>" + CSS
            + "</style>"
            "<script type='application/ld+json'>" + jsonld + "</script>"
            "</head><body>"
            "<nav><a class='logo' href='/'>TRACED</a>"
            "<a style='font-size:10px;color:" + MUTED + ";text-decoration:none;letter-spacing:.08em;text-transform:uppercase' href='/'>&#8592; Search</a>"
            "</nav>"
            + share_bar
            + profile_html
            + embed_code + cite
            + "<script>function searchBrand(n){window.location.href='/?q='+encodeURIComponent(n)}" + share_js + "</script>"
            "</body></html>"
        )

    # ── /scan ─────────────────────────────────────────────────────
    @app.route('/scan')
    def scan_page():
        return (
            page_head('Scan a Barcode — Traced', 'Scan any food barcode to see who really owns the brand.')
            + """<style>
#sw{max-width:500px;margin:0 auto;padding:40px 20px;text-align:center}
.sh2{font-family:'Playfair Display',serif;font-size:28px;margin-bottom:10px}
.ssub{font-size:12px;color:var(--muted);margin-bottom:32px;line-height:1.7}
#vw{position:relative;width:100%;max-width:400px;margin:0 auto 24px;border-radius:16px;overflow:hidden;background:#111;border:1px solid var(--b2)}
video{width:100%;display:block;border-radius:16px}
#sl{position:absolute;left:10%;width:80%;height:2px;background:var(--amber);box-shadow:0 0 8px var(--amber);animation:sc 2s linear infinite;top:40%}
@keyframes sc{0%,100%{top:20%}50%{top:75%}}
#ss{font-size:11px;color:var(--muted);margin-bottom:16px}
#ms{margin-top:32px;border-top:1px solid var(--border);padding-top:24px}
.si{width:100%;background:var(--surface);border:1px solid var(--b2);border-radius:10px;padding:14px 16px;font-family:'DM Mono',monospace;font-size:13px;color:var(--ink);outline:none;margin-bottom:10px}
.sbn{background:var(--amber);border:none;border-radius:8px;padding:12px 24px;font-family:'DM Mono',monospace;font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:#000;cursor:pointer;width:100%}
</style>
<div id="sw">
  <div class="sh2">Scan a Barcode</div>
  <p class="ssub">Point your camera at any food barcode.<br>Works on iPhone Safari and Android Chrome.</p>
  <div id="vw"><video id="video" autoplay muted playsinline></video><div id="sl"></div></div>
  <div id="ss">Starting camera...</div>
  <div id="ms">
    <div style="font-size:10px;color:var(--muted);letter-spacing:.08em;text-transform:uppercase;margin-bottom:12px">Or enter barcode manually</div>
    <input class="si" id="ui" type="tel" placeholder="Enter UPC barcode number" autocomplete="off">
    <button class="sbn" onclick="lu()">Look Up Barcode</button>
  </div>
</div>
<script>
var video=document.getElementById('video'),status=document.getElementById('ss'),scanning=true;
navigator.mediaDevices.getUserMedia({video:{facingMode:'environment'}}).then(function(s){
  video.srcObject=s;status.textContent='Scanning for barcode...';
  if('BarcodeDetector' in window){
    var bd=new BarcodeDetector({formats:['ean_13','ean_8','upc_a','upc_e','code_128']});
    function tick(){if(!scanning)return;bd.detect(video).then(function(c){if(c.length>0){scanning=false;fb(c[0].rawValue);}}).catch(function(){});if(scanning)requestAnimationFrame(tick);}
    video.addEventListener('playing',tick);
  }else{status.textContent='Manual entry only (BarcodeDetector not supported)';}
}).catch(function(){status.textContent='Camera denied — use manual entry';document.getElementById('vw').style.display='none';});
function fb(u){status.textContent='Looking up '+u+'...';fetch('/api/barcode/'+u).then(function(r){return r.json()}).then(function(d){if(d.error){status.textContent='Not found: '+u;scanning=true;return;}window.location.href='/brand/'+(d.brand_id||d.name.toLowerCase().replace(/ /g,'-'));}).catch(function(){status.textContent='Lookup failed';scanning=true;});}
function lu(){var v=document.getElementById('ui').value.trim().replace(/\D/g,'');if(v)fb(v);}
document.getElementById('ui').addEventListener('keydown',function(e){if(e.key==='Enter')lu();});
</script></body></html>"""
        )

    # ── /share/text/<slug> ────────────────────────────────────────
    @app.route('/share/text/<slug>')
    def share_text_route(slug):
        p = full_brand_data(slug)
        if not p:
            return jsonify({'error': 'Brand not found'}), 404
        bslug = p.get('slug') or slug
        issues = p.get('lobbying_issues', [])
        parts = ['🔍 ' + p['name'] + ' on @TracedHealth:']
        if p.get('co_name'):
            parts.append('• Owned by ' + p['co_name'] + (' since ' + str(p['acquired_year']) if p.get('acquired_year') else ''))
        if issues:
            spend = p.get('lobbying_total', 0)
            parts.append('• ' + p['co_name'] + ' spent $' + str(round(spend / 1e6, 1)) + 'M lobbying on ' + issues[0])
        elif p.get('fines_total', 0) > 1e6:
            parts.append('• $' + str(round(p['fines_total'] / 1e6, 1)) + 'M in documented fines')
        if p.get('recall_count', 0) > 0:
            parts.append('• ' + str(p['recall_count']) + ' FDA recalls on record')
        parts.append('tracedhealth.com/brand/' + bslug)
        text = '\n'.join(parts)[:280]
        return jsonify({'brand': p['name'], 'slug': bslug, 'share_text': text, 'char_count': len(text)})

    # ── /share/card/<slug> ────────────────────────────────────────
    @app.route('/share/card/<slug>')
    def share_card_route(slug):
        p = full_brand_data(slug)
        if not p:
            return "Brand not found", 404
        bslug = p.get('slug') or slug
        sc = p.get('contradiction_score', 0)
        col = score_color(sc)
        brand_name = p['name']
        parent_name = p.get('co_name') or 'Independent'

        findings = []
        if p.get('co_name') and p.get('acquired_year'):
            findings.append('Acquired by ' + parent_name + ' in ' + str(p['acquired_year']))
        if p.get('lobbying_issues'):
            findings.append(parent_name + ' lobbied on: ' + ', '.join(p['lobbying_issues'][:2]))
        elif p.get('fines_total', 0) > 1e6:
            findings.append('$' + str(round(p['fines_total'] / 1e6)) + 'M in documented fines')
        if p.get('recall_count', 0) > 0:
            findings.append(str(p['recall_count']) + ' FDA recalls')
        findings = findings[:2]

        findings_js = '\n'.join(
            "ctx.fillText(" + json.dumps('• ' + f[:70]) + "," + str(60) + "," + str(320 + i * 40) + ");"
            for i, f in enumerate(findings)
        )

        canvas_html = (
            "<style>body{background:#000;display:flex;flex-direction:column;align-items:center;padding:40px 20px;font-family:DM Mono,monospace}"
            "canvas{border-radius:12px;max-width:100%}"
            ".dlb{margin-top:16px;background:" + AMBER + ";border:none;border-radius:8px;padding:10px 20px;"
            "font-family:DM Mono,monospace;font-size:11px;letter-spacing:.1em;text-transform:uppercase;color:#000;cursor:pointer}</style>"
            "<canvas id='c' width='1200' height='630'></canvas>"
            "<button class='dlb' onclick='dl()'>Download Card</button>"
            "<script>"
            "var c=document.getElementById('c'),ctx=c.getContext('2d');"
            "ctx.fillStyle='" + BG + "';ctx.fillRect(0,0,1200,630);"
            "ctx.strokeStyle='rgba(255,255,255,0.03)';ctx.lineWidth=1;"
            "for(var x=0;x<1200;x+=60){ctx.beginPath();ctx.moveTo(x,0);ctx.lineTo(x,630);ctx.stroke()}"
            "for(var y=0;y<630;y+=60){ctx.beginPath();ctx.moveTo(0,y);ctx.lineTo(1200,y);ctx.stroke()}"
            "ctx.fillStyle='rgba(255,255,255,0.04)';ctx.fillRect(60,510,1080,28);"
            "ctx.fillStyle='" + col + "';ctx.fillRect(60,510," + str(sc) + "*1080/100,28);"
            "ctx.fillStyle='" + INK + "';ctx.font='bold 80px Arial';ctx.fillText(" + json.dumps(brand_name[:22]) + ",60,200);"
            "ctx.fillStyle='" + AMBER + "';ctx.font='22px Arial';"
            "ctx.fillText(" + json.dumps('Owned by ' + parent_name[:40]) + ",60,245);"
            "ctx.fillStyle='" + col + "';ctx.font='bold 110px Arial';ctx.textAlign='right';ctx.fillText('" + str(sc) + "',1140,200);"
            "ctx.font='15px Arial';ctx.fillText('CONTRADICTION SCORE',1140,225);ctx.textAlign='left';"
            "ctx.fillStyle='rgba(240,234,216,0.5)';ctx.font='20px Arial';"
            + findings_js +
            "ctx.fillStyle='rgba(255,255,255,0.25)';ctx.font='16px Arial';"
            "ctx.fillText('TRACED  ·  tracedhealth.com',60,590);"
            "function dl(){var a=document.createElement('a');a.download='traced-" + bslug + ".png';a.href=c.toDataURL('image/png');a.click();}"
            "</script>"
        )
        return (
            "<!DOCTYPE html><html><head><meta charset='UTF-8'>"
            + FONTS
            + "<title>" + brand_name + " — Traced Card</title>"
            "</head><body>" + canvas_html + "</body></html>"
        )

    # ── /api/docs ─────────────────────────────────────────────────
    @app.route('/api/docs')
    def api_docs():
        endpoints = [
            ('GET', '/api/brand/{name}', 'Full brand profile — ownership, violations, lobbying, contradiction score, flagged additives', '/api/brand/Kashi'),
            ('GET', '/api/barcode/{upc}', 'Brand profile via UPC barcode number', '/api/barcode/00000028'),
            ('GET', '/api/brands', 'All brands with parent company and contradiction score (top 500)', '/api/brands'),
            ('GET', '/api/companies', 'All companies with brand counts and total fines', '/api/companies'),
            ('GET', '/api/stats', 'Database-wide stats: counts, total fines, total lobbying', '/api/stats'),
            ('GET', '/share/text/{slug}', 'Pre-formatted SMS/text share string for a brand', '/share/text/kashi'),
        ]
        ep_html = ''
        for method, path, desc, example in endpoints:
            ep_html += (
                "<div style='border:1px solid " + BDR + ";border-radius:10px;padding:16px 20px;margin-bottom:10px'>"
                "<div style='display:flex;align-items:center;gap:10px;margin-bottom:8px'>"
                "<span style='font-size:9px;background:rgba(212,149,42,.15);color:" + AMBER + ";padding:3px 8px;border-radius:4px'>" + method + "</span>"
                "<span style='font-size:13px;font-weight:500;color:" + INK + "'>" + path + "</span>"
                "</div>"
                "<div style='font-size:11px;color:" + MUTED + ";line-height:1.6;margin-bottom:8px'>" + desc + "</div>"
                "<a href='" + example + "' style='font-size:10px;color:" + AMBER + "'>Try it →</a>"
                "</div>"
            )
        return (
            page_head('API Documentation — Traced', 'Traced brand intelligence API — all endpoints and examples.')
            + "<div style='max-width:800px;margin:0 auto;padding:40px 40px 80px'>"
            "<h1 style='font-size:32px;margin-bottom:8px'>API <em style='color:" + AMBER + "'>Documentation</em></h1>"
            "<p style='font-size:12px;color:" + MUTED + ";margin-bottom:32px;line-height:1.7'>"
            "Traced exposes brand ownership, violation, lobbying, and ingredient data via a simple REST API. "
            "All responses are JSON. No authentication required.</p>"
            "<div style='font-size:9px;letter-spacing:.14em;text-transform:uppercase;color:" + AMBER + ";margin-bottom:16px'>Endpoints</div>"
            + ep_html
            + "<div style='border:1px solid " + BDR + ";border-radius:12px;padding:20px;margin-top:32px'>"
            "<div style='font-size:9px;letter-spacing:.14em;text-transform:uppercase;color:" + AMBER + ";margin-bottom:12px'>Live Example — Annie's</div>"
            "<div id='ej' style='font-size:10px;color:" + MUTED + ";background:#111;border-radius:8px;padding:16px;font-family:DM Mono,monospace;white-space:pre-wrap;max-height:400px;overflow-y:auto'>Loading...</div>"
            "</div>"
            "<div style='border:1px solid " + BDR + ";border-radius:12px;padding:20px;margin-top:16px'>"
            "<div style='font-size:9px;letter-spacing:.14em;text-transform:uppercase;color:" + AMBER + ";margin-bottom:8px'>Rate Limits</div>"
            "<div style='font-size:11px;color:" + MUTED + ";line-height:1.8'>"
            "60 requests/minute per IP. For research or integration inquiries: hello@tracedhealth.com</div>"
            "</div>"
            "<script>fetch(\"/api/brand/Annie's\").then(function(r){return r.json()}).then(function(d){document.getElementById('ej').textContent=JSON.stringify(d,null,2)}).catch(function(e){document.getElementById('ej').textContent='Could not load example'})</script>"
            "</div></body></html>"
        )

    # ── /widget/<slug> ────────────────────────────────────────────
    @app.route('/widget/<slug>')
    def widget(slug):
        p = full_brand_data(slug)
        if not p:
            return "Brand not found", 404
        bslug = p.get('slug') or slug
        sc = p.get('contradiction_score', 0)
        col = score_color(sc)
        lbl = score_label(sc)
        top_finding = ''
        if p.get('lobbying_issues'):
            top_finding = 'Parent lobbied: ' + ', '.join(p['lobbying_issues'][:2])
        elif p.get('fines_total', 0) > 1e6:
            top_finding = '$' + str(round(p['fines_total'] / 1e6, 1)) + 'M in documented fines'
        parent_text = ('Owned by ' + p['co_name']) if p.get('co_name') else 'Independent'
        html = (
            "<!DOCTYPE html><html><head><meta charset='UTF-8'>"
            "<style>*{box-sizing:border-box;margin:0;padding:0}body{background:#0a0906;font-family:'DM Mono',monospace;"
            "width:300px;height:200px;overflow:hidden;border-radius:12px}"
            ".w{padding:18px;height:100%;display:flex;flex-direction:column;justify-content:space-between;"
            "border:1px solid rgba(255,255,255,0.08);border-radius:12px}"
            "a{color:inherit;text-decoration:none}</style></head><body>"
            "<div class='w'>"
            "<div>"
            "<div style='font-size:20px;font-weight:700;color:#f0ead8;margin-bottom:4px'>" + p['name'][:20] + "</div>"
            "<div style='font-size:10px;color:" + AMBER + "'>" + parent_text + "</div>"
            "<div style='font-size:9px;color:rgba(240,234,216,0.5);line-height:1.5;margin-top:8px'>" + top_finding[:80] + "</div>"
            "</div>"
            "<div style='display:flex;align-items:center;justify-content:space-between'>"
            "<div>"
            "<div style='font-size:28px;font-weight:700;color:" + col + ";line-height:1'>" + str(sc) + "</div>"
            "<div style='font-size:8px;letter-spacing:.1em;color:" + col + "'>" + lbl + "</div>"
            "</div>"
            "<div style='flex:1;background:rgba(255,255,255,0.06);border-radius:3px;height:3px;margin:0 10px;overflow:hidden'>"
            "<div style='height:3px;border-radius:3px;background:" + col + ";width:" + str(sc) + "%'></div></div>"
            "<a href='https://tracedhealth.com/brand/" + bslug + "' target='_blank' style='font-size:9px;color:" + AMBER + "'>View →</a>"
            "</div>"
            "<div style='font-size:8px;color:rgba(255,255,255,0.2);letter-spacing:.06em'>TRACED · tracedhealth.com</div>"
            "</div></body></html>"
        )
        return Response(html, mimetype='text/html')

    # ── /embed.js ─────────────────────────────────────────────────
    @app.route('/embed.js')
    def embed_js():
        js = (
            "(function(){"
            "var scripts=document.querySelectorAll('script[data-brand]');"
            "scripts.forEach(function(s){"
            "var slug=s.getAttribute('data-brand');if(!slug)return;"
            "var iframe=document.createElement('iframe');"
            "iframe.src='https://tracedhealth.com/widget/'+slug;"
            "iframe.style.cssText='width:300px;height:200px;border:none;border-radius:12px;display:block';"
            "iframe.title='Traced Brand Widget';"
            "s.parentNode.insertBefore(iframe,s.nextSibling);"
            "});})();"
        )
        return Response(js, mimetype='application/javascript')

    # ── /api/brands ───────────────────────────────────────────────
    @app.route('/api/brands')
    def api_brands_list():
        conn = get_db()
        c = conn.cursor()
        c.execute("""SELECT b.name,b.slug,b.contradiction_score,b.acquired_year,
                            co.name as parent
                     FROM brands b LEFT JOIN companies co ON co.id=b.parent_company_id
                     ORDER BY b.contradiction_score DESC NULLS LAST,b.total_scans DESC NULLS LAST
                     LIMIT 500""")
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return jsonify(rows)

    # ── /api/companies ────────────────────────────────────────────
    @app.route('/api/companies')
    def api_companies_list():
        conn = get_db()
        c = conn.cursor()
        c.execute("""SELECT co.id,co.name,co.type,co.annual_revenue,
                            COUNT(DISTINCT b.id) as brand_count,
                            COUNT(DISTINCT v.id) as violation_count,
                            SUM(COALESCE(v.fine_amount,0)) as total_fines
                     FROM companies co
                     LEFT JOIN brands b ON b.parent_company_id=co.id
                     LEFT JOIN violations v ON v.company_id=co.id
                     GROUP BY co.id ORDER BY brand_count DESC""")
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return jsonify(rows)

    # ── /api/stats ────────────────────────────────────────────────
    @app.route('/api/stats')
    def api_stats():
        conn = get_db()
        c = conn.cursor()
        stats = {}
        for k, q in [
            ('brands',              'SELECT COUNT(*) FROM brands'),
            ('companies',           'SELECT COUNT(*) FROM companies'),
            ('products',            'SELECT COUNT(*) FROM products'),
            ('violations',          'SELECT COUNT(*) FROM violations'),
            ('lobbying_records',    'SELECT COUNT(*) FROM lobbying_records'),
            ('brand_events',        'SELECT COUNT(*) FROM brand_events'),
            ('ingredient_snapshots','SELECT COUNT(*) FROM ingredient_snapshots'),
        ]:
            c.execute(q); stats[k] = c.fetchone()[0]
        c.execute('SELECT SUM(total_spend) FROM lobbying_records')
        stats['total_lobbying_spend'] = c.fetchone()[0] or 0
        c.execute('SELECT SUM(fine_amount) FROM violations WHERE fine_amount IS NOT NULL')
        stats['total_fines'] = c.fetchone()[0] or 0
        conn.close()
        return jsonify(stats)
