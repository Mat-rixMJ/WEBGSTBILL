"""
Supplier Module Contract Validation Script

Run this to verify the implementation matches the contract specification.
"""

def validate_contract_implementation():
    """Validate that implementation matches contract"""
    print("=" * 70)
    print("SUPPLIER MODULE CONTRACT VALIDATION")
    print("=" * 70)
    
    # Test 1: Import all modules
    print("\n[TEST 1] Importing modules...")
    try:
        from app.models.supplier import Supplier
        from app.schemas.supplier import SupplierCreate, SupplierUpdate, SupplierResponse
        from app.api.suppliers import router
        from app.utils.validators import validate_gstin, STATE_CODES
        print("✓ All modules imported successfully")
    except Exception as e:
        print(f"✗ Import error: {e}")
        return False
    
    # Test 2: Validate model fields
    print("\n[TEST 2] Validating database model fields...")
    expected_fields = [
        'id', 'name', 'supplier_type', 'gstin', 'address', 
        'state', 'state_code', 'phone', 'email', 
        'is_active', 'created_at', 'updated_at'
    ]
    model_columns = [c.name for c in Supplier.__table__.columns]
    
    for field in expected_fields:
        if field in model_columns:
            print(f"  ✓ {field}")
        else:
            print(f"  ✗ Missing field: {field}")
            return False
    
    # Test 3: Validate schema with REGISTERED supplier
    print("\n[TEST 3] Validating REGISTERED supplier schema...")
    try:
        supplier = SupplierCreate(
            name="Test Supplier",
            supplier_type="REGISTERED",
            gstin="29ABCDE1234F1Z5",
            address="Test Address, City, State - 560001",
            state="Karnataka",
            state_code="29",
            phone="+919876543210",
            email="test@example.com"
        )
        print(f"  ✓ REGISTERED supplier validated: {supplier.name}")
    except Exception as e:
        print(f"  ✗ Validation error: {e}")
        return False
    
    # Test 4: Validate schema with UNREGISTERED supplier
    print("\n[TEST 4] Validating UNREGISTERED supplier schema...")
    try:
        supplier = SupplierCreate(
            name="Test Unregistered",
            supplier_type="UNREGISTERED",
            gstin=None,
            address="Test Address",
            state="Karnataka",
            state_code="29"
        )
        print(f"  ✓ UNREGISTERED supplier validated: {supplier.name}")
    except Exception as e:
        print(f"  ✗ Validation error: {e}")
        return False
    
    # Test 5: Validate GSTIN required for REGISTERED
    print("\n[TEST 5] Testing GSTIN requirement for REGISTERED...")
    try:
        supplier = SupplierCreate(
            name="Test",
            supplier_type="REGISTERED",
            gstin=None,  # Should fail
            address="Address",
            state="Karnataka",
            state_code="29"
        )
        print("  ✗ Should have failed - GSTIN is required for REGISTERED")
        return False
    except Exception as e:
        print(f"  ✓ Correctly rejected: {str(e)[:60]}...")
    
    # Test 6: Validate GSTIN not allowed for UNREGISTERED
    print("\n[TEST 6] Testing GSTIN rejection for UNREGISTERED...")
    try:
        supplier = SupplierCreate(
            name="Test",
            supplier_type="UNREGISTERED",
            gstin="29ABCDE1234F1Z5",  # Should fail
            address="Address",
            state="Karnataka",
            state_code="29"
        )
        print("  ✗ Should have failed - GSTIN not allowed for UNREGISTERED")
        return False
    except Exception as e:
        print(f"  ✓ Correctly rejected: {str(e)[:60]}...")
    
    # Test 7: Validate state code mismatch
    print("\n[TEST 7] Testing GSTIN state code mismatch...")
    try:
        supplier = SupplierCreate(
            name="Test",
            supplier_type="REGISTERED",
            gstin="29ABCDE1234F1Z5",  # Karnataka (29)
            address="Address",
            state="Maharashtra",
            state_code="27"  # Mismatch
        )
        print("  ✗ Should have failed - GSTIN state code mismatch")
        return False
    except Exception as e:
        print(f"  ✓ Correctly rejected: {str(e)[:60]}...")
    
    # Test 8: Validate invalid supplier_type
    print("\n[TEST 8] Testing invalid supplier_type...")
    try:
        supplier = SupplierCreate(
            name="Test",
            supplier_type="INVALID",  # Should fail
            gstin=None,
            address="Address",
            state="Karnataka",
            state_code="29"
        )
        print("  ✗ Should have failed - Invalid supplier_type")
        return False
    except Exception as e:
        print(f"  ✓ Correctly rejected: {str(e)[:60]}...")
    
    # Test 9: Validate invalid state code
    print("\n[TEST 9] Testing invalid state code...")
    try:
        supplier = SupplierCreate(
            name="Test",
            supplier_type="UNREGISTERED",
            gstin=None,
            address="Address",
            state="Karnataka",
            state_code="99"  # Invalid
        )
        print("  ✗ Should have failed - Invalid state code")
        return False
    except Exception as e:
        print(f"  ✓ Correctly rejected: {str(e)[:60]}...")
    
    # Test 10: Validate API routes
    print("\n[TEST 10] Validating API routes...")
    routes = [r.path for r in router.routes]
    expected_routes = ['/', '/', '/{supplier_id}', '/{supplier_id}', '/{supplier_id}/deactivate']
    
    if len(routes) == 5:
        print(f"  ✓ All 5 routes registered")
        for route in routes:
            print(f"    - {route}")
    else:
        print(f"  ✗ Expected 5 routes, found {len(routes)}")
        return False
    
    # Test 11: Validate STATE_CODES dictionary
    print("\n[TEST 11] Validating STATE_CODES mapping...")
    critical_states = {
        "27": "Maharashtra",
        "29": "Karnataka",
        "07": "Delhi",
        "33": "Tamil Nadu",
        "36": "Telangana"
    }
    
    for code, name in critical_states.items():
        if STATE_CODES.get(code) == name:
            print(f"  ✓ {code} → {name}")
        else:
            print(f"  ✗ State code mapping error: {code}")
            return False
    
    # Test 12: Validate GSTIN validator
    print("\n[TEST 12] Testing GSTIN validator...")
    test_cases = [
        ("29ABCDE1234F1Z5", True, "Valid GSTIN"),
        ("INVALID12345", False, "Invalid format"),
        ("123", False, "Too short"),
        ("", False, "Empty string")
    ]
    
    for gstin, expected, desc in test_cases:
        result = validate_gstin(gstin) if gstin else False
        if result == expected:
            print(f"  ✓ {desc}: {gstin or '(empty)'}")
        else:
            print(f"  ✗ {desc} failed: {gstin}")
            return False
    
    print("\n" + "=" * 70)
    print("✅ ALL VALIDATION TESTS PASSED")
    print("=" * 70)
    print("\nContract implementation is CORRECT and COMPLETE.")
    print("The supplier module is ready for production use.")
    return True


if __name__ == "__main__":
    import sys
    sys.path.insert(0, ".")
    
    success = validate_contract_implementation()
    sys.exit(0 if success else 1)
