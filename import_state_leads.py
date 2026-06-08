#!/usr/bin/env python3
"""
Import state leads CSV files into DepotChaos vendors table for enrichment
"""

import sqlite3
import csv
import json
from pathlib import Path
from datetime import datetime

DB_PATH = "/root/.openclaw/workspace/DepotChaos/depot_chaos.db"
LEADS_DIR = "/root/.openclaw/workspace/AGI_COMPANY/data/leads_final"

def import_state_csv(state_code):
    """Import leads from a state CSV file"""
    csv_path = Path(LEADS_DIR) / f"FINAL_STATE_{state_code}.csv"
    
    if not csv_path.exists():
        print(f"⚠️  File not found: {csv_path}")
        return 0
    
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    
    imported = 0
    skipped = 0
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Skip if missing essential data
            company = row.get('Company', '').strip()
            if not company or company == 'N/A':
                skipped += 1
                continue
            
            city = row.get('City', '').strip()
            county = row.get('County', '').strip()
            state = row.get('State', '').strip()
            
            # Check if already exists
            c.execute("SELECT id FROM vendors WHERE name = ? AND city = ?", (company, city))
            if c.fetchone():
                skipped += 1
                continue
            
            # Build notes from available data
            notes = []
            if row.get('Tags'):
                notes.append(f"Tags: {row['Tags']}")
            if row.get('Notes'):
                notes.append(row['Notes'])
            if row.get('Priority'):
                notes.append(f"Priority: {row['Priority']}")
            if row.get('Email_Valid'):
                notes.append(f"Email Valid: {row['Email_Valid']}")
            
            notes_text = " | ".join(notes) if notes else f"Imported from {state_code} leads"
            
            # Insert vendor
            c.execute("""
                INSERT INTO vendors 
                (name, dba_name, contact_name, phone, email, city, state, zip, 
                 vendor_type, status, source_file, imported_at, notes)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                company,
                row.get('Company', ''),  # DBA same as company for now
                f"{row.get('First Name', '')} {row.get('Last Name', '')}".strip(),
                row.get('Phone', ''),
                row.get('Email', ''),
                city,
                state,
                row.get('Postal Code', ''),
                'County Lead',
                'active',
                f"AGI_County_Leads_{state_code}",
                datetime.now().isoformat(),
                notes_text
            ))
            imported += 1
    
    conn.commit()
    conn.close()
    
    print(f"✅ {state_code}: Imported {imported}, skipped {skipped}")
    return imported

def main():
    states = ['OR', 'WA', 'TX', 'VA', 'PA', 'SC', 'TN', 'UT', 'WI', 'FL', 'AZ', 'NC', 'LA', 'MD', 'CO', 'CA', 'NV', 'MN', 'NY', 'NJ', 'IL', 'OH', 'MI', 'GA', 'IN', 'MO', 'MA', 'CT', 'KS', 'NE', 'IA', 'ID', 'MT', 'ND', 'SD', 'OK', 'AR']
    
    total = 0
    for state in states:
        count = import_state_csv(state)
        total += count
    
    print(f"\n📊 Total imported: {total}")

if __name__ == "__main__":
    main()
