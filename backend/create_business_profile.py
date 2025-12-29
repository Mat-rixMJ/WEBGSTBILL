"""Quick script to create business profile"""
import sys
sys.path.insert(0, '.')

from app.database import SessionLocal
from app.models.business import BusinessProfile

db = SessionLocal()

# Check if business profile already exists
existing = db.query(BusinessProfile).first()
if existing:
    print(f"✓ Business profile already exists: {existing.name}")
    print(f"  GSTIN: {existing.gstin}")
    print(f"  State Code: {existing.state_code}")
    print(f"  City: {existing.city}")
else:
    # Create new business profile
    business = BusinessProfile(
        name="WebGST Demo Business Pvt Ltd",
        gstin="29ABCDE1234F1Z5",
        state_code="29",
        address="123 Business Street, Jayanagar",
        city="Bangalore",
        pincode="560041",
        phone="+91 9876543210",
        email="contact@webgst.com",
        invoice_prefix="INV",
        invoice_start_number=1
    )
    db.add(business)
    db.commit()
    db.refresh(business)
    print(f"✓ Business profile created successfully!")
    print(f"  Name: {business.name}")
    print(f"  GSTIN: {business.gstin}")
    print(f"  State Code: {business.state_code}")
    print(f"  City: {business.city}")
    print(f"  Invoice Prefix: {business.invoice_prefix}")

db.close()
