#!/usr/bin/env python3
"""cheap_enrich.py — FREE enrichment: DDGS search -> real website -> email+phone.
No guess-pattern emails. Only writes high-confidence emails found on the site itself.
Usage: python3 cheap_enrich.py [--limit N] [--city CITY] [--state CA]
"""
import re, sys, time, sqlite3, random, argparse, json
from urllib.parse import urljoin, urlparse

try:
    from ddgs import DDGS
except ImportError:
    from duckduckgo_search import DDGS

import requests
from bs4 import BeautifulSoup

DB = "/root/.openclaw/workspace/DepotChaos/depot_chaos.db"
UA = ("Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
      "(KHTML, like Gecko) Chrome/124.0 Safari/537.36")

EMAIL_RE = re.compile(r"[A-Za-z0-9._%+\-]+@[A-Za-z0-9.\-]+\.[A-Za-z]{2,}")
PHONE_RE = re.compile(r"(?:\+?1[\s.\-]?)?\(?([2-9]\d{2})\)?[\s.\-]?(\d{3})[\s.\-]?(\d{4})")
BAD_EMAIL = re.compile(
    r"(example\.|sentry|wixpress|@2x|\.png|\.jpg|\.jpeg|\.gif|\.webp|\.svg|\.css|\.js$|"
    r"godaddy|squarespace|wix|domain|yourdomain|email@|user@|name@|no-?reply|"
    r"@schema\.org|@w3\.org|@facebook|@instagram|@google|cloudflare|wordpress)", re.I)

SKIP_HOSTS = ("facebook.", "instagram.", "yelp.", "tripadvisor.", "doordash.",
              "grubhub.", "ubereats.", "postmates.", "maps.google", "google.",
              "yellowpages.", "manta.com", "mapquest.", "bbb.org", "wikipedia.",
              "tiktok.", "twitter.", "x.com", "linkedin.", "zomato.", "opentable.",
              "menuism.", "allmenus.", "restaurantji.", "usarestaurants.", "chamberofcommerce.",
              "expertise.com", "birdeye.", "nextdoor.", "pinterest.", "youtube.", "foursquare.")

CONTACT_HINTS = ("contact", "about", "contact-us", "contactus", "reach-us", "info", "hours", "locations")


def norm_phone(m):
    a, b, c = m.group(1), m.group(2), m.group(3)
    return f"({a}) {b}-{c}"


def is_good_email(e):
    if BAD_EMAIL.search(e):
        return False
    if len(e) > 60 or e.count("@") != 1:
        return False
    local, dom = e.split("@")
    if len(local) < 2 or "." not in dom:
        return False
    return True


def fetch(url, timeout=12):
    try:
        r = requests.get(url, headers={"User-Agent": UA,
                                       "Accept": "text/html,application/xhtml+xml"},
                         timeout=timeout, allow_redirects=True)
        if r.status_code == 200 and "html" in r.headers.get("content-type", ""):
            return r.text, r.url
    except Exception:
        pass
    return None, None


def find_site(name, city, state):
    """Return (url, domain) of the most plausible OWN website."""
    queries = [
        f'"{name}" {city} {state}',
        f'{name} {city} {state} contact',
        f'{name} {city} restaurant',
    ]
    seen = []
    for q in queries:
        try:
            with DDGS() as d:
                res = list(d.text(q, max_results=8))
        except Exception:
            res = []
        for r in res:
            href = r.get("href") or r.get("url") or ""
            if not href.startswith("http"):
                continue
            host = urlparse(href).netloc.lower().replace("www.", "")
            if any(s in host for s in SKIP_HOSTS):
                continue
            if host in [h for h, _ in seen]:
                continue
            seen.append((host, href))
        if seen:
            break
        time.sleep(2 + random.random() * 2)
    if not seen:
        return None, None
    # prefer host that partially matches the business name tokens
    toks = [t for t in re.findall(r"[a-z]{4,}", name.lower()) if t not in
            ("the", "and", "restaurant", "cafe", "coffee", "bakery", "taqueria", "grill", "kitchen")]
    for host, href in seen:
        if toks and any(t in host.replace("-", "") for t in toks):
            return href, host
    return seen[0][1], seen[0][0]


