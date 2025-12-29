"""Helper utility functions"""

from decimal import Decimal
from datetime import datetime


def paise_to_rupees(paise: int) -> Decimal:
    """
    Convert paise (smallest unit) to rupees.
    
    Args:
        paise: Amount in paise (integer)
        
    Returns:
        Amount in rupees (Decimal)
    """
    return Decimal(paise) / 100


def rupees_to_paise(rupees: Decimal | float) -> int:
    """
    Convert rupees to paise (smallest unit).
    
    Args:
        rupees: Amount in rupees
        
    Returns:
        Amount in paise (integer)
    """
    return int(Decimal(str(rupees)) * 100)


def format_currency(paise: int) -> str:
    """
    Format paise as Indian currency string.
    
    Args:
        paise: Amount in paise
        
    Returns:
        Formatted string like "₹1,234.56"
    """
    rupees = paise_to_rupees(paise)
    return f"₹{rupees:,.2f}"


def format_date_indian(dt: datetime | None) -> str:
    """
    Format datetime in Indian standard format (DD/MM/YYYY).
    
    Args:
        dt: datetime object
        
    Returns:
        Formatted date string
    """
    if dt is None:
        return ""
    return dt.strftime("%d/%m/%Y")


def round_gst_amount(amount: Decimal) -> int:
    """
    Round GST amount to nearest paise using standard rounding.
    
    Args:
        amount: GST amount as Decimal
        
    Returns:
        Rounded amount in paise
    """
    return round(amount)


def calculate_percentage(amount: int, percentage: Decimal) -> int:
    """
    Calculate percentage of an amount in paise.
    
    Args:
        amount: Base amount in paise
        percentage: Percentage rate
        
    Returns:
        Calculated amount in paise
    """
    return round_gst_amount(Decimal(amount) * percentage / 100)
