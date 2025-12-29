"""
Test Examples for Supplier Module Contract Validation

This file demonstrates correct and incorrect usage of the supplier API
based on the contract specification in SUPPLIER_MODULE_CONTRACT.md

Run these tests manually via:
1. Start backend: python backend/app/main.py
2. Login to get auth token
3. Execute test requests using curl or Postman
"""

# ============================================================================
# TEST 1: Create REGISTERED Supplier (Valid)
# ============================================================================
print("TEST 1: Create REGISTERED Supplier with Valid GSTIN")
print("=" * 70)
print("""
curl -X POST http://localhost:8000/api/suppliers \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \\
  -d '{
    "name": "Maharashtra Steel Industries Pvt Ltd",
    "supplier_type": "REGISTERED",
    "gstin": "27ABCDE1234F1Z5",
    "address": "Plot 45, Industrial Area, Pune, Maharashtra - 411001",
    "state": "Maharashtra",
    "state_code": "27",
    "phone": "+919876543210",
    "email": "contact@msisteel.com"
  }'

Expected: 201 Created
Response includes: id, is_active=true, created_at, updated_at
""")

# ============================================================================
# TEST 2: Create UNREGISTERED Supplier (Valid)
# ============================================================================
print("\nTEST 2: Create UNREGISTERED Supplier without GSTIN")
print("=" * 70)
print("""
curl -X POST http://localhost:8000/api/suppliers \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \\
  -d '{
    "name": "Local Hardware Store",
    "supplier_type": "UNREGISTERED",
    "gstin": null,
    "address": "Main Street, Village Name, Karnataka - 560001",
    "state": "Karnataka",
    "state_code": "29",
    "phone": null,
    "email": null
  }'

Expected: 201 Created
Response: gstin=null, phone=null, email=null
""")

# ============================================================================
# TEST 3: Missing GSTIN for REGISTERED Supplier (Invalid)
# ============================================================================
print("\nTEST 3: REGISTERED Supplier without GSTIN (Should FAIL)")
print("=" * 70)
print("""
curl -X POST http://localhost:8000/api/suppliers \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \\
  -d '{
    "name": "ABC Industries",
    "supplier_type": "REGISTERED",
    "gstin": null,
    "address": "123 Street, Delhi - 110001",
    "state": "Delhi",
    "state_code": "07"
  }'

Expected: 400 Bad Request
Error: "GSTIN is required for REGISTERED suppliers"
""")

# ============================================================================
# TEST 4: GSTIN Provided for UNREGISTERED Supplier (Invalid)
# ============================================================================
print("\nTEST 4: UNREGISTERED Supplier with GSTIN (Should FAIL)")
print("=" * 70)
print("""
curl -X POST http://localhost:8000/api/suppliers \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \\
  -d '{
    "name": "Small Local Vendor",
    "supplier_type": "UNREGISTERED",
    "gstin": "29ABCDE1234F1Z5",
    "address": "Village Road, Karnataka - 560001",
    "state": "Karnataka",
    "state_code": "29"
  }'

Expected: 400 Bad Request
Error: "GSTIN must not be provided for UNREGISTERED suppliers"
""")

# ============================================================================
# TEST 5: GSTIN State Code Mismatch (Invalid)
# ============================================================================
print("\nTEST 5: GSTIN State Code Mismatch (Should FAIL)")
print("=" * 70)
print("""
curl -X POST http://localhost:8000/api/suppliers \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \\
  -d '{
    "name": "Mismatched State Supplier",
    "supplier_type": "REGISTERED",
    "gstin": "29ABCDE1234F1Z5",
    "address": "Mumbai, Maharashtra - 400001",
    "state": "Maharashtra",
    "state_code": "27"
  }'

Expected: 400 Bad Request
Error: "GSTIN state code (29) must match supplier state code (27)"
""")

