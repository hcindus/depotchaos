#!/usr/bin/env python3
import sqlite3, re, random
from collections import Counter
conn = sqlite3.connect('/root/.openclaw/workspace/DepotChaos/depot_chaos.db')
c = conn.cursor()
c.execute("SELECT id,name,city,state,source_file,vendor_type,phone,email,address FROM vendors")
rows = c.fetchall()
US_STATES = set("""AL AK AZ AR CA CO CT DE FL GA HI ID IL IN IA KS KY LA ME MD MA MI MN MS MO MT NE NV NH NJ NM NY NC ND OH OK OR PA RI SC SD TN TX UT VT VA WA WV WI WY""".split())
nums = re.compile(r'^[\d.\-]+(?:[,\s][\d.\-]+)*$')
def classify(r):
    name = (r[1] or '').strip(); state=(r[3] or '').strip()
    if name and nums.match(name):
        return 'synthetic_numeric_name'
    if state not in US_STATES or not state:
        return 'synthetic_bad_or_missing_state'
    return 'text_name_us_state'
cat = Counter(classify(r) for r in rows)
total = len(rows)
print("TOTAL:", total)
for k,v in cat.most_common():
    print(f"  {k}: {v} ({100*v/total:.1f}%)")
text_state = [r for r in rows if classify(r)=='text_name_us_state' and (r[5] or '')=='restaurant']
print("\nSample 'text_name_us_state' restaurant rows:")
random.seed(1)
for r in random.sample(text_state, 18):
    print("   ", r[1], '|', r[2], '|', r[3], '|', r[4][:35])
# source file breakdown of text_name_us_state
print("\nSource breakdown of salvageable text_name_us_state:")
sc = Counter(r[4] for r in rows if classify(r)=='text_name_us_state')
for k,v in sc.most_common():
    print(f"  {v:6d}  {k}")
print("done")
