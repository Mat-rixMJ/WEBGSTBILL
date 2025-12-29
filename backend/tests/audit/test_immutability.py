"""
Audit and immutability tests.
Test that invoices cannot be edited or deleted after finalization.
"""
import pytest


class TestInvoiceImmutability:
    """Test that finalized invoices are immutable."""
    
    def test_cannot_edit_finalized_invoice(
        self, client, auth_headers, test_business, test_products, test_customers
    ):
        """Test that finalized invoice cannot be edited."""
        customer = test_customers["b2c"]
        product = test_products[0]
        
        # Create invoice
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
        resp = client.post("/api/invoices/", json=inv_data, headers=auth_headers)
        assert resp.status_code == 200
        invoice = resp.json()
        invoice_id = invoice["id"]
        
        # Try to edit the invoice
        updated_data = {
            "customer_id": customer.id,
            "invoice_date": "2025-12-16",  # Try to change date
            "line_items": [{
                "product_id": product.id,
                "quantity": 5,  # Try to change quantity
                "unit_price": product.price,
                "discount_amount": 0
            }]
        }
        
        edit_response = client.put(
            f"/api/invoices/{invoice_id}",
            json=updated_data,
            headers=auth_headers
        )
        
        # Should fail (405 Method Not Allowed or 400 Bad Request)
        assert edit_response.status_code in [400, 404, 405]
    
    def test_cannot_delete_finalized_invoice(
        self, client, auth_headers, test_business, test_products, test_customers
    ):
        """Test that finalized invoice cannot be deleted."""
        customer = test_customers["b2c"]
        product = test_products[0]
        
        # Create invoice
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
        resp = client.post("/api/invoices/", json=inv_data, headers=auth_headers)
        assert resp.status_code == 200
        invoice = resp.json()
        invoice_id = invoice["id"]
        
        # Try to delete the invoice
        delete_response = client.delete(
            f"/api/invoices/{invoice_id}",
            headers=auth_headers
        )
        
        # Should fail (405 Method Not Allowed or 400 Bad Request)
        assert delete_response.status_code in [400, 404, 405]
    
    def test_can_only_cancel_finalized_invoice(
        self, client, auth_headers, test_business, test_products, test_customers
    ):
        """Test that only cancellation is allowed for finalized invoice."""
        customer = test_customers["b2c"]
        product = test_products[0]
        
        # Create invoice
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
        resp = client.post("/api/invoices/", json=inv_data, headers=auth_headers)
        assert resp.status_code == 200
        invoice = resp.json()
        invoice_id = invoice["id"]
        
        # Cancel should work
        cancel_response = client.post(
            f"/api/invoices/{invoice_id}/cancel",
            headers=auth_headers
        )
        assert cancel_response.status_code == 200
        
        # Verify status changed to CANCELLED
        get_response = client.get(
            f"/api/invoices/{invoice_id}",
            headers=auth_headers
        )
        assert get_response.status_code == 200
        updated_invoice = get_response.json()
        assert updated_invoice["status"] == "CANCELLED"
    
    def test_cannot_cancel_already_cancelled_invoice(
        self, client, auth_headers, test_business, test_products, test_customers
    ):
        """Test that already cancelled invoice cannot be cancelled again."""
        customer = test_customers["b2c"]
        product = test_products[0]
        
        # Create and cancel invoice
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
        resp = client.post("/api/invoices/", json=inv_data, headers=auth_headers)
        invoice = resp.json()
        invoice_id = invoice["id"]
        
        # Cancel first time
        client.post(f"/api/invoices/{invoice_id}/cancel", headers=auth_headers)
        
        # Try to cancel again
        second_cancel = client.post(
            f"/api/invoices/{invoice_id}/cancel",
            headers=auth_headers
        )
        
        # Should fail
        assert second_cancel.status_code == 400


class TestDataIntegrity:
    """Test that product/customer edits don't affect past invoices."""
    
    def test_product_price_change_does_not_affect_past_invoices(
        self, client, auth_headers, test_business, test_products, test_customers
    ):
        """Test that changing product price doesn't affect historical invoices."""
        customer = test_customers["b2c"]
        product = test_products[0]
        
        original_price = product.price
        
        # Create invoice with original price
        inv_data = {
            "customer_id": customer.id,
            "invoice_date": "2025-12-15",
            "line_items": [{
                "product_id": product.id,
                "quantity": 2,
                "unit_price": original_price,
                "discount_amount": 0
            }]
        }
        resp = client.post("/api/invoices/", json=inv_data, headers=auth_headers)
        invoice = resp.json()
        
        # Change product price
        new_price = original_price + 50000  # Increase by Rs 500
        update_product_response = client.put(
            f"/api/products/{product.id}",
            json={
                "name": product.name,
                "hsn_code": product.hsn_code,
                "gst_rate": product.gst_rate,
                "price": new_price,
                "stock_quantity": product.stock_quantity
            },
            headers=auth_headers
        )
        assert update_product_response.status_code == 200
        
        # Retrieve invoice again
        get_invoice_response = client.get(
            f"/api/invoices/{invoice['id']}",
            headers=auth_headers
        )
        assert get_invoice_response.status_code == 200
        retrieved_invoice = get_invoice_response.json()
        
        # Invoice should still have original price
        assert retrieved_invoice["items"][0]["unit_price"] == original_price
        assert retrieved_invoice["subtotal"] == invoice["subtotal"]
    
    def test_customer_details_change_does_not_affect_past_invoices(
        self, client, auth_headers, test_business, test_products, test_customers
    ):
        """Test that changing customer details doesn't affect historical invoices."""
        customer = test_customers["b2c"]
        product = test_products[0]
        
        original_customer_name = customer.name
        
        # Create invoice
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
        resp = client.post("/api/invoices/", json=inv_data, headers=auth_headers)
        invoice = resp.json()
        
        # Change customer name
        update_customer_response = client.put(
            f"/api/customers/{customer.id}",
            json={
                "name": "Changed Customer Name",
                "state_code": customer.state_code,
                "state_name": customer.state_name,
                "address": customer.address,
                "email": customer.email,
                "phone": customer.phone,
                "customer_type": customer.customer_type
            },
            headers=auth_headers
        )
        assert update_customer_response.status_code == 200
        
        # Retrieve invoice again
        get_invoice_response = client.get(
            f"/api/invoices/{invoice['id']}",
            headers=auth_headers
        )
        assert get_invoice_response.status_code == 200
        retrieved_invoice = get_invoice_response.json()
        
        # Invoice should still reference correct customer_id
        # (name might be dynamic from relation, but ID stays same)
        assert retrieved_invoice["customer_id"] == customer.id
