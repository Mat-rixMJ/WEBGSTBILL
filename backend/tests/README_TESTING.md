# WebGST - Comprehensive Testing Documentation

## 🎯 One-Go Testing System

This testing system allows you to verify **ALL** functionality of the GST billing application with a **SINGLE COMMAND**.

## 📁 Test Structure

```
backend/tests/
├── conftest.py                     # Shared fixtures (test data)
├── run_all_tests.py                # Master test runner
│
├── unit/                           # Unit Tests
│   └── test_gst_calculator_comprehensive.py
│       ├── GST calculation (CGST/SGST vs IGST)
│       ├── All GST rates (0%, 5%, 12%, 18%, 28%)
│       ├── Rounding rules
│       └── Invoice total calculations
│
├── integration/                    # Integration Tests
│   ├── test_invoice_flow.py
│   │   ├── Invoice creation → stock reduction
│   │   ├── Invoice cancellation → stock restoration
│   │   ├── Insufficient stock prevention
│   │   ├── GST calculations (intra/inter-state)
│   │   └── Sequential invoice numbering
│   │
│   └── test_purchase_flow.py
│       ├── Purchase creation → stock increase
│       ├── Purchase cancellation → stock reduction
│       └── GST calculations (intra/inter-state)
│
├── reports/                        # Report Validation Tests
│   └── test_report_accuracy.py
│       ├── Sales register totals = sum of invoices
│       ├── Cancelled invoices excluded from totals
│       ├── GST summary = sales GST - purchase GST
│       ├── Customer report accuracy
│       └── Inventory report = actual stock
│
├── audit/                          # Immutability Tests
│   └── test_immutability.py
│       ├── Cannot edit finalized invoice
│       ├── Cannot delete finalized invoice
│       ├── Can only cancel
│       ├── Product price change doesn't affect past invoices
│       └── Customer change doesn't affect past invoices
│
└── edge_cases/                     # Edge Case & Validation Tests
    └── test_validation_and_edge_cases.py
        ├── Invalid GSTIN rejected
        ├── Invalid GST rate rejected
        ├── Negative quantity/price rejected
        ├── Manipulated totals recalculated
        ├── Zero GST products
        ├── Large quantities
        └── Empty line items rejected
```

## 🚀 Running Tests

### Option 1: PowerShell Script (Recommended)

```powershell
cd D:\WEBGST
.\run_all_tests.ps1
```

### Option 2: Direct Python

```powershell
cd D:\WEBGST\backend
D:\WEBGST\.venv311\Scripts\python.exe -m pytest tests/run_all_tests.py -v
```

### Option 3: Run Specific Test Category

```powershell
# Unit tests only
pytest tests/unit/ -v

# Integration tests only
pytest tests/integration/ -v

# Report validation only
pytest tests/reports/ -v

# Audit tests only
pytest tests/audit/ -v

# Edge cases only
pytest tests/edge_cases/ -v
```

## 📊 Test Data (Shared Fixtures)

All tests use consistent test data defined in `conftest.py`:

### Business Profile
- **Name**: Test GST Business Pvt Ltd
- **GSTIN**: 29ABCDE1234F1Z5
- **State**: Karnataka (29)

### Products (4 items with different GST rates)
1. **Product 5% GST** - Rs 1000.00, HSN: 1001, Stock: 100
2. **Product 12% GST** - Rs 2000.00, HSN: 2002, Stock: 50
3. **Product 18% GST** - Rs 3000.00, HSN: 3003, Stock: 30
4. **Product 28% GST** - Rs 5000.00, HSN: 4004, Stock: 20

### Customers (3 types)
1. **B2B Inter-state** - Maharashtra (27), GSTIN: 27XYZAB5678C1Z9
2. **B2C Intra-state** - Karnataka (29), No GSTIN
3. **B2B Intra-state** - Karnataka (29), GSTIN: 29PQRST1234D1Z6

### Suppliers (2 types)
1. **Registered** - Chhattisgarh (22), GSTIN: 22LMNOP5678E1Z7
2. **Unregistered** - Karnataka (29), No GSTIN

## ✅ Test Coverage

### 1️⃣ Unit Tests (GST Calculation Logic)
- ✓ CGST+SGST for intra-state transactions
- ✓ IGST for inter-state transactions
- ✓ All GST rates: 0%, 5%, 12%, 18%, 28%
- ✓ Rounding to nearest paisa
- ✓ Multiple line items with different GST rates
- ✓ Discount handling

### 2️⃣ API Integration Tests (Full Workflows)
- ✓ Invoice creation reduces stock
- ✓ Invoice cancellation restores stock
- ✓ Insufficient stock prevents invoice
- ✓ Correct GST split (intra/inter-state)
- ✓ Purchase creation increases stock
- ✓ Purchase cancellation reduces stock
- ✓ Sequential invoice numbering

### 3️⃣ Report Validation Tests (Data Accuracy)
- ✓ Sales register totals = sum of invoices
- ✓ Cancelled invoices excluded (default)
- ✓ Cancelled invoices included when requested
- ✓ GST summary = output GST - input GST
- ✓ Customer report shows correct per-customer totals
- ✓ Inventory report reflects actual stock after transactions

