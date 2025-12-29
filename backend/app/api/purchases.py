"""API endpoints for purchase invoice management"""

from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Supplier, PurchaseInvoice, PurchaseItem, Product, BusinessProfile
from app.schemas.purchase import (
    PurchaseInvoiceCreate, PurchaseInvoiceResponse, PurchaseInvoiceCancel, PurchaseListResponse
)
from app.api.auth import get_current_active_user
from app.services.purchase_gst_calculator import calculate_purchase_item_tax, calculate_purchase_invoice_totals

router = APIRouter(prefix="/api/purchases", tags=["purchases"], redirect_slashes=False)


@router.post("", response_model=PurchaseInvoiceResponse, status_code=201)
def create_purchase_invoice(
    purchase: PurchaseInvoiceCreate,
    db = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Create a new purchase invoice (initially in Draft status).
    
    Rules:
    - Supplier must exist and be active
    - At least one item required
    - Tax calculated based on supplier state vs business state
    - Stock NOT updated until finalized
    """
    
    # Validate supplier exists
    supplier = db.query(Supplier).filter(
        Supplier.id == purchase.supplier_id,
        Supplier.is_active == True
    ).first()
    
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")
    
    # Get business state code from BusinessProfile (fallback to Karnataka '29' if not configured)
    business = db.query(BusinessProfile).first()
    business_state_code = business.state_code if business and business.state_code else "29"
    
    # Create purchase invoice header
    db_purchase = PurchaseInvoice(
        supplier_id=purchase.supplier_id,
        supplier_invoice_no=purchase.supplier_invoice_no,
        supplier_invoice_date=purchase.supplier_invoice_date,
        purchase_date=purchase.purchase_date,
        place_of_supply=supplier.state,
        place_of_supply_code=supplier.state_code,
        status="Draft"
    )
    
    # Add items and calculate taxes
    total_quantity = 0.0
    subtotal_value = 0
    cgst_total = 0
    sgst_total = 0
    igst_total = 0
    
    for item_input in purchase.items:
        # Calculate tax for this item
        item_tax = calculate_purchase_item_tax(
            quantity=item_input.quantity,
            unit_rate=item_input.rate,
            gst_rate=item_input.gst_rate,
            supplier_state_code=supplier.state_code,
            business_state_code=business_state_code
        )
        
        # Create PurchaseItem with tax snapshot
        db_item = PurchaseItem(
            item_name=item_input.item_name,
            hsn_code=item_input.hsn_code,
            quantity=item_input.quantity,
            rate=item_input.rate,
            gst_rate=item_input.gst_rate,
            taxable_value=item_tax.subtotal,
            gst_amount=item_tax.cgst_amount + item_tax.sgst_amount + item_tax.igst_amount,
            cgst_amount=item_tax.cgst_amount,
            sgst_amount=item_tax.sgst_amount,
            igst_amount=item_tax.igst_amount,
            total_amount=item_tax.total_amount,
            tax_type=item_tax.tax_type
        )
        
        db_purchase.items.append(db_item)
        
        # Accumulate totals
        total_quantity += item_input.quantity
        subtotal_value += item_tax.subtotal
        cgst_total += item_tax.cgst_amount
        sgst_total += item_tax.sgst_amount
        igst_total += item_tax.igst_amount
    
    # Set purchase invoice totals
    db_purchase.total_quantity = total_quantity
    db_purchase.subtotal_value = subtotal_value
    db_purchase.cgst_amount = cgst_total
    db_purchase.sgst_amount = sgst_total
    db_purchase.igst_amount = igst_total
    db_purchase.total_gst = cgst_total + sgst_total + igst_total
    db_purchase.total_amount = subtotal_value + db_purchase.total_gst
    
    db.add(db_purchase)
    db.commit()
    db.refresh(db_purchase)
    
    return db_purchase


@router.get("", response_model=PurchaseListResponse)
def list_purchases(
    skip: int = Query(0, ge=0),
    limit: int = Query(1000, ge=1, le=1000),
    status: str = Query(None),
    db = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """List all purchase invoices with optional status filter"""
    
    query = db.query(PurchaseInvoice).filter(PurchaseInvoice.is_active == True)
    
    if status:
        query = query.filter(PurchaseInvoice.status == status)
    
    total = query.count()
    purchases = query.offset(skip).limit(limit).all()
    
    return PurchaseListResponse(value=purchases, Count=total)


@router.get("/{purchase_id}", response_model=PurchaseInvoiceResponse)
def get_purchase(
    purchase_id: int,
    db = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Get a specific purchase invoice with all items"""
    
    purchase = db.query(PurchaseInvoice).filter(
        PurchaseInvoice.id == purchase_id,
        PurchaseInvoice.is_active == True
    ).first()
    
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase invoice not found")
    
    return purchase


@router.post("/{purchase_id}/finalize", response_model=PurchaseInvoiceResponse)
def finalize_purchase(
    purchase_id: int,
    db = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Finalize a purchase invoice.
    
    Effects:
    - Locks invoice from editing
    - Updates inventory (increases stock)
    - Marks as Finalized
    """
    
    purchase = db.query(PurchaseInvoice).filter(
        PurchaseInvoice.id == purchase_id
    ).first()
    
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase invoice not found")
    
    if purchase.status == "Finalized":
        raise HTTPException(status_code=400, detail="Purchase is already finalized")
    
    if purchase.status == "Cancelled":
        raise HTTPException(status_code=400, detail="Cannot finalize a cancelled purchase")
    
    # Validate all products exist for their HSN codes before updating inventory
    missing_hsns = []
    for item in purchase.items:
        product = db.query(Product).filter(
            Product.hsn_code == item.hsn_code,
            Product.is_active == True
        ).first()
        if not product:
            missing_hsns.append(item.hsn_code)

    if missing_hsns:
        unique_missing = sorted(set(missing_hsns))
        raise HTTPException(
            status_code=400,
            detail=f"Missing products for HSN codes: {', '.join(unique_missing)}. Create matching products before finalizing."
        )

    # All good: update inventory for each item
    for item in purchase.items:
        product = db.query(Product).filter(
            Product.hsn_code == item.hsn_code,
            Product.is_active == True
        ).first()
        if product:
            product.stock_quantity += int(item.quantity)
    
    # Mark purchase as finalized
    purchase.status = "Finalized"
    purchase.finalized_at = datetime.utcnow()
    
    db.commit()
    db.refresh(purchase)
    
    return purchase


@router.post("/{purchase_id}/cancel", response_model=PurchaseInvoiceResponse)
def cancel_purchase(
    purchase_id: int,
    cancel_request: PurchaseInvoiceCancel,
    db = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Cancel a purchase invoice.
    
    Rules:
    - Can only cancel Draft or Finalized invoices
    - Cannot reverse finalized inventory (Phase-1.5 limitation)
    - Reason required
    """
    
    purchase = db.query(PurchaseInvoice).filter(
        PurchaseInvoice.id == purchase_id
    ).first()
    
    if not purchase:
        raise HTTPException(status_code=404, detail="Purchase invoice not found")
    
    if purchase.status == "Cancelled":
        raise HTTPException(status_code=400, detail="Purchase is already cancelled")
    
    # Mark as cancelled
    purchase.status = "Cancelled"
    purchase.cancel_reason = cancel_request.cancel_reason
    purchase.cancelled_at = datetime.utcnow()
    
    db.commit()
    db.refresh(purchase)
    
    return purchase
