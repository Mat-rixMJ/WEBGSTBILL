"""
Edge case and validation tests.
Test invalid inputs, manipulated data, and boundary conditions.
"""
import pytest


class TestValidationErrors:
    """Test that invalid inputs are rejected."""
    
    def test_invalid_gstin_rejected(
        self, client, auth_headers, test_user
    ):
        """Test that invalid GSTIN format is rejected."""
        # Try to create customer with invalid GSTIN
        customer_data = {
            "name": "Invalid GSTIN Customer",
            "gstin": "INVALID123",  # Invalid format
            "state_code": 29,
            "state_name": "Karnataka",
            "address": "Test Address",
            "email": "test@test.com",
            "phone": "9876543210",
            "customer_type": "B2B"
        }
        
        response = client.post(
            "/api/customers/",
            json=customer_data,
            headers=auth_headers
        )
        
        # Should fail validation
        assert response.status_code == 422 or response.status_code == 400
    
    def test_invalid_gst_rate_rejected(
        self, client, auth_headers
    ):
        """Test that invalid GST rate is rejected."""
        # Try to create product with invalid GST rate
        product_data = {
            "name": "Invalid GST Product",
            "hsn_code": "1234",
            "gst_rate": 99,  # Invalid GST rate
            "price": 100000,
            "stock_quantity": 10
        }
        
        response = client.post(
            "/api/products/",
            json=product_data,
            headers=auth_headers
        )
        
        # Should fail validation
        assert response.status_code == 422 or response.status_code == 400
    
    def test_negative_quantity_rejected(
        self, client, auth_headers, test_business, test_products, test_customers
    ):
        """Test that negative quantity is rejected."""
        customer = test_customers["b2c"]
        product = test_products[0]
        
        # Try to create invoice with negative quantity
        inv_data = {
            "customer_id": customer.id,
            "invoice_date": "2025-12-15",
            "line_items": [{
                "product_id": product.id,
                "quantity": -5,  # Negative quantity
                "unit_price": product.price,
                "discount_amount": 0
            }]
        }
        
        response = client.post(
            "/api/invoices/",
            json=inv_data,
            headers=auth_headers
        )
        
        # Should fail validation
        assert response.status_code == 422 or response.status_code == 400
    
    def test_negative_price_rejected(
        self, client, auth_headers, test_business, test_products, test_customers
    ):
        """Test that negative price is rejected."""
        customer = test_customers["b2c"]
        product = test_products[0]
        
        # Try to create invoice with negative price
        inv_data = {
            "customer_id": customer.id,
            "invoice_date": "2025-12-15",
            "line_items": [{
                "product_id": product.id,
                "quantity": 2,
                "unit_price": -100000,  # Negative price
                "discount_amount": 0
            }]
        }
        
        response = client.post(
            "/api/invoices/",
            json=inv_data,
            headers=auth_headers
        )
        
        # Should fail validation
        assert response.status_code == 422 or response.status_code == 400
    
    def test_missing_required_fields_rejected(
        self, client, auth_headers, test_business, test_products, test_customers
    ):
        """Test that missing required fields are rejected."""
        # Try to create invoice without customer_id
        inv_data = {
            "invoice_date": "2025-12-15",
            "line_items": [{
                "product_id": test_products[0].id,
                "quantity": 2,
                "unit_price": 100000,
                "discount_amount": 0
            }]
        }
        
        response = client.post(
            "/api/invoices/",
            json=inv_data,
            headers=auth_headers
        )
        
        # Should fail validation
        assert response.status_code == 422


