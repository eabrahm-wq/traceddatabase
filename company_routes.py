import sqlite3, os

DB = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'traced.db')

def get_db():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn

def company_profile(company_id):
    conn = get_db()
    c = conn.cursor()
    c.execute("SELECT * FROM companies WHERE id=?", (company_id,))
    co = c.fetchone()
    if not co:
        conn.close()
        return None
    p = dict(co)
    c.execute(
        "SELECT id, name, acquired_year, acquisition_price, total_scans "
        "FROM brands WHERE parent_company_id=? "
        "ORDER BY total_scans DESC NULLS LAST",
        (company_id,))
    p["brands"] = [dict(r) for r in c.fetchall()]
    p["brand_count"] = len(p["brands"])
    p["total_acquisition_spend"] = sum(b["acquisition_price"] or 0 for b in p["brands"])
    c.execute(
        "SELECT violation_type, year, description, outcome, fine_amount "
        "FROM violations WHERE company_id=? AND violation_type != 'FDA recall' "
        "ORDER BY year DESC",
        (company_id,))
    p["fines"] = [dict(r) for r in c.fetchall()]
    c.execute(
        "SELECT violation_type, year, description, outcome "
        "FROM violations WHERE company_id=? AND violation_type='FDA recall' "
        "ORDER BY year DESC LIMIT 10",
        (company_id,))
    p["recalls"] = [dict(r) for r in c.fetchall()]
    p["recall_count"] = c.execute(
        "SELECT COUNT(*) FROM violations WHERE company_id=? AND violation_type='FDA recall'",
        (company_id,)).fetchone()[0]
    c.execute(
        "SELECT year, total_spend, issues FROM lobbying_records "
        "WHERE company_id=? ORDER BY year DESC",
        (company_id,))
    rows = [dict(r) for r in c.fetchall()]
    p["lobbying"] = rows
    p["lobbying_total"] = sum(r["total_spend"] for r in rows)
    c.execute(
        "SELECT SUM(fine_amount) FROM violations "
        "WHERE company_id=? AND fine_amount IS NOT NULL",
        (company_id,))
    p["fines_total"] = c.fetchone()[0] or 0
    conn.close()
    return p

