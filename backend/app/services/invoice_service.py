"""Invoice service - business logic for invoice creation and management"""

from datetime import date
from decimal import Decimal
from sqlalchemy.orm import Session
from fastapi import HTTPException, status

from app.models.business import BusinessProfile
from app.models.customer import Customer
from app.models.product import Product
from app.models.invoice import Invoice, InvoiceItem
from app.models.user import User
from app.schemas.invoice import InvoiceCreate, InvoiceItemCreate
from app.services.gst_calculator import calculate_line_item_tax, aggregate_invoice_taxes, TaxBreakup
from app.utils.validators import validate_hsn_code, extract_state_code_from_gstin
from app.database import get_utc_now

# Lazy-import placeholder for WeasyPrint HTML to allow monkeypatching in tests
HTML = None


ALLOWED_GST_RATES = {Decimal("0"), Decimal("5"), Decimal("12"), Decimal("18"), Decimal("28")}


def create_invoice(
    db: Session,
    invoice_data: InvoiceCreate,
    current_user: User,
    business: BusinessProfile
) -> Invoice:
    """
    Create a new invoice with GST calculation and stock reduction.
    
    Args:
        db: Database session
        invoice_data: Invoice creation data
        current_user: Current authenticated user
        business: Business profile
        
    Returns:
        Created Invoice object
        
    Raises:
        HTTPException: If customer not found, product not found, or insufficient stock
    """
    _validate_invoice_date(invoice_data.invoice_date)
    _validate_business_profile(business)

    # Validate customer exists
    customer = db.query(Customer).filter(
        Customer.id == invoice_data.customer_id,
        Customer.is_active == True
    ).first()
    
    if not customer:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Customer with id {invoice_data.customer_id} not found"
        )

    _validate_customer_for_invoice(customer)
    
    # Create invoice record (invoice number assigned after validations)
    invoice = Invoice(
        invoice_number="",
        invoice_date=invoice_data.invoice_date,
        place_of_supply=invoice_data.place_of_supply or customer.state_code,
        invoice_type="TAX_INVOICE",
        status="FINAL",
        customer_id=customer.id,
        created_by=current_user.id,
        customer_snapshot=_create_customer_snapshot(customer),
        business_snapshot=_create_business_snapshot(business),
        finalized_at=get_utc_now()
    )

    if invoice.place_of_supply != customer.state_code:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Place of supply must match customer state code"
        )
    
    # Process invoice items
    line_tax_breakups: list[TaxBreakup] = []
    
    for item_data in invoice_data.items:
        # Validate product
        product = db.query(Product).filter(
            Product.id == item_data.product_id,
            Product.is_active == True
        ).first()
        
        if not product:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Product with id {item_data.product_id} not found"
            )

        _validate_product_for_invoice(product)
        
        # Check stock availability
        if not product.reduce_stock(item_data.quantity):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient stock for product '{product.name}'. Available: {product.stock_quantity}, Required: {item_data.quantity}"
            )
        
        # Calculate tax for this line item
        tax_breakup = calculate_line_item_tax(
            quantity=item_data.quantity,
            unit_price_paise=product.price_paise,
            gst_rate=product.gst_rate,
            seller_state_code=business.state_code,
            buyer_state_code=customer.state_code
        )
        line_tax_breakups.append(tax_breakup)
        
        # Create invoice item with snapshot
        invoice_item = InvoiceItem(
            product_id=product.id,
            product_name=product.name,
            description=item_data.description or product.description,
            hsn_code=product.hsn_code,
            quantity=item_data.quantity,
            unit=product.unit,
            unit_price_paise=product.price_paise,
            gst_rate=product.gst_rate,
            taxable_amount_paise=tax_breakup["taxable_amount_paise"],
            cgst_paise=tax_breakup["cgst_paise"],
            sgst_paise=tax_breakup["sgst_paise"],
            igst_paise=tax_breakup["igst_paise"],
            gst_amount_paise=tax_breakup["total_tax_paise"],
            total_paise=tax_breakup["total_amount_paise"]
        )
        invoice.items.append(invoice_item)
    
    # Aggregate totals
    invoice_totals = aggregate_invoice_taxes(line_tax_breakups)
    _validate_client_totals(invoice_data.client_totals, invoice_totals)
    invoice.subtotal_paise = invoice_totals["taxable_amount_paise"]
    invoice.cgst_paise = invoice_totals["cgst_paise"]
    invoice.sgst_paise = invoice_totals["sgst_paise"]
    invoice.igst_paise = invoice_totals["igst_paise"]
    invoice.total_paise = invoice_totals["total_amount_paise"]
    invoice.total_taxable_value_paise = invoice_totals["taxable_amount_paise"]
    invoice.total_gst_paise = invoice_totals["total_tax_paise"]
    invoice.grand_total_paise = invoice_totals["total_amount_paise"]
    invoice.round_off_paise = 0

    # Assign invoice number post-validation to minimize gaps
    invoice.invoice_number = business.generate_invoice_number()
    
    # Save to database
    db.add(invoice)
    db.commit()
    db.refresh(invoice)
    
    return invoice


