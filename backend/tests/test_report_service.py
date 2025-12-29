"""
Comprehensive tests for Report Module

Tests cover:
- Data consistency (totals = sum of rows)
- GST accuracy (CGST/SGST vs IGST)
- Cancelled invoice handling
- Date range filtering
- Edge cases (no data, very large values)
"""

import pytest
from datetime import date, datetime
from decimal import Decimal
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.user import User
from app.models.business import BusinessProfile
from app.models.customer import Customer
from app.models.product import Product
from app.models.invoice import Invoice, InvoiceItem
from app.models.supplier import Supplier
from app.models.purchase import PurchaseInvoice, PurchaseItem
from app.services import report_service
from app.services.gst_calculator import calculate_line_item_tax


# In-memory SQLite for testing
@pytest.fixture(scope="function")
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(bind=engine)
    TestingSessionLocal = sessionmaker(bind=engine)
    session = TestingSessionLocal()
    yield session
    session.close()


@pytest.fixture
def seed_master_data(db_session):
    """Seed users, business, customers, products, suppliers"""
    # User
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password="hashed",
        is_active=True
    )
    db_session.add(user)
    db_session.flush()
    
    # Business (Karnataka state code = 29)
    business = BusinessProfile(
        name="Test Business Pvt Ltd",
        gstin="29ABCDE1234F1Z5",
        state_code="29",
        address="Test Address",
        city="Bangalore",
        pincode="560001",
        phone="9876543210",
        email="business@test.com",
        invoice_prefix="INV",
        invoice_start_number=1,
        current_invoice_number=1
    )
    db_session.add(business)
    
    # Customer 1: Same state (Karnataka)
    customer1 = Customer(
        name="ABC Traders",
        customer_type="B2B",
        gstin="29XYZAB1234C1Z2",
        state_code="29",
        state="Karnataka",
        address="Customer Address, Bangalore, 560002",
        phone="9876543211",
        email="abc@test.com",
        is_active=True
    )
    db_session.add(customer1)
    
    # Customer 2: Different state (Tamil Nadu = 33)
    customer2 = Customer(
        name="XYZ Enterprises",
        customer_type="B2B",
        gstin="33PQRST5678D2Z3",
        state_code="33",
        state="Tamil Nadu",
        address="Customer Address 2, Chennai, 600001",
        phone="9876543212",
        email="xyz@test.com",
        is_active=True
    )
    db_session.add(customer2)
    
    # Customer 3: Same state, B2C (no GSTIN)
    customer3 = Customer(
        name="John Doe",
        customer_type="B2C",
        state_code="29",
        state="Karnataka",
        address="Customer Address 3, Bangalore, 560003",
        phone="9876543213",
        email="john@test.com",
        is_active=True
    )
    db_session.add(customer3)
    
    # Product 1: 18% GST
    product1 = Product(
        name="Laptop",
        hsn_code="8471",
        gst_rate=18.0,
        price_paise=5000000,  # ₹50,000
        stock_quantity=10,
        is_active=True
    )
    db_session.add(product1)
    
    # Product 2: 5% GST
    product2 = Product(
        name="Book",
        hsn_code="4901",
        gst_rate=5.0,
        price_paise=50000,  # ₹500
        stock_quantity=100,
        is_active=True
    )
    db_session.add(product2)
    
    # Supplier 1: Same state
    supplier1 = Supplier(
        name="Supplier A Pvt Ltd",
        supplier_type="REGISTERED",
        gstin="29LMNOP1234E1Z6",
        state_code="29",
        state="Karnataka",
        address="Supplier Address, Bangalore, 560010",
        phone="9876543220",
        email="suppliera@test.com",
        is_active=True
    )
    db_session.add(supplier1)
    
    # Supplier 2: Different state
    supplier2 = Supplier(
        name="Supplier B Pvt Ltd",
        supplier_type="REGISTERED",
        gstin="27UVWXY5678F2Z7",
        state_code="27",
        state="Maharashtra",
        address="Supplier Address 2, Mumbai, 400001",
        phone="9876543221",
        email="supplierb@test.com",
        is_active=True
    )
    db_session.add(supplier2)
    
    db_session.commit()
    
    return {
        "user": user,
        "business": business,
        "customer1": customer1,  # Same state
        "customer2": customer2,  # Different state
        "customer3": customer3,  # B2C same state
        "product1": product1,  # 18% GST
        "product2": product2,  # 5% GST
        "supplier1": supplier1,  # Same state
        "supplier2": supplier2   # Different state
    }