CSS = """
:root{--bg:#0a0906;--surface:#121009;--s2:#1a1710;--border:rgba(255,255,255,0.06);--b2:rgba(255,255,255,0.12);--ink:#f0ead8;--muted:rgba(240,234,216,0.4);--amber:#d4952a;--alt:rgba(212,149,42,0.12);--red:#c44444;--rlt:rgba(196,68,68,0.1);--green:#3a8a5a}
*,*::before,*::after{box-sizing:border-box;margin:0;padding:0}
body{background:var(--bg);color:var(--ink);font-family:'DM Mono',monospace;min-height:100vh}
nav{border-bottom:1px solid var(--b2);padding:16px 40px;display:flex;align-items:center;justify-content:space-between;position:sticky;top:0;background:var(--bg);z-index:100}
.logo{font-family:'Bebas Neue',sans-serif;font-size:24px;letter-spacing:.1em;color:var(--amber);text-decoration:none}
.back{font-size:10px;color:var(--muted);text-decoration:none;letter-spacing:.08em;text-transform:uppercase;border:1px solid var(--border);padding:6px 14px;border-radius:6px}
.back:hover{color:var(--amber);border-color:var(--amber)}
.page{max-width:960px;margin:0 auto;padding:40px 40px 80px}
.co-name{font-family:'Bebas Neue',sans-serif;font-size:64px;letter-spacing:.04em;line-height:1;margin-bottom:12px}
.co-meta{display:flex;gap:16px;align-items:center;margin-bottom:8px}
.co-type{font-size:9px;background:var(--alt);color:var(--amber);border-radius:4px;padding:3px 8px;letter-spacing:.08em;text-transform:uppercase}
.co-country{font-size:11px;color:var(--muted)}
.co-ticker{font-size:11px;color:var(--muted)}
.co-rev{font-size:13px;color:var(--muted);margin-bottom:28px}
.stats-row{display:grid;grid-template-columns:repeat(5,1fr);gap:12px;margin-bottom:28px}
.stat{background:var(--surface);border:1px solid var(--border);border-radius:12px;padding:16px 20px}
.stat-label{font-size:9px;color:var(--muted);letter-spacing:.1em;text-transform:uppercase;margin-bottom:6px}
.stat-value{font-size:24px;font-family:'Bebas Neue',sans-serif;letter-spacing:.04em;line-height:1}
.stat-value.red{color:var(--red)}
.stat-value.amber{color:var(--amber)}
.sec{border:1px solid var(--border);border-radius:12px;overflow:hidden;margin-bottom:16px}
.sh{padding:14px 20px;background:var(--surface);border-bottom:1px solid var(--border);display:flex;align-items:center;justify-content:space-between}
.st{font-size:9px;letter-spacing:.14em;text-transform:uppercase;color:var(--amber);font-weight:500}
.sc{font-size:9px;color:var(--muted);background:var(--s2);border-radius:20px;padding:2px 8px}
.brand-grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:1px;background:var(--border)}
.brand-card{background:var(--bg);padding:16px 20px;cursor:pointer;transition:background .15s;text-decoration:none;display:block;color:inherit}
.brand-card:hover{background:var(--surface)}
.brand-card-name{font-size:13px;font-weight:500;margin-bottom:4px;color:var(--ink)}
.brand-card-acq{font-size:9px;color:var(--amber)}
.brand-card-scans{font-size:9px;color:var(--muted)}
.vi{padding:14px 20px;border-bottom:1px solid var(--border)}
.vi:last-child{border-bottom:none}
.vt{display:flex;align-items:center;gap:10px;margin-bottom:6px}
.vy{font-family:'Bebas Neue',sans-serif;font-size:18px;color:var(--red);line-height:1}
.vtype{font-size:8px;background:var(--rlt);color:var(--red);padding:2px 7px;border-radius:4px;letter-spacing:.08em;text-transform:uppercase}
.vo{font-size:8px;background:var(--s2);color:var(--muted);padding:2px 7px;border-radius:4px}
.vf{font-size:11px;color:var(--red);margin-left:auto;font-weight:500}
.vd{font-size:11px;color:rgba(240,234,216,.7);line-height:1.6}
.li{padding:12px 20px;border-bottom:1px solid var(--border);display:grid;grid-template-columns:50px 90px 1fr;gap:16px;align-items:center}
.li:last-child{border-bottom:none}
.ly{font-family:'Bebas Neue',sans-serif;font-size:18px;color:var(--muted);line-height:1}
.ls{font-size:13px;color:var(--amber);font-weight:500}
.lb{height:3px;background:var(--amber);border-radius:2px;margin-bottom:4px}
.liss{font-size:9px;color:var(--muted);line-height:1.5}
.ri{padding:12px 20px;border-bottom:1px solid var(--border);display:grid;grid-template-columns:60px 1fr;gap:16px;align-items:start}
.ri:last-child{border-bottom:none}
.ry{font-family:'Bebas Neue',sans-serif;font-size:18px;color:var(--red);line-height:1}
.rd{font-size:10px;color:rgba(240,234,216,.6);line-height:1.6}
.lt{font-size:11px;color:var(--red);font-weight:500}
@media(max-width:700px){.stats-row{grid-template-columns:repeat(2,1fr)}.co-name{font-size:40px}.page{padding:24px 16px 60px}}
"""

