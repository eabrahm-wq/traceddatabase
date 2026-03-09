from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
import sqlite3, os, json, re, uuid

app = Flask(__name__)
CORS(app)
DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'traced.db')

ADMIN_KEY = os.environ.get('ADMIN_KEY', 'traced-admin-2026')

def _init_submissions_table():
    with sqlite3.connect(DB) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS submissions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                ref_id TEXT UNIQUE NOT NULL,
                biz_name TEXT NOT NULL,
                category TEXT,
                founded_year INTEGER,
                address TEXT,
                website TEXT,
                google_maps_url TEXT,
                ownership_type TEXT,
                owner_names TEXT,
                has_investors TEXT,
                owner_story TEXT,
                contact_name TEXT,
                contact_role TEXT,
                contact_email TEXT,
                instagram TEXT,
                status TEXT DEFAULT 'pending',
                assigned_zone TEXT DEFAULT 'green',
                reject_reason TEXT,
                submitted_at TEXT DEFAULT (datetime('now')),
                reviewed_at TEXT
            )
        """)

_init_submissions_table()

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def brand_profile(search_term):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "SELECT b.id, b.name, b.acquired_year, b.acquisition_price, b.independent, b.total_scans, "
        "co.name as co_name, co.type as co_type, co.hq_country, co.annual_revenue, co.id as co_id "
        "FROM brands b LEFT JOIN companies co ON b.parent_company_id = co.id "
        "WHERE lower(b.name) LIKE lower(?) ORDER BY b.total_scans DESC NULLS LAST LIMIT 1",
        (f"%{search_term}%",))
    brand = c.fetchone()
    if not brand:
        conn.close()
        return None
    p = dict(brand)
    if p["co_id"]:
        c.execute(
            "SELECT name FROM brands WHERE parent_company_id=? AND id!=? AND lower(name)!=lower(?) "
            "ORDER BY total_scans DESC NULLS LAST LIMIT 10",
            (p["co_id"], p["id"], p["name"]))
        p["siblings"] = [r["name"] for r in c.fetchall()]
        c.execute(
            "SELECT violation_type, year, description, outcome, fine_amount "
            "FROM violations WHERE company_id=? AND violation_type != 'FDA recall' ORDER BY year DESC",
            (p["co_id"],))
        p["violations"] = [dict(r) for r in c.fetchall()]
        c.execute(
            "SELECT COUNT(*) FROM violations WHERE company_id=? AND violation_type='FDA recall'",
            (p["co_id"],))
        p["recall_count"] = c.fetchone()[0]
        c.execute(
            "SELECT year, total_spend, issues FROM lobbying_records "
            "WHERE company_id=? ORDER BY year DESC LIMIT 4",
            (p["co_id"],))
        rows = [dict(r) for r in c.fetchall()]
        p["lobbying"] = rows
        p["lobbying_total"] = sum(r["total_spend"] for r in rows)
        p["lobbying_issues"] = []
        for r in rows:
            for issue in r["issues"].split(","):
                issue = issue.strip()
                if issue and issue not in p["lobbying_issues"]:
                    p["lobbying_issues"].append(issue)
        c.execute(
            "SELECT SUM(fine_amount) FROM violations WHERE company_id=? AND fine_amount IS NOT NULL",
            (p["co_id"],))
        p["fines_total"] = c.fetchone()[0] or 0
    else:
        p["siblings"] = []
        p["violations"] = []
        p["recall_count"] = 0
        p["lobbying"] = []
        p["lobbying_total"] = 0
        p["lobbying_issues"] = []
        p["fines_total"] = 0
    c.execute(
        "SELECT event_type, event_date, headline, description, source_url "
        "FROM brand_events WHERE brand_id=? ORDER BY event_date DESC",
        (p["id"],))
    p["events"] = [dict(r) for r in c.fetchall()]
    c.execute(
        "SELECT p.name, s.additives FROM products p "
        "JOIN ingredient_snapshots s ON s.product_id=p.id "
        "WHERE p.brand_id=? AND s.additives!='' "
        "ORDER BY length(s.additives) DESC LIMIT 8",
        (p["id"],))
    p["products"] = [dict(r) for r in c.fetchall()]
    c.execute("SELECT COUNT(*) FROM products WHERE brand_id=?", (p["id"],))
    p["product_count"] = c.fetchone()[0]
    p["contradiction_score"] = calc_contradiction(p)
    conn.close()
    return p

def calc_contradiction(p):
    """
    Score 0-100 flagging how much the brand's 'clean' positioning
    contradicts its parent company's lobbying and violation record.
    """
    if not p.get("co_id"):
        return 0
    score = 0
    clean_keywords = ["organic", "natural", "honest", "simple", "pure", "earth",
                      "green", "clean", "healthy", "naked", "real", "good", "true",
                      "farm", "harvest", "garden", "wild", "free", "kind"]
    name_lower = (p["name"] or "").lower()
    is_clean_brand = any(k in name_lower for k in clean_keywords)
    if is_clean_brand:
        score += 20
    if p.get("acquired_year"):
        score += 15
    lobbying_issues = " ".join(p.get("lobbying_issues", [])).lower()
    if "gmo labeling" in lobbying_issues:
        score += 20
    if "nutrition labeling" in lobbying_issues:
        score += 15
    if "sugar tax" in lobbying_issues or "soda tax" in lobbying_issues:
        score += 10
    if "animal welfare" in lobbying_issues:
        score += 20
    if "organic" in lobbying_issues:
        score += 15
    if p.get("lobbying_total", 0) > 10_000_000:
        score += 10
    if p.get("fines_total", 0) > 5_000_000:
        score += 10
    if p.get("recall_count", 0) > 5:
        score += 5
    return min(score, 100)

def get_stats():
    conn = get_db()
    c = conn.cursor()
    s = {}
    for k, q in [
        ("brands_mapped", "SELECT COUNT(*) FROM brands WHERE parent_company_id IS NOT NULL"),
        ("companies",     "SELECT COUNT(*) FROM companies"),
        ("products",      "SELECT COUNT(*) FROM products"),
        ("violations",    "SELECT COUNT(*) FROM violations"),
    ]:
        c.execute(q)
        s[k] = c.fetchone()[0]
    c.execute("SELECT SUM(total_spend) FROM lobbying_records")
    s["lobbying"] = c.fetchone()[0] or 0
    c.execute("SELECT SUM(fine_amount) FROM violations WHERE fine_amount IS NOT NULL")
    s["fines"] = c.fetchone()[0] or 0
    c.execute("SELECT SUM(acquisition_price) FROM brands WHERE acquisition_price IS NOT NULL")
    s["acquisitions"] = c.fetchone()[0] or 0
    conn.close()
    return s

def search_brands(query, limit=6):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "SELECT b.name, co.name as owner FROM brands b "
        "LEFT JOIN companies co ON b.parent_company_id=co.id "
        "WHERE lower(b.name) LIKE lower(?) "
        "ORDER BY b.total_scans DESC NULLS LAST LIMIT ?",
        (f"%{query}%", limit))
    results = [dict(r) for r in c.fetchall()]
    conn.close()
    return results

def contradiction_label(score):
    if score >= 70: return ("HIGH CONTRADICTION", "#c44444")
    if score >= 40: return ("MODERATE", "#d4952a")
    if score >= 15: return ("LOW", "#888")
    return ("", "")

def render_profile(p):
    def fp(v): return "$" + str(round(v/1e6)) + "M" if v else "undisclosed"
    def fr(v): return "$" + str(round(v/1e9)) + "B" if v else "undisclosed"

    # Contradiction score card
    c_score = p.get("contradiction_score", 0)
    c_label, c_color = contradiction_label(c_score)
    verdict = ""
    if p.get("co_name") and c_score > 0:
        parts = []
        if p.get("acquired_year"):
            parts.append("acquired by " + p["co_name"] + " in " + str(p["acquired_year"]))
        if p.get("lobbying_total", 0) > 0:
            top_issues = p.get("lobbying_issues", [])[:2]
            if top_issues:
                parts.append(p["co_name"] + " spent $" + str(round(p["lobbying_total"]/1e6, 1)) + "M lobbying on " + " & ".join(top_issues))
        if p.get("fines_total", 0) > 0:
            parts.append("$" + str(round(p["fines_total"]/1e6, 1)) + "M in fines & settlements")
        if p.get("recall_count", 0) > 0:
            parts.append(str(p["recall_count"]) + " FDA recalls")
        verdict = ". ".join(parts) + "." if parts else ""

    verdict_html = ""
    if verdict:
        bar_width = c_score
        verdict_html = (
            "<div style='background:#111;border:1px solid rgba(255,255,255,0.08);border-radius:12px;padding:20px 24px;margin-bottom:12px'>"
            "<div style='display:flex;align-items:center;justify-content:space-between;margin-bottom:10px'>"
            "<span style='font-size:9px;letter-spacing:.14em;text-transform:uppercase;color:#888'>Traced Verdict</span>"
        )
        if c_label:
            verdict_html += "<span style='font-size:9px;font-weight:500;color:" + c_color + ";letter-spacing:.08em'>" + c_label + "</span>"
        verdict_html += (
            "</div>"
            "<div style='font-size:12px;color:rgba(240,234,216,0.8);line-height:1.7;margin-bottom:12px'>" + verdict + "</div>"
            "<div style='background:rgba(255,255,255,0.06);border-radius:4px;height:4px;overflow:hidden'>"
            "<div style='height:4px;border-radius:4px;background:" + c_color + ";width:" + str(bar_width) + "%'></div>"
            "</div>"
            "</div>"
        )

    sibs = ""
    if p.get("siblings"):
        sibs = (
            "<div class='sib'><span style='margin-right:8px;color:var(--muted)'>"
            + (p["co_name"] or "") + " also owns:</span>"
            + "".join("<span onclick=\"searchBrand('" + s.replace("'", "\\'") + "')\">" + s + "</span>" for s in p["siblings"])
            + "</div>"
        )

    acq = ""
    if p.get("acquired_year"):
        acq = (
            "<div class='chip red'>"
            "<div class='cy'>" + str(p["acquired_year"]) + "</div>"
            "<div class='cp'>" + fp(p.get("acquisition_price")) + " acquisition</div></div>"
        )
    elif not p.get("co_name"):
        acq = "<div class='chip green'>&#10003; Independent</div>"

    co_link = "/company/" + (p["co_id"] or "") if p.get("co_id") else "#"
    owner = ""
    if p.get("co_name"):
        owner = (
            "<div class='ol'>"
            "<span class='on'><a href='" + co_link + "' style='color:var(--amber);text-decoration:underline;text-underline-offset:3px;text-decoration-style:dotted'>" + p["co_name"] + "</a></span>"
            "<span class='ot'>" + (p.get("co_type") or "") + "</span>"
            "<span class='oh'>" + (p.get("hq_country") or "") + "</span></div>"
            "<div style='font-size:10px;color:var(--muted);margin-bottom:10px'>" + fr(p.get("annual_revenue")) + " annual revenue</div>"
        )
    else:
        owner = "<div class='ol'><span style='color:var(--green);font-size:13px'>&#9679; Independent</span></div>"

    meta = "<div class='mi'>Products<strong>" + str(p["product_count"]) + "</strong></div>"
    if p.get("total_scans"):
        meta += "<div class='mi'>Scans<strong>" + str(p["total_scans"]) + "</strong></div>"
    if p.get("violations"):
        meta += "<div class='mi'>FTC/FDA Fines<strong style='color:var(--red)'>" + str(len(p["violations"])) + "</strong></div>"
    if p.get("recall_count"):
        meta += "<div class='mi'>Recalls<strong style='color:var(--red)'>" + str(p["recall_count"]) + "</strong></div>"
    if p.get("lobbying_total"):
        meta += "<div class='mi'>Lobbying<strong style='color:var(--red)'>$" + str(round(p["lobbying_total"]/1e6, 1)) + "M</strong></div>"

    tmap = {"acquisition":"ta","reformulation":"tr","violation":"tv",
            "label_change":"tl","discontinuation":"tx","brand_event":"tb","recall":"tv"}

    ev = ""
    if p.get("events"):
        rows = ""
        for e in p["events"]:
            tc = tmap.get(e["event_type"], "ta")
            et = e["event_type"].replace("_", " ")
            dt = e["event_date"][:7]
            url = e.get("source_url") or ""
            headline = e["headline"]
            if url:
                hl = "<a href='" + url + "' target='_blank' style='color:inherit;text-decoration:underline;text-underline-offset:3px;opacity:.85'>" + headline + "</a>"
            else:
                hl = headline
            desc = ""
            if e.get("description") and e["description"] != e["headline"]:
                desc = "<div class='td2'>" + e["description"][:200] + "</div>"
            rows += (
                "<div class='ti'>"
                "<span class='td'>" + dt + "</span>"
                "<span class='tt " + tc + "'>" + et + "</span>"
                "<div><div class='th'>" + hl + "</div>" + desc + "</div>"
                "</div>"
            )
        ev = (
            "<div class='sec'><div class='sh'>"
            "<span class='st'>Timeline</span>"
            "<span class='sc'>" + str(len(p["events"])) + " events</span>"
            "</div>" + rows + "</div>"
        )

    vi = ""
    if p.get("violations"):
        rows = ""
        for v in p["violations"]:
            fine = "<span class='vf'>$" + str(round(v["fine_amount"]/1e6, 1)) + "M</span>" if v.get("fine_amount") else ""
            rows += (
                "<div class='vi'><div class='vt'>"
                "<span class='vy'>" + str(v["year"]) + "</span>"
                "<span class='vtype'>" + v["violation_type"] + "</span>"
                "<span class='vo'>" + v["outcome"] + "</span>" + fine + "</div>"
                "<div class='vd'>" + v["description"][:300] + "</div></div>"
            )
        vi = (
            "<div class='sec'><div class='sh'>"
            "<span class='st'>Parent Fines &amp; Settlements</span>"
            "<span class='sc'>" + str(len(p["violations"])) + "</span>"
            "</div>" + rows + "</div>"
        )

    lo = ""
    if p.get("lobbying"):
        mx = max(l["total_spend"] for l in p["lobbying"])
        rows = ""
        for l in p["lobbying"]:
            w = int(l["total_spend"] / mx * 100)
            rows += (
                "<div class='li'><span class='ly'>" + str(l["year"]) + "</span>"
                "<span class='ls'>$" + str(round(l["total_spend"]/1e6, 2)) + "M</span>"
                "<div><div class='lb' style='width:" + str(w) + "%'></div>"
                "<div class='liss'>" + l["issues"] + "</div></div></div>"
            )
        lo = (
            "<div class='sec'><div class='sh'>"
            "<span class='st'>Parent Lobbying</span>"
            "<span class='lt'>$" + str(round(p["lobbying_total"]/1e6, 1)) + "M documented</span>"
            "</div>" + rows + "</div>"
        )

    pr = ""
    if p.get("products"):
        rows = ""
        for prod in p["products"]:
            tags = "".join(
                "<span class='at'>" + a.strip() + "</span>"
                for a in prod["additives"].split(",") if a.strip())
            rows += (
                "<div class='pi'>"
                "<span class='pn'>" + prod["name"] + "</span>"
                "<div class='pa'>" + tags + "</div></div>"
            )
        pr = (
            "<div class='sec'><div class='sh'>"
            "<span class='st'>Products with Flagged Additives</span>"
            "<span class='sc'>" + str(len(p["products"])) + " shown</span>"
            "</div>" + rows + "</div>"
        )

    return (
        "<div class='profile' style='max-width:900px;margin:0 auto;padding:0 40px 80px'>"
        + verdict_html
        + "<div class='ph'><div class='pt'>"
        "<div><div class='bn'>" + p["name"] + "</div>" + owner + "</div>"
        "<div>" + acq + "</div></div>"
        "<div class='pm'>" + meta + "</div>" + sibs + "</div>"
        + ev + vi + lo + pr + "</div>"
    )

CSS = """
:root{--bg:#0a0906;--surface:#121009;--s2:#1a1710;--border:rgba(255,255,255,0.06);--b2:rgba(255,255,255,0.12);--ink:#f0ead8;--muted:rgba(240,234,216,0.4);--amber:#d4952a;--alt:rgba(212,149,42,0.12);--red:#c44444;--rlt:rgba(196,68,68,0.1);--green:#3a8a5a;--glt:rgba(58,138,90,0.1)}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:'DM Mono',monospace;min-height:100vh}
nav{border-bottom:1px solid var(--b2);padding:16px 40px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;background:var(--bg);z-index:100}
.logo{font-family:'Bebas Neue',sans-serif;font-size:24px;letter-spacing:.1em;color:var(--amber);text-decoration:none}
.nav-stats{display:flex;gap:24px}
.ns{font-size:9px;color:var(--muted);letter-spacing:.1em;text-transform:uppercase;text-align:center}
.ns strong{display:block;font-size:14px;color:var(--ink);font-weight:500;margin-bottom:2px;letter-spacing:0;text-transform:none}
.hero{padding:60px 40px 40px;max-width:800px;margin:0 auto;text-align:center}
h1{font-family:'Playfair Display',serif;font-size:clamp(28px,5vw,46px);font-weight:700;line-height:1.15;margin-bottom:14px}
h1 em{font-style:italic;color:var(--amber)}
.sub{font-size:12px;color:var(--muted);line-height:1.7;max-width:500px;margin:0 auto 32px}
.sw{position:relative;max-width:600px;margin:0 auto}
input{width:100%;background:var(--surface);border:1px solid var(--b2);border-radius:12px;padding:18px 100px 18px 20px;font-family:'DM Mono',monospace;font-size:14px;color:var(--ink);outline:none;transition:border-color .2s,box-shadow .2s}
input::placeholder{color:var(--muted)}
input:focus{border-color:var(--amber);box-shadow:0 0 0 1px var(--amber),0 8px 32px var(--alt)}
.sbtn{position:absolute;right:8px;top:50%;transform:translateY(-50%);background:var(--amber);border:none;border-radius:8px;padding:10px 16px;font-family:'DM Mono',monospace;font-size:10px;letter-spacing:.1em;text-transform:uppercase;color:#000;font-weight:500;cursor:pointer}
.sbtn:hover{opacity:.85}
.acd{position:absolute;top:calc(100% + 4px);left:0;right:0;background:var(--s2);border:1px solid var(--b2);border-radius:10px;overflow:hidden;z-index:200;display:none}
.aci{padding:12px 20px;cursor:pointer;display:flex;justify-content:space-between;border-bottom:1px solid var(--border);transition:background .15s}
.aci:last-child{border-bottom:none}
.aci:hover{background:var(--surface)}
.aci-name{font-size:13px;font-weight:500}
.aci-owner{font-size:10px;color:var(--amber)}
.pills{display:flex;flex-wrap:wrap;gap:8px;justify-content:center;margin-top:24px}
.pill{font-size:10px;padding:6px 14px;border-radius:999px;border:1px solid var(--b2);color:var(--muted);cursor:pointer;transition:all .15s;background:var(--surface)}
.pill:hover{border-color:var(--amber);color:var(--amber)}
#res{max-width:900px;margin:32px auto;padding:0 40px 80px}
.profile{animation:fu .3s ease}
@keyframes fu{from{opacity:0;transform:translateY(10px)}to{opacity:1;transform:translateY(0)}}
.ph{border:1px solid var(--b2);border-radius:16px;overflow:hidden;margin-bottom:12px}
.pt{padding:24px 28px;display:grid;grid-template-columns:1fr auto;gap:20px;align-items:start}
.bn{font-family:'Bebas Neue',sans-serif;font-size:48px;letter-spacing:.04em;line-height:1;margin-bottom:8px}
.ol{display:flex;align-items:center;gap:10px;margin-bottom:10px}
.on{font-size:14px;color:var(--amber);font-weight:500}
.ot{font-size:9px;background:var(--alt);color:var(--amber);border-radius:4px;padding:2px 7px;letter-spacing:.08em;text-transform:uppercase}
.oh{font-size:10px;color:var(--muted)}
.chip{display:inline-flex;align-items:center;gap:8px;border-radius:8px;padding:8px 14px;font-size:11px}
.chip.red{background:var(--rlt);border:1px solid rgba(196,68,68,0.2)}
.chip.green{background:var(--glt);border:1px solid rgba(58,138,90,0.2);color:var(--green)}
.cy{font-family:'Bebas Neue',sans-serif;font-size:20px;color:var(--red);line-height:1}
.cp{color:var(--muted)}
.pm{background:var(--surface);border-top:1px solid var(--border);padding:14px 28px;display:flex;gap:32px;flex-wrap:wrap}
.mi{font-size:9px;color:var(--muted);letter-spacing:.08em;text-transform:uppercase}
.mi strong{display:block;font-size:13px;color:var(--ink);font-weight:400;margin-top:2px;letter-spacing:0;text-transform:none}
.sib{padding:14px 28px;background:var(--s2);border-top:1px solid var(--border);font-size:10px;color:var(--muted)}
.sib span{color:var(--ink);margin-right:12px;cursor:pointer;transition:color .15s}
.sib span:hover{color:var(--amber)}
.sec{border:1px solid var(--border);border-radius:12px;overflow:hidden;margin-bottom:12px}
.sh{padding:14px 20px;background:var(--surface);border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between}
.st{font-size:9px;letter-spacing:.14em;text-transform:uppercase;color:var(--amber);font-weight:500}
.sc{font-size:9px;color:var(--muted);background:var(--s2);border-radius:20px;padding:2px 8px}
.ti{padding:14px 20px;border-bottom:1px solid var(--border);display:grid;grid-template-columns:80px 110px 1fr;gap:16px;align-items:start}
.ti:last-child{border-bottom:none}
.td{font-size:10px;color:var(--muted);white-space:nowrap}
.tt{font-size:8px;letter-spacing:.08em;text-transform:uppercase;padding:3px 8px;border-radius:4px;white-space:nowrap;font-weight:500}
.ta{background:rgba(212,149,42,.15);color:var(--amber)}
.tr{background:rgba(196,68,68,.15);color:var(--red)}
.tv{background:rgba(196,68,68,.2);color:var(--red)}
.tl{background:rgba(196,68,68,.15);color:var(--red)}
.tx{background:rgba(100,100,100,.2);color:#888}
.tb{background:rgba(58,138,90,.15);color:var(--green)}
.th{font-size:12px;line-height:1.6}
.td2{font-size:10px;color:var(--muted);margin-top:4px;line-height:1.6}
.vi{padding:14px 20px;border-bottom:1px solid var(--border)}
.vi:last-child{border-bottom:none}
.vt{display:flex;align-items:center;gap:10px;margin-bottom:6px}
.vy{font-family:'Bebas Neue',sans-serif;font-size:18px;color:var(--red);line-height:1}
.vtype{font-size:8px;background:var(--rlt);color:var(--red);padding:2px 7px;border-radius:4px;letter-spacing:.08em;text-transform:uppercase}
.vo{font-size:8px;background:var(--s2);color:var(--muted);padding:2px 7px;border-radius:4px}
.vf{font-size:8px;color:var(--red);margin-left:auto}
.vd{font-size:11px;color:rgba(240,234,216,.7);line-height:1.6}
.lt{font-size:11px;color:var(--red);font-weight:500}
.li{padding:12px 20px;border-bottom:1px solid var(--border);display:grid;grid-template-columns:50px 80px 1fr;gap:16px;align-items:center}
.li:last-child{border-bottom:none}
.ly{font-family:'Bebas Neue',sans-serif;font-size:18px;color:var(--muted);line-height:1}
.ls{font-size:12px;color:var(--amber);font-weight:500}
.lb{height:3px;background:var(--amber);border-radius:2px;margin-bottom:4px}
.liss{font-size:9px;color:var(--muted);line-height:1.5}
.pi{padding:12px 20px;border-bottom:1px solid var(--border);display:flex;justify-content:space-between;align-items:center;gap:16px}
.pi:last-child{border-bottom:none}
.pn{font-size:11px;flex:1}
.pa{display:flex;gap:4px;flex-wrap:wrap;justify-content:flex-end}
.at{font-size:8px;background:var(--rlt);color:var(--red);border-radius:4px;padding:2px 6px;white-space:nowrap}
@media(max-width:600px){nav{padding:12px 16px}.nav-stats{gap:12px}.hero{padding:40px 16px 24px}#res{padding:0 16px 60px}.pt{grid-template-columns:1fr}.ti{grid-template-columns:1fr;gap:6px}}
"""

JS = """
const si=document.getElementById('si'),acd=document.getElementById('acd');
let t;
si.addEventListener('keydown',e=>{if(e.key==='Enter')doSearch()});
si.addEventListener('input',()=>{
  clearTimeout(t);
  const q=si.value.trim();
  if(q.length<2){acd.style.display='none';return}
  t=setTimeout(()=>{
    fetch('/ac?q='+encodeURIComponent(q))
      .then(r=>r.json())
      .then(d=>{
        if(!d.length){acd.style.display='none';return}
        acd.innerHTML='';
        d.forEach(b=>{
          const el=document.createElement('div');
          el.className='aci';
          const n=document.createElement('span');
          n.className='aci-name';
          n.textContent=b.name;
          const o=document.createElement('span');
          o.className='aci-owner';
          o.textContent=b.owner||'Independent';
          el.appendChild(n);
          el.appendChild(o);
          el.addEventListener('click',()=>searchBrand(b.name));
          acd.appendChild(el);
        });
        acd.style.display='block';
      })
  },200)
});
document.addEventListener('click',e=>{if(!e.target.closest('.sw'))acd.style.display='none'});
function searchBrand(n){
  si.value=n;
  acd.style.display='none';
  doSearch();
}
function doSearch(){
  const q=si.value.trim();
  if(!q)return;
  document.getElementById('res').innerHTML='<div style="text-align:center;padding:60px;color:var(--muted);font-size:12px">Searching...</div>';
  fetch('/search?q='+encodeURIComponent(q))
    .then(r=>r.text())
    .then(h=>{document.getElementById('res').innerHTML=h});
}
// Handle ?q= param on load
const urlQ=new URLSearchParams(window.location.search).get('q');
if(urlQ){si.value=urlQ;doSearch();}
"""

@app.route("/")
def index():
    s = get_stats()
    pills = ["Annie's","Kashi","Clif Bar","Naked Juice","Applegate","Vitaminwater","Horizon Organic","KIND","Larabar","Honest Tea"]
    ph = "".join("<div class='pill' onclick=\"searchBrand('" + p.replace("'","\\'") + "')\">" + p + "</div>" for p in pills)
    return (
        "<!DOCTYPE html><html lang='en'><head>"
        "<meta charset='UTF-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1.0'>"
        "<title>Traced &mdash; Brand Intelligence</title>"
        "<link href='https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Mono:wght@300;400;500&family=Playfair+Display:ital,wght@0,700;1,400&display=swap' rel='stylesheet'>"
        "<style>" + CSS + "</style></head><body>"
        "<nav>"
        "<a class='logo' href='/'>TRACED</a>"
        "<div style='display:flex;align-items:center;gap:20px'>"
        "<div class='nav-stats'>"
        "<div class='ns'><strong>" + str(s['brands_mapped']) + "</strong>brands mapped</div>"
        "<div class='ns'><strong>" + str(s['companies']) + "</strong>companies</div>"
        "<div class='ns'><strong>$" + str(round(s['acquisitions']/1e9)) + "B</strong>acquisitions</div>"
        "<div class='ns'><strong>$" + str(round(s['lobbying']/1e6)) + "M</strong>lobbying</div>"
        "<div class='ns'><strong>$" + str(round(s['fines']/1e6)) + "M</strong>fines</div>"
        "</div>"
        "<a href='/scan' style='background:var(--amber);border-radius:8px;padding:8px 14px;font-size:10px;"
        "letter-spacing:.08em;text-transform:uppercase;color:#000;font-weight:500;white-space:nowrap'>&#128247; Scan</a>"
        "<a href='/contradiction' style='font-size:10px;color:var(--muted);letter-spacing:.06em;text-transform:uppercase;white-space:nowrap'>Contradiction Index</a>"
        "</div></nav>"
        "<div class='hero'>"
        "<h1>Who <em>really</em> owns<br>what you buy?</h1>"
        "<p class='sub'>Search any food brand to see the full ownership chain, acquisition history, ingredient changes, FDA violations, and lobbying spend.</p>"
        "<div class='sw'>"
        "<input type='text' id='si' placeholder=\"Search a brand &mdash; Annie's, Kashi, Clif Bar...\" autocomplete='off'>"
        "<button class='sbtn' onclick='doSearch()'>Search</button>"
        "<div class='acd' id='acd'></div>"
        "</div>"
        "<div class='pills'>" + ph + "</div>"
        "</div>"
        "<div id='res'></div>"
        "<script>" + JS + "</script>"
        "</body></html>"
    )

@app.route("/search")
def search():
    q = request.args.get("q","").strip()
    if not q: return ""
    p = brand_profile(q)
    if not p:
        return (
            "<div style='text-align:center;padding:60px;font-family:DM Mono,monospace;color:var(--muted)'>"
            "<div style='font-size:32px;margin-bottom:12px'>&#9675;</div>"
            "<div style='font-size:14px;color:#f0ead8;margin-bottom:6px'>Brand not found</div>"
            "<div style='font-size:11px'>Try another name or spelling</div></div>"
        )
    return render_profile(p)

@app.route("/ac")
def autocomplete():
    q = request.args.get("q","").strip()
    if len(q) < 2: return jsonify([])
    return jsonify(search_brands(q))

@app.route("/company/<company_id>")
def company_page(company_id):
    from company_routes import company_profile, render_company_page
    p = company_profile(company_id)
    if not p:
        return "Company not found", 404
    return render_company_page(p)

@app.route("/barcode/<upc>")
def barcode_lookup(upc):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "SELECT b.name FROM products p "
        "JOIN brands b ON p.brand_id = b.id "
        "WHERE p.upc=? LIMIT 1",
        (upc,))
    row = c.fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Barcode not found", "upc": upc}), 404
    brand_name = row["name"]
    p = brand_profile(brand_name)
    if not p:
        return jsonify({"error": "Brand profile not found", "brand": brand_name}), 404
    s = get_stats()
    profile_html = render_profile(p)
    return (
        "<!DOCTYPE html><html lang='en'><head>"
        "<meta charset='UTF-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1.0'>"
        "<title>" + p["name"] + " &mdash; Traced</title>"
        "<link href='https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Mono:wght@300;400;500&family=Playfair+Display:ital,wght@0,700;1,400&display=swap' rel='stylesheet'>"
        "<style>" + CSS + "</style></head><body>"
        "<nav>"
        "<a class='logo' href='/'>TRACED</a>"
        "<a style='font-size:10px;color:var(--muted);text-decoration:none;letter-spacing:.08em;text-transform:uppercase' href='/'>&#8592; Search</a>"
        "</nav>"
        + profile_html +
        "<script>function searchBrand(n){window.location.href='/?q='+encodeURIComponent(n)}</script>"
        "</body></html>"
    )

@app.route("/api/brand/<name>")
def api_brand(name):
    p = brand_profile(name)
    if not p:
        return jsonify({"error": "Brand not found"}), 404
    # Return clean JSON — remove HTML-heavy fields
    out = {
        "name": p["name"],
        "brand_id": p["id"],
        "parent_company": p.get("co_name"),
        "parent_company_id": p.get("co_id"),
        "parent_country": p.get("hq_country"),
        "parent_revenue": p.get("annual_revenue"),
        "acquired_year": p.get("acquired_year"),
        "acquisition_price": p.get("acquisition_price"),
        "independent": bool(p.get("independent")),
        "total_scans": p.get("total_scans"),
        "product_count": p["product_count"],
        "contradiction_score": p.get("contradiction_score", 0),
        "siblings": p.get("siblings", []),
        "lobbying_total": p.get("lobbying_total", 0),
        "lobbying_issues": p.get("lobbying_issues", []),
        "fines_total": p.get("fines_total", 0),
        "recall_count": p.get("recall_count", 0),
        "violations": p.get("violations", []),
        "lobbying": p.get("lobbying", []),
        "events": p.get("events", []),
        "flagged_products": p.get("products", []),
    }
    return jsonify(out)

@app.route("/api/barcode/<upc>")
def api_barcode(upc):
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "SELECT b.name FROM products p "
        "JOIN brands b ON p.brand_id = b.id "
        "WHERE p.upc=? LIMIT 1",
        (upc,))
    row = c.fetchone()
    conn.close()
    if not row:
        return jsonify({"error": "Barcode not found", "upc": upc}), 404
    return api_brand(row["name"])

# ── Influencer vetting tool helpers ───────────────────────────────

_VET_DOMAIN_MAP = {
    'opensecrets.org': 'OpenSecrets',
    'ftc.gov': 'FTC.gov',
    'sec.gov': 'SEC.gov',
    'fda.gov': 'FDA.gov',
    'justice.gov': 'DOJ.gov',
    'nytimes.com': 'New York Times',
    'wsj.com': 'Wall Street Journal',
    'washingtonpost.com': 'Washington Post',
    'reuters.com': 'Reuters',
    'bloomberg.com': 'Bloomberg',
    'prnewswire.com': 'PR Newswire',
    'businesswire.com': 'Business Wire',
    'eater.com': 'Eater',
    'foodnavigator': 'FoodNavigator',
    'fooddive.com': 'Food Dive',
    'ewg.org': 'EWG',
    'cornucopia.org': 'Cornucopia Institute',
    'topclassactions.com': 'Top Class Actions',
    'agdaily.com': 'AGDaily',
    'perishablenews.com': 'Perishable News',
    'transparencymarket.com': 'Transparency Market Research',
}

_VET_CATEGORY_HINTS = {
    'ag1': 'Supplements', 'momentous': 'Sports Nutrition', 'ghost': 'Sports Nutrition',
    'transparent-labs': 'Sports Nutrition', 'musclepharm': 'Sports Nutrition',
    'david': 'Protein Bars', 'annies': 'Organic Food', 'cheerios': 'Cereals',
    'chobani': 'Yogurt', 'reeses': 'Confectionery', 'tropicana': 'Beverages',
    'halo-top': 'Frozen Desserts', 'salt-straw': 'Ice Cream',
    'beyond-meat': 'Plant-Based Food', 'oatly': 'Plant-Based Beverages',
    'fairlife': 'Dairy', 'honest-tea': 'Beverages', 'naked-juice': 'Beverages',
    'kashi': 'Cereals', 'bolthouse-farms': 'Beverages',
}

def _vet_source_label(url, headline=None, year=None):
    if not url:
        return None
    if headline:
        for sep in (' - ', ' — ', ' | '):
            if sep in headline:
                parts = headline.rsplit(sep, 1)
                if len(parts) == 2 and 3 < len(parts[1]) < 60:
                    pub = parts[1].strip()
                    return pub + (', ' + str(year) if year else '')
    m = re.search(r'https?://(?:www\.)?([^/]+)', url)
    if m:
        domain = m.group(1).lower()
        for k, v in _VET_DOMAIN_MAP.items():
            if k in domain:
                return v + (', ' + str(year) if year else '')
        parts = domain.split('.')
        base = parts[-2] if len(parts) >= 2 else parts[0]
        return base.replace('-', ' ').title() + (', ' + str(year) if year else '')
    return None

def _vet_neutralize(text):
    pairs = [
        (r'\bhides\b', 'does not disclose'),
        (r'\bhidden\b', 'not disclosed'),
        (r'\bconcealed\b', 'not disclosed'),
        (r'\bsecretly\b', ''),
        (r'\bquietly\b', ''),
        (r'\bshockingly\b', ''),
        (r'\btroubling\b', 'notable'),
        (r'\bconcerning\b', 'notable'),
        (r'\bdeceptively?\b', 'inconsistently'),
        (r'\bmisleading\b', 'inconsistent'),
        (r'\bunfortunately\b', ''),
        (r'\bproudly\b', ''),
        (r'\bimpressive\b', 'notable'),
    ]
    for pattern, repl in pairs:
        text = re.sub(pattern, repl, text, flags=re.IGNORECASE)
    return re.sub(r'  +', ' ', text).strip()

def _vet_categorize(text):
    t = text.lower()
    if any(w in t for w in ('acqui', 'pepsico', 'purchased by', 'sold to', 'parent company',
                             'private equity', 'pe firm', 'keurig', 'general mills',
                             'coca-cola', 'ipo ', 'founder', 'ownership')):
        return 'Ownership & Structure'
    if any(w in t for w in ('recall', 'class action', 'lawsuit', 'litigation',
                             'criminal', 'convicted', 'conviction', 'court')):
        return 'Legal & Compliance'
    if any(w in t for w in ('ftc', 'fda', 'sec ', 'warning letter', 'enforcement',
                             'settlement', 'consent decree', 'regulatory', 'fined')):
        return 'Regulatory Record'
    if any(w in t for w in ('ingredient', 'formula', 'recipe', 'reformulat',
                             'proprietary blend', 'dosing', 'protein content',
                             'corn starch', 'collagen', 'serving')):
        return 'Ingredient History'
    if any(w in t for w in ('claim', 'certif', 'endors', 'advertis', 'marketing',
                             'label', 'health benefit', 'coa', 'nsf', 'third-party')):
        return 'Health & Ingredient Claims'
    if any(w in t for w in ('equity', 'investor', 'fund', 'capital', 'valuation',
                             'revenue', 'going concern', 'bankruptcy')):
        return 'Ownership & Structure'
    return 'Research Findings'

def _vet_format_type(ot):
    m = {
        'public_conglomerate': 'Public — Conglomerate',
        'public': 'Public Company',
        'private': 'Private Company',
        'private_equity': 'Private Equity Owned',
        'pe': 'Private Equity Owned',
        'independent': 'Private — Independent',
        'family': 'Private — Family Owned',
        'cooperative': 'Cooperative',
    }
    if not ot:
        return 'Private Company'
    return m.get(ot.lower(), ot.replace('_', ' ').title())


@app.route('/api/vet/search')
def api_vet_search():
    q = request.args.get('q', '').strip()
    if len(q) < 2:
        resp = jsonify([])
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "SELECT b.name, b.slug, b.category, co.name as parent_company"
        " FROM brands b LEFT JOIN companies co ON b.parent_company_id=co.id"
        " WHERE lower(b.name) LIKE lower(?)"
        " ORDER BY b.total_scans DESC NULLS LAST, b.name LIMIT 8",
        ('%' + q + '%',))
    results = [dict(r) for r in c.fetchall()]
    conn.close()
    resp = jsonify(results)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


@app.route('/api/vet/<brand_slug>')
def api_vet_brand(brand_slug):
    slug_pattern = '%' + '%'.join(brand_slug.split('-')) + '%'
    conn = get_db()
    c = conn.cursor()
    c.execute(
        "SELECT b.id, b.name, b.slug, b.category, b.acquired_year, b.founded_year,"
        " b.key_findings, b.headline_finding, b.overall_zone, b.ownership_tier,"
        " co.name as co_name, co.type as co_type, co.ownership_type, co.hq_country"
        " FROM brands b LEFT JOIN companies co ON b.parent_company_id=co.id"
        " WHERE b.slug=? OR lower(b.name) LIKE lower(?)"
        " ORDER BY b.total_scans DESC NULLS LAST LIMIT 1",
        (brand_slug, slug_pattern))
    row = c.fetchone()
    if not row:
        conn.close()
        resp = jsonify({"error": "Brand not found in Traced database"})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp, 404
    brand = dict(row)
    brand_id = brand['id']
    findings = []

    # 1. key_findings JSON (curated, highest priority)
    kf_raw = (brand.get('key_findings') or '').strip()
    kf_list = []
    if kf_raw:
        try:
            kf_list = json.loads(kf_raw)
        except Exception:
            kf_list = []
    for kf in kf_list[:5]:
        title = kf.get('title', '')
        body = kf.get('body', '')
        text = _vet_neutralize((title + '. ' + body).strip() if body else title)
        findings.append({
            'category': _vet_categorize(title + ' ' + body),
            'text': text[:300],
            'source_url': None,
            'source_label': None,
            'sourced': False,
        })

    # 2. brand_events (supplementary)
    if len(findings) < 5:
        c.execute(
            "SELECT event_type, event_date, headline, description, source_url"
            " FROM brand_events WHERE brand_id=? ORDER BY event_date DESC",
            (brand_id,))
        for e in [dict(r) for r in c.fetchall()]:
            if len(findings) >= 5:
                break
            headline = e.get('headline') or ''
            desc = e.get('description') or ''
            text = _vet_neutralize(headline)
            if desc and desc != headline:
                text = (text + '. ' + _vet_neutralize(desc[:150])).strip()
            if not text:
                continue
            url = e.get('source_url') or ''
            year = (e.get('event_date') or '')[:4] or None
            etype = e.get('event_type', '')
            if etype == 'acquisition':
                cat = 'Ownership & Structure'
            elif etype in ('recall', 'legal', 'violation'):
                cat = 'Legal & Compliance'
            elif etype in ('reformulation', 'formulation_change'):
                cat = 'Ingredient History'
            else:
                cat = _vet_categorize(text)
            findings.append({
                'category': cat,
                'text': text[:250],
                'source_url': url or None,
                'source_label': _vet_source_label(url, headline=headline, year=year) if url else None,
                'sourced': bool(url),
            })

    # 3. violations (supplementary, non-recall)
    if len(findings) < 5:
        c.execute(
            "SELECT violation_type, year, description, outcome, source_url"
            " FROM violations WHERE brand_id=? AND violation_type != 'FDA recall'"
            " ORDER BY year DESC LIMIT 3",
            (brand_id,))
        for v in [dict(r) for r in c.fetchall()]:
            if len(findings) >= 5:
                break
            text = _vet_neutralize((v.get('description') or '')[:250])
            if not text:
                continue
            url = v.get('source_url') or ''
            findings.append({
                'category': _vet_categorize((v.get('violation_type') or '') + ' ' + text),
                'text': text,
                'source_url': url or None,
                'source_label': _vet_source_label(url, year=v.get('year')) if url else None,
                'sourced': bool(url),
            })

    # 4. health_claims (supplementary)
    if len(findings) < 5:
        c.execute(
            "SELECT claim_text, source_url FROM health_claims WHERE brand_id=?",
            (brand_id,))
        for h in [dict(r) for r in c.fetchall()]:
            if len(findings) >= 5:
                break
            text = _vet_neutralize((h.get('claim_text') or '')[:250])
            if not text:
                continue
            url = h.get('source_url') or ''
            findings.append({
                'category': 'Health & Ingredient Claims',
                'text': text,
                'source_url': url or None,
                'source_label': _vet_source_label(url) if url else None,
                'sourced': bool(url),
            })

    # 5. ingredient_drift (supplementary)
    if len(findings) < 5:
        c.execute(
            "SELECT change_summary, source_url FROM ingredient_drift"
            " WHERE brand_id=? AND change_summary IS NOT NULL AND change_summary != ''",
            (brand_id,))
        for d in [dict(r) for r in c.fetchall()]:
            if len(findings) >= 5:
                break
            text = _vet_neutralize((d.get('change_summary') or '')[:250])
            if not text:
                continue
            url = d.get('source_url') or ''
            findings.append({
                'category': 'Ingredient History',
                'text': text,
                'source_url': url or None,
                'source_label': _vet_source_label(url) if url else None,
                'sourced': bool(url),
            })

    conn.close()

    # Build ownership metadata
    co_name = brand.get('co_name')
    co_type = brand.get('ownership_type') or brand.get('co_type') or ''
    parent_type = _vet_format_type(co_type)
    if co_name:
        parent_display = co_name
        if brand.get('acquired_year'):
            ownership_phrase = 'acquired by ' + co_name + ' in ' + str(brand['acquired_year'])
        else:
            ownership_phrase = 'owned by ' + co_name
    else:
        parent_display = brand['name'] + ' (Independent)'
        parent_type = 'Private — Independent'
        ownership_phrase = 'independently operated'

    resolved_slug = brand.get('slug') or brand_slug
    cat_str = (brand.get('category') or _VET_CATEGORY_HINTS.get(brand_slug)
               or _VET_CATEGORY_HINTS.get(resolved_slug) or 'consumer goods').lower()
    vetting_summary = brand['name'] + ' is a ' + cat_str + ' brand, ' + ownership_phrase + '.'
    words = vetting_summary.split()
    if len(words) > 28:
        vetting_summary = ' '.join(words[:28]).rstrip('.,') + '.'

    sourced_count = sum(1 for f in findings if f['sourced'])
    if len(findings) >= 4 and sourced_count >= 3:
        completeness = 'full'
    elif len(findings) >= 2:
        completeness = 'partial'
    else:
        completeness = 'minimal'

    resp = jsonify({
        'brand': brand['name'],
        'slug': resolved_slug,
        'parent_company': parent_display,
        'parent_type': parent_type,
        'category': brand.get('category') or _VET_CATEGORY_HINTS.get(brand_slug) or _VET_CATEGORY_HINTS.get(resolved_slug) or '',
        'vetting_summary': vetting_summary,
        'findings': findings,
        'findings_count': len(findings),
        'sources_count': sourced_count,
        'data_completeness': completeness,
        'tracedhealth_url': 'https://tracedhealth.com/brand/' + resolved_slug,
    })
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


# ── Register extended routes ──────────────────────────────────────
try:
    from routes_ext import register as _register_ext
    _register_ext(app)
except Exception as _ext_err:
    import traceback; traceback.print_exc()
    print(f"Warning: could not load routes_ext: {_ext_err}")


@app.route("/api/lookup")
def api_lookup():
    name = request.args.get("name", "").strip()
    if not name:
        return jsonify({"error": "name required"}), 400
    surface = request.headers.get("X-Surface") or request.args.get("surface")
    from traced_resolver import resolve
    result = resolve(name, surface=surface)
    response = jsonify(result)
    response.headers["Access-Control-Allow-Origin"] = "*"
    return response

@app.route("/api/resolver/misses")
def api_resolver_misses():
    from traced_resolver import get_misses
    limit = min(int(request.args.get("limit", 50)), 200)
    misses = get_misses(limit=limit)
    return jsonify({"misses": misses, "count": len(misses)})


@app.route("/api/nearby")
def api_nearby():
    category = request.args.get("category", "").strip()
    limit = min(int(request.args.get("limit", 2)), 5)
    price_tier = request.args.get("price_tier", type=int)
    format_ = request.args.get("format", "").strip()
    if not category:
        return jsonify({"error": "category required"}), 400
    import sqlite3 as _sq
    conn = _sq.connect(DB)
    conn.row_factory = _sq.Row

    rows = []
    # 1. Exact format + exact tier
    if format_ and price_tier:
        rows = conn.execute(
            "SELECT * FROM local_vendors WHERE category=? AND verified=1 AND format=? AND price_tier=? ORDER BY RANDOM() LIMIT ?",
            (category, format_, price_tier, limit)).fetchall()
    # 2. Exact format only (no tier padding with wrong format)
    if not rows and format_:
        rows = conn.execute(
            "SELECT * FROM local_vendors WHERE category=? AND verified=1 AND format=? ORDER BY RANDOM() LIMIT ?",
            (category, format_, limit)).fetchall()
    # 3. Exact tier, no format constraint
    if not rows and price_tier:
        rows = conn.execute(
            "SELECT * FROM local_vendors WHERE category=? AND verified=1 AND price_tier=? ORDER BY RANDOM() LIMIT ?",
            (category, price_tier, limit)).fetchall()
    # 4. Anything in category
    if not rows:
        rows = conn.execute(
            "SELECT * FROM local_vendors WHERE category=? AND verified=1 ORDER BY RANDOM() LIMIT ?",
            (category, limit)).fetchall()

    conn.close()
    result = [dict(r) for r in rows]
    resp = jsonify({"nearby": result, "category": category})
    resp.headers["Access-Control-Allow-Origin"] = "*"
    return resp


@app.route("/api/debug")
def api_debug():
    import os, sqlite3 as sq
    db_path = DB
    size = os.path.getsize(db_path) if os.path.exists(db_path) else -1
    try:
        conn = sq.connect(db_path)
        count = conn.execute("SELECT COUNT(*) FROM brands").fetchone()[0]
        conn.close()
        return jsonify({"db_size": size, "brands": count, "db_path": db_path})
    except Exception as e:
        return jsonify({"db_size": size, "error": str(e), "db_path": db_path})


# ── Barcode scanner API (query-param version, CORS-enabled) ───────────────────

@app.route('/api/barcode')
def api_barcode_scan():
    upc = request.args.get('upc', '').strip()
    if not upc:
        return jsonify({'error': 'upc required'}), 400

    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM products WHERE upc = ? LIMIT 1", (upc,))
    product = c.fetchone()

    if not product:
        conn.close()
        resp = jsonify({'found': False, 'upc': upc,
                        'message': 'Product not in Traced database yet'})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

    if not product['brand_id']:
        conn.close()
        resp = jsonify({'found': True, 'traced': False,
                        'product_name': product['name'],
                        'brand_name': product['brand_name_raw'] or '',
                        'message': 'Product found but brand not yet researched'})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

    c.execute("""
        SELECT b.*,
               co.name          AS co_name,
               co.type          AS co_type,
               co.violation_count     AS co_violations,
               co.violation_summary   AS co_violation_summary,
               co.lobbying_annual     AS co_lobbying,
               co.lobbying_issues     AS co_lobbying_issues
        FROM brands b
        LEFT JOIN companies co ON b.parent_company_id = co.id
        WHERE b.id = ?
    """, (product['brand_id'],))
    brand = c.fetchone()
    conn.close()

    if not brand:
        print(f"[barcode] brand_id={product['brand_id']} not found in brands table")
        resp = jsonify({'found': True, 'traced': False, 'upc': upc,
                        'product_name': product['name'],
                        'brand_name': product['brand_name_raw'] or '',
                        'message': 'Brand record missing from database'})
        resp.headers['Access-Control-Allow-Origin'] = '*'
        return resp

    brand_dict = {
        'id': brand['id'],
        'name': brand['name'],
        'zone': brand['overall_zone'],          # primary field scanner uses
        'overall_zone': brand['overall_zone'],  # redundant alias for safety
        'independent': bool(brand['independent']),
        'pe_owned': bool(brand['pe_owned']),
        'headline': brand['headline_finding'],
        'share_text': brand['share_text'],
        'founder_story': brand['founder_story'],
        'ingredient_drift': bool(brand['ingredient_drift']),
        'ingredient_drift_note': brand['ingredient_drift_note'],
    }
    parent_dict = {
        'name': brand['co_name'],
        'type': brand['co_type'],
        'violations': brand['co_violations'],
        'violation_summary': brand['co_violation_summary'],
        'lobbying_annual': brand['co_lobbying'],
        'lobbying_issues': brand['co_lobbying_issues'],
    } if brand['co_name'] else None

    print(f"[barcode] upc={upc} brand={brand_dict}")

    result = {
        'found': True,
        'traced': bool(brand['overall_zone']),
        'upc': upc,
        'product_name': product['name'],
        'brand': brand_dict,
        'parent': parent_dict,
    }
    resp = jsonify(result)
    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


@app.route('/api/barcode/lookup-external')
def api_barcode_external():
    upc = request.args.get('upc', '').strip()
    if not upc:
        return jsonify({'error': 'upc required'}), 400

    import urllib.request
    import json as jsonlib

    try:
        url = (f'https://world.openfoodfacts.org/api/v2/product/{upc}.json'
               f'?fields=product_name,brands,categories,image_url')
        req = urllib.request.Request(url, headers={'User-Agent': 'TracedHealth/1.0'})
        with urllib.request.urlopen(req, timeout=4) as r:
            data = jsonlib.loads(r.read())

        if data.get('status') == 1:
            p = data.get('product', {})
            brand_name = (p.get('brands') or '').split(',')[0].strip()
            brand_obj = None
            parent_obj = None
            traced = False
            if brand_name:
                from traced_resolver import resolve
                res = resolve(brand_name)
                if res.get('matched'):
                    rb = res['brand']
                    traced = bool(rb.get('overall_zone'))
                    brand_obj = {
                        'id': rb.get('slug') or rb.get('id'),
                        'name': rb.get('name', brand_name),
                        'zone': rb.get('overall_zone'),
                        'independent': bool(rb.get('independent')),
                        'pe_owned': bool(rb.get('pe_owned')),
                        'headline': rb.get('headline_finding'),
                        'share_text': rb.get('share_text'),
                        'founder_story': rb.get('founder_story'),
                        'ingredient_drift': bool(rb.get('ingredient_drift')),
                        'ingredient_drift_note': rb.get('ingredient_drift_note'),
                    }
                    # Use parent_record from resolver if available
                    pr = rb.get('parent_record')
                    if pr:
                        parent_obj = {
                            'name': rb.get('owner'),
                            'type': None,
                            'violations': pr.get('violations'),
                            'violation_summary': pr.get('violation_summary'),
                            'lobbying_annual': pr.get('lobbying_annual'),
                            'lobbying_issues': pr.get('lobbying_issues'),
                        }
            print(f"[barcode-ext] upc={upc} brand_name={brand_name} brand={brand_obj}")
            resp = jsonify({
                'found': True,
                'source': 'open_food_facts',
                'product_name': p.get('product_name', ''),
                'brand_name': brand_name,
                'traced': traced,
                'brand': brand_obj,
                'parent': parent_obj,
                'image_url': p.get('image_url', ''),
                'categories': p.get('categories', ''),
            })
        else:
            resp = jsonify({'found': False, 'source': 'open_food_facts'})

    except Exception as e:
        resp = jsonify({'found': False, 'error': str(e)})

    resp.headers['Access-Control-Allow-Origin'] = '*'
    return resp


@app.route('/scanner/')
@app.route('/scanner')
def scanner_ui():
    import os
    scanner_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'scanner', 'index.html')
    with open(scanner_path) as f:
        return f.read(), 200, {'Content-Type': 'text/html'}



@app.route('/research')
def research_page():
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    return send_from_directory(static_dir, 'research.html')


# ── Submission flow ────────────────────────────────────────────────────────────

def _check_admin(req):
    return req.headers.get('X-Admin-Key') == ADMIN_KEY


def _slugify(text):
    slug = re.sub(r'[^a-z0-9]+', '-', text.lower().strip())
    return slug.strip('-')


@app.route('/submit')
def submit_page():
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    return send_from_directory(static_dir, 'submit.html')


@app.route('/admin/submissions')
def admin_submissions_page():
    static_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static')
    return send_from_directory(static_dir, 'admin-submissions.html')


@app.route('/api/submit-business', methods=['POST'])
def api_submit_business():
    data = request.get_json(silent=True) or {}
    biz_name = (data.get('biz_name') or '').strip()
    if not biz_name:
        return jsonify({'error': 'biz_name is required'}), 400

    ref_id = uuid.uuid4().hex[:8].upper()
    with sqlite3.connect(DB) as conn:
        conn.execute(
            """INSERT INTO submissions
               (ref_id, biz_name, category, founded_year, address, website,
                google_maps_url, ownership_type, owner_names, has_investors,
                owner_story, contact_name, contact_role, contact_email, instagram)
               VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)""",
            (
                ref_id,
                biz_name,
                data.get('category'),
                data.get('founded_year'),
                data.get('address'),
                data.get('website'),
                data.get('google_maps_url'),
                data.get('ownership_type'),
                data.get('owner_names'),
                data.get('has_investors'),
                data.get('owner_story'),
                data.get('contact_name'),
                data.get('contact_role'),
                data.get('contact_email'),
                data.get('instagram'),
            )
        )
    return jsonify({'success': True, 'ref_id': ref_id})


@app.route('/api/admin/submissions', methods=['GET'])
def api_admin_submissions():
    if not _check_admin(request):
        return jsonify({'error': 'unauthorized'}), 401

    status_filter = request.args.get('status', 'all')
    with sqlite3.connect(DB) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()

        # counts
        c.execute("SELECT status, COUNT(*) FROM submissions GROUP BY status")
        counts = {'pending': 0, 'approved': 0, 'rejected': 0}
        for row in c.fetchall():
            if row[0] in counts:
                counts[row[0]] = row[1]

        if status_filter == 'all':
            c.execute("SELECT * FROM submissions ORDER BY submitted_at DESC")
        else:
            c.execute("SELECT * FROM submissions WHERE status=? ORDER BY submitted_at DESC", (status_filter,))
        rows = [dict(r) for r in c.fetchall()]

    return jsonify({'submissions': rows, 'counts': counts})


@app.route('/api/admin/submissions/<int:sub_id>/approve', methods=['POST'])
def api_admin_approve(sub_id):
    if not _check_admin(request):
        return jsonify({'error': 'unauthorized'}), 401

    data = request.get_json(silent=True) or {}
    zone = data.get('zone', 'green')
    if zone not in ('green', 'yellow', 'red'):
        return jsonify({'error': 'zone must be green, yellow, or red'}), 400

    with sqlite3.connect(DB) as conn:
        conn.row_factory = sqlite3.Row
        c = conn.cursor()
        c.execute("SELECT * FROM submissions WHERE id=?", (sub_id,))
        sub = c.fetchone()
        if not sub:
            return jsonify({'error': 'submission not found'}), 404
        sub = dict(sub)

        c.execute(
            "UPDATE submissions SET status='approved', assigned_zone=?, reviewed_at=datetime('now') WHERE id=?",
            (zone, sub_id)
        )

        slug = _slugify(sub['biz_name'])
        c.execute(
            """INSERT OR IGNORE INTO brands
               (id, name, slug, category, founded_year, overall_zone,
                independent, pe_owned, owner)
               VALUES (?,?,?,?,?,?,1,0,?)""",
            (slug, sub['biz_name'], slug, sub.get('category'),
             sub.get('founded_year'), zone, sub.get('contact_name'))
        )

    return jsonify({'success': True, 'slug': slug})


@app.route('/api/admin/submissions/<int:sub_id>/reject', methods=['POST'])
def api_admin_reject(sub_id):
    if not _check_admin(request):
        return jsonify({'error': 'unauthorized'}), 401

    data = request.get_json(silent=True) or {}
    reason = data.get('reason', '')

    with sqlite3.connect(DB) as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM submissions WHERE id=?", (sub_id,))
        if not c.fetchone():
            return jsonify({'error': 'submission not found'}), 404
        c.execute(
            "UPDATE submissions SET status='rejected', reject_reason=?, reviewed_at=datetime('now') WHERE id=?",
            (reason, sub_id)
        )

    return jsonify({'success': True})


if __name__ == "__main__":
    import os
    port = int(os.environ.get("PORT", 5001))
    print(f"Traced running at http://0.0.0.0:{port}")
    app.run(debug=False, port=port, host='0.0.0.0')