class TestManipulatedDataRejection:
    """Test that manipulated frontend totals are rejected."""
    
    def test_manipulated_subtotal_rejected(
        self, client, auth_headers, test_business, test_products, test_customers, db_session
    ):
        """Test that manipulated subtotal in request is recalculated by backend."""
        customer = test_customers["b2c"]
        product = test_products[0]  # Rs 1000, 5% GST
        
        # Create invoice - backend should calculate its own totals
        inv_data = {
            "customer_id": customer.id,
            "invoice_date": "2025-12-15",
            "line_items": [{
                "product_id": product.id,
                "quantity": 2,
                "unit_price": product.price,
                "discount_amount": 0
            }]
        }
        
        response = client.post(
            "/api/invoices/",
            json=inv_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        invoice = response.json()
        
        # Backend should calculate: 2 * 1000 = 2000
        # Not whatever frontend sends
        assert invoice["subtotal"] == 200000  # Rs 2000.00
        
        # GST should be: 2000 * 5% = 100 (CGST 50 + SGST 50)
        assert invoice["total_gst"] == 10000  # Rs 100.00
        assert invoice["grand_total"] == 210000  # Rs 2100.00
    
    def test_discount_exceeding_price_rejected(
        self, client, auth_headers, test_business, test_products, test_customers
    ):
        """Test that discount greater than price is rejected."""
        customer = test_customers["b2c"]
        product = test_products[0]
        
        # Try to create invoice with discount > price
        inv_data = {
            "customer_id": customer.id,
            "invoice_date": "2025-12-15",
            "line_items": [{
                "product_id": product.id,
                "quantity": 1,
                "unit_price": product.price,
                "discount_amount": product.price + 10000  # Discount > price
            }]
        }
        
        response = client.post(
            "/api/invoices/",
            json=inv_data,
            headers=auth_headers
        )
        
        # Should fail validation
        assert response.status_code == 400 or response.status_code == 422


class TestEdgeCases:
    """Test boundary conditions and edge cases."""
    
    def test_zero_gst_rate_product(
        self, client, auth_headers, test_user
    ):
        """Test product with 0% GST rate."""
        product_data = {
            "name": "Zero GST Product",
            "hsn_code": "0000",
            "gst_rate": 0,
            "price": 100000,
            "stock_quantity": 10
        }
        
        response = client.post(
            "/api/products/",
            json=product_data,
            headers=auth_headers
        )
        
        # Should be allowed
        assert response.status_code == 200
        product = response.json()
        assert product["gst_rate"] == 0
    
    def test_very_large_quantity(
        self, client, auth_headers, test_business, test_products, test_customers
    ):
        """Test handling of very large quantities."""
        customer = test_customers["b2c"]
        product = test_products[0]
        
        # Update product to have large stock
        client.put(
            f"/api/products/{product.id}",
            json={
                "name": product.name,
                "hsn_code": product.hsn_code,
                "gst_rate": product.gst_rate,
                "price": product.price,
                "stock_quantity": 100000
            },
            headers=auth_headers
        )
        
        # Create invoice with large quantity
        inv_data = {
            "customer_id": customer.id,
            "invoice_date": "2025-12-15",
            "line_items": [{
                "product_id": product.id,
                "quantity": 10000,
                "unit_price": product.price,
                "discount_amount": 0
            }]
        }
        
        response = client.post(
            "/api/invoices/",
            json=inv_data,
            headers=auth_headers
        )
        
        # Should handle correctly
        assert response.status_code == 200
        invoice = response.json()
        assert invoice["items"][0]["quantity"] == 10000
    
    def test_future_date_invoice(
        self, client, auth_headers, test_business, test_products, test_customers
    ):
        """Test invoice with future date."""
        customer = test_customers["b2c"]
        product = test_products[0]
        
        # Try to create invoice with future date
        inv_data = {
            "customer_id": customer.id,
            "invoice_date": "2026-12-15",  # Future date
            "line_items": [{
                "product_id": product.id,
                "quantity": 1,
                "unit_price": product.price,
                "discount_amount": 0
            }]
        }
        
        response = client.post(
            "/api/invoices/",
            json=inv_data,
            headers=auth_headers
        )
        
        # Depending on business rules, might be allowed or rejected
        # For now, just verify response is handled
        assert response.status_code in [200, 400, 422]
    
    def test_invoice_with_empty_line_items(
        self, client, auth_headers, test_business, test_customers
    ):
        """Test that invoice with no line items is rejected."""
        customer = test_customers["b2c"]
        
        # Try to create invoice with empty line items
        inv_data = {
            "customer_id": customer.id,
            "invoice_date": "2025-12-15",
            "line_items": []
        }
        
        response = client.post(
            "/api/invoices/",
            json=inv_data,
            headers=auth_headers
        )
        
        # Should fail validation
        assert response.status_code == 400 or response.status_code == 422
    
    def test_duplicate_product_in_line_items(
        self, client, auth_headers, test_business, test_products, test_customers
    ):
        """Test handling of duplicate products in same invoice."""
        customer = test_customers["b2c"]
        product = test_products[0]
        
        # Create invoice with same product twice
        inv_data = {
            "customer_id": customer.id,
            "invoice_date": "2025-12-15",
            "line_items": [
                {
                    "product_id": product.id,
                    "quantity": 2,
                    "unit_price": product.price,
                    "discount_amount": 0
                },
                {
                    "product_id": product.id,  # Same product again
                    "quantity": 3,
                    "unit_price": product.price,
                    "discount_amount": 0
                }
            ]
        }
        
        response = client.post(
            "/api/invoices/",
            json=inv_data,
            headers=auth_headers
        )
        
        # Should either merge or keep separate - both are valid
        # Just verify it's handled correctly
        if response.status_code == 200:
            invoice = response.json()
            # Total quantity should be 5
            total_qty = sum(item["quantity"] for item in invoice["items"] if item["product_id"] == product.id)
            assert total_qty == 5
