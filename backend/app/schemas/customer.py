"""Customer schemas"""

from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Self
import re
from app.utils.validators import validate_gstin, extract_state_code_from_gstin, STATE_CODES


class CustomerBase(BaseModel):
    """Base customer schema"""
    name: str = Field(..., min_length=2, max_length=255, description="Customer name")
    customer_type: str = Field(..., pattern="^(B2B|B2C)$", description="Customer type: B2B or B2C")
    gstin: str | None = Field(None, min_length=15, max_length=15, description="GSTIN (required for B2B)")
    address: str = Field(..., min_length=5, max_length=500, description="Complete address")
    state: str = Field(..., min_length=2, max_length=100, description="State name")
    state_code: str = Field(..., min_length=2, max_length=2, pattern="^[0-9]{2}$", description="2-digit state code")
    phone: str | None = Field(None, max_length=15, description="Phone number")
    email: str | None = Field(None, max_length=255, description="Email address")
    
    @field_validator("gstin")
    @classmethod
    def validate_gstin_format(cls, v: str | None) -> str | None:
        """Validate GSTIN format if provided"""
        if v is None or v == "":
            return None
        
        if not validate_gstin(v):
            raise ValueError("Invalid GSTIN format or checksum")
        
        return v.upper()
    
    @field_validator("state_code")
    @classmethod
    def validate_state_code(cls, v: str) -> str:
        """Validate state code is valid"""
        if v not in STATE_CODES:
            raise ValueError(f"Invalid state code '{v}'")
        return v
    
    @model_validator(mode='after')
    def validate_customer_requirements(self) -> Self:
        """Validate B2B requires GSTIN and GSTIN state matches customer state"""
        # B2B must have GSTIN
        if self.customer_type == "B2B":
            if not self.gstin:
                raise ValueError("GSTIN is required for B2B customers")
            
            # GSTIN state code must match customer state code
            gstin_state = extract_state_code_from_gstin(self.gstin)
            if gstin_state != self.state_code:
                raise ValueError(
                    f"GSTIN state code ({gstin_state}) does not match customer state code ({self.state_code})"
                )
        
        # B2C must NOT have GSTIN
        if self.customer_type == "B2C":
            if self.gstin:
                raise ValueError("B2C customers cannot have GSTIN")
        
        return self


class CustomerCreate(CustomerBase):
    """Schema for creating a customer"""
    pass


class CustomerUpdate(BaseModel):
    """Schema for updating a customer (partial update allowed)"""
    name: str | None = Field(None, min_length=2, max_length=255)
    customer_type: str | None = Field(None, pattern="^(B2B|B2C)$")
    gstin: str | None = Field(None, min_length=15, max_length=15)
    address: str | None = Field(None, min_length=5, max_length=500)
    state: str | None = Field(None, min_length=2, max_length=100)
    state_code: str | None = Field(None, min_length=2, max_length=2, pattern="^[0-9]{2}$")
    phone: str | None = None
    email: str | None = None
    is_active: bool | None = None
    
    @field_validator("gstin")
    @classmethod
    def validate_gstin_format(cls, v: str | None) -> str | None:
        """Validate GSTIN format if provided"""
        if v is None or v == "":
            return None
        
        if not validate_gstin(v):
            raise ValueError("Invalid GSTIN format or checksum")
        
        return v.upper()


class CustomerResponse(BaseModel):
    """Schema for customer response - no validation, data already validated in DB"""
    id: int
    name: str
    customer_type: str
    gstin: str | None
    address: str
    state: str
    state_code: str
    phone: str | None
    email: str | None
    is_active: bool
    is_b2b: bool
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True
