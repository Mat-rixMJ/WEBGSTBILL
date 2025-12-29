"""
Shared pytest fixtures for all tests.
This file is automatically loaded by pytest.
"""
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime

from app.main import app
from app.database import Base, get_db
from app.models.user import User
from app.models.business import BusinessProfile
from app.models.product import Product
from app.models.customer import Customer
from app.models.supplier import Supplier
from app.services.auth_service import get_password_hash

# Test database
TEST_DATABASE_URL = "sqlite:///./test_webgst.db"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="function")
def db_session():
    """Create a fresh database for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture(scope="function")
def client(db_session):
    """Create a test client with test database."""
    def override_get_db():
        try:
            yield db_session
        finally:
            pass
    
    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


@pytest.fixture(scope="function")
def test_user(db_session):
    """Create a test user."""
    user = User(
        username="testuser",
        email="test@example.com",
        hashed_password=get_password_hash("testpass123"),
        is_active=True
    )
    db_session.add(user)
    db_session.commit()
    db_session.refresh(user)
    return user


@pytest.fixture(scope="function")
def auth_token(client, test_user):
    """Get authentication token for test user."""
    response = client.post(
        "/api/auth/login",
        data={"username": "testuser", "password": "testpass123"}
    )
    assert response.status_code == 200
    return response.json()["access_token"]


@pytest.fixture(scope="function")
def auth_headers(auth_token):
    """Get authorization headers."""
    return {"Authorization": f"Bearer {auth_token}"}


@pytest.fixture(scope="function")
def test_business(db_session, test_user):
    """Create test business profile."""
    business = BusinessProfile(
        user_id=test_user.id,
        business_name="Test GST Business Pvt Ltd",
        gstin="29ABCDE1234F1Z5",
        state_code=29,
        state_name="Karnataka",
        address="123 Test Street, Bangalore",
        email="business@test.com",
        phone="9876543210",
        invoice_prefix="INV",
        next_invoice_number=1
    )
    db_session.add(business)
    db_session.commit()
    db_session.refresh(business)
    return business


@pytest.fixture(scope="function")
def test_products(db_session, test_user):
    """Create test products with different GST rates."""
    products = [
        Product(
            user_id=test_user.id,
            name="Product 5% GST",
            hsn_code="1001",
            gst_rate=5,
            price=100000,  # Rs 1000.00
            stock_quantity=100,
            is_active=True
        ),
        Product(
            user_id=test_user.id,
            name="Product 12% GST",
            hsn_code="2002",
            gst_rate=12,
            price=200000,  # Rs 2000.00
            stock_quantity=50,
            is_active=True
        ),
        Product(
            user_id=test_user.id,
            name="Product 18% GST",
            hsn_code="3003",
            gst_rate=18,
            price=300000,  # Rs 3000.00
            stock_quantity=30,
            is_active=True
        ),
        Product(
            user_id=test_user.id,
            name="Product 28% GST",
            hsn_code="4004",
            gst_rate=28,
            price=500000,  # Rs 5000.00
            stock_quantity=20,
            is_active=True
        ),
    ]
    for product in products:
        db_session.add(product)
    db_session.commit()
    for product in products:
        db_session.refresh(product)
    return products


@pytest.fixture(scope="function")
def test_customers(db_session, test_user):
    """Create test customers (B2B and B2C)."""
    customers = {
        "b2b": Customer(
            user_id=test_user.id,
            name="B2B Customer Pvt Ltd",
            gstin="27XYZAB5678C1Z9",
            state_code=27,
            state_name="Maharashtra",
            address="456 Business Park, Mumbai",
            email="b2b@customer.com",
            phone="9876543211",
            customer_type="B2B",
            is_active=True
        ),
        "b2c": Customer(
            user_id=test_user.id,
            name="B2C Individual Customer",
            gstin=None,
            state_code=29,
            state_name="Karnataka",
            address="789 Residential Area, Bangalore",
            email="b2c@customer.com",
            phone="9876543212",
            customer_type="B2C",
            is_active=True
        ),
        "b2b_same_state": Customer(
            user_id=test_user.id,
            name="B2B Same State Ltd",
            gstin="29PQRST1234D1Z6",
            state_code=29,
            state_name="Karnataka",
            address="321 Tech Park, Bangalore",
            email="b2bsame@customer.com",
            phone="9876543213",
            customer_type="B2B",
            is_active=True
        )
    }
    for customer in customers.values():
        db_session.add(customer)
    db_session.commit()
    for customer in customers.values():
        db_session.refresh(customer)
    return customers


@pytest.fixture(scope="function")
def test_suppliers(db_session, test_user):
    """Create test suppliers (registered and unregistered)."""
    suppliers = {
        "registered": Supplier(
            user_id=test_user.id,
            name="Registered Supplier Pvt Ltd",
            gstin="22LMNOP5678E1Z7",
            state_code=22,
            state_name="Chhattisgarh",
            address="111 Supplier Street, Raipur",
            email="registered@supplier.com",
            phone="9876543214",
            is_active=True
        ),
        "unregistered": Supplier(
            user_id=test_user.id,
            name="Unregistered Supplier",
            gstin=None,
            state_code=29,
            state_name="Karnataka",
            address="222 Local Market, Bangalore",
            email="unregistered@supplier.com",
            phone="9876543215",
            is_active=True
        )
    }
    for supplier in suppliers.values():
        db_session.add(supplier)
    db_session.commit()
    for supplier in suppliers.values():
        db_session.refresh(supplier)
    return suppliers
