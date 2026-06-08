#!/usr/bin/env python3
"""
DepotChaos Enrichment Claim System
Agents claim records to enrich
"""

import sqlite3
import sys
from datetime import datetime

QUEUE_DB = '/root/.openclaw/workspace/DepotChaos/enrichment_queue/queue.db'

def claim_records(agent_id: str, count: int = 10):
    """Claim records for enrichment."""
    conn = sqlite3.connect(QUEUE_DB)
    cursor = conn.cursor()
    
    # Get available records
    cursor.execute("""
        SELECT id, record_name, record_city, record_state, missing_fields
        FROM enrichment_queue
        WHERE status = 'available'
        ORDER BY priority DESC, id ASC
        LIMIT ?
    """, (count,))
    
    records = cursor.fetchall()
    
    if not records:
        print(f"No available records for {agent_id}")
        conn.close()
        return
    
    # Claim them
    for record in records:
        qid, name, city, state, missing = record
        cursor.execute("""
            UPDATE enrichment_queue
            SET status = 'claimed', claimed_by = ?, claimed_at = ?
            WHERE id = ?
        """, (agent_id, datetime.now().isoformat(), qid))
        
        print(f"Claimed: {name} ({city}, {state}) - Missing: {missing}")
    
    conn.commit()
    conn.close()
    print(f"\n{agent_id} claimed {len(records)} records")

def complete_record(queue_id: int, agent_id: str, data: dict):
    """Mark record as completed with enriched data."""
    conn = sqlite3.connect(QUEUE_DB)
    cursor = conn.cursor()
    
    cursor.execute("""
        UPDATE enrichment_queue
        SET status = 'completed', completed_at = ?, enriched_data = ?
        WHERE id = ? AND claimed_by = ?
    """, (datetime.now().isoformat(), json.dumps(data), queue_id, agent_id))
    
    conn.commit()
    conn.close()
    print(f"Record {queue_id} completed by {agent_id}")

def show_stats():
    """Show queue statistics."""
    conn = sqlite3.connect(QUEUE_DB)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM enrichment_queue WHERE status = 'available'")
    available = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM enrichment_queue WHERE status = 'claimed'")
    claimed = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM enrichment_queue WHERE status = 'completed'")
    completed = cursor.fetchone()[0]
    
    cursor.execute("SELECT claimed_by, COUNT(*) FROM enrichment_queue WHERE status = 'claimed' GROUP BY claimed_by")
    claimed_by = cursor.fetchall()
    
    conn.close()
    
    print("DepotChaos Enrichment Queue Stats")
    print("=" * 40)
    print(f"Available: {available}")
    print(f"Claimed: {claimed}")
    print(f"Completed: {completed}")
    print("\nClaimed by:")
    for agent, count in claimed_by:
        print(f"  {agent}: {count}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python3 claim_system.py claim <agent_id> [count]")
        print("  python3 claim_system.py complete <queue_id> <agent_id>")
        print("  python3 claim_system.py stats")
        sys.exit(1)
    
    cmd = sys.argv[1]
    
    if cmd == 'claim':
        agent = sys.argv[2]
        count = int(sys.argv[3]) if len(sys.argv) > 3 else 10
        claim_records(agent, count)
    elif cmd == 'stats':
        show_stats()
