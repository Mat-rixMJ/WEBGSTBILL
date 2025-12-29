#!/usr/bin/env python3
"""Direct migration script to add customer B2B/B2C columns"""

import sqlite3
import sys

def migrate():
    try:
        conn = sqlite3.connect("./webgst.db")
        cursor = conn.cursor()
        
        # Check if customer_type column already exists
        cursor.execute("PRAGMA table_info(customers)")
        columns = {row[1] for row in cursor.fetchall()}
        
        if 'customer_type' in columns and 'state_code' in columns:
            print("✓ Columns already exist. No migration needed.")
            conn.close()
            return True
        
        # Add missing columns if needed
        if 'customer_type' not in columns:
            print("Adding customer_type column...")
            cursor.execute("ALTER TABLE customers ADD COLUMN customer_type VARCHAR(3) DEFAULT 'B2C' NOT NULL")
            print("✓ customer_type column added")
        
        if 'state_code' not in columns:
            print("Adding state_code column...")
            cursor.execute("ALTER TABLE customers ADD COLUMN state_code VARCHAR(2) DEFAULT '' NOT NULL")
            print("✓ state_code column added")
        
        conn.commit()
        print("\n✅ Migration completed successfully!")
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    success = migrate()
    sys.exit(0 if success else 1)
