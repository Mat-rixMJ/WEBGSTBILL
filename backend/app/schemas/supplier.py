"""Pydantic schemas for supplier management"""

from datetime import datetime
from pydantic import BaseModel, Field, field_validator, model_validator
from typing import Self
from app.utils.validators import validate_gstin, extract_state_code_from_gstin, STATE_CODES, STATE_CODE_MAP


class SupplierBase(BaseModel):
    """Base supplier schema - matches contract specification"""
    name: str = Field(..., min_length=2, max_length=255, description="Supplier name")
    supplier_type: str = Field(..., pattern="^(REGISTERED|UNREGISTERED)$", description="Supplier type: REGISTERED or UNREGISTERED")
    gstin: str | None = Field(None, min_length=15, max_length=15, description="GSTIN (required for REGISTERED)")
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
    def validate_supplier_requirements(self) -> Self:
        """Validate REGISTERED requires GSTIN and GSTIN state matches supplier state"""
        # REGISTERED must have GSTIN
        if self.supplier_type == "REGISTERED":
            if not self.gstin:
                raise ValueError("GSTIN is required for REGISTERED suppliers")
            
            # GSTIN state code must match supplier state code
            gstin_state = extract_state_code_from_gstin(self.gstin)
            if gstin_state != self.state_code:
                raise ValueError(
                    f"GSTIN state code ({gstin_state}) must match supplier state code ({self.state_code})"
                )
        
        # UNREGISTERED must NOT have GSTIN
        if self.supplier_type == "UNREGISTERED":
            if self.gstin:
                raise ValueError("GSTIN must not be provided for UNREGISTERED suppliers")
        
        # Validate state matches state_code
        expected_state = STATE_CODES.get(self.state_code)
        if expected_state and expected_state != self.state:
            raise ValueError(
                f"State '{self.state}' does not match state code '{self.state_code}' (expected '{expected_state}')"
            )
        
        return self


class SupplierCreate(SupplierBase):
    """Schema for creating a supplier"""
    pass


class SupplierUpdate(BaseModel):
    """Schema for updating a supplier - all fields optional"""
    name: str | None = Field(None, min_length=2, max_length=255, description="Supplier name")
    supplier_type: str | None = Field(None, pattern="^(REGISTERED|UNREGISTERED)$", description="Supplier type")
    gstin: str | None = Field(None, min_length=15, max_length=15, description="GSTIN")
    address: str | None = Field(None, min_length=5, max_length=500, description="Complete address")
    state: str | None = Field(None, min_length=2, max_length=100, description="State name")
    state_code: str | None = Field(None, min_length=2, max_length=2, pattern="^[0-9]{2}$", description="2-digit state code")
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
    def validate_state_code(cls, v: str | None) -> str | None:
        """Validate state code is valid if provided"""
        if v is not None and v not in STATE_CODES:
            raise ValueError(f"Invalid state code '{v}'")
        return v
    
    @model_validator(mode='after')
    def validate_supplier_requirements(self) -> Self:
        """Validate REGISTERED requires GSTIN and GSTIN state matches supplier state"""
        # If supplier_type is being updated to REGISTERED, GSTIN must be present
        if self.supplier_type == "REGISTERED":
            if self.gstin is None:
                raise ValueError("GSTIN is required for REGISTERED suppliers")
            
            # If state_code is also being updated, validate match
            if self.state_code:
                gstin_state = extract_state_code_from_gstin(self.gstin)
                if gstin_state != self.state_code:
                    raise ValueError(
                        f"GSTIN state code ({gstin_state}) must match supplier state code ({self.state_code})"
                    )
        
        # If supplier_type is being updated to UNREGISTERED, GSTIN must be None
        if self.supplier_type == "UNREGISTERED":
            if self.gstin:
                raise ValueError("GSTIN must not be provided for UNREGISTERED suppliers")
        
        # Validate state matches state_code if both provided
        if self.state and self.state_code:
            expected_state = STATE_CODES.get(self.state_code)
            if expected_state and expected_state != self.state:
                raise ValueError(
                    f"State '{self.state}' does not match state code '{self.state_code}' (expected '{expected_state}')"
                )
        
        return self


class SupplierResponse(BaseModel):
    """Response schema for supplier (from database)"""
    id: int
    name: str
    supplier_type: str
    gstin: str | None
    address: str
    state: str
    state_code: str
    phone: str | None
    email: str | None
    is_active: bool
    created_at: datetime
    updated_at: datetime
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "name": "XYZ Chemicals Pvt Ltd",
                "supplier_type": "REGISTERED",
                "gstin": "27ABCDE1234F1Z5",
                "address": "123 Industrial Area, Pune, Maharashtra - 411001",
                "state": "Maharashtra",
                "state_code": "27",
                "phone": "+919876543210",
                "email": "contact@xyzchemicals.com",
                "is_active": True,
                "created_at": "2025-12-25T12:00:00Z",
                "updated_at": "2025-12-25T12:00:00Z"
            }
        }
    }
