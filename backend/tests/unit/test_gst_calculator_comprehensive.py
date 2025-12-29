"""
Unit tests for GST calculation logic.
Tests CGST/SGST vs IGST switching and rounding rules.
"""
import pytest
from app.services.gst_calculator import calculate_gst, calculate_invoice_totals


class TestGSTCalculation:
    """Test GST calculation accuracy."""
    
    def test_intra_state_cgst_sgst(self):
        """Test CGST+SGST for same state transaction."""
        result = calculate_gst(
            taxable_amount=100000,  # Rs 1000.00
            gst_rate=18,
            is_intra_state=True
        )
        assert result["cgst_rate"] == 9
        assert result["sgst_rate"] == 9
        assert result["igst_rate"] == 0
        assert result["cgst_amount"] == 9000  # 90.00
        assert result["sgst_amount"] == 9000  # 90.00
        assert result["igst_amount"] == 0
        assert result["total_gst"] == 18000  # 180.00
    
    def test_inter_state_igst(self):
        """Test IGST for different state transaction."""
        result = calculate_gst(
            taxable_amount=100000,  # Rs 1000.00
            gst_rate=18,
            is_intra_state=False
        )
        assert result["cgst_rate"] == 0
        assert result["sgst_rate"] == 0
        assert result["igst_rate"] == 18
        assert result["cgst_amount"] == 0
        assert result["sgst_amount"] == 0
        assert result["igst_amount"] == 18000  # 180.00
        assert result["total_gst"] == 18000  # 180.00
    
    def test_5_percent_gst(self):
        """Test 5% GST calculation."""
        result = calculate_gst(
            taxable_amount=100000,  # Rs 1000.00
            gst_rate=5,
            is_intra_state=True
        )
        assert result["cgst_rate"] == 2.5
        assert result["sgst_rate"] == 2.5
        assert result["total_gst"] == 5000  # 50.00
    
    def test_12_percent_gst(self):
        """Test 12% GST calculation."""
        result = calculate_gst(
            taxable_amount=100000,  # Rs 1000.00
            gst_rate=12,
            is_intra_state=True
        )
        assert result["cgst_rate"] == 6
        assert result["sgst_rate"] == 6
        assert result["total_gst"] == 12000  # 120.00
    
    def test_28_percent_gst(self):
        """Test 28% GST calculation."""
        result = calculate_gst(
            taxable_amount=100000,  # Rs 1000.00
            gst_rate=28,
            is_intra_state=True
        )
        assert result["cgst_rate"] == 14
        assert result["sgst_rate"] == 14
        assert result["total_gst"] == 28000  # 280.00
    
    def test_rounding_rules(self):
        """Test GST rounding to nearest paisa."""
        # Amount that results in fractional paisa
        result = calculate_gst(
            taxable_amount=97533,  # Rs 975.33
            gst_rate=5,
            is_intra_state=True
        )
        # 5% of 97533 = 4876.65 paise
        # Should round to 4877 paise (Rs 48.77)
        assert result["total_gst"] == 4877
    
    def test_zero_amount(self):
        """Test zero taxable amount."""
        result = calculate_gst(
            taxable_amount=0,
            gst_rate=18,
            is_intra_state=True
        )
        assert result["total_gst"] == 0
        assert result["cgst_amount"] == 0
        assert result["sgst_amount"] == 0


class TestInvoiceTotals:
    """Test invoice total calculations."""
    
    def test_single_line_item_intra_state(self):
        """Test invoice with single line item (intra-state)."""
        line_items = [
            {
                "product_name": "Test Product",
                "hsn_code": "1001",
                "quantity": 5,
                "unit_price": 100000,  # Rs 1000.00
                "gst_rate": 18,
                "discount_amount": 0
            }
        ]
        result = calculate_invoice_totals(line_items, is_intra_state=True)
        
        assert result["subtotal"] == 500000  # Rs 5000.00
        assert result["total_cgst"] == 45000  # Rs 450.00
        assert result["total_sgst"] == 45000  # Rs 450.00
        assert result["total_igst"] == 0
        assert result["total_gst"] == 90000  # Rs 900.00
        assert result["grand_total"] == 590000  # Rs 5900.00
    
    def test_multiple_line_items_different_gst_rates(self):
        """Test invoice with multiple items and different GST rates."""
        line_items = [
            {
                "product_name": "Product 5%",
                "hsn_code": "1001",
                "quantity": 2,
                "unit_price": 100000,  # Rs 1000.00
                "gst_rate": 5,
                "discount_amount": 0
            },
            {
                "product_name": "Product 18%",
                "hsn_code": "2002",
                "quantity": 1,
                "unit_price": 200000,  # Rs 2000.00
                "gst_rate": 18,
                "discount_amount": 0
            }
        ]
        result = calculate_invoice_totals(line_items, is_intra_state=True)
        
        # Subtotal: (2*1000) + (1*2000) = 4000.00
        assert result["subtotal"] == 400000
        
        # GST on 2000 @ 5% = 100.00 (CGST 50 + SGST 50)
        # GST on 2000 @ 18% = 360.00 (CGST 180 + SGST 180)
        # Total GST = 460.00
        assert result["total_gst"] == 46000
        assert result["grand_total"] == 446000  # Rs 4460.00
    
    def test_with_discount(self):
        """Test invoice with line item discount."""
        line_items = [
            {
                "product_name": "Test Product",
                "hsn_code": "1001",
                "quantity": 1,
                "unit_price": 100000,  # Rs 1000.00
                "gst_rate": 18,
                "discount_amount": 10000  # Rs 100.00 discount
            }
        ]
        result = calculate_invoice_totals(line_items, is_intra_state=True)
        
        # Taxable = 1000 - 100 = 900
        assert result["subtotal"] == 90000
        # GST on 900 @ 18% = 162.00
        assert result["total_gst"] == 16200
        assert result["grand_total"] == 106200  # Rs 1062.00
