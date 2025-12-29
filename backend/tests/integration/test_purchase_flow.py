"""
Integration tests for purchase flow:
Create purchase → Stock increase → Report validation
"""
import pytest


class TestPurchaseFlow:
    """Test complete purchase creation and stock management flow."""
    
    def test_create_purchase_increases_stock(
        self, client, auth_headers, test_business, test_products, test_suppliers
    ):
        """Test that creating a purchase increases product stock."""
        product = test_products[0]  # 5% GST product
        supplier = test_suppliers["registered"]
        
        # Check initial stock
        initial_stock = product.stock_quantity
        
        # Create purchase
        purchase_data = {
            "supplier_id": supplier.id,
            "purchase_date": "2025-12-10",
            "line_items": [
                {
                    "product_id": product.id,
                    "quantity": 25,
                    "unit_price": product.price,
                    "discount_amount": 0
                }
            ]
        }
        
        response = client.post(
            "/api/purchases/",
            json=purchase_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        purchase = response.json()
        assert purchase["status"] == "FINALIZED"
        
        # Verify stock increased
        product_response = client.get(
            f"/api/products/{product.id}",
            headers=auth_headers
        )
        assert product_response.status_code == 200
        updated_product = product_response.json()
        assert updated_product["stock_quantity"] == initial_stock + 25
    
    def test_cancel_purchase_reduces_stock(
        self, client, auth_headers, test_business, test_products, test_suppliers
    ):
        """Test that cancelling a purchase reduces product stock."""
        product = test_products[1]
        supplier = test_suppliers["unregistered"]
        
        # Create purchase
        purchase_data = {
            "supplier_id": supplier.id,
            "purchase_date": "2025-12-10",
            "line_items": [
                {
                    "product_id": product.id,
                    "quantity": 10,
                    "unit_price": product.price,
                    "discount_amount": 0
                }
            ]
        }
        
        response = client.post(
            "/api/purchases/",
            json=purchase_data,
            headers=auth_headers
        )
        assert response.status_code == 200
        purchase = response.json()
        purchase_id = purchase["id"]
        
        # Get stock after purchase
        product_response = client.get(
            f"/api/products/{product.id}",
            headers=auth_headers
        )
        stock_after_purchase = product_response.json()["stock_quantity"]
        
        # Cancel purchase
        cancel_response = client.post(
            f"/api/purchases/{purchase_id}/cancel",
            headers=auth_headers
        )
        assert cancel_response.status_code == 200
        
        # Verify stock reduced
        product_response = client.get(
            f"/api/products/{product.id}",
            headers=auth_headers
        )
        final_stock = product_response.json()["stock_quantity"]
        assert final_stock == stock_after_purchase - 10
    
    def test_purchase_gst_calculation_inter_state(
        self, client, auth_headers, test_business, test_products, test_suppliers
    ):
        """Test GST calculation for inter-state purchase."""
        product = test_products[2]  # 18% GST
        supplier = test_suppliers["registered"]  # Different state (22)
        
        purchase_data = {
            "supplier_id": supplier.id,
            "purchase_date": "2025-12-10",
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
            "/api/purchases/",
            json=purchase_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        purchase = response.json()
        
        # Verify IGST (inter-state)
        assert purchase["total_cgst"] == 0
        assert purchase["total_sgst"] == 0
        assert purchase["total_igst"] > 0
        
        # Taxable: 2 * 3000 = 6000
        # GST 18%: 1080 (IGST)
        assert purchase["subtotal"] == 600000
        assert purchase["total_gst"] == 108000
        assert purchase["grand_total"] == 708000
    
    def test_purchase_gst_calculation_intra_state(
        self, client, auth_headers, test_business, test_products, test_suppliers
    ):
        """Test GST calculation for intra-state purchase."""
        product = test_products[1]  # 12% GST
        supplier = test_suppliers["unregistered"]  # Same state (29)
        
        purchase_data = {
            "supplier_id": supplier.id,
            "purchase_date": "2025-12-10",
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
            "/api/purchases/",
            json=purchase_data,
            headers=auth_headers
        )
        
        assert response.status_code == 200
        purchase = response.json()
        
        # Verify CGST+SGST (intra-state)
        assert purchase["total_cgst"] > 0
        assert purchase["total_sgst"] > 0
        assert purchase["total_igst"] == 0
        assert purchase["total_cgst"] == purchase["total_sgst"]
        
        # Taxable: 3 * 2000 = 6000
        # GST 12%: 720 (CGST 360 + SGST 360)
        assert purchase["subtotal"] == 600000
        assert purchase["total_gst"] == 72000
        assert purchase["grand_total"] == 672000
