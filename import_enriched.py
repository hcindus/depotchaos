#!/usr/bin/env python3
"""
DepotChaos Enrichment Import
Imports enriched data back into the database
"""

import sqlite3
import csv
import sys
from datetime import datetime

DB_PATH = "/root/.openclaw/workspace/DepotChaos/depot_chaos.db"

def import_enriched(csv_file):
    """Import enriched data from CSV"""
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    updated = 0
    skipped = 0
    errors = 0
    
    with open(csv_file, 'r') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            vendor_id = row.get('vendor_id')
            enriched_phone = row.get('enriched_phone', '').strip()
            enriched_email = row.get('enriched_email', '').strip()
            enriched_contact = row.get('enriched_contact_name', '').strip()
            enriched_title = row.get('enriched_contact_title', '').strip()
            enriched_website = row.get('enriched_website', '').strip()
            enrichment_source = row.get('enrichment_source', '').strip()
            
            # Skip if no enrichment data
            if not enriched_phone and not enriched_email:
                skipped += 1
                continue
            
            try:
                # Build update query dynamically
                updates = []
                params = []
                
                if enriched_phone:
                    updates.append('phone = ?')
                    params.append(enriched_phone)
                
                if enriched_email:
                    updates.append('email = ?')
                    params.append(enriched_email)
                
                if enriched_contact:
                    updates.append('contact_name = ?')
                    params.append(enriched_contact)
                
                # Add enrichment note
                enrichment_note = f"\n[Enriched {datetime.now().strftime('%Y-%m-%d')}"
                if enrichment_source:
                    enrichment_note += f" via {enrichment_source}"
                if enriched_website:
                    enrichment_note += f", Website: {enriched_website}"
                enrichment_note += "]"
                
                updates.append('notes = COALESCE(notes, "") || ?')
                params.append(enrichment_note)
                
                updates.append('last_contact_at = datetime("now")')
                
                query = f"UPDATE vendors SET {', '.join(updates)} WHERE id = ?"
                params.append(vendor_id)
                
                cursor.execute(query, params)
                updated += 1
                
            except Exception as e:
                print(f"❌ Error updating vendor {vendor_id}: {e}")
                errors += 1
    
    conn.commit()
    conn.close()
    
    print(f"\n✅ Import complete!")
    print(f"   Updated: {updated}")
    print(f"   Skipped (no data): {skipped}")
    print(f"   Errors: {errors}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python3 import_enriched.py <enriched_csv_file>")
        sys.exit(1)
    
    import_enriched(sys.argv[1])
