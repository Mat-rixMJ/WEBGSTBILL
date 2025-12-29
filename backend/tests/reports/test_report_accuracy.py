"""
Report validation tests.
Verify that report totals match actual invoice data.
"""
import pytest
from datetime import datetime, date


class TestSalesRegisterAccuracy:
    """Test sales register report accuracy."""
    
    def test_sales_register_totals_match_invoices(
        self, client, auth_headers, test_business, test_products, test_customers
    ):
        """Test that sales register totals equal sum of all invoices."""
        customer1 = test_customers["b2c"]
        customer2 = test_customers["b2b"]
        product = test_products[2]  # 18% GST
        
        # Create multiple invoices
        invoices_created = []
        
        # Invoice 1
        inv1_data = {
            "customer_id": customer1.id,
            "invoice_date": "2025-12-15",
            "line_items": [{
                "product_id": product.id,
                "quantity": 2,
                "unit_price": product.price,
                "discount_amount": 0
            }]
        }
        resp1 = client.post("/api/invoices/", json=inv1_data, headers=auth_headers)
        assert resp1.status_code == 200
        invoices_created.append(resp1.json())
        
        # Invoice 2
        inv2_data = {
            "customer_id": customer2.id,
            "invoice_date": "2025-12-16",
            "line_items": [{
                "product_id": product.id,
                "quantity": 3,
                "unit_price": product.price,
                "discount_amount": 0
            }]
        }
        resp2 = client.post("/api/invoices/", json=inv2_data, headers=auth_headers)
        assert resp2.status_code == 200
        invoices_created.append(resp2.json())
        
        # Get sales register
        report_response = client.get(
            "/api/reports/sales?from_date=2025-12-01&to_date=2025-12-31",
            headers=auth_headers
        )
        assert report_response.status_code == 200
        report = report_response.json()
        
        # Calculate expected totals
        expected_subtotal = sum(inv["subtotal"] for inv in invoices_created)
        expected_gst = sum(inv["total_gst"] for inv in invoices_created)
        expected_grand_total = sum(inv["grand_total"] for inv in invoices_created)
        
        # Verify report totals match
        assert report["totals"]["taxable_amount"] == expected_subtotal
        assert report["totals"]["total_gst"] == expected_gst
        assert report["totals"]["total_amount"] == expected_grand_total
        
        # Verify invoice count
        assert report["totals"]["invoice_count"] == 2
    
    def test_cancelled_invoices_excluded_from_totals(
        self, client, auth_headers, test_business, test_products, test_customers
    ):
        """Test that cancelled invoices are excluded from report totals by default."""
        customer = test_customers["b2c"]
        product = test_products[1]
        
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
        
        # Cancel the invoice
        cancel_resp = client.post(
            f"/api/invoices/{invoice['id']}/cancel",
            headers=auth_headers
        )
        assert cancel_resp.status_code == 200
        
        # Get sales register (default: exclude cancelled)
        report_response = client.get(
            "/api/reports/sales?from_date=2025-12-01&to_date=2025-12-31",
            headers=auth_headers
        )
        assert report_response.status_code == 200
        report = report_response.json()
        
        # Totals should be zero
        assert report["totals"]["taxable_amount"] == 0
        assert report["totals"]["total_gst"] == 0
        assert report["totals"]["invoice_count"] == 0
    
    def test_cancelled_invoices_included_when_requested(
        self, client, auth_headers, test_business, test_products, test_customers
    ):
        """Test that cancelled invoices can be included in report."""
        customer = test_customers["b2c"]
        product = test_products[1]
        
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
        
        client.post(f"/api/invoices/{invoice['id']}/cancel", headers=auth_headers)
        
        # Get sales register WITH cancelled invoices
        report_response = client.get(
            "/api/reports/sales?from_date=2025-12-01&to_date=2025-12-31&include_cancelled=true",
            headers=auth_headers
        )
        assert report_response.status_code == 200
        report = report_response.json()
        
        # Should include the cancelled invoice in list but NOT in totals
        assert len(report["invoices"]) == 1
        assert report["invoices"][0]["status"] == "CANCELLED"


