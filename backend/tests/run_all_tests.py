"""
═══════════════════════════════════════════════════════════
WEBGST - ONE-GO COMPREHENSIVE TEST RUNNER
═══════════════════════════════════════════════════════════
Run all backend tests with a single command.

This script executes:
✓ Unit tests (GST calculations, validators)
✓ Integration tests (invoice flow, purchase flow)
✓ Report validation tests (accuracy checks)
✓ Audit tests (immutability, data integrity)
✓ Edge case tests (validation, error handling)

Usage:
    cd backend
    D:\WEBGST\.venv311\Scripts\python.exe -m pytest tests/run_all_tests.py -v

Or simply:
    pytest tests/run_all_tests.py -v
"""
import pytest
import sys


def run_all_tests():
    """Execute all test suites and report results."""
    
    print("\n" + "="*70)
    print("  WEBGST COMPREHENSIVE TEST SUITE")
    print("="*70 + "\n")
    
    # Test categories
    test_suites = [
        ("UNIT TESTS - GST Calculations", "tests/unit/test_gst_calculator_comprehensive.py"),
        ("INTEGRATION TESTS - Invoice Flow", "tests/integration/test_invoice_flow.py"),
        ("INTEGRATION TESTS - Purchase Flow", "tests/integration/test_purchase_flow.py"),
        ("REPORT VALIDATION TESTS", "tests/reports/test_report_accuracy.py"),
        ("AUDIT TESTS - Immutability", "tests/audit/test_immutability.py"),
        ("EDGE CASE TESTS", "tests/edge_cases/test_validation_and_edge_cases.py"),
    ]
    
    results = []
    
    for suite_name, suite_path in test_suites:
        print(f"\n{'─'*70}")
        print(f"  Running: {suite_name}")
        print(f"{'─'*70}\n")
        
        # Run pytest for this suite
        exit_code = pytest.main([
            suite_path,
            "-v",
            "--tb=short",
            "-p", "no:warnings"
        ])
        
        results.append((suite_name, exit_code == 0))
    
    # Summary report
    print("\n" + "="*70)
    print("  TEST EXECUTION SUMMARY")
    print("="*70 + "\n")
    
    all_passed = True
    for suite_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"  {status:12} {suite_name}")
        if not passed:
            all_passed = False
    
    print("\n" + "="*70)
    
    if all_passed:
        print("  ✅ ALL TESTS PASSED - SYSTEM IS PRODUCTION READY")
    else:
        print("  ❌ SOME TESTS FAILED - SYSTEM NOT PRODUCTION READY")
    
    print("="*70 + "\n")
    
    # Exit with appropriate code
    sys.exit(0 if all_passed else 1)


if __name__ == "__main__":
    run_all_tests()