### 4️⃣ Audit & Immutability Tests (Data Integrity)
- ✓ Cannot edit finalized invoice
- ✓ Cannot delete finalized invoice
- ✓ Can only cancel finalized invoice
- ✓ Cannot cancel already cancelled invoice
- ✓ Product price change doesn't affect historical invoices
- ✓ Customer detail change doesn't affect historical invoices

### 5️⃣ Edge Case & Validation Tests (Error Handling)
- ✓ Invalid GSTIN format rejected
- ✓ Invalid GST rate rejected
- ✓ Negative quantity rejected
- ✓ Negative price rejected
- ✓ Missing required fields rejected
- ✓ Manipulated subtotals recalculated by backend
- ✓ Discount exceeding price rejected
- ✓ Zero GST products allowed
- ✓ Very large quantities handled
- ✓ Future date invoices handled
- ✓ Empty line items rejected
- ✓ Duplicate products in invoice handled

## 🎯 Success Criteria

Tests will **PASS** only if:
- ✅ All GST calculations are accurate
- ✅ Stock management is consistent
- ✅ Report totals match source data
- ✅ Invoices are immutable after finalization
- ✅ Invalid inputs are rejected
- ✅ Backend recalculates totals (ignores manipulated frontend data)

Tests will **FAIL** if:
- ❌ Report totals ≠ sum of invoices
- ❌ GST split is wrong
- ❌ Inventory mismatch occurs
- ❌ Invoices can be edited/deleted
- ❌ Invalid data is accepted
- ❌ Stock is not managed correctly

## 📈 Test Output

### Successful Run
```
═══════════════════════════════════════════════════════════
  TEST EXECUTION SUMMARY
═══════════════════════════════════════════════════════════

  ✅ PASSED     UNIT TESTS - GST Calculations
  ✅ PASSED     INTEGRATION TESTS - Invoice Flow
  ✅ PASSED     INTEGRATION TESTS - Purchase Flow
  ✅ PASSED     REPORT VALIDATION TESTS
  ✅ PASSED     AUDIT TESTS - Immutability
  ✅ PASSED     EDGE CASE TESTS

═══════════════════════════════════════════════════════════
  ✅ ALL TESTS PASSED - SYSTEM IS PRODUCTION READY
═══════════════════════════════════════════════════════════
```

### Failed Run
```
═══════════════════════════════════════════════════════════
  TEST EXECUTION SUMMARY
═══════════════════════════════════════════════════════════

  ✅ PASSED     UNIT TESTS - GST Calculations
  ❌ FAILED     INTEGRATION TESTS - Invoice Flow
  ✅ PASSED     INTEGRATION TESTS - Purchase Flow
  ❌ FAILED     REPORT VALIDATION TESTS
  ✅ PASSED     AUDIT TESTS - Immutability
  ✅ PASSED     EDGE CASE TESTS

═══════════════════════════════════════════════════════════
  ❌ SOME TESTS FAILED - SYSTEM NOT PRODUCTION READY
═══════════════════════════════════════════════════════════
```

## 🔧 Dependencies

Add to `backend/requirements.txt`:
```
pytest==8.0.0
pytest-cov==4.1.0
httpx==0.26.0
```

Install:
```powershell
D:\WEBGST\.venv311\Scripts\pip install pytest pytest-cov httpx
```

## 🎭 Frontend Smoke Tests (Optional - Future Enhancement)

For complete end-to-end testing, add Playwright/Selenium tests:

```javascript
// tests/frontend/smoke_tests.js
test('Login page loads', async ({ page }) => {
  await page.goto('http://127.0.0.1:3000');
  await expect(page.locator('h1')).toContainText('Login');
});

test('Dashboard loads after login', async ({ page }) => {
  // Login
  await page.goto('http://127.0.0.1:3000');
  await page.fill('#username', 'testuser');
  await page.fill('#password', 'testpass123');
  await page.click('button[type="submit"]');
  
  // Verify dashboard
  await expect(page).toHaveURL('http://127.0.0.1:3000/dashboard.html');
});
```

## 📝 Adding New Tests

1. **For unit tests**: Add to `tests/unit/`
2. **For API integration**: Add to `tests/integration/`
3. **For report validation**: Add to `tests/reports/`
4. **For audit/immutability**: Add to `tests/audit/`
5. **For edge cases**: Add to `tests/edge_cases/`

Use existing fixtures from `conftest.py` for consistency.

## 🚨 Important Notes

1. **Isolated Database**: Tests use `test_webgst.db` (separate from production)
2. **Fresh State**: Each test gets a clean database
3. **No Mocks**: All GST logic is tested with real calculations
4. **Real API Calls**: Uses FastAPI TestClient (not mocked)
5. **Idempotent**: Tests can be run multiple times safely

## 🎉 Continuous Integration

Add to GitHub Actions (`.github/workflows/test.yml`):

```yaml
name: Test Suite
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      - run: pip install -r backend/requirements.txt
      - run: cd backend && pytest tests/run_all_tests.py -v
```

---

**Created by**: GitHub Copilot  
**Date**: December 29, 2025  
**Purpose**: Comprehensive one-go testing system for WebGST billing application