def create_invoice_with_items(db_session, entities, customer, invoice_date, items_data, status="FINAL"):
    """Helper to create invoice with items"""
    business = entities["business"]
    user = entities["user"]
    
    # Calculate totals
    total_taxable = 0
    total_gst = 0
    
    for item_data in items_data:
        product = item_data["product"]
        qty = item_data["quantity"]
        
        tax_calc = calculate_line_item_tax(
            unit_price_paise=product.price_paise,
            gst_rate=product.gst_rate,
            quantity=qty
        )
        
        total_taxable += tax_calc["taxable_value_paise"]
        total_gst += tax_calc["gst_amount_paise"]
    
    grand_total = total_taxable + total_gst
    
    # Create invoice
    invoice = Invoice(
        invoice_number=f"INV{str(business.current_invoice_number).zfill(6)}",
        invoice_date=invoice_date,
        place_of_supply=customer.state_code,
        invoice_type="TAX_INVOICE",
        status=status,
        customer_id=customer.id,
        customer_snapshot={
            "name": customer.name,
            "gstin": customer.gstin,
            "state_code": customer.state_code,
            "address": customer.address
        },
        total_taxable_value_paise=total_taxable,
        total_gst_paise=total_gst,
        grand_total_paise=grand_total,
        round_off_paise=0,
        finalized_at=datetime.now(),
        created_by=user.id
    )
    db_session.add(invoice)
    db_session.flush()
    
    # Add items
    for item_data in items_data:
        product = item_data["product"]
        qty = item_data["quantity"]
        
        tax_calc = calculate_line_item_tax(
            unit_price_paise=product.price_paise,
            gst_rate=product.gst_rate,
            quantity=qty
        )
        
        item = InvoiceItem(
            invoice_id=invoice.id,
            product_id=product.id,
            product_snapshot={
                "name": product.name,
                "hsn_code": product.hsn_code,
                "gst_rate": product.gst_rate
            },
            quantity=qty,
            unit_price_paise=product.price_paise,
            taxable_value_paise=tax_calc["taxable_value_paise"],
            gst_rate=product.gst_rate,
            gst_amount_paise=tax_calc["gst_amount_paise"],
            line_total_paise=tax_calc["line_total_paise"],
            description=None
        )
        db_session.add(item)
    
    business.current_invoice_number += 1
    db_session.commit()
    
    return invoice


def create_purchase_with_items(db_session, entities, supplier, invoice_date, items_data, status="FINAL"):
    """Helper to create purchase invoice with items"""
    user = entities["user"]
    
    # Calculate totals
    total_taxable = 0
    total_gst = 0
    
    for item_data in items_data:
        unit_price = item_data["unit_price_paise"]
        gst_rate = item_data["gst_rate"]
        qty = item_data["quantity"]
        
        tax_calc = calculate_line_item_tax(
            unit_price_paise=unit_price,
            gst_rate=gst_rate,
            quantity=qty
        )
        
        total_taxable += tax_calc["taxable_value_paise"]
        total_gst += tax_calc["gst_amount_paise"]
    
    grand_total = total_taxable + total_gst
    
    # Create purchase invoice
    purchase = PurchaseInvoice(
        supplier_invoice_number=f"SUPP-{invoice_date.strftime('%Y%m%d')}-001",
        invoice_date=invoice_date,
        place_of_supply=supplier.state_code,
        status=status,
        supplier_id=supplier.id,
        supplier_snapshot={
            "name": supplier.name,
            "gstin": supplier.gstin,
            "state_code": supplier.state_code,
            "address": supplier.address
        },
        total_taxable_value_paise=total_taxable,
        total_gst_paise=total_gst,
        grand_total_paise=grand_total,
        round_off_paise=0,
        finalized_at=datetime.now(),
        created_by=user.id
    )
    db_session.add(purchase)
    db_session.flush()
    
    # Add items
    for item_data in items_data:
        tax_calc = calculate_line_item_tax(
            unit_price_paise=item_data["unit_price_paise"],
            gst_rate=item_data["gst_rate"],
            quantity=item_data["quantity"]
        )
        
        item = PurchaseItem(
            purchase_invoice_id=purchase.id,
            item_name=item_data["name"],
            hsn_code=item_data["hsn_code"],
            quantity=item_data["quantity"],
            unit_price_paise=item_data["unit_price_paise"],
            taxable_value_paise=tax_calc["taxable_value_paise"],
            gst_rate=item_data["gst_rate"],
            gst_amount_paise=tax_calc["gst_amount_paise"],
            line_total_paise=tax_calc["line_total_paise"],
            description=None
        )
        db_session.add(item)
    
    db_session.commit()
    
    return purchase