def scrape_contact(base_url):
    """Fetch homepage + up to 2 contact pages; return (emails, phones)."""
    emails, phones = [], []
    html, final = fetch(base_url)
    if not html:
        return emails, phones
    pages = [(html, final)]
    soup = BeautifulSoup(html, "html.parser")
    cands = []
    for a in soup.find_all("a", href=True):
        txt = (a.get_text() or "").lower()
        href = a["href"]
        if any(h in txt for h in CONTACT_HINTS) or any(h in href.lower() for h in CONTACT_HINTS):
            u = urljoin(final, href)
            if urlparse(u).netloc == urlparse(final).netloc and u not in cands:
                cands.append(u)
    for u in cands[:2]:
        h2, f2 = fetch(u)
        if h2:
            pages.append((h2, f2))
        time.sleep(0.6)

    domain = urlparse(final).netloc.lower().replace("www.", "")
    for h, _u in pages:
        # mailto links are strongest
        for m in re.findall(r'mailto:([^"\'?>\s]+)', h, re.I):
            m = m.strip()
            if is_good_email(m):
                emails.append(m)
        text = BeautifulSoup(h, "html.parser").get_text(" ", strip=True)
        for e in EMAIL_RE.findall(h) + EMAIL_RE.findall(text):
            e = e.strip(".,;:").lower()
            if is_good_email(e):
                emails.append(e)
        for m in PHONE_RE.finditer(text):
            p = norm_phone(m)
            phones.append(p)

    # dedupe, prefer same-domain emails
    def dedup(lst):
        out = []
        for x in lst:
            if x not in out:
                out.append(x)
        return out
    emails = dedup(emails)
    same = [e for e in emails if e.split("@")[1].endswith(domain) or domain.endswith(e.split("@")[1])]
    if same:
        emails = same + [e for e in emails if e not in same]
    # drop obvious free-mail-only when a domain email exists
    phones = dedup(phones)
    return emails, phones


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=60)
    ap.add_argument("--state", default="CA")
    ap.add_argument("--city", default=None)
    ap.add_argument("--min-yield-report", action="store_true")
    args = ap.parse_args()

    con = sqlite3.connect(DB, timeout=30)
    con.execute("PRAGMA busy_timeout=30000")
    q = ("SELECT id,name,city,state,address,phone,email FROM vendors "
         "WHERE data_class='real' AND (email IS NULL OR email='') "
         f"AND state=? ")
    p = [args.state]
    if args.city:
        q += "AND city=? "
        p.append(args.city)
    q += "ORDER BY city ASC, name ASC LIMIT ?"
    p.append(args.limit)
    rows = con.execute(q, p).fetchall()
    print(f"[start] candidates={len(rows)}", flush=True)

    stats = {"processed": 0, "email": 0, "phone": 0, "site": 0, "fail": 0}
    log = []
    for i, (vid, name, city, state, addr, phone, email) in enumerate(rows, 1):
        stats["processed"] += 1
        dba = name
        print(f"[{i}/{len(rows)}] {name} — {city}, {state}", flush=True)
        try:
            site, host = find_site(dba, city, state)
            if not site:
                stats["fail"] += 1
                print("    no site", flush=True)
                log.append({"id": vid, "name": name, "city": city, "result": "no_site"})
                time.sleep(3 + random.random() * 3)
                continue
            stats["site"] += 1
            emails, phones = scrape_contact(site)
            best_email = emails[0] if emails else None
            best_phone = None
            if not phone:
                best_phone = phones[0] if phones else None
            if best_email:
                stats["email"] += 1
            if best_phone:
                stats["phone"] += 1
            updates, params = [], []
            if best_email:
                updates.append("email=?")
                params.append(best_email)
            if best_phone:
                updates.append("phone=?")
                params.append(best_phone)
            if updates:
                params += [vid]
                con.execute(f"UPDATE vendors SET {', '.join(updates)} WHERE id=?", params)
                con.commit()
            print(f"    site={host} email={best_email} phone={best_phone}", flush=True)
            log.append({"id": vid, "name": name, "city": city, "site": host,
                        "email": best_email, "phone": best_phone,
                        "result": "updated" if updates else "no_contact"})
        except Exception as e:
            stats["fail"] += 1
            print(f"    ERR {e}", flush=True)
            log.append({"id": vid, "name": name, "city": city, "result": f"error:{e}"})
        time.sleep(2.5 + random.random() * 3)

    with open("/root/.openclaw/workspace/DepotChaos/enrich_log.json", "w") as f:
        json.dump(log, f, indent=1)
    print("STATS", json.dumps(stats), flush=True)
    con.close()


if __name__ == "__main__":
    main()
