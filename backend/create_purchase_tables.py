#!/usr/bin/env python3
"""Create purchase and supplier tables"""

import sqlite3
import sys

def create_tables():
    try:
        conn = sqlite3.connect("./webgst.db")
        cursor = conn.cursor()
        
        # Create suppliers table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS suppliers (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(255) NOT NULL,
                supplier_type VARCHAR(20) NOT NULL DEFAULT 'Registered',
                gstin VARCHAR(15),
                address VARCHAR(500) NOT NULL,
                state VARCHAR(100) NOT NULL,
                state_code VARCHAR(2) NOT NULL,
                phone VARCHAR(15),
                email VARCHAR(255),
                is_active BOOLEAN NOT NULL DEFAULT 1,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                UNIQUE(name)
            )
        """)
        print("✓ suppliers table created")
        
        # Create purchase_invoices table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchase_invoices (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                supplier_id INTEGER NOT NULL,
                supplier_invoice_number VARCHAR(100) NOT NULL,
                supplier_invoice_date DATETIME NOT NULL,
                purchase_date DATETIME NOT NULL,
                place_of_supply VARCHAR(100) NOT NULL,
                place_of_supply_code VARCHAR(2) NOT NULL,
                total_quantity FLOAT NOT NULL DEFAULT 0,
                subtotal_value INTEGER NOT NULL DEFAULT 0,
                cgst_amount INTEGER NOT NULL DEFAULT 0,
                sgst_amount INTEGER NOT NULL DEFAULT 0,
                igst_amount INTEGER NOT NULL DEFAULT 0,
                total_gst INTEGER NOT NULL DEFAULT 0,
                total_amount INTEGER NOT NULL DEFAULT 0,
                status VARCHAR(20) NOT NULL DEFAULT 'Draft',
                cancel_reason TEXT,
                is_active BOOLEAN NOT NULL DEFAULT 1,
                created_at DATETIME NOT NULL,
                updated_at DATETIME NOT NULL,
                finalized_at DATETIME,
                cancelled_at DATETIME,
                FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
            )
        """)
        print("✓ purchase_invoices table created")
        
        # Create purchase_items table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS purchase_items (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                invoice_id INTEGER NOT NULL,
                item_name VARCHAR(255) NOT NULL,
                hsn_code VARCHAR(8) NOT NULL,
                quantity FLOAT NOT NULL,
                unit_rate INTEGER NOT NULL,
                gst_rate INTEGER NOT NULL,
                subtotal INTEGER NOT NULL,
                cgst_amount INTEGER NOT NULL DEFAULT 0,
                sgst_amount INTEGER NOT NULL DEFAULT 0,
                igst_amount INTEGER NOT NULL DEFAULT 0,
                total_amount INTEGER NOT NULL,
                tax_type VARCHAR(10) NOT NULL,
                created_at DATETIME NOT NULL,
                FOREIGN KEY (invoice_id) REFERENCES purchase_invoices(id)
            )
        """)
        print("✓ purchase_items table created")
        
        # Create indexes
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_suppliers_state_code ON suppliers(state_code)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_suppliers_gstin ON suppliers(gstin)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_purchase_invoices_supplier_id ON purchase_invoices(supplier_id)")
        cursor.execute("CREATE INDEX IF NOT EXISTS ix_purchase_items_invoice_id ON purchase_items(invoice_id)")
        print("✓ Indexes created")
        
        conn.commit()
        print("\n✅ All purchase tables created successfully!")
        conn.close()
        return True
        
    except sqlite3.Error as e:
        print(f"❌ Database error: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"❌ Error: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    success = create_tables()
    sys.exit(0 if success else 1)
