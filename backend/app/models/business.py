"""Business profile model - single business per installation"""

from sqlalchemy import Boolean, Column, DateTime, Integer, String
from app.database import Base, get_utc_now


class BusinessProfile(Base):
    """Single business entity for GST billing"""
    
    __tablename__ = "business_profile"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False)
    gstin = Column(String(15), unique=True, nullable=False, index=True)
    state_code = Column(String(2), nullable=False)  # First 2 digits of GSTIN
    address = Column(String(500), nullable=False)
    city = Column(String(100), nullable=False)
    pincode = Column(String(6), nullable=False)
    phone = Column(String(15), nullable=True)
    email = Column(String(255), nullable=True)
    
    # Invoice numbering
    invoice_prefix = Column(String(10), default="INV", nullable=False)
    invoice_start_number = Column(Integer, default=1, nullable=False)
    current_invoice_number = Column(Integer, default=1, nullable=False)
    
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)
    
    def __repr__(self):
        return f"<BusinessProfile(id={self.id}, name='{self.name}', gstin='{self.gstin}')>"
    
    def generate_invoice_number(self) -> str:
        """Generate next invoice number and increment counter"""
        invoice_num = f"{self.invoice_prefix}{self.current_invoice_number:06d}"
        self.current_invoice_number += 1
        return invoice_num
