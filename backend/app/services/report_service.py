"""Report generation service for GST billing system

CORE PRINCIPLE:
- Reports ONLY from saved invoices and purchases
- NEVER recalculate GST from master data
- Use stored tax snapshots ONLY
"""

from datetime import date
from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func

from app.models.invoice import Invoice
from app.models.purchase import PurchaseInvoice
from app.models.customer import Customer
from app.models.supplier import Supplier
from app.models.product import Product
from app.models.business import BusinessProfile

from app.schemas.report import (
    SalesRegisterRow, SalesRegisterSummary, SalesRegisterResponse,
    PurchaseRegisterRow, PurchaseRegisterSummary, PurchaseRegisterResponse,
    GSTSummaryOutput, GSTSummaryInput, GSTSummaryResponse,
    CustomerReportRow, CustomerReportSummary, CustomerReportResponse,
    SupplierReportRow, SupplierReportSummary, SupplierReportResponse,
    ProductHSNReportRow, ProductHSNReportSummary, ProductHSNReportResponse,
    InventoryReportRow, InventoryReportResponse,
    BusinessSummaryLedger,
    GSTRReadyB2B, GSTRReadyB2C, GSTRReadyHSN, GSTRReadyResponse,
    ReportFilters
)


def generate_sales_register(
    db: Session,
    from_date: date,
    to_date: date,
    include_cancelled: bool = False,
    customer_id: Optional[int] = None
) -> SalesRegisterResponse:
    """
    Generate sales register report from saved invoices ONLY.
    
    Rules:
    - Cancelled invoices appear in list but NOT in totals (unless include_cancelled=True)
    - Use stored invoice totals (never recalculate)
    - All amounts in rupees (convert from paise)
    """
    # Base query - FINALIZED invoices only
    query = db.query(Invoice).filter(
        and_(
            Invoice.invoice_date >= from_date,
            Invoice.invoice_date <= to_date,
            Invoice.status.in_(['FINAL', 'CANCELLED'])
        )
    )
    
    if customer_id:
        query = query.filter(Invoice.customer_id == customer_id)
    
    invoices = query.order_by(Invoice.invoice_date, Invoice.invoice_number).all()
    
    rows: List[SalesRegisterRow] = []
    
    # Accumulators for totals (exclude CANCELLED unless explicitly included)
    total_taxable = 0.0
    total_cgst = 0.0
    total_sgst = 0.0
    total_igst = 0.0
    total_gst = 0.0
    total_grand = 0.0
    count_cancelled = 0
    
    for inv in invoices:
        # Determine GST breakdown from stored snapshot
        cgst_amount = 0.0
        sgst_amount = 0.0
        igst_amount = 0.0
        
        # Get business state to determine tax type
        business = db.query(BusinessProfile).first()
        
        # Convert Decimal to float
        taxable_val = float(inv.total_taxable_value_rupees)
        gst_val = float(inv.total_gst_rupees)
        
        if business and inv.place_of_supply == business.state_code:
            # Intra-state: CGST + SGST
            cgst_amount = gst_val / 2
            sgst_amount = gst_val / 2
        else:
            # Inter-state: IGST
            igst_amount = gst_val
        
        row = SalesRegisterRow(
            invoice_number=inv.invoice_number,
            invoice_date=inv.invoice_date,
            customer_name=inv.customer_snapshot.get('name', 'Unknown'),
            customer_gstin=inv.customer_snapshot.get('gstin'),
            place_of_supply=inv.place_of_supply,
            taxable_value=taxable_val,
            cgst=cgst_amount,
            sgst=sgst_amount,
            igst=igst_amount,
            total_gst=gst_val,
            grand_total=float(inv.grand_total_rupees),
            status=inv.status
        )
        rows.append(row)
        
        # Add to totals only if not cancelled (or if include_cancelled=True)
        if inv.status != 'CANCELLED' or include_cancelled:
            total_taxable += taxable_val
            total_cgst += cgst_amount
            total_sgst += sgst_amount
            total_igst += igst_amount
            total_gst += gst_val
            total_grand += float(inv.grand_total_rupees)
        
        if inv.status == 'CANCELLED':
            count_cancelled += 1
    
    summary = SalesRegisterSummary(
        total_taxable_value=round(total_taxable, 2),
        total_cgst=round(total_cgst, 2),
        total_sgst=round(total_sgst, 2),
        total_igst=round(total_igst, 2),
        total_gst=round(total_gst, 2),
        total_grand_total=round(total_grand, 2),
        count_invoices=len(invoices),
        count_cancelled=count_cancelled
    )
    
    return SalesRegisterResponse(
        from_date=from_date,
        to_date=to_date,
        rows=rows,
        summary=summary
    )


