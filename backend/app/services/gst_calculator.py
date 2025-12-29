"""GST calculation service - pure functions for tax calculation"""

from decimal import Decimal
from typing import TypedDict

from app.utils.helpers import calculate_percentage, round_gst_amount


class TaxBreakup(TypedDict):
    """Tax calculation result structure"""
    taxable_amount_paise: int
    cgst_paise: int
    sgst_paise: int
    igst_paise: int
    total_tax_paise: int
    total_amount_paise: int


def calculate_gst(
    taxable_amount_paise: int,
    gst_rate: Decimal,
    seller_state_code: str,
    buyer_state_code: str
) -> TaxBreakup:
    """
    Calculate GST based on Indian tax rules.
    
    Rules:
    - Intra-state (same state): CGST + SGST (each half of GST rate)
    - Inter-state (different states): IGST (full GST rate)
    
    Args:
        taxable_amount_paise: Taxable amount in paise
        gst_rate: GST rate (0, 5, 12, 18, or 28)
        seller_state_code: Seller's state code (2 digits)
        buyer_state_code: Buyer's state code (2 digits)
        
    Returns:
        TaxBreakup dict with all tax components
        
    Example:
        >>> calculate_gst(10000, Decimal('18'), '29', '29')
        {
            'taxable_amount_paise': 10000,
            'cgst_paise': 900,
            'sgst_paise': 900,
            'igst_paise': 0,
            'total_tax_paise': 1800,
            'total_amount_paise': 11800
        }
    """
    if seller_state_code == buyer_state_code:
        # Intra-state: CGST + SGST
        half_rate = gst_rate / 2
        cgst = calculate_percentage(taxable_amount_paise, half_rate)
        sgst = calculate_percentage(taxable_amount_paise, half_rate)
        
        return TaxBreakup(
            taxable_amount_paise=taxable_amount_paise,
            cgst_paise=cgst,
            sgst_paise=sgst,
            igst_paise=0,
            total_tax_paise=cgst + sgst,
            total_amount_paise=taxable_amount_paise + cgst + sgst
        )
    else:
        # Inter-state: IGST
        igst = calculate_percentage(taxable_amount_paise, gst_rate)
        
        return TaxBreakup(
            taxable_amount_paise=taxable_amount_paise,
            cgst_paise=0,
            sgst_paise=0,
            igst_paise=igst,
            total_tax_paise=igst,
            total_amount_paise=taxable_amount_paise + igst
        )


def calculate_line_item_tax(
    quantity: int,
    unit_price_paise: int,
    gst_rate: Decimal,
    seller_state_code: str,
    buyer_state_code: str
) -> TaxBreakup:
    """
    Calculate GST for an invoice line item.
    
    Args:
        quantity: Quantity of items
        unit_price_paise: Price per unit in paise
        gst_rate: GST rate
        seller_state_code: Seller's state code
        buyer_state_code: Buyer's state code
        
    Returns:
        TaxBreakup dict with all tax components
    """
    taxable_amount = quantity * unit_price_paise
    return calculate_gst(taxable_amount, gst_rate, seller_state_code, buyer_state_code)


def aggregate_invoice_taxes(line_items: list[TaxBreakup]) -> TaxBreakup:
    """
    Aggregate tax breakups from multiple line items.
    
    Args:
        line_items: List of TaxBreakup dicts from invoice items
        
    Returns:
        Aggregated TaxBreakup for entire invoice
    """
    total_taxable = sum(item["taxable_amount_paise"] for item in line_items)
    total_cgst = sum(item["cgst_paise"] for item in line_items)
    total_sgst = sum(item["sgst_paise"] for item in line_items)
    total_igst = sum(item["igst_paise"] for item in line_items)
    
    return TaxBreakup(
        taxable_amount_paise=total_taxable,
        cgst_paise=total_cgst,
        sgst_paise=total_sgst,
        igst_paise=total_igst,
        total_tax_paise=total_cgst + total_sgst + total_igst,
        total_amount_paise=total_taxable + total_cgst + total_sgst + total_igst
    )
