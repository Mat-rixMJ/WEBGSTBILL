"""Customer model for buyers"""

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from app.database import Base, get_utc_now


class Customer(Base):
    """Customer/Buyer entity - supports B2B and B2C"""
    
    __tablename__ = "customers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    customer_type = Column(String(3), nullable=False, default="B2C")  # B2B or B2C
    gstin = Column(String(15), nullable=True, index=True)  # Required only for B2B
    address = Column(String(500), nullable=False)
    state = Column(String(100), nullable=False)  # Full state name
    state_code = Column(String(2), nullable=False, index=True)  # 2-digit state code
    phone = Column(String(15), nullable=True)
    email = Column(String(255), nullable=True)
    
    # Soft delete
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)
    
    def __repr__(self):
        return f"<Customer(id={self.id}, name='{self.name}', type='{self.customer_type}')>"
    
    @property
    def is_b2b(self) -> bool:
        """Check if B2B transaction (customer_type is B2B)"""
        return self.customer_type == "B2B"