def render_company_page(p):
    def fm(v): return "$" + str(round(v/1e6)) + "M" if v else "&mdash;"
    def fb(v): return "$" + str(round(v/1e9, 1)) + "B" if v else "&mdash;"
    def fr(v): return "$" + str(round(v/1e9)) + "B" if v else "undisclosed"

    stats = (
        "<div class='stat'><div class='stat-label'>Brands Owned</div>"
        "<div class='stat-value amber'>" + str(p["brand_count"]) + "</div></div>"

        "<div class='stat'><div class='stat-label'>Acquisition Spend</div>"
        "<div class='stat-value'>" + fb(p["total_acquisition_spend"]) + "</div></div>"

        "<div class='stat'><div class='stat-label'>FDA Recalls</div>"
        "<div class='stat-value red'>" + str(p["recall_count"]) + "</div></div>"

        "<div class='stat'><div class='stat-label'>Fines &amp; Settlements</div>"
        "<div class='stat-value red'>" + fm(p["fines_total"]) + "</div></div>"

        "<div class='stat'><div class='stat-label'>Lobbying Spend</div>"
        "<div class='stat-value red'>" + fm(p["lobbying_total"]) + "</div></div>"
    )

    brand_cards = ""
    for b in p["brands"]:
        acq = "<div class='brand-card-acq'>Acquired " + str(b["acquired_year"]) + "</div>" if b.get("acquired_year") else ""
        scans = "<div class='brand-card-scans'>" + str(b["total_scans"]) + " scans</div>" if b.get("total_scans") else ""
        url = "/?q=" + b["name"].replace("&", "%26").replace("'", "%27")
        brand_cards += (
            "<a class='brand-card' href='" + url + "'>"
            "<div class='brand-card-name'>" + b["name"] + "</div>"
            + acq + scans +
            "</a>"
        )

    brands_sec = (
        "<div class='sec'><div class='sh'>"
        "<span class='st'>Brand Portfolio</span>"
        "<span class='sc'>" + str(p["brand_count"]) + " brands</span></div>"
        "<div class='brand-grid'>" + brand_cards + "</div></div>"
    )

    fines_sec = ""
    if p["fines"]:
        rows = ""
        for v in p["fines"]:
            fine = "<span class='vf'>$" + str(round(v["fine_amount"]/1e6, 1)) + "M</span>" if v.get("fine_amount") else ""
            rows += (
                "<div class='vi'><div class='vt'>"
                "<span class='vy'>" + str(v["year"]) + "</span>"
                "<span class='vtype'>" + v["violation_type"] + "</span>"
                "<span class='vo'>" + v["outcome"] + "</span>" + fine + "</div>"
                "<div class='vd'>" + v["description"][:300] + "</div></div>"
            )
        fines_sec = (
            "<div class='sec'><div class='sh'>"
            "<span class='st'>FTC / FDA Violations</span>"
            "<span class='sc'>" + str(len(p["fines"])) + "</span></div>"
            + rows + "</div>"
        )

    lo_sec = ""
    if p["lobbying"]:
        mx = max(l["total_spend"] for l in p["lobbying"])
        rows = ""
        for l in p["lobbying"]:
            w = int(l["total_spend"] / mx * 100)
            rows += (
                "<div class='li'><span class='ly'>" + str(l["year"]) + "</span>"
                "<span class='ls'>" + fm(l["total_spend"]) + "</span>"
                "<div><div class='lb' style='width:" + str(w) + "%'></div>"
                "<div class='liss'>" + l["issues"] + "</div></div></div>"
            )
        lo_sec = (
            "<div class='sec'><div class='sh'>"
            "<span class='st'>Lobbying Record</span>"
            "<span class='lt'>" + fm(p["lobbying_total"]) + " documented</span></div>"
            + rows + "</div>"
        )

    recall_sec = ""
    if p["recalls"]:
        rows = ""
        for r in p["recalls"]:
            rows += (
                "<div class='ri'><span class='ry'>" + str(r["year"]) + "</span>"
                "<div class='rd'>" + r["description"][:250] + "</div></div>"
            )
        more = ""
        if p["recall_count"] > len(p["recalls"]):
            more = ("<div style='padding:12px 20px;font-size:10px;color:var(--muted)'>"
                    + str(p["recall_count"] - len(p["recalls"])) + " more recalls not shown</div>")
        recall_sec = (
            "<div class='sec'><div class='sh'>"
            "<span class='st'>FDA Recalls</span>"
            "<span class='sc'>" + str(p["recall_count"]) + " total</span></div>"
            + rows + more + "</div>"
        )

    ticker = "<span class='co-ticker'>" + p["ticker"] + "</span>" if p.get("ticker") else ""

    return (
        "<!DOCTYPE html><html lang='en'><head>"
        "<meta charset='UTF-8'>"
        "<meta name='viewport' content='width=device-width,initial-scale=1.0'>"
        "<title>" + p["name"] + " &mdash; Traced</title>"
        "<link href='https://fonts.googleapis.com/css2?family=Bebas+Neue&family=DM+Mono:wght@300;400;500&family=Playfair+Display:ital,wght@0,700;1,400&display=swap' rel='stylesheet'>"
        "<style>" + CSS + "</style></head><body>"
        "<nav>"
        "<a class='logo' href='/'>TRACED</a>"
        "<a class='back' href='/'>&#8592; Search Brands</a>"
        "</nav>"
        "<div class='page'>"
        "<div class='co-name'>" + p["name"] + "</div>"
        "<div class='co-meta'>"
        "<span class='co-type'>" + (p.get("type") or "") + "</span>"
        "<span class='co-country'>" + (p.get("hq_country") or "") + "</span>"
        + ticker +
        "</div>"
        "<div class='co-rev'>" + fr(p.get("annual_revenue")) + " annual revenue</div>"
        "<div class='stats-row'>" + stats + "</div>"
        + brands_sec + fines_sec + lo_sec + recall_sec +
        "</div>"
        "</body></html>"
    )