# ═══════════════════════════════════════════════════════════
# TEST 1: Data Consistency - Sales Register
# ═══════════════════════════════════════════════════════════
def test_sales_register_totals_match_rows(db_session, seed_master_data):
    """Report totals must equal sum of individual rows"""
    entities = seed_master_data
    
    # Create 3 invoices
    create_invoice_with_items(
        db_session, entities,
        customer=entities["customer1"],
        invoice_date=date(2025, 12, 1),
        items_data=[{"product": entities["product1"], "quantity": 2}]  # 2 laptops
    )
    
    create_invoice_with_items(
        db_session, entities,
        customer=entities["customer2"],
        invoice_date=date(2025, 12, 5),
        items_data=[{"product": entities["product2"], "quantity": 10}]  # 10 books
    )
    
    create_invoice_with_items(
        db_session, entities,
        customer=entities["customer3"],
        invoice_date=date(2025, 12, 10),
        items_data=[{"product": entities["product1"], "quantity": 1}]  # 1 laptop
    )
    
    # Generate report
    report = report_service.generate_sales_register(
        db=db_session,
        from_date=date(2025, 12, 1),
        to_date=date(2025, 12, 31)
    )
    
    # Verify: Summary totals = sum of rows
    sum_taxable = sum(row.taxable_value for row in report.rows)
    sum_cgst = sum(row.cgst for row in report.rows)
    sum_sgst = sum(row.sgst for row in report.rows)
    sum_igst = sum(row.igst for row in report.rows)
    sum_gst = sum(row.total_gst for row in report.rows)
    sum_grand = sum(row.grand_total for row in report.rows)
    
    assert abs(report.summary.total_taxable_value - sum_taxable) < 0.01
    assert abs(report.summary.total_cgst - sum_cgst) < 0.01
    assert abs(report.summary.total_sgst - sum_sgst) < 0.01
    assert abs(report.summary.total_igst - sum_igst) < 0.01
    assert abs(report.summary.total_gst - sum_gst) < 0.01
    assert abs(report.summary.total_grand_total - sum_grand) < 0.01
    
    assert report.summary.count_invoices == 3
    assert report.summary.count_cancelled == 0


