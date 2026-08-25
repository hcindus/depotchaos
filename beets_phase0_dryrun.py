#!/usr/bin/env python3
"""
Beets: DepotChaos Phase-0 DRY-RUN classification report.
Reads ONLY from a COPY; writes nothing to the live depot_chaos.db.
Produces projected purge numbers per rule so the Captain can review.
"""
import sqlite3, re, os, shutil, sys
from collections import Counter

SRC = '/root/.openclaw/workspace/DepotChaos/depot_chaos.db'
COPY = '/tmp/depot_chaos_phase0_DRYRUN.db'

# Build a throwaway copy so we never touch prod
shutil.copy2(SRC, COPY)
conn = sqlite3.connect(COPY)
conn.row_factory = sqlite3.Row
c = conn.cursor()

c.execute("SELECT id,name,city,state,zip,address,source_file,vendor_type,status FROM vendors")
rows = [dict(r) for r in c.fetchall()]
total = len(rows)

US_STATES = set("""AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY""".split())
nums_only = re.compile(r'^[\d.\-]+(?:[,\s][\d.\-]+)*$')
# templated city-restaurant names like "Dover Restaurant", "The Dover Bar & Grill"
tmpl = re.compile(r'^(the\s+)?[\w\s\-&]+?\s+(restaurant|bar & grill|eatery|cafe|lounge|diner|bistro|kitchen)$', re.I)
# templated small-word business names
small = re.compile(r'^(little|big|el|la|golden|blue|red|the)\s+(kitchen|house|eatery|lounge|cafe|tavern|diner|bistro|grill|bar)\s*(lounge|bar|co|restaurant)?$', re.I)
surname_ind = ['williams','jones','brown','miller','garcia','rodriguez','johnson','smith','davis','wilson','martinez','anderson','taylor','thomas','moore','jackson','lee','harris','clark','lewis','walker','young','allen','king','wright','scott','torres','nguyen','hill','flores','green','adams','nelson','baker','hall','rivera','campbell','mitchell','carter','roberts']

def classify(r):
    name = (r['name'] or '').strip()
    state = (r['state'] or '').strip()
    city = (r['city'] or '').strip()
    src = (r['source_file'] or '').strip()
    # 1. numeric names
    if name and nums_only.match(name):
        return 'purge_numeric_name'
    # 2. bad state
    if not state or state not in US_STATES:
        return 'purge_bad_state'
    # 3. county leads (fabricated surnames + industry)
    if src.startswith('AGI_County_Leads'):
        ln = name.strip().lower().split()
        if ln and ln[0] in surname_ind:
            return 'purge_county_leads'
    # 4. templated city-restaurant
    if tmpl.match(name) and ' ' in name.strip():
        return 'purge_templated_location'
    if small.match(name) and not city:
        return 'purge_templated_small'
    if city in ('Metro City',) or state in ('P0','P20','P40','P0-9MOS','P0-6MOS'):
        return 'purge_bad_city_state_marker'
    return 'keep_verify'

cat = Counter()
detail = Counter()
keep = []
for r in rows:
    k = classify(r)
    cat[k] += 1
    if k.startswith('purge'):
        detail[(k, r['source_file'] or 'n/a')] += 1
    else:
        keep.append(r)

print("="*70)
print("DEPOTCHAOS PHASE-0 DRY-RUN CLASSIFICATION (on COPY, prod untouched)")
print("="*70)
print(f"TOTAL RECORDS: {total}\n")
print(f"{'CLASS':<32}{'COUNT':>8}{'PCT':>8}")
print("-"*48)
for k,v in cat.most_common():
    print(f"{k:<32}{v:>8}{100*v/total:>7.1f}%")
purged = sum(v for k,v in cat.items() if k.startswith('purge'))
keepc  = total - purged
print("-"*48)
print(f"{'PURGE TOTAL':<32}{purged:>8}{100*purged/total:>7.1f}%")
print(f"{'KEEP & VERIFY':<32}{keepc:>8}{100*keepc/total:>7.1f}%")

print("\n\nPURGE DETAIL BY RULE + SOURCE (top 25):")
print("-"*75)
for (rule, src), v in detail.most_common(25):
    print(f"  {v:>6}  {rule:<28} {src}")

print("\n\nKEEP-AND-VERIFY SOURCE BREAKDOWN (top 15):")
print("-"*75)
sc = Counter(r['source_file'] or 'n/a' for r in keep)
for src,v in sc.most_common(15):
    print(f"  {v:>6}  {src}")

conn.close()
os.remove(COPY)
print("\n(dry-run copy removed; live DB untouched)")
