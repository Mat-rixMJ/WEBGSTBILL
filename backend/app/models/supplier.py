"""Supplier (Vendor) model for purchase module"""

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from app.database import Base, get_utc_now


class Supplier(Base):
    """Supplier/Vendor entity for purchase transactions"""
    
    __tablename__ = "suppliers"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    supplier_type = Column(String(12), nullable=False, default="UNREGISTERED")  # REGISTERED or UNREGISTERED
    gstin = Column(String(15), nullable=True, index=True)  # Required only for REGISTERED
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
        return f"<Supplier(id={self.id}, name='{self.name}', type='{self.supplier_type}')>"
    
    @property
    def is_registered(self) -> bool:
        """Check if supplier is GST registered"""
        return self.supplier_type == "REGISTERED"