# ═══════════════════════════════════════════════════════════
# TEST 2: GST Accuracy - CGST/SGST vs IGST
# ═══════════════════════════════════════════════════════════
def test_sales_register_cgst_sgst_vs_igst(db_session, seed_master_data):
    """Intra-state invoices must have CGST+SGST; inter-state must have IGST"""
    entities = seed_master_data
    
    # Intra-state invoice (customer1 is same state as business)
    create_invoice_with_items(
        db_session, entities,
        customer=entities["customer1"],
        invoice_date=date(2025, 12, 1),
        items_data=[{"product": entities["product1"], "quantity": 1}]  # 1 laptop @ 18%
    )
    
    # Inter-state invoice (customer2 is different state)
    create_invoice_with_items(
        db_session, entities,
        customer=entities["customer2"],
        invoice_date=date(2025, 12, 2),
        items_data=[{"product": entities["product1"], "quantity": 1}]  # 1 laptop @ 18%
    )
    
    # Generate report
    report = report_service.generate_sales_register(
        db=db_session,
        from_date=date(2025, 12, 1),
        to_date=date(2025, 12, 31)
    )
    
    # Row 1: Intra-state (CGST + SGST, no IGST)
    row1 = report.rows[0]
    assert row1.cgst > 0
    assert row1.sgst > 0
    assert row1.igst == 0
    assert abs(row1.cgst - row1.sgst) < 0.01  # CGST = SGST
    assert abs(row1.total_gst - (row1.cgst + row1.sgst)) < 0.01
    
    # Row 2: Inter-state (IGST only, no CGST/SGST)
    row2 = report.rows[1]
    assert row2.cgst == 0
    assert row2.sgst == 0
    assert row2.igst > 0
    assert abs(row2.total_gst - row2.igst) < 0.01
    
    # Verify both have same total GST amount (same item, same price)
    assert abs(row1.total_gst - row2.total_gst) < 0.01


# ═══════════════════════════════════════════════════════════
# TEST 3: Cancelled Invoices Handling
# ═══════════════════════════════════════════════════════════
def test_sales_register_cancelled_invoices_excluded(db_session, seed_master_data):
    """Cancelled invoices appear in list but NOT in totals"""
    entities = seed_master_data
    
    # Active invoice
    create_invoice_with_items(
        db_session, entities,
        customer=entities["customer1"],
        invoice_date=date(2025, 12, 1),
        items_data=[{"product": entities["product1"], "quantity": 1}],
        status="FINAL"
    )
    
    # Cancelled invoice
    create_invoice_with_items(
        db_session, entities,
        customer=entities["customer2"],
        invoice_date=date(2025, 12, 2),
        items_data=[{"product": entities["product1"], "quantity": 1}],
        status="CANCELLED"
    )
    
    # Generate report (exclude cancelled from totals)
    report = report_service.generate_sales_register(
        db=db_session,
        from_date=date(2025, 12, 1),
        to_date=date(2025, 12, 31),
        include_cancelled=False
    )
    
    # Both invoices appear in list
    assert len(report.rows) == 2
    assert report.rows[0].status == "FINAL"
    assert report.rows[1].status == "CANCELLED"
    
    # Totals should only include FINAL invoice
    assert abs(report.summary.total_grand_total - report.rows[0].grand_total) < 0.01
    assert report.summary.count_invoices == 2
    assert report.summary.count_cancelled == 1
    
    # Test with include_cancelled=True
    report2 = report_service.generate_sales_register(
        db=db_session,
        from_date=date(2025, 12, 1),
        to_date=date(2025, 12, 31),
        include_cancelled=True
    )
    
    # Now totals should include both
    assert abs(report2.summary.total_grand_total - (report2.rows[0].grand_total + report2.rows[1].grand_total)) < 0.01


# ═══════════════════════════════════════════════════════════
# TEST 4: Date Range Filtering
# ═══════════════════════════════════════════════════════════
def test_sales_register_date_filtering(db_session, seed_master_data):
    """Only invoices within date range should appear"""
    entities = seed_master_data
    
    # Create invoices on different dates
    create_invoice_with_items(
        db_session, entities,
        customer=entities["customer1"],
        invoice_date=date(2025, 11, 15),  # November
        items_data=[{"product": entities["product1"], "quantity": 1}]
    )
    
    create_invoice_with_items(
        db_session, entities,
        customer=entities["customer2"],
        invoice_date=date(2025, 12, 10),  # December
        items_data=[{"product": entities["product1"], "quantity": 1}]
    )
    
    create_invoice_with_items(
        db_session, entities,
        customer=entities["customer3"],
        invoice_date=date(2026, 1, 5),  # January next year
        items_data=[{"product": entities["product1"], "quantity": 1}]
    )
    
    # Query December only
    report = report_service.generate_sales_register(
        db=db_session,
        from_date=date(2025, 12, 1),
        to_date=date(2025, 12, 31)
    )
    
    # Only December invoice should appear
    assert len(report.rows) == 1
    assert report.rows[0].invoice_date == date(2025, 12, 10)


