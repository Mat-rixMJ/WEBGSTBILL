"""Create sample invoices for testing"""
import sys
sys.path.insert(0, '.')

from datetime import date, timedelta
from app.database import SessionLocal
from app.models.business import BusinessProfile
from app.models.customer import Customer
from app.models.product import Product
from app.models.user import User
from app.schemas.invoice import InvoiceCreate, InvoiceItemCreate, InvoiceTotalsInput
from app.services import invoice_service
from decimal import Decimal

db = SessionLocal()

# Get business profile
business = db.query(BusinessProfile).first()
if not business:
    print("❌ No business profile found. Please create one first.")
    db.close()
    sys.exit(1)

print(f"✓ Business: {business.name} (State: {business.state_code})")

# Get or use first user
user = db.query(User).first()
if not user:
    print("❌ No user found. Please create a user first.")
    db.close()
    sys.exit(1)

print(f"✓ User: {user.username}")

# Get customers
customers = db.query(Customer).filter(Customer.is_active == True).limit(5).all()
if not customers:
    print("❌ No customers found. Please create some customers first.")
    db.close()
    sys.exit(1)

print(f"✓ Found {len(customers)} customers")

# Get products
products = db.query(Product).filter(Product.is_active == True).limit(10).all()
if not products:
    print("❌ No products found. Please create some products first.")
    db.close()
    sys.exit(1)

print(f"✓ Found {len(products)} products\n")

# Create sample invoices
sample_invoices = []
base_date = date.today() - timedelta(days=30)

# Invoice 1: Intra-state B2B (same state as business)
same_state_customer = next((c for c in customers if c.state_code == business.state_code and c.gstin), None)
if same_state_customer and len(products) >= 2:
    print(f"Creating Invoice 1: Intra-state B2B with {same_state_customer.name}...")
    
    invoice1_data = InvoiceCreate(
        customer_id=same_state_customer.id,
        invoice_date=base_date + timedelta(days=1),
        place_of_supply=same_state_customer.state_code,  # Use state_code
        items=[
            InvoiceItemCreate(
                product_id=products[0].id,
                quantity=5,
                description=products[0].description
            ),
            InvoiceItemCreate(
                product_id=products[1].id,
                quantity=3,
                description=products[1].description
            )
        ]
    )
    
    try:
        invoice1 = invoice_service.create_invoice(db, invoice1_data, user, business)
        sample_invoices.append(invoice1)
        print(f"  ✓ Created {invoice1.invoice_number}")
    except Exception as e:
        print(f"  ❌ Failed: {e}")

# Invoice 2: Inter-state B2B (different state)
diff_state_customer = next((c for c in customers if c.state_code != business.state_code and c.gstin), None)
if diff_state_customer and len(products) >= 1:
    print(f"Creating Invoice 2: Inter-state B2B with {diff_state_customer.name}...")
    
    invoice2_data = InvoiceCreate(
        customer_id=diff_state_customer.id,
        invoice_date=base_date + timedelta(days=5),
        place_of_supply=diff_state_customer.state_code,
        items=[
            InvoiceItemCreate(
                product_id=products[0].id,
                quantity=2,
                description=products[0].description
            )
        ]
    )
    
    try:
        invoice2 = invoice_service.create_invoice(db, invoice2_data, user, business)
        sample_invoices.append(invoice2)
        print(f"  ✓ Created {invoice2.invoice_number}")
    except Exception as e:
        print(f"  ❌ Failed: {e}")

# Invoice 3: B2C (same state, no GSTIN)
b2c_customer = next((c for c in customers if not c.gstin and c.state_code == business.state_code), None)
if b2c_customer and len(products) >= 1:
    print(f"Creating Invoice 3: Intra-state B2C with {b2c_customer.name}...")
    
    invoice3_data = InvoiceCreate(
        customer_id=b2c_customer.id,
        invoice_date=base_date + timedelta(days=10),
        place_of_supply=b2c_customer.state_code,
        items=[
            InvoiceItemCreate(
                product_id=products[1].id,
                quantity=5,
                description=products[1].description
            )
        ]
    )
    
    try:
        invoice3 = invoice_service.create_invoice(db, invoice3_data, user, business)
        sample_invoices.append(invoice3)
        print(f"  ✓ Created {invoice3.invoice_number}")
    except Exception as e:
        print(f"  ❌ Failed: {e}")

# Commit all changes
if sample_invoices:
    print(f"\n✓ Created {len(sample_invoices)} sample invoices:")
    for inv in sample_invoices:
        print(f"  - {inv.invoice_number}: {inv.customer_snapshot['name']} - ₹{inv.grand_total:.2f} ({inv.status})")
else:
    print("\n⚠ No sample invoices created. Check if you have customers in different states and products with stock.")

db.close()