def generate_purchase_register(
    db: Session,
    from_date: date,
    to_date: date,
    include_cancelled: bool = False,
    supplier_id: Optional[int] = None
) -> PurchaseRegisterResponse:
    """
    Generate purchase register report from saved purchase invoices ONLY.
    
    Rules:
    - Cancelled purchases appear in list but NOT in totals (unless include_cancelled=True)
    - Use stored purchase totals (never recalculate)
    - All amounts in rupees (convert from paise)
    """
    # Base query - FINALIZED purchases only
    query = db.query(PurchaseInvoice).filter(
        and_(
            PurchaseInvoice.purchase_date >= from_date,
            PurchaseInvoice.purchase_date <= to_date,
            PurchaseInvoice.status.in_(['FINAL', 'CANCELLED'])
        )
    )
    
    if supplier_id:
        query = query.filter(PurchaseInvoice.supplier_id == supplier_id)
    
    purchases = query.order_by(PurchaseInvoice.purchase_date, PurchaseInvoice.supplier_invoice_no).all()
    
    rows: List[PurchaseRegisterRow] = []
    
    # Accumulators for totals
    total_taxable = 0.0
    total_cgst = 0.0
    total_sgst = 0.0
    total_igst = 0.0
    total_gst = 0.0
    total_grand = 0.0
    count_cancelled = 0
    
    for purchase in purchases:
        # Determine GST breakdown (same logic as sales)
        cgst_amount = 0.0
        sgst_amount = 0.0
        igst_amount = 0.0
        
        business = db.query(BusinessProfile).first()
        
        # Convert Decimal to float
        taxable_val = float(purchase.total_taxable_value_rupees)
        gst_val = float(purchase.total_gst_rupees)
        
        if business and purchase.place_of_supply == business.state_code:
            # Intra-state: CGST + SGST
            cgst_amount = gst_val / 2
            sgst_amount = gst_val / 2
        else:
            # Inter-state: IGST
            igst_amount = gst_val
        
        row = PurchaseRegisterRow(
            supplier_name=purchase.supplier_snapshot.get('name', 'Unknown'),
            supplier_gstin=purchase.supplier_snapshot.get('gstin'),
            supplier_invoice_number=purchase.supplier_invoice_no,
            invoice_date=purchase.supplier_invoice_date.date() if purchase.supplier_invoice_date else purchase.purchase_date.date(),
            taxable_value=taxable_val,
            input_cgst=cgst_amount,
            input_sgst=sgst_amount,
            input_igst=igst_amount,
            total_input_gst=gst_val,
            grand_total=float(purchase.grand_total_rupees),
            status=purchase.status
        )
        rows.append(row)
        
        # Add to totals only if not cancelled (or if include_cancelled=True)
        if purchase.status != 'CANCELLED' or include_cancelled:
            total_taxable += taxable_val
            total_cgst += cgst_amount
            total_sgst += sgst_amount
            total_igst += igst_amount
            total_gst += gst_val
            total_grand += float(purchase.grand_total_rupees)
        
        if purchase.status == 'CANCELLED':
            count_cancelled += 1
    
    summary = PurchaseRegisterSummary(
        total_taxable_value=round(total_taxable, 2),
        total_input_cgst=round(total_cgst, 2),
        total_input_sgst=round(total_sgst, 2),
        total_input_igst=round(total_igst, 2),
        total_input_gst=round(total_gst, 2),
        total_grand_total=round(total_grand, 2),
        count_purchases=len(purchases),
        count_cancelled=count_cancelled
    )
    
    return PurchaseRegisterResponse(
        from_date=from_date,
        to_date=to_date,
        rows=rows,
        summary=summary
    )