class TestGSTSummaryAccuracy:
    """Test GST summary report accuracy."""
    
    def test_gst_summary_matches_sales_and_purchases(
        self, client, auth_headers, test_business, test_products, test_customers, test_suppliers
    ):
        """Test that GST summary correctly aggregates from sales and purchases."""
        customer = test_customers["b2c"]
        supplier = test_suppliers["registered"]
        product = test_products[2]  # 18% GST
        
        # Create one sale
        sale_data = {
            "customer_id": customer.id,
            "invoice_date": "2025-12-15",
            "line_items": [{
                "product_id": product.id,
                "quantity": 2,
                "unit_price": product.price,
                "discount_amount": 0
            }]
        }
        sale_resp = client.post("/api/invoices/", json=sale_data, headers=auth_headers)
        sale = sale_resp.json()
        
        # Create one purchase
        purchase_data = {
            "supplier_id": supplier.id,
            "purchase_date": "2025-12-10",
            "line_items": [{
                "product_id": product.id,
                "quantity": 5,
                "unit_price": product.price,
                "discount_amount": 0
            }]
        }
        purchase_resp = client.post("/api/purchases/", json=purchase_data, headers=auth_headers)
        purchase = purchase_resp.json()
        
        # Get GST summary
        gst_response = client.get(
            "/api/reports/gst-summary?from_date=2025-12-01&to_date=2025-12-31",
            headers=auth_headers
        )
        assert gst_response.status_code == 200
        gst_summary = gst_response.json()
        
        # Verify output GST (from sales)
        assert gst_summary["output_gst"]["total"] == sale["total_gst"]
        
        # Verify input GST (from purchases)
        assert gst_summary["input_gst"]["total"] == purchase["total_gst"]
        
        # Verify net GST payable
        expected_net = sale["total_gst"] - purchase["total_gst"]
        assert gst_summary["net_gst_payable"] == expected_net


class TestCustomerReportAccuracy:
    """Test customer-wise report accuracy."""
    
    def test_customer_report_totals(
        self, client, auth_headers, test_business, test_products, test_customers
    ):
        """Test customer report shows correct totals per customer."""
        customer1 = test_customers["b2c"]
        customer2 = test_customers["b2b"]
        product = test_products[1]
        
        # Create invoices for customer1
        for _ in range(2):
            inv_data = {
                "customer_id": customer1.id,
                "invoice_date": "2025-12-15",
                "line_items": [{
                    "product_id": product.id,
                    "quantity": 1,
                    "unit_price": product.price,
                    "discount_amount": 0
                }]
            }
            client.post("/api/invoices/", json=inv_data, headers=auth_headers)
        
        # Create invoice for customer2
        inv_data = {
            "customer_id": customer2.id,
            "invoice_date": "2025-12-15",
            "line_items": [{
                "product_id": product.id,
                "quantity": 3,
                "unit_price": product.price,
                "discount_amount": 0
            }]
        }
        client.post("/api/invoices/", json=inv_data, headers=auth_headers)
        
        # Get customer report
        report_response = client.get(
            "/api/reports/customers?from_date=2025-12-01&to_date=2025-12-31",
            headers=auth_headers
        )
        assert report_response.status_code == 200
        report = report_response.json()
        
        # Find customer1 in report
        cust1_data = next(c for c in report["customers"] if c["customer_id"] == customer1.id)
        assert cust1_data["invoice_count"] == 2
        
        # Find customer2 in report
        cust2_data = next(c for c in report["customers"] if c["customer_id"] == customer2.id)
        assert cust2_data["invoice_count"] == 1


class TestInventoryReportAccuracy:
    """Test inventory report accuracy."""
    
    def test_inventory_stock_after_transactions(
        self, client, auth_headers, test_business, test_products, test_customers, test_suppliers
    ):
        """Test inventory report reflects current stock after transactions."""
        product = test_products[0]
        customer = test_customers["b2c"]
        supplier = test_suppliers["unregistered"]
        
        initial_stock = product.stock_quantity
        
        # Create purchase (add 50)
        purchase_data = {
            "supplier_id": supplier.id,
            "purchase_date": "2025-12-10",
            "line_items": [{
                "product_id": product.id,
                "quantity": 50,
                "unit_price": product.price,
                "discount_amount": 0
            }]
        }
        client.post("/api/purchases/", json=purchase_data, headers=auth_headers)
        
        # Create sale (remove 20)
        sale_data = {
            "customer_id": customer.id,
            "invoice_date": "2025-12-15",
            "line_items": [{
                "product_id": product.id,
                "quantity": 20,
                "unit_price": product.price,
                "discount_amount": 0
            }]
        }
        client.post("/api/invoices/", json=sale_data, headers=auth_headers)
        
        # Get inventory report
        report_response = client.get(
            "/api/reports/inventory",
            headers=auth_headers
        )
        assert report_response.status_code == 200
        report = report_response.json()
        
        # Find product in report
        product_data = next(p for p in report["products"] if p["product_id"] == product.id)
        
        # Expected stock: initial + 50 - 20
        expected_stock = initial_stock + 50 - 20
        assert product_data["current_stock"] == expected_stock
