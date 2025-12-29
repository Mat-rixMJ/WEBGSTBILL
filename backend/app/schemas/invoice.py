"""Invoice schemas"""

from datetime import datetime, date
from decimal import Decimal
from pydantic import BaseModel, Field


class InvoiceItemCreate(BaseModel):
    """Schema for creating an invoice item"""
    product_id: int = Field(..., gt=0)
    quantity: int = Field(..., gt=0)
    description: str | None = Field(None, max_length=500)


class InvoiceTotalsInput(BaseModel):
    """Optional client totals for tamper detection (rupees)."""
    total_taxable_value: Decimal
    total_gst: Decimal
    grand_total: Decimal


class InvoiceItemResponse(BaseModel):
    """Schema for invoice item response"""
    id: int
    item_name: str
    description: str | None
    hsn_code: str
    quantity: int
    unit: str
    rate: Decimal
    gst_rate: Decimal
    taxable_value: Decimal
    gst_amount: Decimal
    cgst: Decimal
    sgst: Decimal
    igst: Decimal
    total: Decimal
    created_at: datetime
    
    class Config:
        from_attributes = True


class InvoiceCreate(BaseModel):
    """Schema for creating an invoice"""
    customer_id: int = Field(..., gt=0)
    invoice_date: date = Field(default_factory=date.today)
    place_of_supply: str | None = Field(None, min_length=2, max_length=100)
    items: list[InvoiceItemCreate] = Field(..., min_length=1)
    client_totals: InvoiceTotalsInput | None = None


class InvoiceResponse(BaseModel):
    """Schema for invoice response"""
    id: int
    invoice_number: str
    invoice_date: date
    place_of_supply: str
    invoice_type: str
    status: str
    customer_id: int
    customer_snapshot: dict
    business_snapshot: dict
    total_taxable_value: Decimal
    total_gst: Decimal
    grand_total: Decimal
    cgst: Decimal
    sgst: Decimal
    igst: Decimal
    round_off: Decimal
    is_interstate: bool
    is_cancelled: bool
    cancelled_at: datetime | None
    cancellation_reason: str | None
    created_at: datetime
    updated_at: datetime
    items: list[InvoiceItemResponse]
    
    class Config:
        from_attributes = True


class InvoiceListResponse(BaseModel):
    """Schema for invoice list item (without items)"""
    id: int
    invoice_number: str
    invoice_date: date
    place_of_supply: str
    customer_id: int
    customer_name: str
    grand_total: Decimal
    status: str
    is_cancelled: bool
    created_at: datetime
    
    class Config:
        from_attributes = True