def generate_gst_summary(
    db: Session,
    from_date: date,
    to_date: date
) -> GSTSummaryResponse:
    """
    Generate GST summary for a date range from saved invoices and purchases.
    
    Rules:
    - Output GST = sum of sales invoices (FINAL only, exclude CANCELLED)
    - Input GST = sum of purchase invoices (FINAL only, exclude CANCELLED)
    - NO ITC offset calculation
    - NO payable GST calculation
    """
    
    # Query sales invoices
    sales = db.query(Invoice).filter(
        and_(
            Invoice.invoice_date >= from_date,
            Invoice.invoice_date <= to_date,
            Invoice.status == 'FINAL'
        )
    ).all()
    
    # Query purchase invoices
    purchases = db.query(PurchaseInvoice).filter(
        and_(
            PurchaseInvoice.purchase_date >= from_date,
            PurchaseInvoice.purchase_date <= to_date,
            PurchaseInvoice.status == 'FINAL'
        )
    ).all()
    
    # Calculate output GST (sales)
    output_cgst = 0.0
    output_sgst = 0.0
    output_igst = 0.0
    
    business = db.query(BusinessProfile).first()
    
    for inv in sales:
        if business and inv.place_of_supply == business.state_code:
            # Intra-state: CGST + SGST
            output_cgst += float(inv.total_gst_rupees) / 2
            output_sgst += float(inv.total_gst_rupees) / 2
        else:
            # Inter-state: IGST
            output_igst += float(inv.total_gst_rupees)
    
    # Calculate input GST (purchases)
    input_cgst = 0.0
    input_sgst = 0.0
    input_igst = 0.0
    
    for purchase in purchases:
        if business and purchase.place_of_supply == business.state_code:
            # Intra-state: CGST + SGST
            input_cgst += float(purchase.total_gst_rupees) / 2
            input_sgst += float(purchase.total_gst_rupees) / 2
        else:
            # Inter-state: IGST
            input_igst += float(purchase.total_gst_rupees)
    
    output_gst = GSTSummaryOutput(
        cgst=round(output_cgst, 2),
        sgst=round(output_sgst, 2),
        igst=round(output_igst, 2),
        total=round(output_cgst + output_sgst + output_igst, 2)
    )
    
    input_gst = GSTSummaryInput(
        cgst=round(input_cgst, 2),
        sgst=round(input_sgst, 2),
        igst=round(input_igst, 2),
        total=round(input_cgst + input_sgst + input_igst, 2)
    )
    
    return GSTSummaryResponse(
        month=to_date.month,
        year=to_date.year,
        output_gst=output_gst,
        input_gst=input_gst,
        sales_count=len(sales),
        purchase_count=len(purchases)
    )


def generate_customer_report(
    db: Session,
    from_date: date,
    to_date: date,
    customer_id: Optional[int] = None
) -> CustomerReportResponse:
    """
    Generate customer-wise sales summary from saved invoices ONLY.
    
    Groups sales by customer with B2B vs B2C breakdown.
    Optional: Filter by specific customer_id.
    """
    # Get all customers with sales in date range
    query = db.query(Invoice).filter(
        and_(
            Invoice.invoice_date >= from_date,
            Invoice.invoice_date <= to_date,
            Invoice.status == 'FINAL'
        )
    )
    
    if customer_id:
        query = query.filter(Invoice.customer_id == customer_id)
    
    invoices = query.all()
    
    # Group by customer
    customer_data = {}
    business = db.query(BusinessProfile).first()
    
    for inv in invoices:
        cust_id = inv.customer_id
        if cust_id not in customer_data:
            cust = db.query(Customer).filter(Customer.id == cust_id).first()
            if cust:
                customer_data[cust_id] = {
                    'name': cust.name,
                    'type': cust.customer_type,
                    'gstin': cust.gstin,
                    'invoices': [],
                    'total_sales': 0.0,
                    'total_taxable': 0.0,
                    'total_cgst': 0.0,
                    'total_sgst': 0.0,
                    'total_igst': 0.0,
                    'total_gst': 0.0
                }
        
        if cust_id in customer_data:
            # Calculate GST breakdown
            cgst = sgst = igst = 0.0
            gst_val = float(inv.total_gst_rupees)
            if business and inv.place_of_supply == business.state_code:
                cgst = gst_val / 2
                sgst = gst_val / 2
            else:
                igst = gst_val
            
            customer_data[cust_id]['invoices'].append(inv.invoice_number)
            customer_data[cust_id]['total_sales'] += float(inv.grand_total_rupees)
            customer_data[cust_id]['total_taxable'] += float(inv.total_taxable_value_rupees)
            customer_data[cust_id]['total_cgst'] += cgst
            customer_data[cust_id]['total_sgst'] += sgst
            customer_data[cust_id]['total_igst'] += igst
            customer_data[cust_id]['total_gst'] += gst_val
    
    # Build rows
    rows: List[CustomerReportRow] = []
    total_b2b = 0.0
    total_b2c = 0.0
    total_gst_collected = 0.0
    
    for cust_id, data in customer_data.items():
        row = CustomerReportRow(
            customer_id=cust_id,
            customer_name=data['name'],
            customer_type=data['type'],
            customer_gstin=data['gstin'],
            total_invoices=len(data['invoices']),
            total_sales_value=round(data['total_sales'], 2),
            total_taxable_value=round(data['total_taxable'], 2),
            total_cgst=round(data['total_cgst'], 2),
            total_sgst=round(data['total_sgst'], 2),
            total_igst=round(data['total_igst'], 2),
            total_gst_collected=round(data['total_gst'], 2)
        )
        rows.append(row)
        
        if data['type'] == 'B2B':
            total_b2b += data['total_sales']
        else:
            total_b2c += data['total_sales']
        total_gst_collected += data['total_gst']
    
    # Calculate totals
    total_sales = sum(d['total_sales'] for d in customer_data.values())
    total_taxable = sum(d['total_taxable'] for d in customer_data.values())
    
    summary = CustomerReportSummary(
        total_customers=len(customer_data),
        total_invoices=len(invoices),
        b2b_sales=round(total_b2b, 2),
        b2c_sales=round(total_b2c, 2),
        total_sales_value=round(total_sales, 2),
        total_taxable_value=round(total_taxable, 2),
        total_gst_collected=round(total_gst_collected, 2)
    )
    
    return CustomerReportResponse(
        from_date=from_date,
        to_date=to_date,
        rows=sorted(rows, key=lambda x: x.customer_name),
        summary=summary
    )


