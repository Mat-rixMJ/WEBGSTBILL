"""Suppliers API routes"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.supplier import Supplier
from app.models.user import User
from app.schemas.supplier import SupplierCreate, SupplierUpdate, SupplierResponse
from app.api.auth import get_current_active_user

router = APIRouter(prefix="/api/suppliers", tags=["suppliers"], redirect_slashes=False)


@router.post("", response_model=SupplierResponse, status_code=status.HTTP_201_CREATED)
def create_supplier(
    supplier_data: SupplierCreate,
    db = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create a new supplier.
    
    Contract rules enforced by Pydantic schema:
    - GSTIN required for REGISTERED suppliers
    - GSTIN must NOT be provided for UNREGISTERED suppliers
    - GSTIN state code must match supplier state code
    """
    # Check for duplicate GSTIN if registered
    if supplier_data.gstin:
        existing_gstin = db.query(Supplier).filter(
            Supplier.gstin == supplier_data.gstin,
            Supplier.is_active == True
        ).first()
        if existing_gstin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Supplier with GSTIN {supplier_data.gstin} already exists"
            )
    
    supplier = Supplier(**supplier_data.model_dump())
    db.add(supplier)
    db.commit()
    db.refresh(supplier)
    return supplier


@router.get("", response_model=list[SupplierResponse])
def list_suppliers(
    skip: int = 0,
    limit: int = 100,
    active_only: bool = True,
    db = Depends(get_db)
):
    """List all suppliers with optional filtering"""
    query = db.query(Supplier)
    if active_only:
        query = query.filter(Supplier.is_active == True)
    return query.offset(skip).limit(limit).all()


@router.get("/{supplier_id}", response_model=SupplierResponse)
def get_supplier(supplier_id: int, db = Depends(get_db)):
    """Get supplier by ID"""
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with id {supplier_id} not found"
        )
    return supplier


@router.put("/{supplier_id}", response_model=SupplierResponse)
def update_supplier(
    supplier_id: int,
    supplier_data: SupplierUpdate,
    db = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update a supplier.
    
    Note: Editing supplier does NOT affect past purchase invoices.
    Past purchases retain the original supplier snapshot.
    """
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with id {supplier_id} not found"
        )
    
    # Check for duplicate GSTIN if being updated
    if supplier_data.gstin and supplier_data.gstin != supplier.gstin:
        existing_gstin = db.query(Supplier).filter(
            Supplier.gstin == supplier_data.gstin,
            Supplier.is_active == True,
            Supplier.id != supplier_id
        ).first()
        if existing_gstin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Another supplier with GSTIN {supplier_data.gstin} already exists"
            )
    
    # Update only provided fields
    update_data = supplier_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(supplier, field, value)
    
    db.commit()
    db.refresh(supplier)
    return supplier


@router.patch("/{supplier_id}/deactivate", status_code=status.HTTP_200_OK)
def deactivate_supplier(
    supplier_id: int,
    db = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Soft delete a supplier (sets is_active to False).
    
    Deactivated suppliers are hidden from listings but remain in database.
    Past purchase invoices referencing this supplier are NOT affected.
    """
    supplier = db.query(Supplier).filter(Supplier.id == supplier_id).first()
    if not supplier:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Supplier with id {supplier_id} not found"
        )
    
    if not supplier.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Supplier is already deactivated"
        )
    
    supplier.is_active = False
    db.commit()
    
    return {"message": f"Supplier '{supplier.name}' deactivated successfully"}
