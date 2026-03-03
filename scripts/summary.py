#!/usr/bin/env python3
"""
Traced Database — Comprehensive Summary
Run: python scripts/summary.py
"""
import sqlite3, sys
from collections import Counter

DB = 'traced.db'

def main():
    try:
        conn = sqlite3.connect(DB)
    except Exception as e:
        print(f"Cannot open {DB}: {e}")
        sys.exit(1)
    c = conn.cursor()

    print("=" * 60)
    print("TRACED DATABASE SUMMARY")
    print("=" * 60)

    for label, query in [
        ("Companies",        "SELECT COUNT(*) FROM companies"),
        ("Brands",           "SELECT COUNT(*) FROM brands"),
        ("Products",         "SELECT COUNT(*) FROM products"),
        ("Violations",       "SELECT COUNT(*) FROM violations"),
        ("Lobbying Records", "SELECT COUNT(*) FROM lobbying_records"),
        ("Brand Events",     "SELECT COUNT(*) FROM brand_events"),
        ("Ingredient Snaps", "SELECT COUNT(*) FROM ingredient_snapshots"),
    ]:
        c.execute(query)
        print(f"  {label:<22} {c.fetchone()[0]:>8,}")

    print("\nVIOLATIONS BY TYPE")
    c.execute("SELECT violation_type, COUNT(*) cnt FROM violations GROUP BY violation_type ORDER BY cnt DESC")
    for vtype, cnt in c.fetchall():
        print(f"  {vtype:<40} {cnt:>5,}")

    c.execute("SELECT SUM(total_spend) FROM lobbying_records")
    spend = c.fetchone()[0] or 0
    c.execute("SELECT MIN(year), MAX(year) FROM lobbying_records")
    yr_min, yr_max = c.fetchone()
    print(f"\nLOBBYING  ${spend:,.0f} total  ({yr_min}–{yr_max})")

    print("\nTOP CONTRADICTION BRANDS (score >= 70)")
    c.execute("""SELECT b.name, co.name, b.contradiction_score
                 FROM brands b JOIN companies co ON co.id = b.parent_company_id
                 WHERE b.contradiction_score >= 70
                 ORDER BY b.contradiction_score DESC LIMIT 20""")
    for bname, coname, score in c.fetchall():
        print(f"  [{score:3d}] {bname:<35} — {coname}")

    print("\nTOP ADDITIVES (product count)")
    c.execute("SELECT additives FROM ingredient_snapshots WHERE additives IS NOT NULL AND additives != ''")
    counter = Counter()
    for (row,) in c.fetchall():
        for a in row.split(', '):
            if a.strip():
                counter[a.strip()] += 1
    for additive, count in counter.most_common(10):
        print(f"  {additive:<35} {count:>7,}")

    print("\nCOMPANIES BY VIOLATION COUNT")
    c.execute("""SELECT co.name, COUNT(v.id) cnt FROM companies co
                 JOIN violations v ON v.company_id = co.id
                 GROUP BY co.id ORDER BY cnt DESC LIMIT 15""")
    for coname, cnt in c.fetchall():
        print(f"  {coname:<35} {cnt:>5,}")

    print()
    conn.close()

if __name__ == '__main__':
    main()