# ============================================================================
# TEST 6: Invalid GSTIN Format (Invalid)
# ============================================================================
print("\nTEST 6: Invalid GSTIN Format (Should FAIL)")
print("=" * 70)
print("""
curl -X POST http://localhost:8000/api/suppliers \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \\
  -d '{
    "name": "Invalid GSTIN Supplier",
    "supplier_type": "REGISTERED",
    "gstin": "INVALID12345",
    "address": "123 Street, Delhi - 110001",
    "state": "Delhi",
    "state_code": "07"
  }'

Expected: 400 Bad Request
Error: "Invalid GSTIN format or checksum"
""")

# ============================================================================
# TEST 7: Invalid State Code (Invalid)
# ============================================================================
print("\nTEST 7: Invalid State Code (Should FAIL)")
print("=" * 70)
print("""
curl -X POST http://localhost:8000/api/suppliers \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \\
  -d '{
    "name": "Invalid State Code Supplier",
    "supplier_type": "UNREGISTERED",
    "gstin": null,
    "address": "123 Street, Maharashtra",
    "state": "Maharashtra",
    "state_code": "99"
  }'

Expected: 400 Bad Request
Error: "Invalid state code '99'"
""")

# ============================================================================
# TEST 8: List All Suppliers (Valid)
# ============================================================================
print("\nTEST 8: List All Active Suppliers")
print("=" * 70)
print("""
curl -X GET http://localhost:8000/api/suppliers?active_only=true&limit=100 \\
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

Expected: 200 OK
Response: Array of supplier objects
""")

# ============================================================================
# TEST 9: Get Supplier by ID (Valid)
# ============================================================================
print("\nTEST 9: Get Supplier by ID")
print("=" * 70)
print("""
curl -X GET http://localhost:8000/api/suppliers/1 \\
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

Expected: 200 OK (if exists), 404 Not Found (if doesn't exist)
Response: Single supplier object
""")

# ============================================================================
# TEST 10: Update Supplier (Valid)
# ============================================================================
print("\nTEST 10: Update Supplier (Partial Update)")
print("=" * 70)
print("""
curl -X PUT http://localhost:8000/api/suppliers/1 \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \\
  -d '{
    "phone": "+919988776655",
    "email": "newemail@supplier.com"
  }'

Expected: 200 OK
Response: Updated supplier object with new phone and email
Note: Past purchase invoices NOT affected
""")

# ============================================================================
# TEST 11: Deactivate Supplier (Valid)
# ============================================================================
print("\nTEST 11: Deactivate Supplier (Soft Delete)")
print("=" * 70)
print("""
curl -X PATCH http://localhost:8000/api/suppliers/1/deactivate \\
  -H "Authorization: Bearer YOUR_TOKEN_HERE"

Expected: 200 OK
Response: {"message": "Supplier 'Name' deactivated successfully"}
Note: Supplier still in database with is_active=false
""")

# ============================================================================
# TEST 12: Unauthorized Access (Invalid)
# ============================================================================
print("\nTEST 12: Unauthorized Access (Should FAIL)")
print("=" * 70)
print("""
curl -X GET http://localhost:8000/api/suppliers

Expected: 401 Unauthorized
Error: Missing or invalid authentication token
""")

# ============================================================================
# TEST 13: Duplicate GSTIN (Invalid)
# ============================================================================
print("\nTEST 13: Create Supplier with Duplicate GSTIN (Should FAIL)")
print("=" * 70)
print("""
# First, create a supplier with GSTIN 27ABCDE1234F1Z5
# Then try to create another with the same GSTIN:

curl -X POST http://localhost:8000/api/suppliers \\
  -H "Content-Type: application/json" \\
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \\
  -d '{
    "name": "Another Supplier",
    "supplier_type": "REGISTERED",
    "gstin": "27ABCDE1234F1Z5",
    "address": "Different Address, Maharashtra",
    "state": "Maharashtra",
    "state_code": "27"
  }'

Expected: 400 Bad Request
Error: "Supplier with GSTIN 27ABCDE1234F1Z5 already exists"
""")

# ============================================================================
# PYTHON CODE EXAMPLES
# ============================================================================
print("\n" + "=" * 70)
print("PYTHON CODE EXAMPLES")
print("=" * 70)