# ═══════════════════════════════════════════════════════════
# TEST 5: Edge Case - No Invoices
# ═══════════════════════════════════════════════════════════
def test_sales_register_no_invoices(db_session, seed_master_data):
    """Report with no invoices should return empty with zero totals"""
    report = report_service.generate_sales_register(
        db=db_session,
        from_date=date(2025, 12, 1),
        to_date=date(2025, 12, 31)
    )
    
    assert len(report.rows) == 0
    assert report.summary.total_taxable_value == 0
    assert report.summary.total_gst == 0
    assert report.summary.total_grand_total == 0
    assert report.summary.count_invoices == 0
    assert report.summary.count_cancelled == 0


# ═══════════════════════════════════════════════════════════
# TEST 6: Purchase Register - Basic Functionality
# ═══════════════════════════════════════════════════════════
def test_purchase_register_basic(db_session, seed_master_data):
    """Purchase register should work similar to sales register"""
    entities = seed_master_data
    
    # Create purchases
    create_purchase_with_items(
        db_session, entities,
        supplier=entities["supplier1"],  # Same state
        invoice_date=date(2025, 12, 1),
        items_data=[{
            "name": "Raw Material A",
            "hsn_code": "1234",
            "quantity": 10,
            "unit_price_paise": 100000,  # ₹1000
            "gst_rate": 18.0
        }]
    )
    
    create_purchase_with_items(
        db_session, entities,
        supplier=entities["supplier2"],  # Different state
        invoice_date=date(2025, 12, 5),
        items_data=[{
            "name": "Raw Material B",
            "hsn_code": "5678",
            "quantity": 5,
            "unit_price_paise": 200000,  # ₹2000
            "gst_rate": 12.0
        }]
    )
    
    # Generate report
    report = report_service.generate_purchase_register(
        db=db_session,
        from_date=date(2025, 12, 1),
        to_date=date(2025, 12, 31)
    )
    
    assert len(report.rows) == 2
    assert report.summary.count_purchases == 2
    
    # Row 1: Same state (CGST + SGST)
    row1 = report.rows[0]
    assert row1.input_cgst > 0
    assert row1.input_sgst > 0
    assert row1.input_igst == 0
    
    # Row 2: Different state (IGST)
    row2 = report.rows[1]
    assert row2.input_cgst == 0
    assert row2.input_sgst == 0
    assert row2.input_igst > 0


# ═══════════════════════════════════════════════════════════
# TEST 7: GST Summary - Monthly Aggregation
# ═══════════════════════════════════════════════════════════
def test_gst_summary_monthly(db_session, seed_master_data):
    """GST summary should aggregate sales and purchases for a month"""
    entities = seed_master_data
    
    # Create sales invoices
    create_invoice_with_items(
        db_session, entities,
        customer=entities["customer1"],  # Same state
        invoice_date=date(2025, 12, 10),
        items_data=[{"product": entities["product1"], "quantity": 1}]
    )
    
    create_invoice_with_items(
        db_session, entities,
        customer=entities["customer2"],  # Different state
        invoice_date=date(2025, 12, 15),
        items_data=[{"product": entities["product1"], "quantity": 1}]
    )
    
    # Create purchase invoices
    create_purchase_with_items(
        db_session, entities,
        supplier=entities["supplier1"],  # Same state
        invoice_date=date(2025, 12, 20),
        items_data=[{
            "name": "Raw Material",
            "hsn_code": "1234",
            "quantity": 5,
            "unit_price_paise": 100000,
            "gst_rate": 18.0
        }]
    )
    
    # Generate GST summary
    summary = report_service.generate_gst_summary(
        db=db_session,
        month=12,
        year=2025
    )
    
    assert summary.month == 12
    assert summary.year == 2025
    assert summary.sales_count == 2
    assert summary.purchase_count == 1
    
    # Output GST should have both CGST/SGST and IGST
    assert summary.output_gst.cgst > 0  # From customer1
    assert summary.output_gst.sgst > 0
    assert summary.output_gst.igst > 0  # From customer2
    assert abs(summary.output_gst.total - (summary.output_gst.cgst + summary.output_gst.sgst + summary.output_gst.igst)) < 0.01
    
    # Input GST should have CGST/SGST only (supplier1 same state)
    assert summary.input_gst.cgst > 0
    assert summary.input_gst.sgst > 0
    assert summary.input_gst.igst == 0
    assert abs(summary.input_gst.total - (summary.input_gst.cgst + summary.input_gst.sgst)) < 0.01


