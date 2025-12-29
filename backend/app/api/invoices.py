"""Invoices API routes"""

from fastapi import APIRouter, Depends, HTTPException, status, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models.business import BusinessProfile
from app.models.user import User
from app.schemas.invoice import InvoiceCreate, InvoiceResponse, InvoiceListResponse
from app.services import invoice_service
from app.api.auth import get_current_active_user

router = APIRouter()


def get_business(db: Session = Depends(get_db)) -> BusinessProfile:
    """Dependency to get business profile"""
    business = db.query(BusinessProfile).first()
    if not business:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Business profile not configured. Please set up business profile first."
        )
    return business


@router.post("/", response_model=InvoiceResponse, status_code=status.HTTP_201_CREATED)
def create_invoice(
    invoice_data: InvoiceCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_active_user),
    business: BusinessProfile = Depends(get_business)
):
    """
    Create a new tax invoice with automatic GST calculation and stock reduction.
    """
    invoice = invoice_service.create_invoice(db, invoice_data, current_user, business)
    return invoice


@router.get("/", response_model=list[InvoiceListResponse])
def list_invoices(
    skip: int = 0,
    limit: int = 100,
    include_cancelled: bool = False,
    db = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """List all invoices"""
    invoices = invoice_service.list_invoices(db, skip, limit, include_cancelled)
    
    # Map to list response schema
    return [
        InvoiceListResponse(
            id=inv.id,
            invoice_number=inv.invoice_number,
            invoice_date=inv.invoice_date,
            place_of_supply=inv.place_of_supply,
            customer_id=inv.customer_id,
            customer_name=inv.customer_snapshot.get("name", ""),
            grand_total=inv.grand_total,
            status=inv.status,
            is_cancelled=inv.is_cancelled,
            created_at=inv.created_at
        )
        for inv in invoices
    ]


@router.get("/{invoice_id}", response_model=InvoiceResponse)
def get_invoice(
    invoice_id: int,
    db = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get invoice by ID with all details"""
    invoice = invoice_service.get_invoice_by_id(db, invoice_id)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with id {invoice_id} not found"
        )
    return invoice


@router.get("/number/{invoice_number}", response_model=InvoiceResponse)
def get_invoice_by_number(
    invoice_number: str,
    db = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Get invoice by invoice number"""
    invoice = invoice_service.get_invoice_by_number(db, invoice_number)
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice {invoice_number} not found"
        )
    return invoice


@router.post("/{invoice_id}/cancel", response_model=InvoiceResponse)
def cancel_invoice(
    invoice_id: int,
    reason: str = "",
    db = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """
    Cancel an invoice (soft delete) and restore stock quantities.
    """
    invoice = invoice_service.cancel_invoice(db, invoice_id, reason)
    return invoice


@router.get("/{invoice_id}/pdf")
def get_invoice_pdf(
    invoice_id: int,
    db = Depends(get_db),
    current_user: User = Depends(get_current_active_user)
):
    """Generate GST-compliant PDF for an invoice."""
    pdf_bytes, filename = invoice_service.render_invoice_pdf(db, invoice_id)
    return Response(content=pdf_bytes, media_type="application/pdf", headers={"Content-Disposition": f"attachment; filename={filename}"})
