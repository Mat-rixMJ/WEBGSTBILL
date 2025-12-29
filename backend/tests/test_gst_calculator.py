"""Unit tests for GST calculator"""

import pytest
from decimal import Decimal
from app.services.gst_calculator import (
    calculate_gst,
    calculate_line_item_tax,
    aggregate_invoice_taxes
)


def test_intrastate_gst_calculation():
    """Test CGST + SGST for intra-state transaction"""
    result = calculate_gst(
        taxable_amount_paise=10000,  # ₹100
        gst_rate=Decimal('18'),
        seller_state_code='29',  # Karnataka
        buyer_state_code='29'     # Karnataka
    )
    
    assert result['taxable_amount_paise'] == 10000
    assert result['cgst_paise'] == 900  # 9% of 10000
    assert result['sgst_paise'] == 900  # 9% of 10000
    assert result['igst_paise'] == 0
    assert result['total_tax_paise'] == 1800
    assert result['total_amount_paise'] == 11800


def test_interstate_gst_calculation():
    """Test IGST for inter-state transaction"""
    result = calculate_gst(
        taxable_amount_paise=10000,  # ₹100
        gst_rate=Decimal('18'),
        seller_state_code='29',  # Karnataka
        buyer_state_code='27'     # Maharashtra
    )
    
    assert result['taxable_amount_paise'] == 10000
    assert result['cgst_paise'] == 0
    assert result['sgst_paise'] == 0
    assert result['igst_paise'] == 1800  # 18% of 10000
    assert result['total_tax_paise'] == 1800
    assert result['total_amount_paise'] == 11800


def test_zero_gst_rate():
    """Test zero-rated items"""
    result = calculate_gst(
        taxable_amount_paise=10000,
        gst_rate=Decimal('0'),
        seller_state_code='29',
        buyer_state_code='29'
    )
    
    assert result['cgst_paise'] == 0
    assert result['sgst_paise'] == 0
    assert result['igst_paise'] == 0
    assert result['total_tax_paise'] == 0
    assert result['total_amount_paise'] == 10000


def test_5_percent_gst():
    """Test 5% GST rate"""
    result = calculate_gst(
        taxable_amount_paise=10000,
        gst_rate=Decimal('5'),
        seller_state_code='29',
        buyer_state_code='29'
    )
    
    # 2.5% CGST = 250, 2.5% SGST = 250
    assert result['cgst_paise'] == 250
    assert result['sgst_paise'] == 250
    assert result['total_tax_paise'] == 500


def test_28_percent_gst():
    """Test 28% GST rate (highest slab)"""
    result = calculate_gst(
        taxable_amount_paise=10000,
        gst_rate=Decimal('28'),
        seller_state_code='29',
        buyer_state_code='27'  # Interstate
    )
    
    assert result['igst_paise'] == 2800  # 28% of 10000


def test_line_item_calculation():
    """Test line item GST calculation"""
    result = calculate_line_item_tax(
        quantity=5,
        unit_price_paise=2000,  # ₹20 per unit
        gst_rate=Decimal('12'),
        seller_state_code='29',
        buyer_state_code='29'
    )
    
    # Taxable amount = 5 * 2000 = 10000
    # CGST = 6% of 10000 = 600
    # SGST = 6% of 10000 = 600
    assert result['taxable_amount_paise'] == 10000
    assert result['cgst_paise'] == 600
    assert result['sgst_paise'] == 600
    assert result['total_amount_paise'] == 11200


def test_aggregate_invoice_taxes():
    """Test aggregation of multiple line items"""
    line_items = [
        calculate_gst(10000, Decimal('18'), '29', '29'),
        calculate_gst(5000, Decimal('12'), '29', '29'),
        calculate_gst(2000, Decimal('5'), '29', '29'),
    ]
    
    result = aggregate_invoice_taxes(line_items)
    
    # Total taxable = 10000 + 5000 + 2000 = 17000
    assert result['taxable_amount_paise'] == 17000
    
    # Total CGST = 900 + 300 + 50 = 1250
    assert result['cgst_paise'] == 1250
    
    # Total SGST = 900 + 300 + 50 = 1250
    assert result['sgst_paise'] == 1250
    
    # Total tax = 2500
    assert result['total_tax_paise'] == 2500
    
    # Total amount = 17000 + 2500 = 19500
    assert result['total_amount_paise'] == 19500


def test_rounding_edge_case():
    """Test GST calculation with rounding"""
    # Amount that doesn't divide evenly
    result = calculate_gst(
        taxable_amount_paise=10001,
        gst_rate=Decimal('18'),
        seller_state_code='29',
        buyer_state_code='29'
    )
    
    # 9% of 10001 = 900.09 → rounds to 900
    assert result['cgst_paise'] == 900
    assert result['sgst_paise'] == 900
    assert result['total_tax_paise'] == 1800
