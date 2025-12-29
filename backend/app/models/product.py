"""Product model for inventory management"""

from decimal import Decimal
from sqlalchemy import Boolean, Column, DateTime, Integer, Numeric, String
from app.database import Base, get_utc_now


class Product(Base):
    """Product/Service with HSN and GST rate"""
    
    __tablename__ = "products"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(255), nullable=False, index=True)
    description = Column(String(500), nullable=True)
    hsn_code = Column(String(8), nullable=False, index=True)  # 4/6/8 digit HSN
    gst_rate = Column(Numeric(5, 2), nullable=False)  # 0, 5, 12, 18, 28
    
    # Pricing in paise (to avoid float precision issues)
    price_paise = Column(Integer, nullable=False)
    
    # Stock management
    stock_quantity = Column(Integer, default=0, nullable=False)
    unit = Column(String(10), default="PCS", nullable=False)  # PCS, KG, LTR, etc.
    
    # Soft delete
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)
    
    def __repr__(self):
        return f"<Product(id={self.id}, name='{self.name}', hsn='{self.hsn_code}')>"
    
    @property
    def price_rupees(self) -> Decimal:
        """Convert paise to rupees for display"""
        return Decimal(self.price_paise) / 100
    
    def reduce_stock(self, quantity: int) -> bool:
        """Reduce stock quantity, return False if insufficient"""
        if self.stock_quantity >= quantity:
            self.stock_quantity -= quantity
            return True
        return False
