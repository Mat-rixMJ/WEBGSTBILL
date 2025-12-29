"""Tests for invoice service: stock, totals, and tamper detection."""

from decimal import Decimal

import pytest
from fastapi import HTTPException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.database import Base
from app.models.business import BusinessProfile
from app.models.customer import Customer
from app.models.product import Product
from app.models.user import User
from app.schemas.invoice import InvoiceCreate, InvoiceItemCreate, InvoiceTotalsInput
from app.services import invoice_service


@pytest.fixture
def db_session():
    engine = create_engine("sqlite:///:memory:", connect_args={"check_same_thread": False})
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


def _seed_entities(db):
    business = BusinessProfile(
        name="Acme Corp",
        gstin="29ABCDE1234F1Z5",
        state_code="29",
        address="123 MG Road",
        city="Bengaluru",
        pincode="560001",
        invoice_prefix="INV",
        invoice_start_number=1,
        current_invoice_number=1,
    )
    user = User(username="tester", email="t@example.com", hashed_password="x")
    product = Product(
        name="Widget",
        hsn_code="1234",
        gst_rate=Decimal("18"),
        price_paise=10000,
        stock_quantity=10,
        unit="PCS",
        is_active=True,
    )
    customer = Customer(
        name="Customer A",
        customer_type="B2C",
        gstin=None,
        address="Somewhere",
        state="Karnataka",
        state_code="29",
        phone=None,
        email=None,
        is_active=True,
    )
    db.add_all([business, user, product, customer])
    db.commit()
    return business, user, product, customer


def test_invoice_creation_reduces_stock_and_sets_totals(db_session):
    business, user, product, customer = _seed_entities(db_session)
    invoice_data = InvoiceCreate(
        customer_id=customer.id,
        items=[InvoiceItemCreate(product_id=product.id, quantity=2)],
        client_totals=InvoiceTotalsInput(total_taxable_value=Decimal("200.00"), total_gst=Decimal("36.00"), grand_total=Decimal("236.00")),
    )

    invoice = invoice_service.create_invoice(db_session, invoice_data, user, business)

    db_session.refresh(product)
    assert product.stock_quantity == 8  # reduced by 2

    assert invoice.total_taxable_value_paise == 20000
    assert invoice.total_gst_paise == 3600
    assert invoice.grand_total_paise == 23600
    assert invoice.status == "FINAL"

    # Cancel should restore stock
    cancelled = invoice_service.cancel_invoice(db_session, invoice.id, reason="Customer request")
    db_session.refresh(product)
    assert product.stock_quantity == 10
    assert cancelled.status == "CANCELLED"


def test_client_totals_mismatch_rejected(db_session):
    business, user, product, customer = _seed_entities(db_session)
    bad_totals = InvoiceTotalsInput(total_taxable_value=Decimal("1000.00"), total_gst=Decimal("10.00"), grand_total=Decimal("1010.00"))
    invoice_data = InvoiceCreate(
        customer_id=customer.id,
        items=[InvoiceItemCreate(product_id=product.id, quantity=1)],
        client_totals=bad_totals,
    )

    with pytest.raises(HTTPException) as excinfo:
        invoice_service.create_invoice(db_session, invoice_data, user, business)

    assert excinfo.value.status_code == 400
    assert "totals" in excinfo.value.detail.lower()


def test_place_of_supply_must_match_customer_state(db_session):
    business, user, product, customer = _seed_entities(db_session)
    invoice_data = InvoiceCreate(
        customer_id=customer.id,
        place_of_supply="Maharashtra",
        items=[InvoiceItemCreate(product_id=product.id, quantity=1)],
    )

    with pytest.raises(HTTPException) as excinfo:
        invoice_service.create_invoice(db_session, invoice_data, user, business)

    assert excinfo.value.status_code == 400
    assert "place of supply" in excinfo.value.detail.lower()


def test_cancel_twice_is_rejected(db_session):
    business, user, product, customer = _seed_entities(db_session)
    invoice_data = InvoiceCreate(
        customer_id=customer.id,
        items=[InvoiceItemCreate(product_id=product.id, quantity=1)],
    )
    invoice = invoice_service.create_invoice(db_session, invoice_data, user, business)

    invoice_service.cancel_invoice(db_session, invoice.id, reason="test")

    with pytest.raises(HTTPException) as excinfo:
        invoice_service.cancel_invoice(db_session, invoice.id, reason="again")

    assert excinfo.value.status_code == 400
    assert "already cancelled" in excinfo.value.detail.lower()


def test_invoice_immutability_after_product_change(db_session):
    business, user, product, customer = _seed_entities(db_session)
    invoice_data = InvoiceCreate(
        customer_id=customer.id,
        items=[InvoiceItemCreate(product_id=product.id, quantity=1)],
    )
    invoice = invoice_service.create_invoice(db_session, invoice_data, user, business)

    # Change product price after invoice creation
    product.price_paise = 50000
    db_session.commit()
    db_session.refresh(invoice)

    assert invoice.total_taxable_value_paise == 10000
    assert invoice.total_gst_paise == 1800
    assert invoice.grand_total_paise == 11800


def test_invoice_numbers_increment(db_session):
    business, user, product, customer = _seed_entities(db_session)
    inv1 = invoice_service.create_invoice(db_session, InvoiceCreate(customer_id=customer.id, items=[InvoiceItemCreate(product_id=product.id, quantity=1)]), user, business)
    inv2 = invoice_service.create_invoice(db_session, InvoiceCreate(customer_id=customer.id, items=[InvoiceItemCreate(product_id=product.id, quantity=1)]), user, business)
    assert inv1.invoice_number != inv2.invoice_number


def test_rounding_edge_cases(db_session):
    business, user, product, customer = _seed_entities(db_session)
    product.price_paise = 1234  # ₹12.34
    db_session.commit()

    inv = invoice_service.create_invoice(db_session, InvoiceCreate(customer_id=customer.id, items=[InvoiceItemCreate(product_id=product.id, quantity=1)]), user, business)
    # gst 18% of 12.34 = 2.2212 -> round to 2.22 => 222 paise
    assert inv.total_gst_paise in (222, 223)  # allow banker rounding variance
    assert inv.grand_total_paise in (1456, 1457)


def test_pdf_snapshot_uses_stored_values(db_session, monkeypatch):
    business, user, product, customer = _seed_entities(db_session)
    invoice = invoice_service.create_invoice(db_session, InvoiceCreate(customer_id=customer.id, items=[InvoiceItemCreate(product_id=product.id, quantity=1)]), user, business)

    class FakeHTML:
        def __init__(self, string):
            self.string = string
        def write_pdf(self):
            # Ensure rendered HTML contains invoice number snapshot
            assert invoice.invoice_number in self.string
            return b"PDF"

    monkeypatch.setattr(invoice_service, "HTML", FakeHTML)
    pdf_bytes, filename = invoice_service.render_invoice_pdf(db_session, invoice.id)
    assert pdf_bytes == b"PDF"
    assert invoice.invoice_number in filename