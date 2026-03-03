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
    "<div style='display:flex;gap:0;font-size:10px;letter-spacing:.07em;align-items:center'>"
    # INVESTIGATE dropdown
    "<div class='nav-group'>"
    "<span class='nav-label'>INVESTIGATE ▾</span>"
    "<div class='nav-dropdown'>"
    "<a href='/contradiction'>CONTRADICTION INDEX</a>"
    "<a href='/categories'>BY CATEGORY</a>"
    "<a href='/watchlist'>WATCH LIST</a>"
    "<a href='/scan'>BARCODE SCAN</a>"
    "</div></div>"
    # DISCOVER dropdown
    "<div class='nav-group'>"
    "<span class='nav-label'>DISCOVER ▾</span>"
    "<div class='nav-dropdown'>"
    "<a href='/independent'>INDEPENDENT BRANDS</a>"
    "<a href='/transparent50'>TOP 50 TRANSPARENT</a>"
    "<a href='/founders'>FOUNDER-LED</a>"
    "<a href='/certifications'>CERTIFICATIONS</a>"
    "</div></div>"
    # TOOLS dropdown
    "<div class='nav-group'>"
    "<span class='nav-label'>TOOLS ▾</span>"
    "<div class='nav-dropdown'>"
    "<a href='/audit'>RECEIPT AUDIT</a>"
    "<a href='/retailers'>RETAILER SCORES</a>"
    "<a href='/local'>LOCAL MARKETS</a>"
    "</div></div>"
    # DATA link
    "<a href='/api/docs' style='color:" + MUTED + ";padding:8px 12px'>DATA</a>"
    "</div>"
    # Nav dropdown CSS (injected once per page)
    "<style>"
    ".nav-group{position:relative}"
    ".nav-label{color:" + MUTED + ";padding:8px 12px;cursor:pointer;user-select:none;"
    "white-space:nowrap;display:inline-block}"
    ".nav-group:hover .nav-label{color:" + INK + "}"
    ".nav-dropdown{display:none;position:absolute;top:100%;left:0;background:" + BG + ";"
    "border:1px solid " + B2 + ";border-radius:8px;padding:8px 0;min-width:180px;z-index:200;"
    "box-shadow:0 8px 32px rgba(0,0,0,0.6)}"
    ".nav-group:hover .nav-dropdown{display:block}"
    ".nav-dropdown a{display:block;padding:8px 16px;color:" + MUTED + ";font-size:10px;"
    "letter-spacing:.07em;white-space:nowrap}"
    ".nav-dropdown a:hover{color:" + INK + ";background:rgba(255,255,255,0.04);text-decoration:none}"
    "@media(max-width:640px){.nav-group{display:none}}"
    "</style>"
)

