"""Business profile API routes"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.business import BusinessProfile
from app.models.user import User
from app.schemas.business import BusinessProfileCreate, BusinessProfileUpdate, BusinessProfileResponse
from app.api.auth import get_current_active_user

router = APIRouter()


@router.post("/", response_model=BusinessProfileResponse, status_code=status.HTTP_201_CREATED)
def create_business_profile(
    business_data: BusinessProfileCreate,
    db = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Create business profile (single business per installation).
    """
    # Check if business profile already exists
    existing = db.query(BusinessProfile).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Business profile already exists. Use update endpoint to modify."
        )
    
    # Create business profile
    business = BusinessProfile(**business_data.model_dump())
    db.add(business)
    db.commit()
    db.refresh(business)
    
    return business


@router.get("/", response_model=BusinessProfileResponse)
def get_business_profile(db = Depends(get_db)):
    """Get business profile"""
    business = db.query(BusinessProfile).first()
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not configured. Please set up business profile first."
        )
    return business


@router.put("/", response_model=BusinessProfileResponse)
def update_business_profile(
    business_data: BusinessProfileUpdate,
    db = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Update business profile (limited fields only).
    
    Note: GSTIN and invoice numbering cannot be changed.
    """
    business = db.query(BusinessProfile).first()
    if not business:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Business profile not found"
        )
    
    # Update only provided fields
    update_data = business_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(business, field, value)
    
    db.commit()
    db.refresh(business)
    
    return business
