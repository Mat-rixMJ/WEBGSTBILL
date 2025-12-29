"""Pydantic schemas for purchase invoice management"""

from typing import List, Optional
from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_serializer
from typing_extensions import Self


class PurchaseItemInput(BaseModel):
    """Schema for a purchase invoice line item (input) - matches contract"""
    item_name: str = Field(..., min_length=1, max_length=255, description="Item/product name")
    hsn_code: str = Field(..., min_length=4, max_length=8, description="4, 6, or 8-digit HSN code")
    quantity: float = Field(..., gt=0, description="Quantity in units")
    rate: int = Field(..., ge=0, description="Rate per unit in paise")
    gst_rate: int = Field(..., description="GST rate: 0, 5, 12, 18, or 28 percent")
    
    @field_validator("gst_rate")
    @classmethod
    def validate_gst_rate(cls, v):
        valid_rates = [0, 5, 12, 18, 28]
        if v not in valid_rates:
            raise ValueError(f"GST rate must be one of {valid_rates}")
        return v
    
    @field_validator("hsn_code")
    @classmethod
    def validate_hsn_length(cls, v):
        length = len(v)
        if length not in [4, 6, 8]:
            raise ValueError("HSN code must be 4, 6, or 8 digits")
        if not v.isdigit():
            raise ValueError("HSN code must contain only digits")
        return v


class PurchaseItemResponse(BaseModel):
    """Response schema for a purchase line item"""
    id: int
    invoice_id: int
    item_name: str
    hsn_code: str
    quantity: float
    rate: int  # Rate per unit in paise
    gst_rate: int
    taxable_value: int  # Subtotal in paise
    gst_amount: int  # Total GST (CGST+SGST or IGST) in paise
    cgst_amount: int  # In paise
    sgst_amount: int  # In paise
    igst_amount: int  # In paise
    total_amount: int  # In paise
    tax_type: str  # CGST_SGST or IGST
    created_at: datetime
    
    model_config = {"from_attributes": True}


class PurchaseInvoiceBase(BaseModel):
    """Base schema for purchase invoice - matches contract"""
    supplier_id: int = Field(..., description="Supplier ID (UUID in contract, int in implementation)")
    supplier_invoice_no: str = Field(..., min_length=1, max_length=100, description="Supplier's invoice number")
    supplier_invoice_date: datetime = Field(..., description="Invoice date from supplier")
    purchase_date: datetime = Field(..., description="Date goods were received")


class PurchaseInvoiceCreate(PurchaseInvoiceBase):
    """Schema for creating a purchase invoice"""
    items: List[PurchaseItemInput] = Field(..., min_length=1, description="At least one item required")
    
    @field_validator("items")
    @classmethod
    def validate_items_count(cls, v):
        if len(v) == 0:
            raise ValueError("At least one item is required")
        return v


class PurchaseInvoiceCancel(BaseModel):
    """Schema for cancelling a purchase invoice"""
    cancel_reason: str = Field(..., min_length=1, max_length=500, description="Reason for cancellation")


class PurchaseInvoiceResponse(BaseModel):
    """Response schema for purchase invoice - matches contract"""
    id: int
    supplier_id: int
    supplier_invoice_no: str
    supplier_invoice_date: datetime
    purchase_date: datetime
    place_of_supply: str  # State name
    total_taxable_value: int  # Subtotal in paise
    total_gst: int  # Total GST in paise
    grand_total: int  # Grand total in paise
    cgst_amount: int  # In paise
    sgst_amount: int  # In paise
    igst_amount: int  # In paise
    status: str  # Draft, Finalized, Cancelled
    items: List[PurchaseItemResponse] = []
    created_at: datetime
    updated_at: datetime
    finalized_at: Optional[datetime]
    cancelled_at: Optional[datetime]
    cancel_reason: Optional[str]
    
    @model_serializer
    def serialize_model(self) -> dict:
        """Custom serializer to map database fields to contract fields"""
        data = {
            "id": self.id,
            "supplier_id": self.supplier_id,
            "supplier_invoice_no": self.supplier_invoice_no,
            "supplier_invoice_date": self.supplier_invoice_date,
            "purchase_date": self.purchase_date,
            "place_of_supply": self.place_of_supply,
            "total_taxable_value": self.total_taxable_value,
            "total_gst": self.total_gst,
            "grand_total": self.grand_total,
            "cgst_amount": self.cgst_amount,
            "sgst_amount": self.sgst_amount,
            "igst_amount": self.igst_amount,
            "status": self.status,
            "items": self.items,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "finalized_at": self.finalized_at,
            "cancelled_at": self.cancelled_at,
            "cancel_reason": self.cancel_reason
        }
        return data
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "supplier_id": 1,
                "supplier_invoice_no": "INV-2025-001",
                "supplier_invoice_date": "2025-12-20T00:00:00",
                "purchase_date": "2025-12-22T00:00:00",
                "place_of_supply": "Maharashtra",
                "total_taxable_value": 100000,  # 1000 in paise
                "total_gst": 18000,  # Total GST
                "grand_total": 118000,  # Grand total
                "cgst_amount": 9000,  # 9% CGST
                "sgst_amount": 9000,  # 9% SGST
                "igst_amount": 0,
                "status": "Finalized",
                "items": [],
                "created_at": "2025-12-25T12:00:00",
                "updated_at": "2025-12-25T12:00:00",
                "finalized_at": "2025-12-25T12:05:00",
                "cancelled_at": None,
                "cancel_reason": None
            }
        }
    }


class PurchaseListResponse(BaseModel):
    """Response for paginated list of purchases"""
    value: List[PurchaseInvoiceResponse]
    Count: int