def generate_supplier_report(
    db: Session,
    from_date: date,
    to_date: date,
    supplier_id: Optional[int] = None
) -> SupplierReportResponse:
    """
    Generate supplier-wise purchase summary from saved purchases ONLY.
    
    Groups purchases by supplier with Registered vs Unregistered split.
    Optional: Filter by specific supplier_id.
    """
    # Get all purchases in date range
    query = db.query(PurchaseInvoice).filter(
        and_(
            PurchaseInvoice.purchase_date >= from_date,
            PurchaseInvoice.purchase_date <= to_date,
            PurchaseInvoice.status == 'FINAL'
        )
    )
    
    if supplier_id:
        query = query.filter(PurchaseInvoice.supplier_id == supplier_id)
    
    purchases = query.all()
    
    # Group by supplier
    supplier_data = {}
    business = db.query(BusinessProfile).first()
    
    for purch in purchases:
        supp_id = purch.supplier_id
        if supp_id not in supplier_data:
            supp = db.query(Supplier).filter(Supplier.id == supp_id).first()
            if supp:
                is_registered = bool(supp.gstin)
                supplier_data[supp_id] = {
                    'name': supp.name,
                    'type': 'Registered' if is_registered else 'Unregistered',
                    'gstin': supp.gstin,
                    'purchases': [],
                    'total_value': 0.0,
                    'total_taxable': 0.0,
                    'total_cgst': 0.0,
                    'total_sgst': 0.0,
                    'total_igst': 0.0,
                    'total_gst': 0.0
                }
        
        if supp_id in supplier_data:
            # Calculate GST breakdown
            cgst = sgst = igst = 0.0
            gst_val = float(purch.total_gst_rupees)
            if business and purch.place_of_supply == business.state_code:
                cgst = gst_val / 2
                sgst = gst_val / 2
            else:
                igst = gst_val
            
            supplier_data[supp_id]['purchases'].append(purch.supplier_invoice_no)
            supplier_data[supp_id]['total_value'] += float(purch.grand_total_rupees)
            supplier_data[supp_id]['total_taxable'] += float(purch.total_taxable_value_rupees)
            supplier_data[supp_id]['total_cgst'] += cgst
            supplier_data[supp_id]['total_sgst'] += sgst
            supplier_data[supp_id]['total_igst'] += igst
            supplier_data[supp_id]['total_gst'] += gst_val
    
    # Build rows
    rows: List[SupplierReportRow] = []
    total_registered = 0.0
    total_unregistered = 0.0
    total_input_gst = 0.0
    
    for supp_id, data in supplier_data.items():
        row = SupplierReportRow(
            supplier_id=supp_id,
            supplier_name=data['name'],
            supplier_type=data['type'],
            supplier_gstin=data['gstin'],
            total_purchases=len(data['purchases']),
            total_purchase_value=round(data['total_value'], 2),
            total_taxable_value=round(data['total_taxable'], 2),
            total_input_cgst=round(data['total_cgst'], 2),
            total_input_sgst=round(data['total_sgst'], 2),
            total_input_igst=round(data['total_igst'], 2),
            total_input_gst_paid=round(data['total_gst'], 2)
        )
        rows.append(row)
        
        if data['type'] == 'Registered':
            total_registered += data['total_value']
        else:
            total_unregistered += data['total_value']
        total_input_gst += data['total_gst']
    
    total_value = sum(d['total_value'] for d in supplier_data.values())
    
    summary = SupplierReportSummary(
        total_suppliers=len(supplier_data),
        total_purchases=len(purchases),
        registered_purchases=round(total_registered, 2),
        unregistered_purchases=round(total_unregistered, 2),
        total_purchase_value=round(total_value, 2),
        total_input_gst_paid=round(total_input_gst, 2)
    )
    
    return SupplierReportResponse(
        from_date=from_date,
        to_date=to_date,
        rows=sorted(rows, key=lambda x: x.supplier_name),
        summary=summary
    )


