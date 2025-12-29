"""Business profile schemas"""

from datetime import datetime
from pydantic import BaseModel, Field, field_validator
import re


class BusinessProfileBase(BaseModel):
    """Base business profile schema"""
    name: str = Field(..., min_length=2, max_length=255)
    gstin: str = Field(..., min_length=15, max_length=15)
    state_code: str = Field(..., min_length=2, max_length=2)
    address: str = Field(..., min_length=5, max_length=500)
    city: str = Field(..., min_length=2, max_length=100)
    pincode: str = Field(..., min_length=6, max_length=6)
    phone: str | None = Field(None, max_length=15)
    email: str | None = Field(None, max_length=255)
    
    @field_validator("gstin")
    @classmethod
    def validate_gstin(cls, v: str) -> str:
        """Validate GSTIN format"""
        pattern = r"^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$"
        if not re.match(pattern, v):
            raise ValueError("Invalid GSTIN format")
        return v
    
    @field_validator("pincode")
    @classmethod
    def validate_pincode(cls, v: str) -> str:
        """Validate pincode is 6 digits"""
        if not v.isdigit() or len(v) != 6:
            raise ValueError("Pincode must be 6 digits")
        return v


class BusinessProfileCreate(BusinessProfileBase):
    """Schema for creating business profile"""
    invoice_prefix: str = Field(default="INV", max_length=10)
    invoice_start_number: int = Field(default=1, ge=1)


class BusinessProfileUpdate(BaseModel):
    """Schema for updating business profile (limited fields)"""
    name: str | None = Field(None, min_length=2, max_length=255)
    address: str | None = Field(None, min_length=5, max_length=500)
    city: str | None = Field(None, min_length=2, max_length=100)
    pincode: str | None = Field(None, min_length=6, max_length=6)
    phone: str | None = Field(None, max_length=15)
    email: str | None = Field(None, max_length=255)


class BusinessProfileResponse(BusinessProfileBase):
    """Schema for business profile response"""
    id: int
    invoice_prefix: str
    invoice_start_number: int
    current_invoice_number: int
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
