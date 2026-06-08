#!/usr/bin/env python3
"""
DepotChaos Enrichment Export
Exports vendors needing real contact data for manual/web enrichment
Creates editable CSV that can be re-imported
"""

import sqlite3
import csv
import json
from datetime import datetime
from pathlib import Path

DB_PATH = "/root/.openclaw/workspace/DepotChaos/depot_chaos.db"
EXPORT_DIR = "/root/.openclaw/workspace/DepotChaos/enrichment_queue"

def export_for_enrichment(batch_size=100):
    """Export vendors needing enrichment to CSV"""
    
    Path(EXPORT_DIR).mkdir(parents=True, exist_ok=True)
    
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Get vendors needing enrichment
    # Prioritize those with real business names (not just numbers)
    cursor.execute("""
        SELECT 
            v.id,
            v.name as business_name,
            v.dba_name,
            v.contact_name,
            v.phone as current_phone,
            v.email as current_email,
            v.address,
            v.city,
            v.state,
            v.zip,
            v.vendor_type,
            v.status,
            v.source_file,
            v.notes
        FROM vendors v
        WHERE (v.phone IS NULL OR v.phone = '' OR v.phone LIKE '%555%')
          AND v.name NOT LIKE '%[0-9]%'
          AND length(v.name) > 3
        ORDER BY 
            CASE WHEN v.city IS NOT NULL THEN 0 ELSE 1 END,
            v.name
        LIMIT ?
    """, (batch_size,))
    
    vendors = cursor.fetchall()
    
    if not vendors:
        print("✅ No vendors need enrichment")
        return None
    
    # Create export file
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    export_file = f"{EXPORT_DIR}/enrichment_batch_{timestamp}.csv"
    
    headers = [
        'vendor_id', 'business_name', 'dba_name', 'current_contact',
        'current_phone', 'current_email', 'current_address',
        'city', 'state', 'zip', 'vendor_type', 'status',
        'source_file', 'notes',
        # Enrichment fields (to be filled in)
        'enriched_phone', 'enriched_email', 'enriched_contact_name',
        'enriched_contact_title', 'enriched_website', 'enrichment_source',
        'enrichment_date', 'enriched_by', 'verified'
    ]
    
    with open(export_file, 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        
        for v in vendors:
            row = list(v) + [''] * 9  # Empty enrichment fields
            writer.writerow(row)
    
    # Mark these vendors as "in_progress" 
    vendor_ids = [v[0] for v in vendors]
    placeholders = ','.join('?' * len(vendor_ids))
    cursor.execute(f"""
        UPDATE vendors 
        SET notes = COALESCE(notes, '') || '\n[Enrichment Queue: {timestamp}]'
        WHERE id IN ({placeholders})
    """, vendor_ids)
    conn.commit()
    conn.close()
    
    print(f"✅ Exported {len(vendors)} vendors for enrichment")
    print(f"📁 File: {export_file}")
    print(f"\n📊 Summary:")
    print(f"   - Business names will be searched online")
    print(f"   - Real phone/email to be added in enriched_phone/enriched_email columns")
    print(f"   - Import back using: python3 import_enriched.py {export_file}")
    
    return export_file

def preview_export():
    """Show sample of what will be exported"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT name, city, state, vendor_type
        FROM vendors
        WHERE (phone IS NULL OR phone = '') 
          AND name NOT LIKE '%[0-9]%'
          AND length(name) > 3
        ORDER BY RANDOM()
        LIMIT 10
    """)
    
    print("\n📋 Sample vendors ready for enrichment:\n")
    print(f"{'Business Name':<40} {'City':<20} {'Type':<15}")
    print("-" * 75)
    for row in cursor.fetchall():
        print(f"{row[0]:<40} {row[1] or 'N/A':<20} {row[3] or 'N/A':<15}")
    
    # Count total
    cursor.execute("""
        SELECT COUNT(*)
        FROM vendors
        WHERE (phone IS NULL OR phone = '') 
          AND name NOT LIKE '%[0-9]%'
          AND length(name) > 3
    """)
    total = cursor.fetchone()[0]
    print(f"\n📊 Total vendors needing enrichment: {total}")
    
    conn.close()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--preview":
        preview_export()
    else:
        print("="*60)
        print("🚀 DEPOTCHAOS ENRICHMENT EXPORT")
        print("="*60)
        preview_export()
        print()
        
        export_file = export_for_enrichment(batch_size=100)
        
        if export_file:
            print(f"\n✅ Export complete!")
            print(f"\nNext steps:")
            print(f"1. Open: {export_file}")
            print(f"2. Use browser/web search to find real phone/email")
            print(f"3. Fill in enriched_phone and enriched_email columns")
            print(f"4. Import back: python3 import_enriched.py {export_file}")