def _create_customer_snapshot(customer: Customer) -> dict:
    """Create customer data snapshot for invoice"""
    return {
        "id": customer.id,
        "name": customer.name,
        "gstin": customer.gstin,
        "state_code": customer.state_code,
        "address": customer.address,
        "city": getattr(customer, "city", None),
        "pincode": getattr(customer, "pincode", None),
        "phone": customer.phone,
        "email": customer.email
    }


def _create_business_snapshot(business: BusinessProfile) -> dict:
    """Create business data snapshot for invoice"""
    return {
        "id": business.id,
        "name": business.name,
        "gstin": business.gstin,
        "state_code": business.state_code,
        "address": business.address,
        "city": business.city,
        "pincode": business.pincode,
        "phone": business.phone,
        "email": business.email
    }


def cancel_invoice(
    db: Session,
    invoice_id: int,
    reason: str = ""
) -> Invoice:
    """
    Cancel an invoice (soft delete).
    
    Note: Does NOT restore stock quantities.
    
    Args:
        db: Database session
        invoice_id: Invoice ID to cancel
        reason: Cancellation reason
        
    Returns:
        Cancelled Invoice object
        
    Raises:
        HTTPException: If invoice not found or already cancelled
    """
    invoice = db.query(Invoice).filter(Invoice.id == invoice_id).first()
    
    if not invoice:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Invoice with id {invoice_id} not found"
        )
    
    if invoice.is_cancelled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invoice {invoice.invoice_number} is already cancelled"
        )
    
    # Restore stock quantities
    for item in invoice.items:
        if item.product_id:
            product = db.query(Product).filter(Product.id == item.product_id).first()
            if product:
                product.stock_quantity += item.quantity
    
    invoice.cancel(reason)
    invoice.status = "CANCELLED"
    db.commit()
    db.refresh(invoice)
    
    return invoice


def get_invoice_by_id(db: Session, invoice_id: int) -> Invoice | None:
    """Get invoice by ID with all relationships loaded"""
    return db.query(Invoice).filter(Invoice.id == invoice_id).first()


def get_invoice_by_number(db: Session, invoice_number: str) -> Invoice | None:
    """Get invoice by invoice number"""
    return db.query(Invoice).filter(Invoice.invoice_number == invoice_number).first()


def list_invoices(
    db: Session,
    skip: int = 0,
    limit: int = 100,
    include_cancelled: bool = False
) -> list[Invoice]:
    """List invoices with pagination"""
    query = db.query(Invoice)
    
    if not include_cancelled:
        query = query.filter(Invoice.is_cancelled == False)
    
    return query.order_by(Invoice.created_at.desc()).offset(skip).limit(limit).all()


def render_invoice_pdf(db: Session, invoice_id: int) -> tuple[bytes, str]:
    """Render invoice as PDF using stored snapshot values."""
    invoice = get_invoice_by_id(db, invoice_id)
    if not invoice:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=f"Invoice with id {invoice_id} not found")

    global HTML
    if HTML is None:
        try:
            from weasyprint import HTML as _HTML
            HTML = _HTML
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="PDF generation unavailable: weasyprint not installed"
            ) from exc

    html = _render_invoice_html(invoice)
    pdf_bytes = HTML(string=html).write_pdf()
    filename = f"invoice_{invoice.invoice_number}.pdf" if invoice.invoice_number else f"invoice_{invoice.id}.pdf"
    return pdf_bytes, filename


def _validate_invoice_date(invoice_date: date) -> None:
    """Ensure invoice date is not in the future."""
    if invoice_date > date.today():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invoice date cannot be in the future"
        )


