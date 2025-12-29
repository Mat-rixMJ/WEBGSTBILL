"""GST calculation service for purchase invoices (INPUT GST / ITC)"""

from typing import List, Tuple, NamedTuple
from app.config import settings


class PurchaseItemTax(NamedTuple):
    """Calculated tax for a purchase item"""
    subtotal: int  # In paise
    cgst_amount: int  # In paise
    sgst_amount: int  # In paise
    igst_amount: int  # In paise
    total_amount: int  # In paise
    tax_type: str  # "CGST_SGST" or "IGST"


def calculate_purchase_item_tax(
    quantity: float,
    unit_rate: int,
    gst_rate: int,
    supplier_state_code: str,
    business_state_code: str = None
) -> PurchaseItemTax:
    """
    Calculate tax for a purchase item.
    
    Args:
        quantity: Quantity in units
        unit_rate: Rate per unit in paise
        gst_rate: GST rate (0, 5, 12, 18, 28)
        supplier_state_code: 2-digit state code of supplier
        business_state_code: 2-digit state code of business (if None, will use settings)
    
    Returns:
        PurchaseItemTax with calculated amounts
    
    GST Rules:
    - Same state: CGST + SGST (each = gst_rate / 2)
    - Different state: IGST (= gst_rate)
    """
    
    # Get business state code if not provided
    if business_state_code is None:
        # For now, we assume the business is in the state of the first supplier
        # In production, get this from BusinessProfile table
        business_state_code = "29"  # Default for now (will be dynamic in Phase-2)
    
    # Calculate subtotal
    subtotal = int(quantity * unit_rate)
    
    # Determine tax type based on state codes
    is_same_state = supplier_state_code == business_state_code
    
    if gst_rate == 0:
        # Zero-rated / Exempt goods
        cgst_amount = 0
        sgst_amount = 0
        igst_amount = 0
        tax_type = "CGST_SGST"  # Mark as CGST/SGST even though no tax
    elif is_same_state:
        # Same state: CGST + SGST
        gst_per_half = gst_rate / 2
        cgst_amount = int((subtotal * gst_per_half) / 100)
        sgst_amount = int((subtotal * gst_per_half) / 100)
        igst_amount = 0
        tax_type = "CGST_SGST"
    else:
        # Different state: IGST only
        cgst_amount = 0
        sgst_amount = 0
        igst_amount = int((subtotal * gst_rate) / 100)
        tax_type = "IGST"
    
    total_tax = cgst_amount + sgst_amount + igst_amount
    total_amount = subtotal + total_tax
    
    return PurchaseItemTax(
        subtotal=subtotal,
        cgst_amount=cgst_amount,
        sgst_amount=sgst_amount,
        igst_amount=igst_amount,
        total_amount=total_amount,
        tax_type=tax_type
    )


def calculate_purchase_invoice_totals(
    items_with_tax: List[Tuple[float, int, int, str, str, str]]
) -> dict:
    """
    Calculate totals for entire purchase invoice.
    
    Args:
        items_with_tax: List of tuples:
            (quantity, unit_rate, gst_rate, supplier_state_code, business_state_code, item_name)
    
    Returns:
        dict with totals:
        {
            'total_quantity': float,
            'subtotal_value': int (paise),
            'cgst_amount': int (paise),
            'sgst_amount': int (paise),
            'igst_amount': int (paise),
            'total_gst': int (paise),
            'total_amount': int (paise)
        }
    """
    
    total_quantity = 0.0
    subtotal_value = 0
    cgst_total = 0
    sgst_total = 0
    igst_total = 0
    
    for quantity, unit_rate, gst_rate, supplier_state, business_state, _ in items_with_tax:
        item_tax = calculate_purchase_item_tax(
            quantity=quantity,
            unit_rate=unit_rate,
            gst_rate=gst_rate,
            supplier_state_code=supplier_state,
            business_state_code=business_state
        )
        
        total_quantity += quantity
        subtotal_value += item_tax.subtotal
        cgst_total += item_tax.cgst_amount
        sgst_total += item_tax.sgst_amount
        igst_total += item_tax.igst_amount
    
    total_gst = cgst_total + sgst_total + igst_total
    total_amount = subtotal_value + total_gst
    
    return {
        'total_quantity': total_quantity,
        'subtotal_value': subtotal_value,
        'cgst_amount': cgst_total,
        'sgst_amount': sgst_total,
        'igst_amount': igst_total,
        'total_gst': total_gst,
        'total_amount': total_amount
    }