# ═══════════════════════════════════════════════════════════
# TEST 8: Edge Case - Very Large Invoice Values
# ═══════════════════════════════════════════════════════════
def test_sales_register_large_values(db_session, seed_master_data):
    """Report should handle very large invoice amounts correctly"""
    entities = seed_master_data
    
    # Create product with very high price
    expensive_product = Product(
        name="Industrial Machinery",
        hsn_code="8479",
        gst_rate=18.0,
        price_paise=10000000000,  # ₹1,00,00,000 (1 crore)
        stock_quantity=5,
        is_active=True
    )
    db_session.add(expensive_product)
    db_session.commit()
    
    # Create invoice
    create_invoice_with_items(
        db_session, entities,
        customer=entities["customer1"],
        invoice_date=date(2025, 12, 1),
        items_data=[{"product": expensive_product, "quantity": 2}]  # 2 crore order
    )
    
    # Generate report
    report = report_service.generate_sales_register(
        db=db_session,
        from_date=date(2025, 12, 1),
        to_date=date(2025, 12, 31)
    )
    
    assert len(report.rows) == 1
    # Verify no overflow or precision issues
    assert report.rows[0].grand_total > 2000000  # Should be > 2 crore
    assert report.summary.total_grand_total == report.rows[0].grand_total


# ═══════════════════════════════════════════════════════════
# TEST 9: Customer/Supplier Filtering
# ═══════════════════════════════════════════════════════════
def test_sales_register_customer_filter(db_session, seed_master_data):
    """Should filter by customer ID when provided"""
    entities = seed_master_data
    
    # Create invoices for different customers
    create_invoice_with_items(
        db_session, entities,
        customer=entities["customer1"],
        invoice_date=date(2025, 12, 1),
        items_data=[{"product": entities["product1"], "quantity": 1}]
    )
    
    create_invoice_with_items(
        db_session, entities,
        customer=entities["customer2"],
        invoice_date=date(2025, 12, 2),
        items_data=[{"product": entities["product1"], "quantity": 1}]
    )
    
    # Filter by customer1 only
    report = report_service.generate_sales_register(
        db=db_session,
        from_date=date(2025, 12, 1),
        to_date=date(2025, 12, 31),
        customer_id=entities["customer1"].id
    )
    
    assert len(report.rows) == 1
    assert report.rows[0].customer_name == entities["customer1"].name


# ═══════════════════════════════════════════════════════════
# TEST 10: Mixed GST Rates
# ═══════════════════════════════════════════════════════════
def test_sales_register_mixed_gst_rates(db_session, seed_master_data):
    """Invoice with items at different GST rates"""
    entities = seed_master_data
    
    # Invoice with both 18% and 5% GST items
    create_invoice_with_items(
        db_session, entities,
        customer=entities["customer1"],
        invoice_date=date(2025, 12, 1),
        items_data=[
            {"product": entities["product1"], "quantity": 1},  # 18%
            {"product": entities["product2"], "quantity": 5}   # 5%
        ]
    )
    
    # Generate report
    report = report_service.generate_sales_register(
        db=db_session,
        from_date=date(2025, 12, 1),
        to_date=date(2025, 12, 31)
    )
    
    assert len(report.rows) == 1
    # Total GST should be sum of GST from both items
    row = report.rows[0]
    assert row.total_gst > 0
    # Verify CGST = SGST (intra-state)
    assert abs(row.cgst - row.sgst) < 0.01
    assert abs(row.total_gst - (row.cgst + row.sgst)) < 0.01