def generate_product_hsn_report(
    db: Session,
    from_date: date,
    to_date: date,
    product_id: Optional[int] = None
) -> ProductHSNReportResponse:
    """
    Generate product/HSN-wise sales summary for GSTR-1 preparation.
    
    Aggregates quantity sold and GST collected by HSN code.
    Optional: Filter by specific product_id.
    """
    from app.models.invoice import InvoiceItem
    
    # Get all invoice items in date range from FINAL invoices
    query = db.query(InvoiceItem).join(Invoice).filter(
        and_(
            Invoice.invoice_date >= from_date,
            Invoice.invoice_date <= to_date,
            Invoice.status == 'FINAL'
        )
    )
    
    if product_id:
        query = query.filter(InvoiceItem.product_id == product_id)
    
    items = query.all()
    
    # Group by product/HSN
    product_data = {}
    
    for item in items:
        prod = db.query(Product).filter(Product.id == item.product_id).first()
        if not prod:
            continue
        
        key = (prod.id, prod.name, prod.hsn_code, prod.gst_rate, prod.unit)
        if key not in product_data:
            product_data[key] = {
                'quantity': 0.0,
                'taxable': 0.0,
                'gst': 0.0
            }
        
        product_data[key]['quantity'] += item.quantity
        product_data[key]['taxable'] += float(item.taxable_value)
        product_data[key]['gst'] += float(item.gst_amount_rupees)
    
    # Build rows
    rows: List[ProductHSNReportRow] = []
    total_qty = 0.0
    total_taxable = 0.0
    total_gst = 0.0
    
    for (prod_id, name, hsn, rate, unit), data in product_data.items():
        row = ProductHSNReportRow(
            product_id=prod_id,
            product_name=name,
            hsn_code=hsn,
            gst_rate=rate,
            quantity_sold=round(data['quantity'], 2),
            unit=unit,
            taxable_value=round(data['taxable'], 2),
            total_gst_collected=round(data['gst'], 2)
        )
        rows.append(row)
        total_qty += data['quantity']
        total_taxable += data['taxable']
        total_gst += data['gst']
    
    summary = ProductHSNReportSummary(
        total_products=len(product_data),
        total_quantity=round(total_qty, 2),
        total_taxable_value=round(total_taxable, 2),
        total_gst_collected=round(total_gst, 2)
    )
    
    return ProductHSNReportResponse(
        from_date=from_date,
        to_date=to_date,
        rows=sorted(rows, key=lambda x: x.hsn_code),
        summary=summary
    )


