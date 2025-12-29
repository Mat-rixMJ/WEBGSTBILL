"""Product schemas"""

from datetime import datetime
from decimal import Decimal
from pydantic import BaseModel, Field, field_validator


class ProductBase(BaseModel):
    """Base product schema"""
    name: str = Field(..., min_length=2, max_length=255)
    description: str | None = Field(None, max_length=500)
    hsn_code: str = Field(..., min_length=4, max_length=8)
    gst_rate: Decimal = Field(..., ge=0, le=28)
    price_paise: int = Field(..., ge=0)
    stock_quantity: int = Field(default=0, ge=0)
    unit: str = Field(default="PCS", max_length=10)
    
    @field_validator("hsn_code")
    @classmethod
    def validate_hsn(cls, v: str) -> str:
        """Validate HSN code is 4, 6, or 8 digits"""
        if not v.isdigit() or len(v) not in [4, 6, 8]:
            raise ValueError("HSN code must be 4, 6, or 8 digits")
        return v
    
    @field_validator("gst_rate")
    @classmethod
    def validate_gst_rate(cls, v: Decimal) -> Decimal:
        """Validate GST rate is one of standard rates"""
        valid_rates = [Decimal('0'), Decimal('5'), Decimal('12'), Decimal('18'), Decimal('28')]
        if v not in valid_rates:
            raise ValueError("GST rate must be 0, 5, 12, 18, or 28")
        return v


class ProductCreate(ProductBase):
    """Schema for creating a product"""
    pass


class ProductUpdate(BaseModel):
    """Schema for updating a product"""
    name: str | None = Field(None, min_length=2, max_length=255)
    description: str | None = Field(None, max_length=500)
    hsn_code: str | None = Field(None, min_length=4, max_length=8)
    gst_rate: Decimal | None = Field(None, ge=0, le=28)
    price_paise: int | None = Field(None, ge=0)
    stock_quantity: int | None = Field(None, ge=0)
    unit: str | None = Field(None, max_length=10)
    is_active: bool | None = None


class ProductResponse(ProductBase):
    """Schema for product response"""
    id: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    price_rupees: Decimal
    
    class Config:
        from_attributes = True
