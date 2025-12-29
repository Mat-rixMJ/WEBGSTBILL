"""Invoice and invoice items models"""

from datetime import date
from decimal import Decimal
from typing import TYPE_CHECKING
from sqlalchemy import Boolean, Column, Date, DateTime, ForeignKey, Integer, JSON, Numeric, String
from sqlalchemy.orm import relationship
from app.database import Base, get_utc_now

if TYPE_CHECKING:
    from app.models.customer import Customer
    from app.models.product import Product
    from app.models.user import User


class Invoice(Base):
    """Tax invoice with GST calculation"""
    
    __tablename__ = "invoices"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_number = Column(String(50), unique=True, nullable=False, index=True)
    invoice_date = Column(Date, default=date.today, nullable=False, index=True)
    place_of_supply = Column(String(100), nullable=False)
    invoice_type = Column(String(20), nullable=False, default="TAX_INVOICE")
    status = Column(String(20), nullable=False, default="FINAL")  # DRAFT, FINAL, CANCELLED
    finalized_at = Column(DateTime, nullable=True)
    
    # Foreign keys
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    created_by = Column(Integer, ForeignKey("users.id"), nullable=False)
    
    # Relationships
    customer = relationship("Customer", foreign_keys=[customer_id])
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")
    creator = relationship("User", foreign_keys=[created_by])
    
    # Snapshots (denormalized for historical accuracy)
    customer_snapshot = Column(JSON, nullable=False)  # Customer data at time of invoice
    business_snapshot = Column(JSON, nullable=False)  # Business data at time of invoice
    
    # Tax calculation totals (stored in paise)
    subtotal_paise = Column(Integer, nullable=False, default=0)
    cgst_paise = Column(Integer, nullable=False, default=0)
    sgst_paise = Column(Integer, nullable=False, default=0)
    igst_paise = Column(Integer, nullable=False, default=0)
    total_paise = Column(Integer, nullable=False, default=0)
    total_taxable_value_paise = Column(Integer, nullable=False, default=0)
    total_gst_paise = Column(Integer, nullable=False, default=0)
    grand_total_paise = Column(Integer, nullable=False, default=0)
    round_off_paise = Column(Integer, nullable=False, default=0)
    
    # Status
    is_cancelled = Column(Boolean, default=False, nullable=False)
    cancelled_at = Column(DateTime, nullable=True)
    cancellation_reason = Column(String(500), nullable=True)
    
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    updated_at = Column(DateTime, default=get_utc_now, onupdate=get_utc_now, nullable=False)
    
    def __repr__(self):
        return f"<Invoice(id={self.id}, number='{self.invoice_number}', total={self.total_rupees})>"
    
    @property
    def total_rupees(self) -> Decimal:
        """Convert total paise to rupees"""
        return Decimal(self.total_paise) / 100

    @property
    def total_taxable_value_rupees(self) -> Decimal:
        return Decimal(self.total_taxable_value_paise) / 100

    @property
    def total_taxable_value(self) -> Decimal:
        return self.total_taxable_value_rupees

    @property
    def total_gst_rupees(self) -> Decimal:
        return Decimal(self.total_gst_paise) / 100

    @property
    def total_gst(self) -> Decimal:
        return self.total_gst_rupees

    @property
    def grand_total_rupees(self) -> Decimal:
        return Decimal(self.grand_total_paise) / 100

    @property
    def grand_total(self) -> Decimal:
        return self.grand_total_rupees

    @property
    def cgst(self) -> Decimal:
        return Decimal(self.cgst_paise) / 100

    @property
    def sgst(self) -> Decimal:
        return Decimal(self.sgst_paise) / 100

    @property
    def igst(self) -> Decimal:
        return Decimal(self.igst_paise) / 100

    @property
    def round_off(self) -> Decimal:
        return Decimal(self.round_off_paise) / 100
    
    @property
    def is_interstate(self) -> bool:
        """Check if invoice is interstate (IGST applicable)"""
        return self.igst_paise > 0
    
    def cancel(self, reason: str = ""):
        """Cancel invoice (soft delete)"""
        self.is_cancelled = True
        self.cancelled_at = get_utc_now()
        self.cancellation_reason = reason


class InvoiceItem(Base):
    """Line item in an invoice with tax snapshot"""
    
    __tablename__ = "invoice_items"
    
    id = Column(Integer, primary_key=True, index=True)
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False, index=True)
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True)  # Nullable if product deleted
    
    # Relationship
    invoice = relationship("Invoice", back_populates="items")
    product = relationship("Product", foreign_keys=[product_id])
    
    # Snapshot data (immutable - captured at time of invoice creation)
    product_name = Column(String(255), nullable=False)
    description = Column(String(500), nullable=True)
    hsn_code = Column(String(8), nullable=False)
    quantity = Column(Integer, nullable=False)
    unit = Column(String(10), nullable=False)
    unit_price_paise = Column(Integer, nullable=False)
    gst_rate = Column(Numeric(5, 2), nullable=False)
    
    # Calculated amounts (stored in paise)
    taxable_amount_paise = Column(Integer, nullable=False)
    cgst_paise = Column(Integer, nullable=False, default=0)
    sgst_paise = Column(Integer, nullable=False, default=0)
    igst_paise = Column(Integer, nullable=False, default=0)
    gst_amount_paise = Column(Integer, nullable=False, default=0)
    total_paise = Column(Integer, nullable=False)
    
    created_at = Column(DateTime, default=get_utc_now, nullable=False)
    
    def __repr__(self):
        return f"<InvoiceItem(id={self.id}, product='{self.product_name}', qty={self.quantity})>"
    
    @property
    def total_rupees(self) -> Decimal:
        """Convert total paise to rupees"""
        return Decimal(self.total_paise) / 100

    @property
    def item_name(self) -> str:
        return self.product_name

    @property
    def rate_rupees(self) -> Decimal:
        return Decimal(self.unit_price_paise) / 100

    @property
    def gst_amount_rupees(self) -> Decimal:
        return Decimal(self.gst_amount_paise) / 100

    @property
    def rate(self) -> Decimal:
        return self.rate_rupees

    @property
    def taxable_value(self) -> Decimal:
        return Decimal(self.taxable_amount_paise) / 100

    @property
    def gst_amount(self) -> Decimal:
        return self.gst_amount_rupees

    @property
    def cgst(self) -> Decimal:
        return Decimal(self.cgst_paise) / 100

    @property
    def sgst(self) -> Decimal:
        return Decimal(self.sgst_paise) / 100

    @property
    def igst(self) -> Decimal:
        return Decimal(self.igst_paise) / 100

    @property
    def total(self) -> Decimal:
        return Decimal(self.total_paise) / 100