def generate_inventory_report(
    db: Session,
    as_of_date: date,
) -> InventoryReportResponse:
    """
    Generate inventory report as of a specific date.
    
    Shows opening stock, purchases, sales, and closing stock per product.
    Note: No FIFO/LIFO valuation in Phase-1.
    """
    from app.models.invoice import InvoiceItem
    
    products = db.query(Product).filter(Product.is_active == True).all()
    
    rows: List[InventoryReportRow] = []
    
    for prod in products:
        # Opening stock = stock_quantity (as of report date)
        # In Phase-1, we don't track stock history, so use current stock
        opening = prod.stock_quantity
        
        # Get sales before report date
        sale_items = db.query(InvoiceItem).join(Invoice).filter(
            and_(
                InvoiceItem.product_id == prod.id,
                Invoice.invoice_date <= as_of_date,
                Invoice.status == 'FINAL'
            )
        ).all()
        sold_qty = sum(si.quantity for si in sale_items)
        
        # Note: In Phase-1, we don't track purchases by product (PurchaseItem has no product_id)
        # So purchased_qty = 0. To track purchases, product_id must be added to PurchaseItem model.
        purchased_qty = 0.0
        
        # Closing = opening + purchased - sold
        closing = opening + purchased_qty - sold_qty
        
        row = InventoryReportRow(
            product_id=prod.id,
            product_name=prod.name,
            hsn_code=prod.hsn_code,
            unit=prod.unit,
            opening_stock=round(opening, 2),
            purchased_quantity=round(purchased_qty, 2),
            sold_quantity=round(sold_qty, 2),
            closing_stock=round(closing, 2)
        )
        rows.append(row)
    
    return InventoryReportResponse(
        as_of_date=as_of_date,
        rows=rows
    )


def generate_business_summary_ledger(
    db: Session,
    from_date: date,
    to_date: date,
) -> BusinessSummaryLedger:
    """
    Generate business summary ledger (informational only).
    
    NOT a statutory accounting ledger. Shows total sales, purchases, and GST position.
    """
    # Get all invoices and purchases
    invoices = db.query(Invoice).filter(
        and_(
            Invoice.invoice_date >= from_date,
            Invoice.invoice_date <= to_date,
            Invoice.status == 'FINAL'
        )
    ).all()
    
    purchases = db.query(PurchaseInvoice).filter(
        and_(
            PurchaseInvoice.purchase_date >= from_date,
            PurchaseInvoice.purchase_date <= to_date,
            PurchaseInvoice.status == 'FINAL'
        )
    ).all()
    
    business = db.query(BusinessProfile).first()
    
    # Calculate totals
    total_sales = sum(float(inv.grand_total_rupees) for inv in invoices)
    total_purchases = sum(float(p.grand_total_rupees) for p in purchases)
    
    # Calculate output GST
    output_gst = 0.0
    for inv in invoices:
        output_gst += float(inv.total_gst_rupees)
    
    # Calculate input GST
    input_gst = 0.0
    for p in purchases:
        input_gst += float(p.total_gst_rupees)
    
    # Net GST position (informational - not ITC offset)
    net_gst = output_gst - input_gst
    
    from_str = from_date.strftime('%b %Y')
    to_str = to_date.strftime('%b %Y')
    period = f"{from_str} to {to_str}"
    
    return BusinessSummaryLedger(
        period=period,
        total_sales=round(total_sales, 2),
        total_purchases=round(total_purchases, 2),
        total_output_gst=round(output_gst, 2),
        total_input_gst=round(input_gst, 2),
        net_gst_position=round(net_gst, 2)
    )