def _validate_business_profile(business: BusinessProfile) -> None:
    """Validate minimal business profile requirements for invoicing."""
    if not business.state_code or len(business.state_code) != 2:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid business state code. Please configure a valid 2-digit state code."
        )


def _validate_customer_for_invoice(customer: Customer) -> None:
    """Validate customer GST requirements before invoicing."""
    if customer.is_b2b:
        if not customer.gstin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="B2B customer must have a valid GSTIN"
            )
        gst_state = extract_state_code_from_gstin(customer.gstin)
        if gst_state != customer.state_code:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Customer GSTIN state code does not match stored state code"
            )
    else:
        if customer.gstin:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="B2C customers cannot have GSTIN"
            )


def _validate_product_for_invoice(product: Product) -> None:
    """Validate product tax attributes before invoicing."""
    if Decimal(product.gst_rate) not in ALLOWED_GST_RATES:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid GST rate {product.gst_rate}. Allowed rates: {sorted(ALLOWED_GST_RATES)}"
        )
    if not validate_hsn_code(str(product.hsn_code)):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid HSN code for product"
        )
    if product.price_paise < 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Product price cannot be negative"
        )


def _validate_client_totals(client_totals: dict | None, computed: TaxBreakup) -> None:
    """Reject manipulated frontend totals if provided (rupees)."""
    if not client_totals:
        return
    # Convert paise to rupees for comparison
    taxable_rupees = Decimal(computed["taxable_amount_paise"]) / 100
    gst_rupees = Decimal(computed["total_tax_paise"]) / 100
    grand_rupees = Decimal(computed["total_amount_paise"]) / 100
    if (
        taxable_rupees != client_totals.total_taxable_value
        or gst_rupees != client_totals.total_gst
        or grand_rupees != client_totals.grand_total
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Provided totals do not match server-calculated totals"
        )


def _render_invoice_html(invoice: Invoice) -> str:
    """Simple HTML template for PDF rendering (values already snapshot)."""
    rows = "".join(
        f"""
        <tr>
            <td>{item.item_name}</td>
            <td>{item.hsn_code}</td>
            <td style='text-align:right'>{item.quantity}</td>
            <td style='text-align:right'>{item.rate}</td>
            <td style='text-align:right'>{item.taxable_value}</td>
            <td style='text-align:right'>{item.gst_amount}</td>
            <td style='text-align:right'>{item.total}</td>
        </tr>
        """
        for item in invoice.items
    )

    html = f"""
    <html>
    <head>
        <style>
            body {{ font-family: Arial, sans-serif; }}
            table {{ width: 100%; border-collapse: collapse; }}
            th, td {{ border: 1px solid #444; padding: 6px; font-size: 12px; }}
            th {{ background: #f2f2f2; }}
        </style>
    </head>
    <body>
        <h2 style='text-align:center'>TAX INVOICE</h2>
        <p><strong>Invoice No:</strong> {invoice.invoice_number} &nbsp; <strong>Date:</strong> {invoice.invoice_date}</p>
        <p><strong>Seller:</strong> {invoice.business_snapshot.get('name','')} | GSTIN: {invoice.business_snapshot.get('gstin','')} | State: {invoice.business_snapshot.get('state_code','')}</p>
        <p><strong>Buyer:</strong> {invoice.customer_snapshot.get('name','')} | GSTIN: {invoice.customer_snapshot.get('gstin','') or 'NA'} | State: {invoice.customer_snapshot.get('state_code','')}</p>
        <table>
            <thead>
                <tr>
                    <th>Item</th><th>HSN</th><th>Qty</th><th>Rate</th><th>Taxable</th><th>GST</th><th>Total</th>
                </tr>
            </thead>
            <tbody>
                {rows}
            </tbody>
        </table>
        <p><strong>Taxable Value:</strong> {invoice.total_taxable_value} &nbsp; <strong>Total GST:</strong> {invoice.total_gst} &nbsp; <strong>Grand Total:</strong> {invoice.grand_total}</p>
        <p><strong>CGST:</strong> {invoice.cgst} &nbsp; <strong>SGST:</strong> {invoice.sgst} &nbsp; <strong>IGST:</strong> {invoice.igst}</p>
        <p>Authorized Signatory</p>
    </body>
    </html>
    """
    return html
