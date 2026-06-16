#!/usr/bin/env python3
"""
DepotChaos Yelp Enrichment
Uses Yelp Fusion API to find real contact data for businesses
"""

import sqlite3
import csv
import json
import time
import os
import requests
from datetime import datetime
from pathlib import Path

DB_PATH = "/root/.openclaw/workspace/aoscros_brain/DepotChaos/depot_chaos.db"
LOG_FILE = "/var/log/aos/yelp_enrichment.log"
CACHE_FILE = "/root/.openclaw/workspace/aoscros_brain/DepotChaos/yelp_cache.json"

YELP_API_KEY = os.environ.get('YELP_API_KEY', '5DUaC-eBObfSXkjf4YfLNlViO-WqwwCk0UJYewfhav25gbTrCaPvPR_nhokKyfBNKnduMHkqd5Z_v_0RwHSj2fXs8ziaJ-O_RAkuRvc6L6Lt9dwEboKoYHBpBuL1aXYx')

class YelpEnricher:
    def __init__(self):
        self.enriched_count = 0
        self.not_found = 0
        self.errors = 0
        self.cache = self.load_cache()
        
    def log(self, message):
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"[{timestamp}] {message}"
        print(log_entry)
        Path(LOG_FILE).parent.mkdir(parents=True, exist_ok=True)
        with open(LOG_FILE, 'a') as f:
            f.write(log_entry + "\n")
    
    def load_cache(self):
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except:
            return {}
    
    def save_cache(self):
        with open(CACHE_FILE, 'w') as f:
            json.dump(self.cache, f, indent=2)
    
    def search_yelp(self, business_name, city="", state=""):
        """Search Yelp for business details"""
        cache_key = f"{business_name}_{city}_{state}"
        
        if cache_key in self.cache:
            return self.cache[cache_key]
        
        headers = {'Authorization': f'Bearer {YELP_API_KEY}'}
        search_url = 'https://api.yelp.com/v3/businesses/search'
        
        # Build location string
        location = city if city else "California"
        if state and state not in location:
            location = f"{city}, {state}" if city else state
        
        params = {
            'term': business_name,
            'location': location,
            'limit': 3  # Get top 3 matches
        }
        
        try:
            response = requests.get(search_url, headers=headers, params=params, timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                businesses = data.get('businesses', [])
                
                if businesses:
                    # Return the best match
                    best_match = businesses[0]
                    result = {
                        'name': best_match.get('name'),
                        'phone': best_match.get('phone', ''),
                        'address': ', '.join(best_match.get('location', {}).get('display_address', [])),
                        'city': best_match.get('location', {}).get('city', ''),
                        'state': best_match.get('location', {}).get('state', ''),
                        'zip': best_match.get('location', {}).get('zip_code', ''),
                        'rating': best_match.get('rating', 0),
                        'review_count': best_match.get('review_count', 0),
                        'yelp_url': best_match.get('url', ''),
                        'categories': [c.get('title') for c in best_match.get('categories', [])]
                    }
                    self.cache[cache_key] = result
                    return result
                else:
                    self.cache[cache_key] = None
                    return None
            else:
                self.log(f"Yelp API error: {response.status_code} - {response.text[:100]}")
                return None
                
        except Exception as e:
            self.log(f"Yelp API exception: {e}")
            self.errors += 1
            return None
    
    def get_vendors_to_enrich(self, limit=100):
        """Get vendors needing enrichment"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, name, city, state
            FROM vendors
            WHERE (phone IS NULL OR phone = '' OR phone LIKE '%555%')
              AND name NOT LIKE '%[0-9]%'
              AND length(name) > 3
              AND (notes IS NULL OR notes NOT LIKE '%[Yelp Enriched]%')
            ORDER BY RANDOM()
            LIMIT ?
        """, (limit,))
        
        vendors = []
        for row in cursor.fetchall():
            vendors.append({
                'id': row[0],
                'name': row[1],
                'city': row[2] or '',
                'state': row[3] or ''
            })
        
        conn.close()
        return vendors
    
    def update_vendor(self, vendor_id, yelp_data):
        """Update vendor with Yelp data"""
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # Build update
        updates = []
        params = []
        
        if yelp_data.get('phone'):
            updates.append('phone = ?')
            params.append(yelp_data['phone'])
        
        if yelp_data.get('address'):
            updates.append('address = ?')
            params.append(yelp_data['address'])
        
        if yelp_data.get('city'):
            updates.append('city = ?')
            params.append(yelp_data['city'])
            
        if yelp_data.get('state'):
            updates.append('state = ?')
            params.append(yelp_data['state'])
            
        if yelp_data.get('zip'):
            updates.append('zip = ?')
            params.append(yelp_data['zip'])
        
        # Add note about enrichment
        note = f"\n[Yelp Enriched {datetime.now().strftime('%Y-%m-%d')}]"
        note += f" Rating: {yelp_data.get('rating', 'N/A')}"
        note += f" | Reviews: {yelp_data.get('review_count', 0)}"
        if yelp_data.get('categories'):
            note += f" | Type: {', '.join(yelp_data['categories'][:2])}"
        
        updates.append('notes = COALESCE(notes, "") || ?')
        params.append(note)
        
        updates.append('last_contact_at = datetime("now")')
        
        query = f"UPDATE vendors SET {', '.join(updates)} WHERE id = ?"
        params.append(vendor_id)
        
        cursor.execute(query, params)
        conn.commit()
        conn.close()
    
    def run(self, batch_size=50):
        """Run enrichment process"""
        self.log("="*60)
        self.log("🚀 YELP ENRICHMENT STARTED")
        self.log("="*60)
        
        vendors = self.get_vendors_to_enrich(limit=batch_size)
        
        if not vendors:
            self.log("✅ No vendors need enrichment")
            return 0
        
        self.log(f"📊 Processing {len(vendors)} vendors")
        
        for i, vendor in enumerate(vendors, 1):
            try:
                self.log(f"🔍 [{i}/{len(vendors)}] Searching: {vendor['name'][:40]}")
                
                yelp_data = self.search_yelp(
                    vendor['name'],
                    vendor['city'],
                    vendor['state']
                )
                
                if yelp_data:
                    self.update_vendor(vendor['id'], yelp_data)
                    self.enriched_count += 1
                    self.log(f"   ✅ Enriched: {yelp_data.get('name')} | "
                              f"Phone: {yelp_data.get('phone', 'N/A')} | "
                              f"Rating: {yelp_data.get('rating', 'N/A')}★")
                else:
                    self.not_found += 1
                    self.log(f"   ⚠️  Not found on Yelp")
                
                # Rate limiting - Yelp allows 5000 requests/day
                time.sleep(0.2)
                
            except Exception as e:
                self.log(f"   ❌ Error: {e}")
                self.errors += 1
        
        self.save_cache()
        
        self.log(f"\n📊 COMPLETE")
        self.log(f"   Enriched: {self.enriched_count}")
        self.log(f"   Not found: {self.not_found}")
        self.log(f"   Errors: {self.errors}")
        
        return self.enriched_count

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description='Yelp Enrichment Tool')
    parser.add_argument('--single', type=int, help='Enrich single vendor by ID')
    parser.add_argument('--batch-size', type=int, default=100, help='Number of vendors to process')
    args = parser.parse_args()
    
    enricher = YelpEnricher()
    
    if args.single:
        # Single vendor mode
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, city, state FROM vendors WHERE id = ?", (args.single,))
        row = cursor.fetchone()
        conn.close()
        
        if row:
            vendor = {'id': row[0], 'name': row[1], 'city': row[2] or '', 'state': row[3] or ''}
            enricher.log(f"🔍 Single enrichment: {vendor['name']}")
            yelp_data = enricher.search_yelp(vendor['name'], vendor['city'], vendor['state'])
            if yelp_data:
                enricher.update_vendor(vendor['id'], yelp_data)
                enricher.log(f"✅ Enriched: {yelp_data.get('name')}")
                enricher.save_cache()
                exit(0)
            else:
                enricher.log(f"⚠️ Not found")
                exit(1)
        else:
            enricher.log(f"❌ Vendor {args.single} not found")
            exit(1)
    else:
        # Batch mode
        enricher.run(batch_size=args.batch_size)