def generate_gstr_ready_export(
    db: Session,
    from_date: date,
    to_date: date,
) -> GSTRReadyResponse:
    """
    Generate GSTR-1 ready export (preparation only).
    
    Exports B2B invoices, B2C summary, and HSN summary in GSTR-1 format.
    Manual filing on gst.gov.in required.
    """
    from datetime import datetime
    
    # Get invoices
    invoices = db.query(Invoice).filter(
        and_(
            Invoice.invoice_date >= from_date,
            Invoice.invoice_date <= to_date,
            Invoice.status == 'FINAL'
        )
    ).all()
    
    # Separate B2B and B2C
    b2b_invoices: List[GSTRReadyB2B] = []
    b2c_data = {}  # State-wise B2C summary
    business = db.query(BusinessProfile).first()
    
    for inv in invoices:
        cust = db.query(Customer).filter(Customer.id == inv.customer_id).first()
        if not cust:
            continue
        
        # Determine GST breakdown
        cgst = sgst = igst = 0.0
        if business and inv.place_of_supply == business.state_code:
            cgst = float(inv.total_gst_rupees) / 2
            sgst = float(inv.total_gst_rupees) / 2
        else:
            igst = float(inv.total_gst_rupees)
        
        if cust.customer_type == 'B2B' and cust.gstin:
            # B2B with GSTIN
            b2b = GSTRReadyB2B(
                invoice_number=inv.invoice_number,
                invoice_date=inv.invoice_date,
                customer_name=cust.name,
                customer_gstin=cust.gstin,
                taxable_value=round(float(inv.total_taxable_value_rupees), 2),
                cgst=round(cgst, 2),
                sgst=round(sgst, 2),
                igst=round(igst, 2),
                total_value=round(float(inv.grand_total_rupees), 2)
            )
            b2b_invoices.append(b2b)
        else:
            # B2B without GSTIN or B2C - group by state
            state = inv.place_of_supply
            if state not in b2c_data:
                b2c_data[state] = {
                    'taxable': 0.0,
                    'cgst': 0.0,
                    'sgst': 0.0,
                    'igst': 0.0,
                    'total': 0.0
                }
            b2c_data[state]['taxable'] += float(inv.total_taxable_value_rupees)
            b2c_data[state]['cgst'] += cgst
            b2c_data[state]['sgst'] += sgst
            b2c_data[state]['igst'] += igst
            b2c_data[state]['total'] += float(inv.grand_total_rupees)
    
    b2c_invoices: List[GSTRReadyB2C] = []
    for state, data in b2c_data.items():
        b2c = GSTRReadyB2C(
            invoice_date=to_date,
            state_code=state,
            taxable_value=round(data['taxable'], 2),
            cgst=round(data['cgst'], 2),
            sgst=round(data['sgst'], 2),
            igst=round(data['igst'], 2),
            total_value=round(data['total'], 2)
        )
        b2c_invoices.append(b2c)
    
    # Generate HSN summary
    from app.models.invoice import InvoiceItem
    hsn_data = {}
    
    items = db.query(InvoiceItem).join(Invoice).filter(
        and_(
            Invoice.invoice_date >= from_date,
            Invoice.invoice_date <= to_date,
            Invoice.status == 'FINAL'
        )
    ).all()
    
    for item in items:
        prod = db.query(Product).filter(Product.id == item.product_id).first()
        if not prod:
            continue
        
        key = (prod.hsn_code, prod.gst_rate)
        if key not in hsn_data:
            hsn_data[key] = {
                'quantity': 0.0,
                'taxable': 0.0,
                'cgst': 0.0,
                'sgst': 0.0,
                'igst': 0.0,
                'total': 0.0
            }
        
        hsn_data[key]['quantity'] += item.quantity
        hsn_data[key]['taxable'] += float(item.taxable_value)
        
        # Determine GST breakdown
        inv = db.query(Invoice).filter(Invoice.id == item.invoice_id).first()
        if business and inv and inv.place_of_supply == business.state_code:
            hsn_data[key]['cgst'] += float(item.gst_amount_rupees) / 2
            hsn_data[key]['sgst'] += float(item.gst_amount_rupees) / 2
        else:
            hsn_data[key]['igst'] += float(item.gst_amount_rupees)
        
        hsn_data[key]['total'] += float(item.taxable_value) + float(item.gst_amount_rupees)
    
    hsn_invoices: List[GSTRReadyHSN] = []
    total_output_gst = 0.0
    
    for (hsn, rate), data in hsn_data.items():
        hsn_row = GSTRReadyHSN(
            hsn_code=hsn,
            quantity=round(data['quantity'], 2),
            unit='UNIT',  # Simplified
            taxable_value=round(data['taxable'], 2),
            cgst_rate=rate // 2,  # Simplified
            cgst=round(data['cgst'], 2),
            sgst_rate=rate // 2,
            sgst=round(data['sgst'], 2),
            igst_rate=rate,
            igst=round(data['igst'], 2),
            total_value=round(data['total'], 2)
        )
        hsn_invoices.append(hsn_row)
        total_output_gst += data['cgst'] + data['sgst'] + data['igst']
    
    period = f"{from_date.strftime('%b %Y')} to {to_date.strftime('%b %Y')}"
    
    return GSTRReadyResponse(
        period=period,
        b2b_invoices=b2b_invoices,
        b2c_summary=b2c_invoices,
        hsn_summary=hsn_invoices,
        total_output_gst=round(total_output_gst, 2)
    )
