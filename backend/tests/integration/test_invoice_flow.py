"""
Integration tests for complete invoice flow:
Create invoice → Stock reduction → Report validation
"""
import pytest
from datetime import datetime


class TestInvoiceFlow:
    """Test complete invoice creation and stock management flow."""
    
    def test_create_invoice_reduces_stock(
        self, client, auth_headers, test_business, test_products, test_customers
    ):
        """Test that creating an invoice reduces product stock."""
        product = test_products[2]  # 18% GST product
        customer = test_customers["b2c"]
        
        # Check initial stock
        initial_stock = product.stock_quantity
        assert initial_stock == 30
        
        # Create invoice
        invoice_data = {
            "customer_id": customer.id,
            "invoice_date": "2025-12-15",
            "line_items": [
                {
                    "product_id": product.id,
                    "quantity": 5,
                    "unit_price": product.price,
                    "discount_amount": 0
                }
            ]
        }
        
        response = client.post(
            "/api/invoices/",
            json=invoice_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        invoice = response.json()
        assert invoice["status"] == "FINALIZED"
        
        # Verify stock reduced
        product_response = client.get(
            f"/api/products/{product.id}",
            headers=auth_headers
        )
        assert product_response.status_code == 200
        updated_product = product_response.json()
        assert updated_product["stock_quantity"] == initial_stock - 5
    
    def test_cancel_invoice_restores_stock(
        self, client, auth_headers, test_business, test_products, test_customers
    ):
        """Test that cancelling an invoice restores product stock."""
        product = test_products[1]  # 12% GST product
        customer = test_customers["b2c"]
        
        # Create invoice
        invoice_data = {
            "customer_id": customer.id,
            "invoice_date": "2025-12-15",
            "line_items": [
                {
                    "product_id": product.id,
                    "quantity": 3,
                    "unit_price": product.price,
                    "discount_amount": 0
                }
            ]
        }
        
        response = client.post(
            "/api/invoices/",
            json=invoice_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        invoice = response.json()
        invoice_id = invoice["id"]
        
        # Get stock after invoice
        product_response = client.get(
            f"/api/products/{product.id}",
            headers=auth_headers
        )
        stock_after_invoice = product_response.json()["stock_quantity"]
        
        # Cancel invoice
        cancel_response = client.post(
            f"/api/invoices/{invoice_id}/cancel",
            headers=auth_headers
        )
        assert cancel_response.status_code == 200
        
        # Verify stock restored
        product_response = client.get(
            f"/api/products/{product.id}",
            headers=auth_headers
        )
        final_stock = product_response.json()["stock_quantity"]
        assert final_stock == stock_after_invoice + 3
    
    def test_insufficient_stock_prevents_invoice(
        self, client, auth_headers, test_business, test_products, test_customers
    ):
        """Test that invoice creation fails when stock is insufficient."""
        product = test_products[0]  # Product with 100 stock
        customer = test_customers["b2c"]
        
        # Try to create invoice for more than available stock
        invoice_data = {
            "customer_id": customer.id,
            "invoice_date": "2025-12-15",
            "line_items": [
                {
                    "product_id": product.id,
                    "quantity": 150,  # More than 100 available
                    "unit_price": product.price,
                    "discount_amount": 0
                }
            ]
        }
        
        response = client.post(
            "/api/invoices/",
            json=invoice_data,
            headers=auth_headers
        )
        
        # Should fail
        assert response.status_code == 400
        assert "insufficient stock" in response.json()["detail"].lower()
    
    def test_invoice_gst_calculation_intra_state(
        self, client, auth_headers, test_business, test_products, test_customers
    ):
        """Test GST calculation for intra-state invoice."""
        product = test_products[2]  # 18% GST, Rs 3000
        customer = test_customers["b2c"]  # Same state as business (29)
        
        invoice_data = {
            "customer_id": customer.id,
            "invoice_date": "2025-12-15",
            "line_items": [
                {
                    "product_id": product.id,
                    "quantity": 2,
                    "unit_price": product.price,
                    "discount_amount": 0
                }
            ]
        }
        
        response = client.post(
            "/api/invoices/",
            json=invoice_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        invoice = response.json()
        
        # Verify CGST+SGST (intra-state)
        assert invoice["total_cgst"] > 0
        assert invoice["total_sgst"] > 0
        assert invoice["total_igst"] == 0
        assert invoice["total_cgst"] == invoice["total_sgst"]
        
        # Taxable: 2 * 3000 = 6000
        # GST 18%: 1080 (CGST 540 + SGST 540)
        assert invoice["subtotal"] == 600000  # Rs 6000.00
        assert invoice["total_gst"] == 108000  # Rs 1080.00
        assert invoice["grand_total"] == 708000  # Rs 7080.00
    
    def test_invoice_gst_calculation_inter_state(
        self, client, auth_headers, test_business, test_products, test_customers
    ):
        """Test GST calculation for inter-state invoice."""
        product = test_products[1]  # 12% GST, Rs 2000
        customer = test_customers["b2b"]  # Different state (27 - Maharashtra)
        
        invoice_data = {
            "customer_id": customer.id,
            "invoice_date": "2025-12-15",
            "line_items": [
                {
                    "product_id": product.id,
                    "quantity": 3,
                    "unit_price": product.price,
                    "discount_amount": 0
                }
            ]
        }
        
        response = client.post(
            "/api/invoices/",
            json=invoice_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        invoice = response.json()
        
        # Verify IGST (inter-state)
        assert invoice["total_cgst"] == 0
        assert invoice["total_sgst"] == 0
        assert invoice["total_igst"] > 0
        
        # Taxable: 3 * 2000 = 6000
        # GST 12%: 720 (IGST 720)
        assert invoice["subtotal"] == 600000  # Rs 6000.00
        assert invoice["total_gst"] == 72000  # Rs 720.00
        assert invoice["total_igst"] == 72000
        assert invoice["grand_total"] == 672000  # Rs 6720.00
    
    def test_multiple_products_in_invoice(
        self, client, auth_headers, test_business, test_products, test_customers
    ):
        """Test invoice with multiple products with different GST rates."""
        customer = test_customers["b2c"]
        
        invoice_data = {
            "customer_id": customer.id,
            "invoice_date": "2025-12-15",
            "line_items": [
                {
                    "product_id": test_products[0].id,  # 5% GST, Rs 1000
                    "quantity": 2,
                    "unit_price": test_products[0].price,
                    "discount_amount": 0
                },
                {
                    "product_id": test_products[1].id,  # 12% GST, Rs 2000
                    "quantity": 1,
                    "unit_price": test_products[1].price,
                    "discount_amount": 0
                },
                {
                    "product_id": test_products[2].id,  # 18% GST, Rs 3000
                    "quantity": 1,
                    "unit_price": test_products[2].price,
                    "discount_amount": 0
                }
            ]
        }
        
        response = client.post(
            "/api/invoices/",
            json=invoice_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        invoice = response.json()
        
        # Subtotal: (2*1000) + (1*2000) + (1*3000) = 7000
        assert invoice["subtotal"] == 700000
        
        # GST: (2000*5%) + (2000*12%) + (3000*18%)
        #    = 100 + 240 + 540 = 880
        assert invoice["total_gst"] == 88000
        assert invoice["grand_total"] == 788000  # Rs 7880.00
        
        # Verify 3 line items
        assert len(invoice["items"]) == 3
    
    def test_invoice_number_sequential(
        self, client, auth_headers, test_business, test_products, test_customers
    ):
        """Test that invoice numbers are sequential and immutable."""
        customer = test_customers["b2c"]
        product = test_products[0]
        
        invoice_data = {
            "customer_id": customer.id,
            "invoice_date": "2025-12-15",
            "line_items": [
                {
                    "product_id": product.id,
                    "quantity": 1,
                    "unit_price": product.price,
                    "discount_amount": 0
                }
            ]
        }
        
        # Create first invoice
        response1 = client.post(
            "/api/invoices/",
            json=invoice_data,
            headers=auth_headers
        )
        assert response1.status_code == 200
        invoice1 = response1.json()
        invoice_num1 = invoice1["invoice_number"]
        
        # Create second invoice
        response2 = client.post(
            "/api/invoices/",
            json=invoice_data,
            headers=auth_headers
        )
        assert response2.status_code == 200
        invoice2 = response2.json()
        invoice_num2 = invoice2["invoice_number"]
        
        # Extract numbers from invoice numbers (e.g., INV000001, INV000002)
        num1 = int(invoice_num1.replace("INV", ""))
        num2 = int(invoice_num2.replace("INV", ""))
        
        # Verify sequential
        assert num2 == num1 + 1
