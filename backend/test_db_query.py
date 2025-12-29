#!/usr/bin/env python3
"""Test direct database query to verify schema"""

import sqlite3

def test_db():
    try:
        conn = sqlite3.connect("./webgst.db")
        cursor = conn.cursor()
        
        # Try the exact query that's failing
        cursor.execute("""
            SELECT customers.id, customers.name, customers.customer_type, 
                   customers.gstin, customers.address, customers.state, 
                   customers.state_code, customers.phone, customers.email, 
                   customers.is_active, customers.created_at, customers.updated_at
            FROM customers
            WHERE customers.is_active = 1
            LIMIT 1000 OFFSET 0
        """)
        
        rows = cursor.fetchall()
        print(f"✅ Query successful! Found {len(rows)} active customers")
        
        if rows:
            print(f"Sample customer: {rows[0]}")
        
        conn.close()
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    test_db()
