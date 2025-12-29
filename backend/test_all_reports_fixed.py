#!/usr/bin/env python3
"""Test all 8 report service functions with database."""
import sys
from datetime import date
from sqlalchemy.orm import Session
from app.database import SessionLocal
from app.services import report_service

def test_reports():
    """Test all 8 report service functions."""
    db = SessionLocal()
    try:
        from_date = date(2025, 12, 1)
        to_date = date(2025, 12, 31)
        as_of_date = date(2025, 12, 31)
        
        print("Testing all 8 report service functions...")
        print("=" * 60)
        
        # Test 1: Sales Register
        print("\n1. Testing generate_sales_register()...")
        sales = report_service.generate_sales_register(db, from_date, to_date)
        print(f"   [OK] Sales Register: {len(sales.rows)} rows")
        print(f"   [OK] Total Taxable: Rs {sales.summary.total_taxable_value:,.2f}")
        print(f"   [OK] Total GST: Rs {sales.summary.total_gst:,.2f}")
        
        # Test 2: Purchase Register
        print("\n2. Testing generate_purchase_register()...")
        purchases = report_service.generate_purchase_register(db, from_date, to_date)
        print(f"   [OK] Purchase Register: {len(purchases.rows)} rows")
        print(f"   [OK] Total Taxable: Rs {purchases.summary.total_taxable_value:,.2f}")
        print(f"   [OK] Total GST: Rs {purchases.summary.total_input_gst:,.2f}")
        
        # Test 3: GST Summary
        print("\n3. Testing generate_gst_summary()...")
        gst_summary = report_service.generate_gst_summary(db, from_date, to_date)
        print(f"   [OK] GST Summary: Output GST Rs {gst_summary.output_gst.total:,.2f}, Input GST Rs {gst_summary.input_gst.total:,.2f}")
        
        # Test 4: Customer Report
        print("\n4. Testing generate_customer_report()...")
        cust_report = report_service.generate_customer_report(db, from_date, to_date)
        print(f"   [OK] Customer Report: {len(cust_report.rows)} customers")
        print(f"   [OK] Total B2B Sales: Rs {cust_report.summary.b2b_sales:,.2f}")
        print(f"   [OK] Total B2C Sales: Rs {cust_report.summary.b2c_sales:,.2f}")
        
        # Test 5: Supplier Report
        print("\n5. Testing generate_supplier_report()...")
        supp_report = report_service.generate_supplier_report(db, from_date, to_date)
        print(f"   [OK] Supplier Report: {len(supp_report.rows)} suppliers")
        print(f"   [OK] Total Registered: Rs {supp_report.summary.registered_purchases:,.2f}")
        print(f"   [OK] Total Unregistered: Rs {supp_report.summary.unregistered_purchases:,.2f}")
        
        # Test 6: Product/HSN Report
        print("\n6. Testing generate_product_hsn_report()...")
        prod_report = report_service.generate_product_hsn_report(db, from_date, to_date)
        print(f"   [OK] Product/HSN Report: {len(prod_report.rows)} HSN codes")
        print(f"   [OK] Total Quantity: {prod_report.summary.total_quantity:,.2f}")
        print(f"   [OK] Total Taxable: Rs {prod_report.summary.total_taxable_value:,.2f}")
        
        # Test 7: Inventory Report
        print("\n7. Testing generate_inventory_report()...")
        inv_report = report_service.generate_inventory_report(db, as_of_date)
        print(f"   [OK] Inventory Report: {len(inv_report.rows)} products")
        if inv_report.rows:
            total_closing = sum(r.closing_stock for r in inv_report.rows)
            print(f"   [OK] Total Closing Stock: {total_closing:,.2f} units")
        
        # Test 8: Business Summary Ledger
        print("\n8. Testing generate_business_summary_ledger()...")
        ledger = report_service.generate_business_summary_ledger(db, from_date, to_date)
        print(f"   [OK] Business Summary Ledger:")
        print(f"       - Total Sales: Rs {ledger.total_sales:,.2f}")
        print(f"       - Total Purchases: Rs {ledger.total_purchases:,.2f}")
        print(f"       - Output GST: Rs {ledger.total_output_gst:,.2f}")
        print(f"       - Input GST: Rs {ledger.total_input_gst:,.2f}")
        print(f"       - Net GST: Rs {ledger.net_gst_position:,.2f}")
        
        # Test 9: GSTR Ready Export
        print("\n9. Testing generate_gstr_ready_export()...")
        gstr = report_service.generate_gstr_ready_export(db, from_date, to_date)
        print(f"   [OK] GSTR Ready Export:")
        print(f"       - B2B Invoices: {len(gstr.b2b_invoices)}")
        print(f"       - B2C States: {len(gstr.b2c_summary)}")
        print(f"       - HSN Codes: {len(gstr.hsn_summary)}")
        print(f"       - Total Output GST: Rs {gstr.total_output_gst:,.2f}")
        
        print("\n" + "=" * 60)
        print("[PASS] All 8 report functions tested successfully!")
        return 0
        
    except Exception as e:
        print(f"\n[FAIL] Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    finally:
        db.close()

if __name__ == '__main__':
    sys.exit(test_reports())