def page_head(title, desc='', slug='', canonical='', jsonld=None):
    og_img = ('https://tracedhealth.com/share/card/' + slug) if slug else ''
    canon_url = canonical or (('https://tracedhealth.com/brand/' + slug) if slug else '')
    parts = [
        "<!DOCTYPE html><html lang='en'><head>",
        "<meta charset='UTF-8'>",
        "<meta name='viewport' content='width=device-width,initial-scale=1.0'>",
        "<title>" + title + "</title>",
        "<meta name='description' content='" + desc.replace("'", "&#39;") + "'>",
        "<meta property='og:title' content='" + title + "'>",
        "<meta property='og:description' content='" + desc.replace("'", "&#39;") + "'>",
        "<meta property='og:site_name' content='Traced'>",
        "<meta property='og:type' content='website'>",
        "<meta name='twitter:site' content='@tracedhealth'>",
    ]
    if canon_url:
        parts.append("<link rel='canonical' href='" + canon_url + "'>")
        parts.append("<meta property='og:url' content='" + canon_url + "'>")
    if og_img:
        parts += [
            "<meta property='og:image' content='" + og_img + "'>",
            "<meta name='twitter:card' content='summary_large_image'>",
            "<meta name='twitter:image' content='" + og_img + "'>",
        ]
    if jsonld:
        parts.append("<script type='application/ld+json'>" + json.dumps(jsonld) + "</script>")
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
    # ── /transparency ── (redirects to /independent in v3) ─────────
    @app.route('/transparency')
    def transparency_index():
        from flask import redirect
        return redirect('/independent', code=301)


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

    # ══════════════════════════════════════════════════════════════════
    # PHASE 5 — CATEGORY PAGES
    # ══════════════════════════════════════════════════════════════════

    CATEGORY_DEFS = {
        'protein-supplements': {'label': 'Protein & Supplements', 'icon': '💪',
            'desc': 'Protein powders, bars, shakes, and supplement brands — who really owns them.'},
        'baby-food': {'label': 'Baby Food', 'icon': '🍼',
            'desc': 'Baby food brands and their parent companies, plus heavy metal recall history.'},
        'functional-beverages': {'label': 'Functional Beverages', 'icon': '⚡',
            'desc': 'Hydration, energy, prebiotic soda, and electrolyte brands and their owners.'},
        'plant-based': {'label': 'Plant-Based Foods', 'icon': '🌱',
            'desc': 'Plant-based meat and dairy alternative brands — often owned by conventional meat companies.'},
        'snacks': {'label': 'Snacks', 'icon': '🥜',
            'desc': 'Snack brands and their conglomerate owners.'},
        'vitamins': {'label': 'Vitamins & Supplements', 'icon': '💊',
            'desc': 'Vitamin and supplement brands, many owned by pharmaceutical conglomerates.'},
        'cereals': {'label': 'Cereals & Breakfast', 'icon': '🥣',
            'desc': 'Breakfast brands including cereals, granola, and oats.'},
        'beverages': {'label': 'Beverages', 'icon': '🧃',
            'desc': 'Juice, water, coffee, and other beverage brands.'},
    }

    CAT_MAP = {
        'protein-supplements': ['Supplements', 'Protein'],
        'baby-food': ['Baby Food', 'Baby'],
        'functional-beverages': ['Beverages', 'Functional', 'Hydration'],
        'plant-based': ['Plant-Based', 'Vegan'],
        'snacks': ['Snacks', 'Chips', 'Bars'],
        'vitamins': ['Vitamins', 'Supplements'],
        'cereals': ['Cereal', 'Breakfast', 'Granola'],
        'beverages': ['Beverages', 'Drinks', 'Juice'],
    }

    @app.route('/categories')
    def categories_index():
        conn = get_db()
        c = conn.cursor()
        cards = ''
        for slug_key, meta in CATEGORY_DEFS.items():
            terms = CAT_MAP.get(slug_key, [meta['label']])
            placeholders = ','.join('?' * len(terms))
            c.execute(
                "SELECT COUNT(*) FROM brands WHERE category IN (" + placeholders + ")",
                terms)
            total = c.fetchone()[0]
            c.execute(
                "SELECT COUNT(*) FROM brands WHERE category IN (" + placeholders + ") AND (acquired_year IS NOT NULL OR parent_company_id IS NOT NULL)",
                terms)
            acquired = c.fetchone()[0]
            pct = round(acquired * 100 / total) if total else 0
            cards += (
                "<a href='/category/" + slug_key + "' style='display:block;border:1px solid var(--border);"
                "border-radius:12px;padding:20px 24px;text-decoration:none;transition:border-color .2s'>"
                "<div style='font-size:28px;margin-bottom:8px'>" + meta['icon'] + "</div>"
                "<div style='font-family:\"Playfair Display\",serif;font-size:18px;color:var(--ink);margin-bottom:4px'>" + meta['label'] + "</div>"
                "<div style='font-size:10px;color:var(--muted);margin-bottom:12px'>" + meta['desc'] + "</div>"
                "<div style='display:flex;gap:16px;font-size:10px'>"
                "<span style='color:var(--amber)'>" + str(total) + " brands tracked</span>"
                "<span style='color:var(--red)'>" + str(pct) + "% conglomerate-owned</span>"
                "</div></a>"
            )
        conn.close()
        html = (
            page_head('Brand Categories | Traced', 'Browse food and supplement brands by category. See who owns what.')
            + "<main style='max-width:1200px;margin:0 auto;padding:40px 20px'>"
            + "<h1 style='font-size:32px;margin-bottom:8px'>Browse by Category</h1>"
            + "<p style='color:var(--muted);font-size:12px;margin-bottom:32px'>Select a category to see brand ownership, contradiction scores, and independent alternatives.</p>"
            + "<div style='display:grid;grid-template-columns:repeat(auto-fill,minmax(280px,1fr));gap:16px'>"
            + cards
            + "</div></main></body></html>"
        )
        return html

    @app.route('/category/<cat_slug>')
    def category_page(cat_slug):
        meta = CATEGORY_DEFS.get(cat_slug)
        if not meta:
            return "Category not found", 404
        terms = CAT_MAP.get(cat_slug, [meta['label']])
        conn = get_db()
        c = conn.cursor()
        placeholders = ','.join('?' * len(terms))
        c.execute(
            "SELECT b.name, b.slug, b.acquired_year, b.founded_year, b.contradiction_score,"
            " b.headline_finding, b.pe_owned, b.certifications,"
            " co.name as parent_name, co.ownership_type"
            " FROM brands b LEFT JOIN companies co ON b.parent_company_id=co.id"
            " WHERE b.category IN (" + placeholders + ")"
            " ORDER BY b.contradiction_score DESC NULLS LAST, b.name",
            terms)
        rows = c.fetchall()
        conn.close()
        conglomerate_count = sum(1 for r in rows if r['parent_name'])
        independent_count = len(rows) - conglomerate_count
        rows_html = ''
        for r in rows:
            sc = r['contradiction_score'] or 0
            col = score_color(sc)
            parent_txt = r['parent_name'] or '✓ Independent'
            parent_col = GREEN if not r['parent_name'] else AMBER
            pe_badge = ("<span style='font-size:8px;background:var(--rlt);color:var(--red);"
                        "border-radius:4px;padding:1px 5px;margin-left:6px'>PE</span>") if r['pe_owned'] else ''
            acq_yr = (' &middot; acq. ' + str(r['acquired_year'])) if r['acquired_year'] else ''
            b_slug = r['slug'] or ''
            certs = r['certifications'] or ''
            cert_pills = ''.join(
                "<span style='font-size:8px;border:1px solid rgba(58,138,90,0.4);border-radius:20px;"
                "padding:1px 7px;color:var(--green);margin-right:4px'>" + ct.strip() + "</span>"
                for ct in certs.split(',') if ct.strip()
            )
            headline = r['headline_finding'] or ''
            rows_html += (
                "<div style='border:1px solid var(--border);border-radius:10px;padding:16px 20px;"
                "display:flex;align-items:center;gap:16px'>"
                "<div style='flex:1'>"
                "<div style='display:flex;align-items:center;gap:8px;margin-bottom:2px'>"
                "<a href='/brand/" + b_slug + "' style='font-size:15px;font-weight:700;color:var(--ink)'>" + (r['name'] or '') + "</a>"
                + pe_badge +
                "</div>"
                "<div style='font-size:10px;color:" + parent_col + ";margin-bottom:4px'>" + parent_txt + acq_yr + "</div>"
                + (("<div style='font-size:9px;color:var(--muted);margin-bottom:6px'>" + headline[:120] + ("…" if len(headline) > 120 else "") + "</div>") if headline else "")
                + cert_pills
                + "</div>"
                "<div style='text-align:right;min-width:48px'>"
                "<div style='font-size:24px;font-weight:700;color:" + col + "'>" + str(sc) + "</div>"
                "<div style='font-size:8px;color:var(--muted)'>score</div>"
                "</div>"
                "</div>"
            )
        html = (
            page_head(meta['label'] + ' | Traced', meta['desc'])
            + "<main style='max-width:900px;margin:0 auto;padding:40px 20px'>"
            + "<div style='margin-bottom:8px'><a href='/categories' style='font-size:10px;color:var(--muted)'>← All Categories</a></div>"
            + "<div style='font-size:32px;margin-bottom:4px'>" + meta['icon'] + "</div>"
            + "<h1 style='font-size:32px;margin-bottom:8px'>" + meta['label'] + "</h1>"
            + "<p style='color:var(--muted);font-size:12px;margin-bottom:16px'>" + meta['desc'] + "</p>"
            + "<div style='display:flex;gap:24px;font-size:11px;margin-bottom:32px'>"
            + "<span><span style='color:var(--red)'>" + str(conglomerate_count) + "</span> conglomerate-owned</span>"
            + "<span><span style='color:var(--green)'>" + str(independent_count) + "</span> independent</span>"
            + "<span style='color:var(--muted)'>" + str(len(rows)) + " total tracked</span>"
            + "</div>"
            + "<div style='display:flex;flex-direction:column;gap:10px'>" + rows_html + "</div>"
            + "</main></body></html>"
        )
        return html

    @app.route('/category/<cat_slug>/independent')
    def category_independent(cat_slug):
        meta = CATEGORY_DEFS.get(cat_slug)
        if not meta:
            return "Category not found", 404
        terms = CAT_MAP.get(cat_slug, [meta['label']])
        conn = get_db()
        c = conn.cursor()
        placeholders = ','.join('?' * len(terms))
        c.execute(
            "SELECT b.name, b.slug, b.founded_year, b.contradiction_score,"
            " b.certifications, b.headline_finding"
            " FROM brands b"
            " WHERE b.category IN (" + placeholders + ")"
            " AND b.parent_company_id IS NULL AND (b.acquired_year IS NULL OR b.acquired_year='')"
            " ORDER BY b.founded_year ASC NULLS LAST",
            terms)
        rows = c.fetchall()
        conn.close()
        rows_html = ''
        for r in rows:
            certs = r['certifications'] or ''
            cert_pills = ''.join(
                "<span style='font-size:8px;border:1px solid rgba(58,138,90,0.4);border-radius:20px;"
                "padding:1px 7px;color:var(--green);margin-right:4px'>" + ct.strip() + "</span>"
                for ct in certs.split(',') if ct.strip()
            )
            b_slug = r['slug'] or ''
            rows_html += (
                "<div style='border:1px solid rgba(58,138,90,0.2);border-radius:10px;padding:14px 18px'>"
                "<a href='/brand/" + b_slug + "' style='font-size:14px;font-weight:700;color:var(--ink)'>" + (r['name'] or '') + "</a>"
                + (("<div style='color:var(--green);font-size:10px;margin:2px 0'>Founded " + str(r['founded_year']) + "</div>") if r['founded_year'] else "")
                + cert_pills
                + "</div>"
            )
        html = (
            page_head('Independent ' + meta['label'] + ' | Traced', 'Independent ' + meta['label'] + ' brands with no major corporate acquisition.')
            + "<main style='max-width:900px;margin:0 auto;padding:40px 20px'>"
            + "<div style='margin-bottom:8px'><a href='/category/" + cat_slug + "' style='font-size:10px;color:var(--muted)'>← " + meta['label'] + "</a></div>"
            + "<h1 style='font-size:28px;margin-bottom:8px'>Independent " + meta['label'] + "</h1>"
            + "<p style='color:var(--muted);font-size:12px;margin-bottom:28px'>These brands have not been acquired by a major conglomerate. Independence does not guarantee quality.</p>"
            + "<div style='display:grid;grid-template-columns:repeat(auto-fill,minmax(220px,1fr));gap:12px'>" + rows_html + "</div>"
            + "</main></body></html>"
        )
        return html

    # ══════════════════════════════════════════════════════════════════
    # PHASE 6 — RECEIPT AUDIT
    # ══════════════════════════════════════════════════════════════════

    @app.route('/audit')
    def audit_page():
        html = (
            page_head('Receipt Audit | Traced', 'Paste your grocery receipt and get a contradiction report on every brand.')
            + "<main style='max-width:800px;margin:0 auto;padding:40px 20px'>"
            + "<h1 style='font-size:32px;margin-bottom:8px'>Receipt Audit</h1>"
            + "<p style='color:var(--muted);font-size:12px;margin-bottom:24px'>"
            + "Paste your grocery receipt below. Traced will identify every brand and score your basket.</p>"
            + "<textarea id='receipt-input' placeholder='Paste your receipt here...\n\nExample:\nKashi GOLEAN Cereal $4.99\nAnnie&#39;s Mac and Cheese $2.49\nNaked Juice Green Machine $3.79\nChomps Beef Sticks $11.99'"
            + " style='width:100%;height:200px;background:var(--surface);border:1px solid var(--b2);"
            + "border-radius:10px;padding:16px;color:var(--ink);font-family:inherit;font-size:12px;"
            + "resize:vertical;outline:none;margin-bottom:16px'></textarea>"
            + "<button onclick='runAudit()' style='background:var(--amber);color:#000;border:none;"
            + "border-radius:8px;padding:12px 28px;font-family:inherit;font-size:11px;"
            + "letter-spacing:.08em;cursor:pointer;text-transform:uppercase'>Audit My Receipt</button>"
            + "<div id='audit-results' style='margin-top:32px'></div>"
            + "<script>"
            + "async function runAudit(){"
            + "const txt=document.getElementById('receipt-input').value;"
            + "if(!txt.trim()){alert('Paste a receipt first');return;}"
            + "document.getElementById('audit-results').innerHTML='<div style=\"color:var(--muted);font-size:12px\">Analyzing...</div>';"
            + "try{"
            + "const r=await fetch('/api/v1/audit',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({text:txt})});"
            + "const d=await r.json();"
            + "renderAudit(d);"
            + "}catch(e){document.getElementById('audit-results').innerHTML='<div style=\"color:var(--red)\">Error connecting to Traced API.</div>';}"
            + "}"
            + "function renderAudit(d){"
            + "if(!d.results||!d.results.length){document.getElementById('audit-results').innerHTML='<div style=\"color:var(--muted)\">No brands detected in your receipt.</div>';return;}"
            + "let avg=d.avg_score||0;"
            + "let col=avg>=70?'var(--red)':avg>=40?'var(--amber)':'var(--green)';"
            + "let html='<div style=\"border:1px solid var(--border);border-radius:12px;padding:20px 24px;margin-bottom:24px\">';"
            + "html+='<div style=\"font-size:11px;color:var(--muted);margin-bottom:4px\">BASKET SCORE</div>';"
            + "html+='<div style=\"font-size:48px;font-weight:700;color:'+col+'\">'+(Math.round(avg)||0)+'</div>';"
            + "html+='<div style=\"font-size:10px;color:var(--muted)\">'+(d.results.length)+' brands detected &middot; '+(d.conglomerate_count||0)+' conglomerate-owned &middot; '+(d.independent_count||0)+' independent</div>';"
            + "html+='</div>';"
            + "d.results.forEach(b=>{"
            + "let sc=b.contradiction_score||0;"
            + "let c=sc>=70?'var(--red)':sc>=40?'var(--amber)':'var(--green)';"
            + "let parent=b.parent||'Independent';"
            + "let parentCol=b.parent?'var(--amber)':'var(--green)';"
            + "html+='<div style=\"border:1px solid var(--border);border-radius:10px;padding:14px 18px;margin-bottom:10px;display:flex;align-items:center;gap:16px\">';"
            + "html+='<div style=\"flex:1\">';"
            + "html+='<a href=\"/brand/'+(b.slug||'')+('\" style=\"font-size:14px;font-weight:700;color:var(--ink)\">')+b.name+'</a>';"
            + "html+='<div style=\"font-size:10px;color:'+parentCol+';margin-top:2px\">'+parent+'</div>';"
            + "html+=(b.headline_finding?'<div style=\"font-size:9px;color:var(--muted);margin-top:4px\">'+b.headline_finding.substring(0,100)+'...</div>':'');"
            + "html+='</div><div style=\"font-size:22px;font-weight:700;color:'+c+'\">'+sc+'</div></div>';"
            + "});"
            + "document.getElementById('audit-results').innerHTML=html;"
            + "}"
            + "</script>"
            + "</main></body></html>"
        )
        return html

    # ══════════════════════════════════════════════════════════════════
    # PHASE 7 — WATCHLIST
    # ══════════════════════════════════════════════════════════════════

    @app.route('/watchlist')
    def watchlist_page():
        html = (
            page_head('My Watchlist | Traced', 'Track brands you care about. Get alerts when ownership or ingredients change.')
            + "<main style='max-width:800px;margin:0 auto;padding:40px 20px'>"
            + "<h1 style='font-size:32px;margin-bottom:8px'>My Watchlist</h1>"
            + "<p style='color:var(--muted);font-size:12px;margin-bottom:24px'>"
            + "Brands you're watching. Add brands from any brand page.</p>"
            + "<div id='watchlist-empty' style='display:none;color:var(--muted);font-size:12px;padding:40px;text-align:center'>"
            + "Your watchlist is empty.<br>Visit a brand page and click <strong style='color:var(--amber)'>+ Watch</strong>.</div>"
            + "<div id='watchlist-items' style='display:flex;flex-direction:column;gap:10px'></div>"
            + "<script>"
            + "(function(){"
            + "const slugs=JSON.parse(localStorage.getItem('traced_watchlist')||'[]');"
            + "const container=document.getElementById('watchlist-items');"
            + "const empty=document.getElementById('watchlist-empty');"
            + "if(!slugs.length){empty.style.display='block';return;}"
            + "slugs.forEach(async slug=>{"
            + "try{"
            + "const r=await fetch('/api/brand/'+slug);"
            + "const d=await r.json();"
            + "if(d.error){return;}"
            + "const sc=d.contradiction_score||0;"
            + "const col=sc>=70?'var(--red)':sc>=40?'var(--amber)':'var(--green)';"
            + "const parent=d.parent_company||'Independent';"
            + "const parentCol=d.parent_company?'var(--amber)':'var(--green)';"
            + "const div=document.createElement('div');"
            + "div.style.cssText='border:1px solid var(--border);border-radius:10px;padding:14px 18px;display:flex;align-items:center;gap:16px';"
            + "div.innerHTML='<div style=\"flex:1\"><a href=\"/brand/'+slug+'\" style=\"font-size:14px;font-weight:700;color:var(--ink)\">'+d.name+'</a>"
            + "<div style=\"font-size:10px;color:'+parentCol+';margin-top:2px\">'+parent+'</div></div>"
            + "<div style=\"font-size:22px;font-weight:700;color:'+col+'\">'+sc+'</div>"
            + "<button onclick=\"removeFromWatchlist(\\\"'+slug+'\\\")\" style=\"background:none;border:1px solid var(--border);border-radius:6px;padding:4px 10px;color:var(--muted);cursor:pointer;font-size:9px\">Remove</button>';"
            + "container.appendChild(div);"
            + "}catch(e){}"
            + "});"
            + "})()"
            + "function removeFromWatchlist(slug){"
            + "let list=JSON.parse(localStorage.getItem('traced_watchlist')||'[]');"
            + "list=list.filter(s=>s!==slug);"
            + "localStorage.setItem('traced_watchlist',JSON.stringify(list));"
            + "location.reload();"
            + "}"
            + "</script>"
            + "</main></body></html>"
        )
        return html

    @app.route('/api/brand/<bslug>/alerts')
    def brand_alerts(bslug):
        conn = get_db()
        c = conn.cursor()
        c.execute(
            "SELECT event_type, event_date, headline, description FROM brand_events"
            " WHERE brand_id=(SELECT id FROM brands WHERE slug=? OR lower(name)=lower(?))"
            " ORDER BY event_date DESC LIMIT 10",
            (bslug, bslug))
        events = [dict(r) for r in c.fetchall()]
        conn.close()
        return jsonify({'slug': bslug, 'alerts': events})

    # ══════════════════════════════════════════════════════════════════
    # ══════════════════════════════════════════════════════════════════
    # PHASE 11 — API v1 WITH FILTERING + RECEIPT AUDIT POST
    # ══════════════════════════════════════════════════════════════════

    @app.route('/api/v1/brands')
    def api_v1_brands():
        category   = request.args.get('category', '').strip()
        owner      = request.args.get('owner', '').strip()
        pe_owned   = request.args.get('pe_owned', '').strip()
        independent = request.args.get('independent', '').strip()
        min_score  = request.args.get('min_score', '').strip()
        max_score  = request.args.get('max_score', '').strip()
        limit      = min(int(request.args.get('limit', 50)), 200)
        offset_v   = int(request.args.get('offset', 0))

        where = []
        params = []
        if category:
            where.append("b.category LIKE ?"); params.append('%' + category + '%')
        if owner:
            where.append("co.name LIKE ?"); params.append('%' + owner + '%')
        if pe_owned == '1':
            where.append("b.pe_owned = 1")
        if independent == '1':
            where.append("b.parent_company_id IS NULL")
        if min_score:
            where.append("b.contradiction_score >= ?"); params.append(int(min_score))
        if max_score:
            where.append("b.contradiction_score <= ?"); params.append(int(max_score))

        where_clause = ('WHERE ' + ' AND '.join(where)) if where else ''
        conn = get_db()
        c = conn.cursor()
        c.execute(
            "SELECT b.name, b.slug, b.category, b.sub_category, b.contradiction_score,"
            " b.acquired_year, b.founded_year, b.pe_owned, b.headline_finding,"
            " b.certifications, co.name as parent_company, co.ownership_type"
            " FROM brands b LEFT JOIN companies co ON b.parent_company_id=co.id "
            + where_clause +
            " ORDER BY b.contradiction_score DESC NULLS LAST LIMIT ? OFFSET ?",
            params + [limit, offset_v])
        rows = [dict(r) for r in c.fetchall()]
        c.execute("SELECT COUNT(*) FROM brands b LEFT JOIN companies co ON b.parent_company_id=co.id " + where_clause, params)
        total = c.fetchone()[0]
        conn.close()
        return jsonify({'total': total, 'limit': limit, 'offset': offset_v, 'results': rows})

    @app.route('/api/v1/brand/<bslug>')
    def api_v1_brand(bslug):
        conn = get_db()
        c = conn.cursor()
        c.execute(
            "SELECT b.*, co.name as parent_company, co.ownership_type, co.description as company_description"
            " FROM brands b LEFT JOIN companies co ON b.parent_company_id=co.id"
            " WHERE b.slug=? OR lower(b.name)=lower(?)",
            (bslug, bslug))
        row = c.fetchone()
        if not row:
            conn.close(); return jsonify({'error': 'Brand not found'}), 404
        d = dict(row)
        if d.get('contradiction_reasons'):
            try: d['contradiction_reasons'] = json.loads(d['contradiction_reasons'])
            except: pass
        # ingredient drift
        c.execute(
            "SELECT change_date, change_summary, ingredients_added, ingredients_removed, pre_acquisition_ingredients, post_acquisition_ingredients"
            " FROM ingredient_drift WHERE brand_id=? ORDER BY change_date DESC",
            (d['id'],))
        d['ingredient_drift'] = [dict(r) for r in c.fetchall()]
        # brand events
        c.execute(
            "SELECT event_type, event_date, headline, description, source_url"
            " FROM brand_events WHERE brand_id=? ORDER BY event_date DESC LIMIT 10",
            (d['id'],))
        d['events'] = [dict(r) for r in c.fetchall()]
        conn.close()
        return jsonify(d)

    @app.route('/api/v1/categories')
    def api_v1_categories():
        conn = get_db()
        c = conn.cursor()
        c.execute(
            "SELECT category, COUNT(*) as count,"
            " AVG(contradiction_score) as avg_score,"
            " SUM(CASE WHEN parent_company_id IS NOT NULL THEN 1 ELSE 0 END) as acquired_count"
            " FROM brands WHERE category IS NOT NULL AND category != ''"
            " GROUP BY category ORDER BY count DESC")
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return jsonify(rows)

    @app.route('/api/v1/audit', methods=['POST'])
    def api_v1_audit():
        data = request.get_json(force=True) or {}
        text = data.get('text', '')
        if not text:
            return jsonify({'error': 'No text provided'}), 400
        # Extract candidate brand names (capitalized words/phrases)
        words = re.findall(r"[A-Z][a-z]+(?:\s+[A-Z][a-z'&]+)*", text)
        # Also try 2-word combos
        candidates = list(set(words))
        candidates += [' '.join(t) for t in zip(words, words[1:])]

        conn = get_db()
        c = conn.cursor()
        results = []
        seen = set()
        for cand in candidates:
            cand = cand.strip()
            if len(cand) < 3 or cand.lower() in seen:
                continue
            c.execute(
                "SELECT b.name, b.slug, b.contradiction_score, b.headline_finding,"
                " b.pe_owned, co.name as parent"
                " FROM brands b LEFT JOIN companies co ON b.parent_company_id=co.id"
                " WHERE lower(b.name)=lower(?) OR b.slug=lower(?)"
                " LIMIT 1",
                (cand, re.sub(r'[^a-z0-9]+', '-', cand.lower())))
            row = c.fetchone()
            if row and row['name'].lower() not in seen:
                seen.add(row['name'].lower())
                results.append(dict(row))
        conn.close()
        if not results:
            return jsonify({'results': [], 'avg_score': 0, 'conglomerate_count': 0, 'independent_count': 0})
        avg = sum(r['contradiction_score'] or 0 for r in results) / len(results)
        conglomerate_count = sum(1 for r in results if r['parent'])
        independent_count = len(results) - conglomerate_count
        return jsonify({
            'results': results,
            'avg_score': round(avg, 1),
            'conglomerate_count': conglomerate_count,
            'independent_count': independent_count,
        })

    @app.route('/api/v1/ingredient-drift')
    def api_v1_ingredient_drift():
        brand_slug = request.args.get('brand', '').strip()
        conn = get_db()
        c = conn.cursor()
        if brand_slug:
            c.execute(
                "SELECT id.* FROM ingredient_drift id"
                " JOIN brands b ON id.brand_id=b.id"
                " WHERE b.slug=? OR lower(b.name)=lower(?)"
                " ORDER BY id.change_date DESC",
                (brand_slug, brand_slug))
        else:
            c.execute("SELECT * FROM ingredient_drift ORDER BY change_date DESC LIMIT 50")
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return jsonify(rows)

    @app.route('/api/v1/stats')
    def api_v1_stats():
        conn = get_db()
        c = conn.cursor()
        stats = {}
        for k, q in [
            ('brands',           'SELECT COUNT(*) FROM brands'),
            ('companies',        'SELECT COUNT(*) FROM companies'),
            ('products',         'SELECT COUNT(*) FROM products'),
            ('violations',       'SELECT COUNT(*) FROM violations'),
            ('lobbying_records', 'SELECT COUNT(*) FROM lobbying_records'),
            ('brand_events',     'SELECT COUNT(*) FROM brand_events'),
            ('ingredient_drift', 'SELECT COUNT(*) FROM ingredient_drift'),
        ]:
            c.execute(q); stats[k] = c.fetchone()[0]
        c.execute("SELECT SUM(total_spend) FROM lobbying_records")
        stats['total_lobbying_spend'] = round(c.fetchone()[0] or 0)
        c.execute("SELECT SUM(fine_amount) FROM violations WHERE fine_amount IS NOT NULL")
        stats['total_fines'] = round(c.fetchone()[0] or 0)
        c.execute("SELECT COUNT(*) FROM brands WHERE parent_company_id IS NOT NULL")
        stats['brands_acquired'] = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM brands WHERE parent_company_id IS NULL")
        stats['brands_independent'] = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM brands WHERE pe_owned=1")
        stats['brands_pe_owned'] = c.fetchone()[0]
        conn.close()
        return jsonify(stats)

    # ════════════════════════════════════════════════════════════════════
    # PHASE 5 — LAYER 2: POSITIVE DISCOVERY ROUTES
    # ════════════════════════════════════════════════════════════════════

    # ── /independent ────────────────────────────────────────────────────
    @app.route('/independent')
    def independent_brands():
        conn = get_db(); c = conn.cursor()
        cat = request.args.get('category', '')
        sql = (
            "SELECT b.name, b.slug, b.category, b.sub_category, b.founded_year, "
            "b.transparency_label, b.ingredient_transparency, b.ownership_tier, "
            "b.founder_still_involved, b.notes as description, b.origin_story, "
            "b.contradiction_score, b.certifications "
            "FROM brands b "
            "WHERE b.transparency_label='transparent' "
            "AND (b.parent_company_id IS NULL OR b.independent=1) "
        )
        params = []
        if cat:
            sql += "AND b.category=? "
            params.append(cat)
        sql += "ORDER BY b.total_scans DESC NULLS LAST LIMIT 200"
        c.execute(sql, params)
        brands = [dict(r) for r in c.fetchall()]

        # category list for filter
        c.execute("SELECT DISTINCT category FROM brands WHERE transparency_label='transparent' AND category IS NOT NULL ORDER BY category")
        cats = [r['category'] for r in c.fetchall()]

        # stats
        c.execute("SELECT COUNT(*) FROM brands WHERE transparency_label='transparent' AND (parent_company_id IS NULL OR independent=1)")
        total_indep = c.fetchone()[0]
        c.execute("SELECT COUNT(*) FROM brands WHERE transparency_label='transparent' AND founder_still_involved=1")
        founder_count = c.fetchone()[0]
        conn.close()

        # category filter bar
        cat_links = "<a href='/independent' style='color:" + ("var(--amber)" if not cat else "var(--muted)") + ";font-size:10px;letter-spacing:.08em'>ALL</a> "
        for cc in cats:
            active = cat == cc
            cat_links += (
                "<a href='/independent?category=" + cc + "' "
                "style='color:" + ("var(--amber)" if active else "var(--muted)") + ";"
                "font-size:10px;letter-spacing:.08em'>" + cc.upper().replace('-', ' ') + "</a> "
            )

        rows = ''
        for b in brands:
            label_color = GREEN
            it = b.get('ingredient_transparency') or ''
            it_badge = ''
            if it == 'high':
                it_badge = "<span style='color:var(--green);font-size:9px'>FULL DISCLOSURE</span>"
            elif it == 'medium':
                it_badge = "<span style='color:var(--amber);font-size:9px'>MEDIUM TRANSPARENCY</span>"
            certs = b.get('certifications') or ''
            cert_str = ''
            if certs:
                for cert in certs.split(',')[:3]:
                    cert = cert.strip()
                    if cert:
                        cert_str += "<span style='background:var(--glt);color:var(--green);font-size:9px;padding:2px 6px;border-radius:3px;margin-right:4px'>" + cert + "</span>"
            founded = (' · Est. ' + str(b['founded_year'])) if b.get('founded_year') else ''
            rows += (
                "<div style='border:1px solid var(--border);border-radius:8px;padding:20px;"
                "margin-bottom:12px;background:var(--surface)'>"
                "<div style='display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px'>"
                "<div>"
                "<a href='/brand/" + (b['slug'] or '') + "' style='font-size:18px;font-weight:600;color:var(--ink)'>" + b['name'] + "</a>"
                "<span style='color:var(--muted);font-size:10px;margin-left:10px'>" + (b.get('category') or '').upper().replace('-', ' ') + founded + "</span>"
                "</div>"
                "<span style='background:var(--glt);color:var(--green);font-size:10px;padding:4px 10px;border-radius:4px;font-weight:600'>TRANSPARENT</span>"
                "</div>"
                + ("<div style='color:var(--muted);font-size:12px;margin-top:8px;line-height:1.5'>" + (b.get('description') or '')[:160] + "...</div>" if b.get('description') else '')
                + "<div style='margin-top:10px;display:flex;gap:8px;flex-wrap:wrap;align-items:center'>"
                + it_badge + cert_str
                + ("  <span style='color:var(--green);font-size:9px'>FOUNDER-LED</span>" if b.get('founder_still_involved') else '')
                + "</div></div>"
            )

        head = page_head(
            'Independent & Transparent Brands — Traced',
            'Discover ' + str(total_indep) + ' genuinely transparent, independent food and wellness brands vetted by Traced.',
            canonical='https://tracedhealth.com/independent'
        )
        html = (
            head
            + "<div style='max-width:900px;margin:0 auto;padding:40px 20px'>"
            + "<h1 style='font-size:clamp(28px,5vw,48px);margin-bottom:8px'>Independent &amp; Transparent Brands</h1>"
            + "<p style='color:var(--muted);font-size:13px;margin-bottom:24px'>"
            + str(total_indep) + " brands verified as founder-led or cooperative, "
            + "with honest ingredient disclosure and no documented deception. "
            + str(founder_count) + " still led by original founders."
            + "</p>"
            + "<div style='display:flex;gap:12px;flex-wrap:wrap;margin-bottom:24px'>"
            + cat_links
            + "</div>"
            + rows
            + "</div></body></html>"
        )
        return html

    # ── /transparent50 ──────────────────────────────────────────────────
    @app.route('/transparent50')
    def transparent50():
        conn = get_db(); c = conn.cursor()
        c.execute(
            "SELECT b.name, b.slug, b.category, b.transparency_label, "
            "b.ingredient_transparency, b.ownership_tier, b.founder_still_involved, "
            "b.notes as description, b.contradiction_score, b.certifications, b.founded_year, "
            "co.name as parent_name "
            "FROM brands b LEFT JOIN companies co ON b.parent_company_id=co.id "
            "WHERE b.transparency_label IN ('transparent','complicated') "
            "ORDER BY b.transparency_label ASC, b.total_scans DESC NULLS LAST LIMIT 50"
        )
        brands = [dict(r) for r in c.fetchall()]
        conn.close()

        rows = ''
        for i, b in enumerate(brands):
            label = b.get('transparency_label') or 'complicated'
            if label == 'transparent':
                bg = "var(--glt)"; border_col = "var(--green)"; label_txt = "TRANSPARENT"
            else:
                bg = "rgba(212,149,42,0.08)"; border_col = "var(--amber)"; label_txt = "COMPLICATED"
            it = (b.get('ingredient_transparency') or '').upper()
            rows += (
                "<div style='display:flex;align-items:center;gap:16px;padding:14px 0;"
                "border-bottom:1px solid var(--border)'>"
                "<span style='color:var(--muted);font-size:13px;width:28px;text-align:right'>" + str(i+1) + "</span>"
                "<div style='flex:1'>"
                "<a href='/brand/" + (b['slug'] or '') + "' style='font-size:15px;color:var(--ink);font-weight:600'>" + b['name'] + "</a>"
                + ("<span style='color:var(--muted);font-size:10px;margin-left:8px'>" + (b.get('parent_name') or '') + "</span>" if b.get('parent_name') else '')
                + "<div style='color:var(--muted);font-size:10px;margin-top:2px'>"
                + (b.get('category') or '').upper().replace('-', ' ')
                + ((" · " + it + " TRANSPARENCY") if it else '')
                + "</div></div>"
                "<span style='background:" + bg + ";color:" + border_col + ";"
                "font-size:9px;padding:3px 8px;border-radius:3px;white-space:nowrap'>" + label_txt + "</span>"
                "</div>"
            )

        head = page_head(
            'Top 50 Transparent Brands — Traced',
            'The 50 most transparent food brands ranked by ingredient honesty, founder involvement, and ownership integrity.',
            canonical='https://tracedhealth.com/transparent50'
        )
        return (
            head
            + "<div style='max-width:800px;margin:0 auto;padding:40px 20px'>"
            "<h1 style='font-size:clamp(28px,5vw,46px);margin-bottom:8px'>Top 50 Transparent Brands</h1>"
            "<p style='color:var(--muted);font-size:13px;margin-bottom:32px'>"
            "Ranked by ingredient transparency, ownership integrity, and founder involvement. "
            "No conglomerate ownership, no documented deception."
            "</p>"
            + rows
            + "<div style='margin-top:32px;padding:16px;background:var(--surface);border-radius:8px'>"
            "<p style='color:var(--muted);font-size:11px'>Methodology: brands scored on ingredient disclosure, "
            "founder involvement, ownership tier, certification integrity, and absence of FTC/FDA actions. "
            "<a href='/api/docs'>API docs</a></p></div>"
            "</div></body></html>"
        )

    # ── /founders ───────────────────────────────────────────────────────
    @app.route('/founders')
    def founders_page():
        conn = get_db(); c = conn.cursor()
        c.execute(
            "SELECT b.name, b.slug, b.category, b.sub_category, b.founded_year, "
            "b.transparency_label, b.ingredient_transparency, b.ownership_tier, "
            "b.founder_still_involved, b.notes as description, b.origin_story, "
            "b.contradiction_score, b.recently_acquired, b.acquisition_age_years, "
            "co.name as parent_name "
            "FROM brands b LEFT JOIN companies co ON b.parent_company_id=co.id "
            "WHERE b.founder_still_involved=1 "
            "ORDER BY b.transparency_label ASC, b.total_scans DESC NULLS LAST LIMIT 100"
        )
        brands = [dict(r) for r in c.fetchall()]
        conn.close()

        rows = ''
        for b in brands:
            label = b.get('transparency_label') or ''
            if label == 'transparent':
                badge = "<span style='background:var(--glt);color:var(--green);font-size:9px;padding:3px 8px;border-radius:3px'>TRANSPARENT</span>"
            elif label == 'documented_deception':
                badge = "<span style='background:var(--rlt);color:var(--red);font-size:9px;padding:3px 8px;border-radius:3px'>DOCUMENTED DECEPTION</span>"
            elif label == 'conflicted':
                badge = "<span style='background:var(--rlt);color:var(--red);font-size:9px;padding:3px 8px;border-radius:3px'>CONFLICTED</span>"
            else:
                badge = "<span style='background:rgba(212,149,42,0.1);color:var(--amber);font-size:9px;padding:3px 8px;border-radius:3px'>COMPLICATED</span>"
            origin = (b.get('origin_story') or b.get('description') or '')[:180]
            acquired_warn = ''
            if b.get('recently_acquired'):
                acquired_warn = (
                    "<div style='background:rgba(196,68,68,0.08);border:1px solid rgba(196,68,68,0.2);"
                    "border-radius:6px;padding:8px 12px;margin-top:10px;font-size:11px;color:var(--red)'>"
                    "Recently acquired by " + (b.get('parent_name') or 'conglomerate') + " — founder may be transitioning out"
                    "</div>"
                )
            rows += (
                "<div style='border:1px solid var(--border);border-radius:8px;padding:20px;margin-bottom:12px;background:var(--surface)'>"
                "<div style='display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px'>"
                "<div>"
                "<a href='/brand/" + (b['slug'] or '') + "' style='font-size:17px;font-weight:600;color:var(--ink)'>" + b['name'] + "</a>"
                "<span style='color:var(--muted);font-size:10px;margin-left:8px'>"
                + (b.get('category') or '').upper().replace('-', ' ')
                + ((' · Est. ' + str(b['founded_year'])) if b.get('founded_year') else '')
                + "</span>"
                "</div>" + badge
                + "</div>"
                + ("<div style='color:var(--muted);font-size:12px;margin-top:8px;line-height:1.5'>" + origin + ("..." if len(origin) == 180 else "") + "</div>" if origin else '')
                + acquired_warn
                + "</div>"
            )

        head = page_head(
            'Founder-Led Brands — Traced',
            'Brands still led by their original founders — the people who built them and still stand behind them.',
            canonical='https://tracedhealth.com/founders'
        )
        return (
            head
            + "<div style='max-width:900px;margin:0 auto;padding:40px 20px'>"
            "<h1 style='font-size:clamp(28px,5vw,46px);margin-bottom:8px'>Founder-Led Brands</h1>"
            "<p style='color:var(--muted);font-size:13px;margin-bottom:32px'>"
            + str(len(brands)) + " brands still operated by their founders. "
            "The people who built these brands still have skin in the game."
            "</p>"
            + rows
            + "</div></body></html>"
        )

    # ── /certifications ─────────────────────────────────────────────────
    @app.route('/certifications')
    def certifications_page():
        conn = get_db(); c = conn.cursor()
        # Brands with certifications, grouped by cert type
        c.execute(
            "SELECT b.name, b.slug, b.category, b.certifications, "
            "b.transparency_label, b.certifications_maintained_post_acquisition, "
            "b.certification_notes, b.ownership_tier, co.name as parent_name "
            "FROM brands b LEFT JOIN companies co ON b.parent_company_id=co.id "
            "WHERE b.certifications IS NOT NULL AND b.certifications != '' "
            "ORDER BY b.certifications_maintained_post_acquisition DESC, b.total_scans DESC NULLS LAST"
        )
        brands = [dict(r) for r in c.fetchall()]
        conn.close()

        # group by cert type
        cert_map = {}
        for b in brands:
            certs_raw = b.get('certifications') or ''
            for cert in certs_raw.split(','):
                cert = cert.strip()
                if not cert: continue
                cert_map.setdefault(cert, []).append(b)

        cert_sections = ''
        for cert_name in sorted(cert_map.keys()):
            cert_brands = cert_map[cert_name]
            brand_chips = ''
            for b in cert_brands[:20]:
                label = b.get('transparency_label') or ''
                col = GREEN if label == 'transparent' else (RED if label in ('conflicted', 'documented_deception') else AMBER)
                maintained = b.get('certifications_maintained_post_acquisition')
                border_style = ''
                if maintained == 0 and b.get('parent_name'):
                    border_style = "border:1px solid rgba(196,68,68,0.4);"
                brand_chips += (
                    "<a href='/brand/" + (b['slug'] or '') + "' "
                    "style='display:inline-block;background:var(--surface);" + border_style
                    + "border-radius:6px;padding:6px 12px;margin:4px;font-size:12px;color:var(--ink)'>"
                    + b['name']
                    + ("  <span style='color:var(--red);font-size:9px'>LAPSED</span>" if maintained == 0 and b.get('parent_name') else '')
                    + "</a>"
                )
            cert_sections += (
                "<div style='margin-bottom:32px'>"
                "<h2 style='font-size:16px;color:var(--amber);letter-spacing:.06em;margin-bottom:12px'>"
                + cert_name.upper() + " <span style='color:var(--muted);font-size:11px;font-family:DM Mono'>(" + str(len(cert_brands)) + ")</span>"
                "</h2>"
                "<div style='display:flex;flex-wrap:wrap'>" + brand_chips + "</div>"
                "</div>"
            )

        head = page_head(
            'Certified Brands — Traced',
            'Browse food and wellness brands by certification type — organic, non-GMO, B Corp, and more.',
            canonical='https://tracedhealth.com/certifications'
        )
        return (
            head
            + "<div style='max-width:900px;margin:0 auto;padding:40px 20px'>"
            "<h1 style='font-size:clamp(28px,5vw,46px);margin-bottom:8px'>Certified Brands</h1>"
            "<p style='color:var(--muted);font-size:13px;margin-bottom:32px'>"
            "Certifications by type. Brands marked LAPSED lost certification after acquisition."
            "</p>"
            + cert_sections
            + "</div></body></html>"
        )

    # ════════════════════════════════════════════════════════════════════
    # PHASE 6 — LAYER 3: SOLUTIONS ROUTES
    # ════════════════════════════════════════════════════════════════════

    # ── /swap/<brand_slug> ──────────────────────────────────────────────
    @app.route('/swap/<slug>')
    def clean_swap(slug):
        conn = get_db(); c = conn.cursor()
        c.execute(
            "SELECT b.id, b.name, b.slug, b.category, b.transparency_label, "
            "b.headline_finding, b.ownership_tier, b.ingredient_transparency, "
            "co.name as parent_name "
            "FROM brands b LEFT JOIN companies co ON b.parent_company_id=co.id "
            "WHERE b.slug=? OR lower(b.name)=lower(?)",
            (slug, slug)
        )
        brand = c.fetchone()
        if not brand:
            conn.close()
            return "<h1>Brand not found</h1>", 404
        b = dict(brand)

        # Look up clean swaps
        c.execute(
            "SELECT cs.reason, cs.category, "
            "ab.name as alt_name, ab.slug as alt_slug, ab.notes as alt_desc, "
            "ab.transparency_label as alt_label, ab.ingredient_transparency as alt_it, "
            "ab.founded_year as alt_founded, ab.certifications as alt_certs, "
            "ab.ownership_tier as alt_tier "
            "FROM clean_swaps cs "
            "JOIN brands ab ON cs.alternative_brand_id = ab.id "
            "WHERE cs.brand_id=?",
            (b['id'],)
        )
        swaps = [dict(r) for r in c.fetchall()]

        # Fallback: find by category
        if not swaps:
            c.execute(
                "SELECT b2.name, b2.slug, b2.description, b2.transparency_label, "
                "b2.ingredient_transparency, b2.founded_year, b2.certifications, "
                "b2.ownership_tier "
                "FROM brands b2 "
                "WHERE b2.category=? AND b2.transparency_label='transparent' "
                "AND b2.id != ? "
                "ORDER BY b2.total_scans DESC NULLS LAST LIMIT 5",
                (b.get('category') or '', b['id'])
            )
            rows = [dict(r) for r in c.fetchall()]
            swaps = [{'alt_name': r['name'], 'alt_slug': r['slug'], 'alt_desc': r.get('description'),
                      'alt_label': r['transparency_label'], 'alt_it': r.get('ingredient_transparency'),
                      'alt_founded': r.get('founded_year'), 'alt_certs': r.get('certifications'),
                      'alt_tier': r.get('ownership_tier'), 'reason': 'Independent alternative in same category',
                      'category': b.get('category')} for r in rows]
        conn.close()

        label = b.get('transparency_label') or ''
        if label == 'documented_deception':
            warn_color = RED; warn_bg = "rgba(196,68,68,0.08)"
            warn_text = b.get('headline_finding') or ('Documented deception linked to ' + b['name'])
        elif label == 'conflicted':
            warn_color = RED; warn_bg = "rgba(196,68,68,0.06)"
            warn_text = b.get('headline_finding') or ((b.get('parent_name') or '') + ' owns ' + b['name'])
        else:
            warn_color = AMBER; warn_bg = "rgba(212,149,42,0.06)"
            warn_text = "Owned by " + (b.get('parent_name') or 'undisclosed parent')

        swap_cards = ''
        for s in swaps:
            alt_label = s.get('alt_label') or ''
            it_txt = (s.get('alt_it') or '').upper()
            certs_raw = s.get('alt_certs') or ''
            cert_chips = ''
            for cert in certs_raw.split(',')[:3]:
                cert = cert.strip()
                if cert:
                    cert_chips += "<span style='background:var(--glt);color:var(--green);font-size:9px;padding:2px 6px;border-radius:3px;margin-right:4px'>" + cert + "</span>"
            swap_cards += (
                "<div style='border:1px solid rgba(58,138,90,0.3);border-radius:8px;padding:20px;"
                "background:rgba(58,138,90,0.05);margin-bottom:12px'>"
                "<div style='display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px'>"
                "<div>"
                "<a href='/brand/" + (s.get('alt_slug') or '') + "' style='font-size:17px;font-weight:600;color:var(--ink)'>"
                + (s.get('alt_name') or '') + "</a>"
                + ((" · Est. " + str(s['alt_founded'])) if s.get('alt_founded') else '')
                + "</div>"
                "<span style='background:var(--glt);color:var(--green);font-size:9px;padding:3px 8px;border-radius:3px'>TRANSPARENT</span>"
                "</div>"
                + ("<div style='color:var(--muted);font-size:12px;margin-top:8px;line-height:1.5'>" + (s.get('alt_desc') or '')[:160] + "...</div>" if s.get('alt_desc') else '')
                + "<div style='margin-top:10px;display:flex;gap:8px;flex-wrap:wrap;align-items:center'>"
                + cert_chips
                + ("  <span style='color:var(--green);font-size:9px'>" + it_txt + " TRANSPARENCY</span>" if it_txt else '')
                + "</div>"
                + "<div style='color:var(--muted);font-size:10px;margin-top:8px'><em>" + (s.get('reason') or '') + "</em></div>"
                "</div>"
            )

        if not swap_cards:
            swap_cards = "<p style='color:var(--muted);font-size:13px'>No verified swaps yet. <a href='/independent?category=" + (b.get('category') or '') + "'>Browse independent brands in this category</a>.</p>"

        head = page_head(
            'Clean Swap for ' + b['name'] + ' — Traced',
            'Find independent alternatives to ' + b['name'] + '. Transparent brands in the same category.',
            slug=b['slug']
        )
        return (
            head
            + "<div style='max-width:800px;margin:0 auto;padding:40px 20px'>"
            + "<div style='background:" + warn_bg + ";border-left:3px solid " + warn_color + ";"
            + "padding:16px 20px;border-radius:0 8px 8px 0;margin-bottom:32px'>"
            + "<div style='color:" + warn_color + ";font-size:11px;letter-spacing:.08em;margin-bottom:6px'>WHY SWAP?</div>"
            + "<div style='font-size:15px;font-weight:600;color:var(--ink)'>" + warn_text + "</div>"
            + "<a href='/brand/" + (b['slug'] or '') + "' style='font-size:11px;color:var(--muted);margin-top:6px;display:inline-block'>See full profile for " + b['name'] + " →</a>"
            + "</div>"
            + "<h1 style='font-size:clamp(24px,4vw,38px);margin-bottom:8px'>Clean Swaps for " + b['name'] + "</h1>"
            + "<p style='color:var(--muted);font-size:13px;margin-bottom:28px'>Independent alternatives in the same category with verified ingredient transparency.</p>"
            + swap_cards
            + "<div style='margin-top:32px;border-top:1px solid var(--border);padding-top:24px'>"
            + "<a href='/independent?category=" + (b.get('category') or '') + "' style='color:var(--amber)'>Browse all independent brands in this category →</a>"
            + "</div>"
            + "</div></body></html>"
        )

    # ── /retailers ──────────────────────────────────────────────────────
    @app.route('/retailers')
    def retailer_scorecards():
        conn = get_db(); c = conn.cursor()
        c.execute(
            "SELECT retailer_name, retailer_slug, independent_brand_pct, "
            "conglomerate_brand_pct, pe_brand_pct, transparency_score, "
            "total_brands_tracked, notes "
            "FROM retailer_scores ORDER BY transparency_score DESC"
        )
        retailers = [dict(r) for r in c.fetchall()]
        conn.close()

        rows = ''
        for i, r in enumerate(retailers):
            score = r.get('transparency_score') or 0
            if score >= 70:
                score_col = GREEN; score_bg = "var(--glt)"
            elif score >= 50:
                score_col = AMBER; score_bg = "rgba(212,149,42,0.1)"
            else:
                score_col = RED; score_bg = "var(--rlt)"
            indep_pct = r.get('independent_brand_pct') or 0
            indep_bar_w = str(min(100, indep_pct)) + "%"
            cong_pct = r.get('conglomerate_brand_pct') or 0
            cong_bar_w = str(min(100, cong_pct)) + "%"
            rows += (
                "<div style='border:1px solid var(--border);border-radius:8px;padding:24px;"
                "margin-bottom:16px;background:var(--surface)'>"
                "<div style='display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;margin-bottom:16px'>"
                "<div>"
                "<h2 style='font-size:18px;font-weight:600;margin-bottom:4px'>" + r['retailer_name'] + "</h2>"
                "<span style='color:var(--muted);font-size:11px'>" + (r.get('notes') or '') + "</span>"
                "</div>"
                "<div style='text-align:center'>"
                "<div style='font-size:32px;font-weight:700;font-family:Bebas Neue;color:" + score_col + "'>" + str(score) + "</div>"
                "<div style='font-size:9px;letter-spacing:.08em;color:var(--muted)'>TRANSPARENCY SCORE</div>"
                "</div>"
                "</div>"
                # bar charts
                "<div style='margin-bottom:8px'>"
                "<div style='display:flex;justify-content:space-between;font-size:10px;color:var(--muted);margin-bottom:4px'>"
                "<span>INDEPENDENT BRANDS</span><span>" + str(round(indep_pct)) + "%</span>"
                "</div>"
                "<div style='background:var(--border);border-radius:4px;height:6px'>"
                "<div style='background:var(--green);border-radius:4px;height:6px;width:" + indep_bar_w + "'></div>"
                "</div></div>"
                "<div>"
                "<div style='display:flex;justify-content:space-between;font-size:10px;color:var(--muted);margin-bottom:4px'>"
                "<span>CONGLOMERATE BRANDS</span><span>" + str(round(cong_pct)) + "%</span>"
                "</div>"
                "<div style='background:var(--border);border-radius:4px;height:6px'>"
                "<div style='background:var(--red);border-radius:4px;height:6px;width:" + cong_bar_w + "'></div>"
                "</div></div>"
                "</div>"
            )

        head = page_head(
            'Retailer Transparency Scorecards — Traced',
            'Which grocery stores carry the most independent brands? Scored by % independent, % conglomerate, and transparency.',
            canonical='https://tracedhealth.com/retailers'
        )
        return (
            head
            + "<div style='max-width:800px;margin:0 auto;padding:40px 20px'>"
            "<h1 style='font-size:clamp(28px,5vw,46px);margin-bottom:8px'>Retailer Transparency Scorecards</h1>"
            "<p style='color:var(--muted);font-size:13px;margin-bottom:32px'>"
            "Which grocery stores give independent brands shelf space? Ranked by percentage of independent brands tracked in each retailer's assortment."
            "</p>"
            + rows
            + "<div style='margin-top:32px;padding:16px;background:var(--surface);border-radius:8px'>"
            "<p style='color:var(--muted);font-size:11px'>"
            "Methodology: brands scored against Traced database of 881 brands. "
            "Retailer assortments estimated from product database. Updated quarterly. "
            "<a href='/api/v1/retailers'>API endpoint available</a>."
            "</p></div>"
            "</div></body></html>"
        )

    # ── /local ──────────────────────────────────────────────────────────
    @app.route('/local')
    def local_markets_page():
        conn = get_db(); c = conn.cursor()
        zip_q = request.args.get('zip', '')
        city_q = request.args.get('city', '').strip()

        sql = ("SELECT id, name, type, address, city, state, zip, "
               "hours, website, accepts_ebt, organic_vendors, year_round "
               "FROM local_markets ")
        params = []
        if zip_q:
            sql += "WHERE zip LIKE ? "; params.append(zip_q[:5] + '%')
        elif city_q:
            sql += "WHERE lower(city) LIKE ? "; params.append('%' + city_q.lower() + '%')
        sql += "ORDER BY name LIMIT 100"
        c.execute(sql, params)
        markets = [dict(r) for r in c.fetchall()]
        c.execute("SELECT COUNT(*) FROM local_markets"); total = c.fetchone()[0]
        conn.close()

        search_form = (
            "<form method='get' action='/local' style='display:flex;gap:12px;flex-wrap:wrap;margin-bottom:32px'>"
            "<input name='zip' value='" + zip_q + "' placeholder='ZIP code' "
            "style='background:var(--surface);border:1px solid var(--border);border-radius:6px;"
            "padding:10px 14px;color:var(--ink);font-family:DM Mono;font-size:13px;width:140px'>"
            "<input name='city' value='" + city_q + "' placeholder='City name' "
            "style='background:var(--surface);border:1px solid var(--border);border-radius:6px;"
            "padding:10px 14px;color:var(--ink);font-family:DM Mono;font-size:13px;flex:1;min-width:160px'>"
            "<button type='submit' style='background:var(--amber);color:#000;border:none;border-radius:6px;"
            "padding:10px 20px;font-family:DM Mono;font-size:12px;cursor:pointer;font-weight:600'>SEARCH</button>"
            "</form>"
        )

        market_cards = ''
        if markets:
            for m in markets:
                type_colors = {'farmers_market': GREEN, 'csa': AMBER, 'food_coop': GREEN, 'natural_grocer': AMBER}
                type_col = type_colors.get(m.get('type') or '', MUTED)
                badges = ''
                if m.get('accepts_ebt'):
                    badges += "<span style='background:rgba(58,138,90,0.1);color:var(--green);font-size:9px;padding:2px 6px;border-radius:3px;margin-right:4px'>EBT ACCEPTED</span>"
                if m.get('year_round'):
                    badges += "<span style='background:var(--surface);color:var(--muted);font-size:9px;padding:2px 6px;border-radius:3px;border:1px solid var(--border);margin-right:4px'>YEAR-ROUND</span>"
                if m.get('organic_vendors'):
                    badges += "<span style='background:var(--glt);color:var(--green);font-size:9px;padding:2px 6px;border-radius:3px'>ORGANIC VENDORS</span>"
                market_cards += (
                    "<div style='border:1px solid var(--border);border-radius:8px;padding:18px;"
                    "margin-bottom:12px;background:var(--surface)'>"
                    "<div style='display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:8px'>"
                    "<div>"
                    "<div style='font-size:16px;font-weight:600;margin-bottom:4px'>" + (m.get('name') or '') + "</div>"
                    "<div style='color:var(--muted);font-size:11px'>"
                    + (m.get('address') or '') + ", " + (m.get('city') or '') + ", " + (m.get('state') or '') + " " + (m.get('zip') or '')
                    + "</div>"
                    "</div>"
                    "<span style='color:" + type_col + ";font-size:9px;letter-spacing:.08em'>" + (m.get('type') or '').upper().replace('_', ' ') + "</span>"
                    "</div>"
                    "<div style='margin-top:10px;display:flex;gap:8px;flex-wrap:wrap;align-items:center'>"
                    + badges
                    + ("  <a href='" + m['website'] + "' style='color:var(--amber);font-size:10px;margin-left:auto' target='_blank'>Website →</a>" if m.get('website') else '')
                    + ("  <span style='color:var(--muted);font-size:10px'>" + m['hours'] + "</span>" if m.get('hours') else '')
                    + "</div>"
                    "</div>"
                )
        elif zip_q or city_q:
            market_cards = (
                "<div style='text-align:center;padding:60px 20px;color:var(--muted)'>"
                "<p style='font-size:16px;margin-bottom:12px'>No markets found for that location yet.</p>"
                "<p style='font-size:12px'>We're building this database. "
                "<a href='mailto:hello@tracedhealth.com'>Submit a market to add.</a></p>"
                "</div>"
            )
        else:
            market_cards = (
                "<div style='text-align:center;padding:60px 20px;color:var(--muted)'>"
                "<p style='font-size:14px'>" + str(total) + " markets in database. Search by ZIP or city to find markets near you.</p>"
                "</div>"
            )

        head = page_head(
            'Local Farmers Markets & Food Co-ops — Traced',
            'Find farmers markets, food co-ops, and CSA programs near you that carry independent and organic food brands.',
            canonical='https://tracedhealth.com/local'
        )
        return (
            head
            + "<div style='max-width:800px;margin:0 auto;padding:40px 20px'>"
            "<h1 style='font-size:clamp(28px,5vw,46px);margin-bottom:8px'>Local Markets &amp; Co-ops</h1>"
            "<p style='color:var(--muted);font-size:13px;margin-bottom:24px'>"
            "Farmers markets, food co-ops, and CSA programs near you. "
            "Skip the conglomerate shelf — buy direct from farmers and local producers."
            "</p>"
            + search_form
            + market_cards
            + "</div></body></html>"
        )

    # ════════════════════════════════════════════════════════════════════
    # PHASE 7+8 — NAV REDESIGN + BRAND PROFILE UPGRADES
    # ════════════════════════════════════════════════════════════════════

    # ── /brand-v3/<slug> — new brand profile page ───────────────────────
    @app.route('/brand/<slug>')
    def brand_profile_v3(slug):
        conn = get_db(); c = conn.cursor()
        c.execute(
            "SELECT b.id, b.name, b.slug, b.category, b.sub_category, b.founded_year, "
            "b.acquired_year, b.acquisition_price, b.independent, b.total_scans, "
            "b.contradiction_score, b.contradiction_reasons, b.headline_finding, b.share_text, "
            "b.transparency_label, b.transparency_label_reasons, b.ownership_tier, "
            "b.ingredient_transparency, b.ingredient_transparency_notes, b.health_claim_flags, "
            "b.certifications, b.certifications_maintained_post_acquisition, b.certification_notes, "
            "b.price_change_post_acquisition, b.watch_list, b.watch_list_reason, "
            "b.recently_acquired, b.acquisition_age_years, b.founder_still_involved, "
            "b.clean_swap_brands, b.notes as description, b.origin_story, b.pe_owned, "
            "co.name as co_name, co.type as co_type, co.hq_country, co.annual_revenue, "
            "co.id as co_id, co.description as co_desc "
            "FROM brands b LEFT JOIN companies co ON b.parent_company_id=co.id "
            "WHERE b.slug=? OR lower(b.name)=lower(?) "
            "ORDER BY b.total_scans DESC NULLS LAST LIMIT 1",
            (slug, slug)
        )
        brand = c.fetchone()
        if not brand:
            conn.close(); return "<h1>Brand not found</h1>", 404
        b = dict(brand)
        co_id = b.get('co_id')

        # related data
        siblings = []; violations = []; lobbying = []; events = []; products = []
        recall_count = 0; fines_total = 0; lobbying_total = 0; lobbying_issues = []
        if co_id:
            c.execute("SELECT name, slug FROM brands WHERE parent_company_id=? AND id!=? ORDER BY total_scans DESC NULLS LAST LIMIT 10", (co_id, b['id']))
            siblings = [dict(r) for r in c.fetchall()]
            c.execute("SELECT violation_type,year,description,outcome,fine_amount FROM violations WHERE company_id=? AND violation_type!='FDA recall' ORDER BY year DESC", (co_id,))
            violations = [dict(r) for r in c.fetchall()]
            c.execute("SELECT COUNT(*) FROM violations WHERE company_id=? AND violation_type='FDA recall'", (co_id,))
            recall_count = c.fetchone()[0]
            c.execute("SELECT year,total_spend,issues FROM lobbying_records WHERE company_id=? ORDER BY year DESC LIMIT 5", (co_id,))
            lobbying = [dict(r) for r in c.fetchall()]
            lobbying_total = sum(r['total_spend'] for r in lobbying)
            for r in lobbying:
                for issue in (r['issues'] or '').split(','):
                    issue = issue.strip()
                    if issue and issue not in lobbying_issues:
                        lobbying_issues.append(issue)
            c.execute("SELECT SUM(fine_amount) FROM violations WHERE company_id=? AND fine_amount IS NOT NULL", (co_id,))
            fines_total = c.fetchone()[0] or 0

        c.execute("SELECT event_type,event_date,headline,description,source_url FROM brand_events WHERE brand_id=? ORDER BY event_date DESC", (b['id'],))
        events = [dict(r) for r in c.fetchall()]
        c.execute("SELECT p.name,s.additives FROM products p JOIN ingredient_snapshots s ON s.product_id=p.id WHERE p.brand_id=? AND s.additives!='' ORDER BY length(s.additives) DESC LIMIT 8", (b['id'],))
        products = [dict(r) for r in c.fetchall()]
        c.execute("SELECT COUNT(*) FROM products WHERE brand_id=?", (b['id'],))
        product_count = c.fetchone()[0]

        # Clean swaps
        c.execute(
            "SELECT cs.reason, ab.name as alt_name, ab.slug as alt_slug, ab.ingredient_transparency as alt_it "
            "FROM clean_swaps cs JOIN brands ab ON cs.alternative_brand_id=ab.id WHERE cs.brand_id=?",
            (b['id'],)
        )
        swaps = [dict(r) for r in c.fetchall()]

        # Health claims
        c.execute(
            "SELECT claim_text, claim_type, challenged_by, outcome, year, fine_amount FROM health_claims WHERE brand_id=? ORDER BY year DESC",
            (b['id'],)
        )
        health_claims = [dict(r) for r in c.fetchall()]

        conn.close()

        # ── transparency label badge ──
        label = b.get('transparency_label') or ''
        if label == 'transparent':
            label_color = GREEN; label_bg = "var(--glt)"; label_txt = "TRANSPARENT"
        elif label == 'documented_deception':
            label_color = RED; label_bg = "var(--rlt)"; label_txt = "DOCUMENTED DECEPTION"
        elif label == 'conflicted':
            label_color = RED; label_bg = "var(--rlt)"; label_txt = "CONFLICTED"
        else:
            label_color = AMBER; label_bg = "rgba(212,149,42,0.1)"; label_txt = "COMPLICATED"

        # ── ownership tier badge ──
        tier = b.get('ownership_tier') or ''
        tier_labels = {
            'public_conglomerate': ('PUBLIC CONGLOMERATE', RED),
            'private_conglomerate': ('PRIVATE CONGLOMERATE', RED),
            'pe_firm': ('PRIVATE EQUITY', RED),
            'vc_backed': ('VC-BACKED', AMBER),
            'celebrity_backed': ('CELEBRITY-BACKED', AMBER),
            'public_independent': ('PUBLIC INDEPENDENT', AMBER),
            'cooperative': ('COOPERATIVE', GREEN),
            'founder_led': ('FOUNDER-LED', GREEN),
        }
        tier_txt, tier_col = tier_labels.get(tier, ('INDEPENDENT', GREEN))

        # ── headline section ──
        headline = b.get('headline_finding') or ''
        origin = b.get('origin_story') or b.get('description') or ''

        # ── watch list banner ──
        watch_banner = ''
        if b.get('watch_list'):
            watch_banner = (
                "<div style='background:rgba(212,149,42,0.08);border:1px solid rgba(212,149,42,0.3);"
                "border-radius:8px;padding:16px 20px;margin-bottom:24px'>"
                "<div style='color:var(--amber);font-size:10px;letter-spacing:.1em;margin-bottom:6px'>WATCH LIST</div>"
                "<div style='font-size:14px;color:var(--ink)'>" + (b.get('watch_list_reason') or '') + "</div>"
                "</div>"
            )

        # ── recently acquired banner ──
        acquired_banner = ''
        if b.get('recently_acquired'):
            age = b.get('acquisition_age_years') or 0
            age_str = "just acquired" if age == 0 else (str(age) + " year" + ("s" if age != 1 else "") + " ago")
            acquired_banner = (
                "<div style='background:rgba(196,68,68,0.06);border-left:3px solid " + RED + ";"
                "padding:14px 18px;border-radius:0 6px 6px 0;margin-bottom:20px'>"
                "<span style='color:var(--red);font-size:10px;letter-spacing:.08em'>RECENTLY ACQUIRED — " + age_str.upper() + "</span>"
                "<div style='font-size:13px;color:var(--muted);margin-top:4px'>"
                "Formula changes typically occur within 12–24 months of acquisition. Monitor for ingredient drift."
                "</div>"
                "</div>"
            )

        # ── ingredient transparency section ──
        it = b.get('ingredient_transparency') or ''
        it_section = ''
        if it:
            it_labels = {
                'high': ('FULL INGREDIENT DISCLOSURE', GREEN, "All ingredients, sources, and quantities disclosed."),
                'medium': ('PARTIAL DISCLOSURE', AMBER, "Most ingredients listed; some sourcing opacity."),
                'low': ('LIMITED DISCLOSURE', RED, "Key ingredients or sources not disclosed."),
                'opaque': ('OPAQUE', RED, "Proprietary blends or significant undisclosed ingredients."),
            }
            it_txt, it_col, it_desc = it_labels.get(it, ('UNKNOWN', MUTED, ''))
            it_notes = b.get('ingredient_transparency_notes') or ''
            it_section = (
                "<div style='border:1px solid var(--border);border-radius:8px;padding:16px;margin-bottom:16px'>"
                "<div style='font-size:10px;letter-spacing:.08em;color:var(--muted);margin-bottom:8px'>INGREDIENT TRANSPARENCY</div>"
                "<div style='color:" + it_col + ";font-size:14px;font-weight:600;margin-bottom:6px'>" + it_txt + "</div>"
                "<div style='color:var(--muted);font-size:12px'>" + it_desc
                + (" " + it_notes if it_notes else '')
                + "</div>"
                "</div>"
            )

        # ── health claims section ──
        hc_section = ''
        if health_claims:
            hc_rows = ''
            for hc in health_claims:
                outcome = hc.get('outcome') or ''
                out_col = RED if outcome in ('convicted', 'settled_paid') else AMBER
                fine_str = (' · $' + str(round(hc['fine_amount']/1e6, 1)) + 'M fine') if hc.get('fine_amount') else ''
                hc_rows += (
                    "<div style='padding:12px 0;border-bottom:1px solid var(--border)'>"
                    "<div style='font-size:12px;color:var(--ink);margin-bottom:4px'>" + (hc.get('claim_text') or '') + "</div>"
                    "<div style='font-size:10px;color:" + out_col + "'>"
                    + (hc.get('challenged_by') or '') + " · " + outcome.upper().replace('_', ' ')
                    + fine_str + ((' · ' + str(hc['year'])) if hc.get('year') else '')
                    + "</div>"
                    "</div>"
                )
            hc_section = (
                "<div style='border:1px solid rgba(196,68,68,0.3);border-radius:8px;padding:16px;margin-bottom:16px'>"
                "<div style='font-size:10px;letter-spacing:.08em;color:var(--red);margin-bottom:8px'>HEALTH CLAIM RECORD</div>"
                + hc_rows
                + "</div>"
            )

        # ── certifications ──
        cert_section = ''
        certs_raw = b.get('certifications') or ''
        if certs_raw:
            maintained = b.get('certifications_maintained_post_acquisition')
            cert_notes = b.get('certification_notes') or ''
            cert_chips = ''
            for cert in certs_raw.split(','):
                cert = cert.strip()
                if cert:
                    cert_chips += "<span style='background:var(--glt);color:var(--green);font-size:10px;padding:3px 10px;border-radius:4px;margin-right:6px;margin-bottom:6px;display:inline-block'>" + cert + "</span>"
            status_txt = ''
            if maintained == 0 and b.get('co_id'):
                status_txt = "<div style='color:var(--red);font-size:11px;margin-top:8px'>⚠ Certification status reduced or dropped post-acquisition. " + cert_notes + "</div>"
            elif cert_notes:
                status_txt = "<div style='color:var(--muted);font-size:11px;margin-top:8px'>" + cert_notes + "</div>"
            cert_section = (
                "<div style='border:1px solid var(--border);border-radius:8px;padding:16px;margin-bottom:16px'>"
                "<div style='font-size:10px;letter-spacing:.08em;color:var(--muted);margin-bottom:10px'>CERTIFICATIONS</div>"
                "<div style='display:flex;flex-wrap:wrap'>" + cert_chips + "</div>"
                + status_txt
                + "</div>"
            )

        # ── clean swap section ──
        swap_section = ''
        if swaps or label in ('conflicted', 'documented_deception'):
            if swaps:
                swap_rows = ''
                for s in swaps[:3]:
                    it_badge = ''
                    it_val = s.get('alt_it') or ''
                    if it_val in ('high', 'medium'):
                        it_badge = "<span style='color:var(--green);font-size:9px'>" + it_val.upper() + " TRANSPARENCY</span>"
                    swap_rows += (
                        "<div style='display:flex;justify-content:space-between;align-items:center;"
                        "padding:10px 0;border-bottom:1px solid var(--border)'>"
                        "<div>"
                        "<a href='/brand/" + (s.get('alt_slug') or '') + "' style='color:var(--ink);font-size:14px;font-weight:600'>" + (s.get('alt_name') or '') + "</a>"
                        "<div style='color:var(--muted);font-size:10px;margin-top:2px'>" + (s.get('reason') or '') + "</div>"
                        "</div>" + it_badge
                        + "</div>"
                    )
                swap_section = (
                    "<div style='border:1px solid rgba(58,138,90,0.3);border-radius:8px;padding:16px;margin-bottom:16px'>"
                    "<div style='display:flex;justify-content:space-between;align-items:center;margin-bottom:12px'>"
                    "<div style='font-size:10px;letter-spacing:.08em;color:var(--green)'>CLEAN SWAPS</div>"
                    "<a href='/swap/" + (b['slug'] or '') + "' style='font-size:10px;color:var(--amber)'>See all →</a>"
                    "</div>"
                    + swap_rows
                    + "</div>"
                )
            else:
                swap_section = (
                    "<div style='border:1px solid rgba(58,138,90,0.3);border-radius:8px;padding:16px;margin-bottom:16px'>"
                    "<div style='font-size:10px;letter-spacing:.08em;color:var(--green);margin-bottom:8px'>FIND A CLEAN SWAP</div>"
                    "<a href='/swap/" + (b['slug'] or '') + "' style='color:var(--amber);font-size:13px'>"
                    "Browse independent alternatives to " + b['name'] + " →</a>"
                    "</div>"
                )

        # ── siblings section ──
        sibling_html = ''
        if siblings:
            sib_chips = ''
            for s in siblings[:8]:
                sib_chips += "<a href='/brand/" + (s.get('slug') or s['name'].lower().replace(' ', '-')) + "' style='display:inline-block;background:var(--surface);border:1px solid var(--border);border-radius:5px;padding:5px 10px;font-size:11px;color:var(--muted);margin:3px'>" + s['name'] + "</a>"
            sibling_html = (
                "<div style='margin-bottom:24px'>"
                "<div style='font-size:10px;letter-spacing:.08em;color:var(--muted);margin-bottom:10px'>"
                "OTHER BRANDS OWNED BY " + (b.get('co_name') or '').upper()
                + "</div><div style='display:flex;flex-wrap:wrap'>" + sib_chips + "</div>"
                "</div>"
            )

        # ── violations section ──
        violation_html = ''
        if violations or recall_count or fines_total:
            v_rows = ''
            for v in violations[:5]:
                fine_str = (' · $' + str(round(v['fine_amount']/1e6,1)) + 'M') if v.get('fine_amount') else ''
                v_rows += (
                    "<div style='padding:10px 0;border-bottom:1px solid var(--border);font-size:12px'>"
                    "<span style='color:var(--red)'>" + (v.get('violation_type') or '') + "</span>"
                    " — " + (v.get('description') or '') + fine_str
                    + (" <em>(" + str(v['year']) + ")</em>" if v.get('year') else '')
                    + "</div>"
                )
            if recall_count:
                v_rows += "<div style='padding:10px 0;border-bottom:1px solid var(--border);font-size:12px;color:var(--amber)'>" + str(recall_count) + " FDA Recall(s) on record</div>"
            violation_html = (
                "<div style='border:1px solid rgba(196,68,68,0.25);border-radius:8px;padding:16px;margin-bottom:16px'>"
                "<div style='font-size:10px;letter-spacing:.08em;color:var(--red);margin-bottom:8px'>"
                "PARENT VIOLATIONS"
                + (" · $" + str(round(fines_total/1e6, 1)) + "M IN FINES" if fines_total > 0 else '')
                + "</div>"
                + v_rows
                + "</div>"
            )

        # ── events timeline ──
        events_html = ''
        if events:
            ev_rows = ''
            for ev in events[:6]:
                ev_rows += (
                    "<div style='display:flex;gap:12px;padding:10px 0;border-bottom:1px solid var(--border)'>"
                    "<span style='color:var(--muted);font-size:11px;white-space:nowrap;width:90px'>" + (ev.get('event_date') or '')[:10] + "</span>"
                    "<div style='font-size:12px'>"
                    "<div style='color:var(--amber);font-size:9px;letter-spacing:.06em;margin-bottom:3px'>" + (ev.get('event_type') or '').upper().replace('_', ' ') + "</div>"
                    + (ev.get('headline') or ev.get('description') or '')
                    + "</div>"
                    "</div>"
                )
            events_html = (
                "<div style='border:1px solid var(--border);border-radius:8px;padding:16px;margin-bottom:16px'>"
                "<div style='font-size:10px;letter-spacing:.08em;color:var(--muted);margin-bottom:8px'>BRAND TIMELINE</div>"
                + ev_rows
                + "</div>"
            )

        # ── lobbying section ──
        lobby_html = ''
        if lobbying_total > 0:
            issue_chips = ''.join(
                "<span style='background:var(--surface);border:1px solid var(--border);border-radius:4px;"
                "font-size:9px;padding:2px 7px;margin-right:5px;color:var(--muted)'>" + iss + "</span>"
                for iss in lobbying_issues[:6]
            )
            lobby_html = (
                "<div style='border:1px solid var(--border);border-radius:8px;padding:16px;margin-bottom:16px'>"
                "<div style='font-size:10px;letter-spacing:.08em;color:var(--muted);margin-bottom:8px'>PARENT LOBBYING</div>"
                "<div style='font-size:20px;font-family:Bebas Neue;color:var(--amber);margin-bottom:8px'>"
                "$" + str(round(lobbying_total/1e6,1)) + "M lobbied since "
                + (str(lobbying[-1]['year']) if lobbying else '')
                + "</div>"
                + ("<div style='margin-bottom:8px'>" + issue_chips + "</div>" if issue_chips else '')
                + "</div>"
            )

        # ── products section ──
        product_html = ''
        if products:
            prod_rows = ''
            for p in products[:5]:
                additives = (p.get('additives') or '').split(',')
                additive_chips = ''.join(
                    "<span style='background:var(--rlt);color:var(--red);font-size:9px;padding:1px 5px;border-radius:3px;margin-right:3px'>" + a.strip() + "</span>"
                    for a in additives[:5] if a.strip()
                )
                prod_rows += (
                    "<div style='padding:8px 0;border-bottom:1px solid var(--border)'>"
                    "<div style='font-size:12px;margin-bottom:4px'>" + (p.get('name') or '') + "</div>"
                    + ("<div>" + additive_chips + "</div>" if additive_chips else '')
                    + "</div>"
                )
            product_html = (
                "<div style='border:1px solid var(--border);border-radius:8px;padding:16px;margin-bottom:16px'>"
                "<div style='font-size:10px;letter-spacing:.08em;color:var(--muted);margin-bottom:8px'>"
                "PRODUCT ADDITIVES (" + str(product_count) + " PRODUCTS TRACKED)"
                "</div>"
                + prod_rows
                + "</div>"
            )

        # ── share strip ──
        share_text_val = (b.get('share_text') or '').replace("'", "&#39;")
        share_strip = (
            "<div style='display:flex;gap:12px;margin-bottom:24px;flex-wrap:wrap'>"
            "<a href='/swap/" + (b['slug'] or '') + "' style='background:var(--green);color:#fff;font-size:11px;"
            "padding:8px 16px;border-radius:6px;font-weight:600;text-decoration:none'>FIND CLEAN SWAP</a>"
            "<a href='/share/card/" + (b['slug'] or '') + "' style='background:var(--surface);border:1px solid var(--border);"
            "color:var(--muted);font-size:11px;padding:8px 16px;border-radius:6px;text-decoration:none'>SHARE CARD</a>"
            "<a href='/api/v1/brand/" + (b['slug'] or '') + "' style='background:var(--surface);border:1px solid var(--border);"
            "color:var(--muted);font-size:11px;padding:8px 16px;border-radius:6px;text-decoration:none'>API</a>"
            "</div>"
        )

        # ── JSON-LD ──
        jld = {
            "@context": "https://schema.org",
            "@type": "Brand",
            "name": b['name'],
            "description": origin[:160] if origin else '',
            "url": "https://tracedhealth.com/brand/" + (b['slug'] or ''),
        }
        if b.get('co_name'):
            jld["parentOrganization"] = {"@type": "Organization", "name": b['co_name']}

        head = page_head(
            b['name'] + ' — Brand Investigation · Traced',
            (headline or origin)[:160],
            slug=b['slug'] or '',
            jsonld=jld
        )

        # ── parent company section ──
        parent_section = ''
        if b.get('co_name'):
            acquisition_price_str = ''
            if b.get('acquisition_price'):
                ap = b['acquisition_price']
                acquisition_price_str = ' for $' + (str(round(ap/1e9, 2)) + 'B' if ap >= 1e9 else str(round(ap/1e6, 0)) + 'M')
            parent_section = (
                "<div style='background:var(--surface);border:1px solid var(--border);border-radius:8px;padding:16px;margin-bottom:16px'>"
                "<div style='font-size:10px;letter-spacing:.08em;color:var(--muted);margin-bottom:8px'>PARENT COMPANY</div>"
                "<div style='display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:8px'>"
                "<div>"
                "<div style='font-size:16px;font-weight:600'><a href='/company/" + (b.get('co_id') or '') + "' style='color:var(--ink)'>" + b['co_name'] + "</a></div>"
                + (("<div style='color:var(--muted);font-size:11px;margin-top:3px'>Acquired " + str(b['acquired_year']) + acquisition_price_str + "</div>") if b.get('acquired_year') else '')
                + "</div>"
                "<span style='color:" + tier_col + ";font-size:9px;letter-spacing:.06em'>" + tier_txt + "</span>"
                "</div>"
                "</div>"
            )
        else:
            parent_section = (
                "<div style='background:var(--glt);border:1px solid rgba(58,138,90,0.3);border-radius:8px;padding:16px;margin-bottom:16px'>"
                "<div style='font-size:10px;letter-spacing:.08em;color:var(--green);margin-bottom:4px'>" + tier_txt + "</div>"
                "<div style='font-size:13px;color:var(--ink)'>No parent company on record. Independently owned.</div>"
                "</div>"
            )

        # ── final assembly ──
        return (
            head
            + "<div style='max-width:900px;margin:0 auto;padding:40px 20px'>"
            # title row
            + "<div style='display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:12px;margin-bottom:6px'>"
            + "<h1 style='font-size:clamp(28px,5vw,52px);margin:0'>" + b['name'] + "</h1>"
            + "<span style='background:" + label_bg + ";color:" + label_color + ";"
            + "font-size:11px;padding:6px 14px;border-radius:6px;font-weight:600;align-self:flex-start'>"
            + label_txt + "</span>"
            + "</div>"
            + ("<div style='color:var(--muted);font-size:12px;margin-bottom:20px'>"
               + (b.get('category') or '').upper().replace('-', ' ')
               + ((' · Est. ' + str(b['founded_year'])) if b.get('founded_year') else '')
               + ("  ·  " + str(b.get('total_scans', 0)) + " scans" if b.get('total_scans') else '')
               + "</div>")
            # watch / acquired banners
            + watch_banner + acquired_banner
            # headline
            + ("<div style='font-size:clamp(15px,2.5vw,19px);line-height:1.6;color:var(--ink);"
               "margin-bottom:24px;font-family:Playfair Display,serif;font-style:italic'>"
               + headline + "</div>" if headline else '')
            # share strip
            + share_strip
            # origin story
            + ("<div style='background:var(--surface);border-left:3px solid var(--amber);"
               "padding:16px 20px;border-radius:0 8px 8px 0;margin-bottom:24px'>"
               "<div style='font-size:10px;letter-spacing:.08em;color:var(--amber);margin-bottom:8px'>ORIGIN STORY</div>"
               "<div style='font-size:13px;color:var(--muted);line-height:1.7'>" + origin + "</div>"
               "</div>" if origin else '')
            # parent company + tier
            + parent_section
            # ingredient transparency
            + it_section
            # health claims
            + hc_section
            # certifications
            + cert_section
            # violations
            + violation_html
            # lobbying
            + lobby_html
            # clean swaps
            + swap_section
            # timeline
            + events_html
            # siblings
            + sibling_html
            # products
            + product_html
            + "</div></body></html>"
        )

    # ════════════════════════════════════════════════════════════════════
    # PHASE 10 — API v1 EXPANSION
    # ════════════════════════════════════════════════════════════════════

    @app.route('/api/v1/transparent50')
    def api_transparent50():
        conn = get_db(); c = conn.cursor()
        c.execute(
            "SELECT b.name, b.slug, b.category, b.transparency_label, "
            "b.ingredient_transparency, b.ownership_tier, b.founder_still_involved, "
            "b.founded_year, b.certifications, "
            "co.name as parent_name "
            "FROM brands b LEFT JOIN companies co ON b.parent_company_id=co.id "
            "WHERE b.transparency_label IN ('transparent','complicated') "
            "ORDER BY b.transparency_label ASC, b.total_scans DESC NULLS LAST LIMIT 50"
        )
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return jsonify(rows)

    @app.route('/api/v1/independent')
    def api_independent():
        conn = get_db(); c = conn.cursor()
        cat = request.args.get('category', '')
        limit = min(int(request.args.get('limit', 100)), 200)
        sql = ("SELECT b.name, b.slug, b.category, b.transparency_label, "
               "b.ingredient_transparency, b.ownership_tier, b.founder_still_involved, "
               "b.founded_year, b.certifications, b.notes as description "
               "FROM brands b WHERE b.transparency_label='transparent' "
               "AND (b.parent_company_id IS NULL OR b.independent=1) ")
        params = []
        if cat:
            sql += "AND b.category=? "; params.append(cat)
        sql += "ORDER BY b.total_scans DESC NULLS LAST LIMIT ?"
        params.append(limit)
        c.execute(sql, params)
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return jsonify({'count': len(rows), 'brands': rows})

    @app.route('/api/v1/swap/<slug>')
    def api_swap(slug):
        conn = get_db(); c = conn.cursor()
        c.execute(
            "SELECT b.id, b.name, b.slug, b.transparency_label, b.category "
            "FROM brands b WHERE b.slug=? OR lower(b.name)=lower(?)",
            (slug, slug)
        )
        brand = c.fetchone()
        if not brand:
            conn.close(); return jsonify({'error': 'Brand not found'}), 404
        b = dict(brand)
        c.execute(
            "SELECT cs.reason, cs.category, "
            "ab.name as alt_name, ab.slug as alt_slug, "
            "ab.transparency_label as alt_label, ab.ingredient_transparency as alt_it, "
            "ab.certifications as alt_certs "
            "FROM clean_swaps cs JOIN brands ab ON cs.alternative_brand_id=ab.id "
            "WHERE cs.brand_id=?",
            (b['id'],)
        )
        swaps = [dict(r) for r in c.fetchall()]
        conn.close()
        return jsonify({'brand': b['name'], 'slug': b['slug'],
                        'transparency_label': b['transparency_label'], 'swaps': swaps})

    @app.route('/api/v1/retailers')
    def api_retailers():
        conn = get_db(); c = conn.cursor()
        c.execute(
            "SELECT retailer_name, retailer_slug, independent_brand_pct, "
            "conglomerate_brand_pct, pe_brand_pct, transparency_score, "
            "total_brands_tracked, notes FROM retailer_scores ORDER BY transparency_score DESC"
        )
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return jsonify(rows)

    @app.route('/api/v1/local')
    def api_local():
        conn = get_db(); c = conn.cursor()
        zip_q = request.args.get('zip', '')
        city_q = request.args.get('city', '')
        sql = ("SELECT id, name, type, address, city, state, zip, "
               "hours, website, accepts_ebt, organic_vendors, year_round "
               "FROM local_markets ")
        params = []
        if zip_q:
            sql += "WHERE zip LIKE ? "; params.append(zip_q[:5] + '%')
        elif city_q:
            sql += "WHERE lower(city) LIKE ? "; params.append('%' + city_q.lower() + '%')
        sql += "ORDER BY name LIMIT 100"
        c.execute(sql, params)
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return jsonify({'count': len(rows), 'markets': rows})

    @app.route('/api/v1/health-claims/<slug>')
    def api_health_claims(slug):
        conn = get_db(); c = conn.cursor()
        c.execute(
            "SELECT b.id FROM brands b WHERE b.slug=? OR lower(b.name)=lower(?)", (slug, slug)
        )
        row = c.fetchone()
        if not row:
            conn.close(); return jsonify({'error': 'Brand not found'}), 404
        c.execute(
            "SELECT claim_text, claim_type, challenged_by, outcome, year, fine_amount, source_url "
            "FROM health_claims WHERE brand_id=? ORDER BY year DESC",
            (row['id'],)
        )
        claims = [dict(r) for r in c.fetchall()]
        conn.close()
        return jsonify({'brand_slug': slug, 'claims': claims})

    @app.route('/api/v1/certifications/<slug>')
    def api_certifications_brand(slug):
        conn = get_db(); c = conn.cursor()
        c.execute(
            "SELECT b.id, b.certifications, b.certifications_maintained_post_acquisition, "
            "b.certification_notes FROM brands b WHERE b.slug=? OR lower(b.name)=lower(?)",
            (slug, slug)
        )
        row = c.fetchone()
        if not row:
            conn.close(); return jsonify({'error': 'Brand not found'}), 404
        b = dict(row)
        c.execute(
            "SELECT certification_type, granted_year, revoked_year, "
            "maintained_post_acquisition, notes, source_url "
            "FROM certifications WHERE brand_id=?",
            (b['id'],)
        )
        certs = [dict(r) for r in c.fetchall()]
        conn.close()
        return jsonify({
            'brand_slug': slug,
            'certifications_string': b.get('certifications'),
            'maintained_post_acquisition': b.get('certifications_maintained_post_acquisition'),
            'notes': b.get('certification_notes'),
            'certification_records': certs
        })

    @app.route('/api/v1/recently-acquired')
    def api_recently_acquired():
        conn = get_db(); c = conn.cursor()
        c.execute(
            "SELECT b.name, b.slug, b.category, b.transparency_label, b.ownership_tier, "
            "b.acquisition_age_years, b.watch_list_reason, b.headline_finding, "
            "co.name as parent_name "
            "FROM brands b LEFT JOIN companies co ON b.parent_company_id=co.id "
            "WHERE b.recently_acquired=1 ORDER BY b.acquisition_age_years ASC"
        )
        rows = [dict(r) for r in c.fetchall()]
        conn.close()
        return jsonify({'count': len(rows), 'brands': rows})

    # ════════════════════════════════════════════════════════════════════
    # PHASE 11 — SOCIAL SHARING UPGRADES
    # ════════════════════════════════════════════════════════════════════

    @app.route('/share/card/<slug>')
    def share_card(slug):
        conn = get_db(); c = conn.cursor()
        c.execute(
            "SELECT b.name, b.slug, b.category, b.transparency_label, b.headline_finding, "
            "b.ownership_tier, b.contradiction_score, "
            "co.name as parent_name "
            "FROM brands b LEFT JOIN companies co ON b.parent_company_id=co.id "
            "WHERE b.slug=? OR lower(b.name)=lower(?)",
            (slug, slug)
        )
        brand = c.fetchone()
        conn.close()
        if not brand:
            return "<h1>Brand not found</h1>", 404
        b = dict(brand)
        label = b.get('transparency_label') or ''

        # Color scheme by label
        if label == 'documented_deception':
            card_bg = '#1a0505'; accent = '#c44444'; label_txt = 'DOCUMENTED DECEPTION'
        elif label == 'conflicted':
            card_bg = '#120505'; accent = '#c44444'; label_txt = 'CONFLICTED'
        elif label == 'transparent':
            card_bg = '#051209'; accent = '#3a8a5a'; label_txt = 'TRANSPARENT'
        else:
            card_bg = '#100d05'; accent = '#d4952a'; label_txt = 'COMPLICATED'

        headline = b.get('headline_finding') or ('Owned by ' + (b.get('parent_name') or 'an undisclosed parent'))
        category_txt = (b.get('category') or '').upper().replace('-', ' ')

        html = (
            "<!DOCTYPE html><html><head>"
            "<meta charset='UTF-8'>"
            "<meta name='viewport' content='width=1200'>"
            + FONTS
            + "<style>"
            "body{margin:0;background:" + card_bg + ";color:#f0ead8;font-family:'DM Mono',monospace;"
            "width:1200px;height:630px;overflow:hidden;display:flex;align-items:center;justify-content:center}"
            ".card{width:1100px;padding:60px}"
            ".logo{font-family:'Bebas Neue';font-size:22px;letter-spacing:.12em;color:" + accent + ";margin-bottom:32px}"
            ".label{font-size:11px;letter-spacing:.12em;color:" + accent + ";margin-bottom:16px}"
            ".brand{font-family:'Playfair Display';font-size:72px;font-weight:700;line-height:1.1;margin-bottom:16px}"
            ".hl{font-family:'Playfair Display';font-style:italic;font-size:22px;color:rgba(240,234,216,0.7);line-height:1.5;margin-bottom:32px}"
            ".footer{font-size:12px;color:rgba(240,234,216,0.35);letter-spacing:.06em}"
            "</style></head><body>"
            "<div class='card'>"
            "<div class='logo'>TRACED</div>"
            "<div class='label'>" + label_txt + " · " + category_txt + "</div>"
            "<div class='brand'>" + b['name'] + "</div>"
            "<div class='hl'>" + headline[:200] + "</div>"
            "<div class='footer'>tracedhealth.com/brand/" + (b['slug'] or '') + "</div>"
            "</div></body></html>"
        )
        return Response(html, mimetype='text/html')

    @app.route('/share/text/<slug>')
    def share_text_v3(slug):
        conn = get_db(); c = conn.cursor()
        c.execute(
            "SELECT b.name, b.slug, b.share_text, b.transparency_label, b.headline_finding, "
            "co.name as parent_name "
            "FROM brands b LEFT JOIN companies co ON b.parent_company_id=co.id "
            "WHERE b.slug=? OR lower(b.name)=lower(?)",
            (slug, slug)
        )
        brand = c.fetchone()
        conn.close()
        if not brand:
            return jsonify({'error': 'Brand not found'}), 404
        b = dict(brand)
        text = (
            b.get('share_text')
            or (b['name'] + " is owned by " + (b.get('parent_name') or 'an undisclosed parent') + ". Check it on Traced. tracedhealth.com/brand/" + (b['slug'] or ''))
        )
        return jsonify({'slug': b['slug'], 'text': text,
                        'url': 'https://tracedhealth.com/brand/' + (b['slug'] or ''),
                        'label': b.get('transparency_label')})

    # ════════════════════════════════════════════════════════════════════
    # PHASE 12 — SEO UPDATES: SITEMAP + ROBOTS
    # ════════════════════════════════════════════════════════════════════

    @app.route('/sitemap.xml')
    def sitemap_xml():
        conn = get_db(); c = conn.cursor()
        c.execute("SELECT slug FROM brands WHERE slug IS NOT NULL AND slug != '' ORDER BY total_scans DESC NULLS LAST")
        brand_slugs = [r['slug'] for r in c.fetchall()]
        c.execute("SELECT DISTINCT category FROM brands WHERE category IS NOT NULL AND category != '' ORDER BY category")
        cats = [r['category'] for r in c.fetchall()]
        conn.close()

        base = 'https://tracedhealth.com'
        lines = ['<?xml version="1.0" encoding="UTF-8"?>',
                 '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">']
        static_pages = [
            ('/', '1.0', 'daily'),
            ('/contradiction', '0.9', 'weekly'),
            ('/transparency', '0.9', 'weekly'),
            ('/independent', '0.9', 'weekly'),
            ('/transparent50', '0.8', 'weekly'),
            ('/founders', '0.8', 'weekly'),
            ('/certifications', '0.8', 'weekly'),
            ('/categories', '0.8', 'weekly'),
            ('/audit', '0.7', 'monthly'),
            ('/watchlist', '0.6', 'monthly'),
            ('/retailers', '0.7', 'monthly'),
            ('/local', '0.6', 'monthly'),
            ('/scan', '0.6', 'monthly'),
        ]
        for path, pri, freq in static_pages:
            lines.append('<url><loc>' + base + path + '</loc>'
                         '<changefreq>' + freq + '</changefreq>'
                         '<priority>' + pri + '</priority></url>')
        for cat in cats:
            lines.append('<url><loc>' + base + '/category/' + cat + '</loc>'
                         '<changefreq>weekly</changefreq><priority>0.7</priority></url>')
            lines.append('<url><loc>' + base + '/category/' + cat + '/independent</loc>'
                         '<changefreq>weekly</changefreq><priority>0.6</priority></url>')
        for sl in brand_slugs:
            lines.append('<url><loc>' + base + '/brand/' + sl + '</loc>'
                         '<changefreq>monthly</changefreq><priority>0.5</priority></url>')
            lines.append('<url><loc>' + base + '/swap/' + sl + '</loc>'
                         '<changefreq>monthly</changefreq><priority>0.4</priority></url>')
        lines.append('</urlset>')
        return Response('\n'.join(lines), mimetype='application/xml')

    @app.route('/robots.txt')
    def robots_txt():
        txt = (
            "User-agent: *\n"
            "Allow: /\n"
            "Disallow: /api/\n"
            "Disallow: /embed.js\n"
            "Disallow: /widget/\n\n"
            "Sitemap: https://tracedhealth.com/sitemap.xml\n"
        )
        return Response(txt, mimetype='text/plain')

