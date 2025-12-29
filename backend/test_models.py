#!/usr/bin/env python3
"""Test if SQLAlchemy models are properly configured"""

import sys
sys.path.insert(0, '.')

from app.database import Base, SessionLocal
from app.models import customer, user, product, business, invoice

def test_models():
    try:
        # Test database connection
        db = SessionLocal()
        
        # Try to query customers
        customers = db.query(customer.Customer).filter(customer.Customer.is_active == True).limit(10).all()
        print(f"✅ Successfully queried {len(customers)} customers from SQLAlchemy")
        
        for c in customers:
            print(f"  - {c.name} ({c.customer_type}): {c.state_code}")
        
        db.close()
        return True
        
    except Exception as e:
        import traceback
        print(f"❌ Error: {e}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_models()