print("""
# Example 1: Valid REGISTERED Supplier
valid_registered_supplier = {
    "name": "TechSupply Industries Pvt Ltd",
    "supplier_type": "REGISTERED",
    "gstin": "29ABCDE1234F1Z5",
    "address": "Plot 78, Electronics City, Bangalore, Karnataka - 560100",
    "state": "Karnataka",
    "state_code": "29",
    "phone": "+919876543210",
    "email": "contact@techsupply.com"
}

# Example 2: Valid UNREGISTERED Supplier
valid_unregistered_supplier = {
    "name": "Local Stationery Mart",
    "supplier_type": "UNREGISTERED",
    "gstin": None,
    "address": "Shop 5, Main Road, Chennai, Tamil Nadu - 600001",
    "state": "Tamil Nadu",
    "state_code": "33",
    "phone": "+919876543211",
    "email": "local@stationery.com"
}

# Example 3: Invalid - Missing GSTIN for REGISTERED
invalid_missing_gstin = {
    "name": "Invalid Supplier",
    "supplier_type": "REGISTERED",  # REGISTERED requires GSTIN
    "gstin": None,  # ❌ This will fail
    "address": "Address",
    "state": "Delhi",
    "state_code": "07"
}

# Example 4: Invalid - GSTIN for UNREGISTERED
invalid_gstin_unregistered = {
    "name": "Invalid Supplier",
    "supplier_type": "UNREGISTERED",  # UNREGISTERED cannot have GSTIN
    "gstin": "29ABCDE1234F1Z5",  # ❌ This will fail
    "address": "Address",
    "state": "Karnataka",
    "state_code": "29"
}

# Example 5: Invalid - State Code Mismatch
invalid_state_mismatch = {
    "name": "Invalid Supplier",
    "supplier_type": "REGISTERED",
    "gstin": "29ABCDE1234F1Z5",  # Karnataka (29)
    "address": "Address in Maharashtra",
    "state": "Maharashtra",
    "state_code": "27"  # ❌ Mismatch: GSTIN says 29, state_code says 27
}
""")

# ============================================================================
# FRONTEND VALIDATION CHECKLIST
# ============================================================================
print("\n" + "=" * 70)
print("FRONTEND VALIDATION CHECKLIST")
print("=" * 70)

print("""
✅ Frontend MUST validate:

1. Supplier Type Selection:
   - Radio buttons for REGISTERED / UNREGISTERED
   - Default to UNREGISTERED
   
2. GSTIN Field Behavior:
   - DISABLED when supplier_type = UNREGISTERED
   - ENABLED and REQUIRED when supplier_type = REGISTERED
   - Auto-uppercase input
   - Format validation: ^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$
   
3. State Selection:
   - Dropdown with all Indian states
   - Auto-fill state_code when state selected
   
4. State Code Derivation:
   - Auto-fill from GSTIN first 2 digits
   - Auto-fill from state selection
   - Read-only field (user cannot edit directly)
   - Validate match between GSTIN and state_code
   
5. Client-Side Validation Before Submit:
   - Check supplier_type = REGISTERED → gstin must be present
   - Check supplier_type = UNREGISTERED → gstin must be null
   - Check gstin state code matches state_code field
   - Check state matches state_code
   
6. Error Display:
   - Clear, user-friendly error messages
   - Highlight invalid fields
   - Scroll to error message
   
7. Form Reset:
   - Clear all fields when adding new supplier
   - Pre-fill fields when editing existing supplier
   - Reset validation states
""")

# ============================================================================
# STATE CODE QUICK REFERENCE
# ============================================================================
print("\n" + "=" * 70)
print("STATE CODE QUICK REFERENCE (Top 10 Most Common)")
print("=" * 70)

print("""
Code | State Name
-----|------------------
27   | Maharashtra
29   | Karnataka
33   | Tamil Nadu
07   | Delhi
24   | Gujarat
36   | Telangana
37   | Andhra Pradesh
09   | Uttar Pradesh
19   | West Bengal
32   | Kerala

Full list in SUPPLIER_MODULE_CONTRACT.md
""")

print("\n" + "=" * 70)
print("END OF TEST EXAMPLES")
print("=" * 70)
