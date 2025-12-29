"""Purchase invoice models for raw material and expense tracking"""

from sqlalchemy import Boolean, Column, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import relationship
from app.database import Base, get_utc_now


class PurchaseInvoice(Base):
    """Purchase invoice header - tracks supplier invoices and INPUT GST"""
    
    __tablename__ = "purchase_invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    supplier_id = Column(Integer, ForeignKey("suppliers.id"), nullable=False, index=True)
    
    # Supplier invoice reference
    supplier_invoice_no = Column(String(100), nullable=False)
    supplier_invoice_date = Column(DateTime, nullable=False)
    purchase_date = Column(DateTime, nullable=False)  # When goods received
    
    # Place of supply (GST jurisdiction)
    place_of_supply = Column(String(100), nullable=False)  # Supplier state name
    place_of_supply_code = Column(String(2), nullable=False)  # Supplier state code
    
    # Totals (stored for audit trail, not recalculated)
    total_quantity = Column(Float, default=0, nullable=False)
    subtotal_value = Column(Integer, default=0, nullable=False)  # In paise
    cgst_amount = Column(Integer, default=0, nullable=False)  # Input CGST (paise)
    sgst_amount = Column(Integer, default=0, nullable=False)  # Input SGST (paise)
    igst_amount = Column(Integer, default=0, nullable=False)  # Input IGST (paise)
    total_gst = Column(Integer, default=0, nullable=False)  # Total tax (paise)
    total_amount = Column(Integer, default=0, nullable=False)  # Grand total (paise)
    
    # Status
    status = Column(String(20), default="Draft", nullable=False)  # Draft, Finalized, Cancelled
    cancel_reason = Column(Text, nullable=True)
    
    # Soft delete / cancellation
    is_active = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)
    finalized_at = Column(DateTime, nullable=True)
    cancelled_at = Column(DateTime, nullable=True)
    
    # Relationships
    items = relationship("PurchaseItem", back_populates="invoice", cascade="all, delete-orphan")
    
    def __repr__(self):
        return f"<PurchaseInvoice(id={self.id}, supplier_id={self.supplier_id}, status='{self.status}')>"
    
    @property
    def total_taxable_value(self) -> int:
        """Contract field name for subtotal_value"""
        return self.subtotal_value
    
    @property
    def grand_total(self) -> int:
        """Contract field name for total_amount"""
        return self.total_amount
    
    @property
    def is_finalized(self) -> bool:
        """Check if invoice is locked for editing"""
        return self.status == "Finalized"
    
    @property
    def is_cancelled(self) -> bool:
        """Check if invoice is cancelled"""
        return self.status == "Cancelled"


class PurchaseItem(Base):
    """Line items in a purchase invoice - with tax snapshot"""
    
    __tablename__ = "purchase_items"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("purchase_invoices.id"), nullable=False, index=True)
    
    # Item description
    item_name = Column(String(255), nullable=False)
    hsn_code = Column(String(8), nullable=False)  # 4, 6, or 8 digit HSN
    
    # Quantity and rate
    quantity = Column(Float, nullable=False)
    rate = Column(Integer, nullable=False)  # In paise per unit
    
    # GST rate snapshot (at time of purchase)
    gst_rate = Column(Integer, nullable=False)  # 0, 5, 12, 18, 28 (stored as is)
    
    # Calculated totals (snapshot at save time)
    taxable_value = Column(Integer, nullable=False)  # qty * rate (paise) - contract field name
    gst_amount = Column(Integer, nullable=False)  # Total GST for item (paise) - contract field name
    cgst_amount = Column(Integer, default=0, nullable=False)  # Input CGST (paise)
    sgst_amount = Column(Integer, default=0, nullable=False)  # Input SGST (paise)
    igst_amount = Column(Integer, default=0, nullable=False)  # Input IGST (paise)
    total_amount = Column(Integer, nullable=False)  # taxable_value + gst_amount (paise)
    
    # Tax type used (CGST/SGST or IGST)
    tax_type = Column(String(10), nullable=False)  # "CGST_SGST" or "IGST"
    
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    
    # Relationships
    invoice = relationship("PurchaseInvoice", back_populates="items")
    
    def __repr__(self):
        return f"<PurchaseItem(id={self.id}, invoice_id={self.invoice_id}, hsn='{self.hsn_code}')>"
