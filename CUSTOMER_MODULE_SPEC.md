# GST-Compliant Customer Management Module

## Overview

Complete implementation of Indian GST-compliant customer management supporting both B2B (Business-to-Business) and B2C (Business-to-Consumer) transactions with GSTIN validation and GST portal verification.

---

## 1. DATABASE SCHEMA

### Customers Table

```sql
CREATE TABLE customers (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    customer_type VARCHAR(3) NOT NULL DEFAULT 'B2C',  -- 'B2B' or 'B2C'
    gstin VARCHAR(15),                                -- Required for B2B, NULL for B2C
    address VARCHAR(500) NOT NULL,
    state VARCHAR(100) NOT NULL,                      -- Full state name
    state_code VARCHAR(2) NOT NULL,                   -- 2-digit GST state code
    phone VARCHAR(15),
    email VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,

    INDEX idx_name (name),
    INDEX idx_gstin (gstin),
    INDEX idx_state_code (state_code)
);
```

### Model Properties

- **id**: Auto-increment primary key
- **name**: Customer name (2-255 chars)
- **customer_type**: 'B2B' or 'B2C' (required)
- **gstin**: 15-char GSTIN (required for B2B, NULL for B2C)
- **address**: Complete address (5-500 chars)
- **state**: Full state name (e.g., "Karnataka")
- **state_code**: 2-digit GST state code (e.g., "29")
- **phone**: Optional phone number (max 15 chars)
- **email**: Optional email (max 255 chars)
- **is_active**: Soft delete flag
- **created_at/updated_at**: Timezone-aware timestamps (UTC)

### Computed Property

```python
@property
def is_b2b(self) -> bool:
    """Check if B2B transaction"""
    return self.customer_type == "B2B"
```

---

## 2. GSTIN VALIDATION

### Format Rules

```
GSTIN Format: 2-digit state + 10-char PAN + entity + Z + checksum
Example: 29ABCDE1234F1Z5

Components:
- [0-1]: State code (01-38)
- [2-11]: PAN (5 letters + 4 digits + 1 letter)
- [12]: Entity number (1-9, A-Z)
- [13]: Always 'Z'
- [14]: Checksum digit (0-9, A-Z)
```

### Validation Function

```python
def validate_gstin(gstin: str) -> bool:
    """
    Validate GSTIN format and checksum.

    - Checks 15-character length
    - Validates pattern format
    - Verifies checksum (modulo 36 algorithm)

    Returns: True if valid, False otherwise
    """
```

### State Code Extraction

```python
def extract_state_code_from_gstin(gstin: str) -> str | None:
    """Extract first 2 digits of GSTIN as state code"""
    if validate_gstin(gstin):
        return gstin[:2]
    return None
```

### Business Rules

1. **B2B Customers**: GSTIN is **required**
2. **B2C Customers**: GSTIN must be **NULL** (not allowed)
3. **State Consistency**: GSTIN state code must match customer's state code
4. **Format Validation**: Local validation only (no government API calls)
5. **Checksum Verification**: Modulo 36 algorithm applied

---

## 3. GST PORTAL VERIFICATION

### Implementation Pattern (LEGAL & COMPLIANT)

**URL Format:**

```
https://services.gst.gov.in/services/searchtp?gstin=<GSTIN>
```

**Frontend Implementation:**

```javascript
function verifyOnGSTPortal() {
  const gstin = document.getElementById("gstin").value.trim();

  // Validate format first
  if (!gstin || gstin.length !== 15) {
    alert("Please enter valid GSTIN");
    return;
  }

  // Open GST portal in new tab with GSTIN pre-filled
  const url = `https://services.gst.gov.in/services/searchtp?gstin=${gstin}`;
  window.open(url, "_blank");
}
```

**Rules:**

- ✅ Button shown only for B2B customers
- ✅ GSTIN validated locally before opening link
- ✅ Opens in new browser tab
- ✅ User completes CAPTCHA manually on GST portal
- ✅ No background API calls or automation
- ✅ Legal disclaimer displayed

**Disclaimer Text:**

```
"GSTIN format is validated by the system.
 Final verification is done on the GST portal."
```

**What This Does:**

1. User enters GSTIN in form
2. System validates format locally (pattern + checksum)
3. User clicks "Verify on GST Portal" button
4. GST portal opens in new tab with GSTIN pre-filled
5. User manually completes CAPTCHA on portal
6. User verifies taxpayer details on portal
7. User returns to application and proceeds

**What This Does NOT Do:**

- ❌ No scraping of GST portal
- ❌ No automated verification API calls
- ❌ No storage of "verified" status
- ❌ No government database access
- ❌ No CAPTCHA bypass attempts

---

## 4. API ENDPOINTS

### Base Path: `/api/customers`

#### 1. Create Customer

```
POST /api/customers/
Authorization: Bearer {token}
Content-Type: application/json

Request Body (B2B):
{
    "name": "ABC Trading Pvt Ltd",
    "customer_type": "B2B",
    "gstin": "29ABCDE1234F1Z5",
    "address": "123 MG Road, Jayanagar",
    "state": "Karnataka",
    "state_code": "29",
    "phone": "+91 9876543210",
    "email": "contact@abctrading.com"
}

Request Body (B2C):
{
    "name": "John Doe",
    "customer_type": "B2C",
    "gstin": null,
    "address": "456 Residency Road",
    "state": "Karnataka",
    "state_code": "29",
    "phone": "+91 8765432109",
    "email": null
}

Response: 201 Created
{
    "id": 1,
    "name": "ABC Trading Pvt Ltd",
    "customer_type": "B2B",
    "gstin": "29ABCDE1234F1Z5",
    "address": "123 MG Road, Jayanagar",
    "state": "Karnataka",
    "state_code": "29",
    "phone": "+91 9876543210",
    "email": "contact@abctrading.com",
    "is_active": true,
    "is_b2b": true,
    "created_at": "2025-12-25T06:00:00Z",
    "updated_at": "2025-12-25T06:00:00Z"
}
```

#### 2. List Customers

```
GET /api/customers/?skip=0&limit=100&active_only=true

Response: 200 OK
[
    {
        "id": 1,
        "name": "ABC Trading Pvt Ltd",
        "customer_type": "B2B",
        ...
    }
]
```

#### 3. Get Customer by ID

```
GET /api/customers/{customer_id}

Response: 200 OK
{
    "id": 1,
    "name": "ABC Trading Pvt Ltd",
    ...
}
```

#### 4. Update Customer

```
PUT /api/customers/{customer_id}
Authorization: Bearer {token}
Content-Type: application/json

Request Body (partial update):
{
    "phone": "+91 9999888877",
    "email": "newemail@abctrading.com"
}

Response: 200 OK
{
    "id": 1,
    "phone": "+91 9999888877",
    "email": "newemail@abctrading.com",
    ...
}
```

#### 5. Deactivate Customer

```
PATCH /api/customers/{customer_id}/deactivate
Authorization: Bearer {token}

Response: 204 No Content
```

Note: Sets `is_active = false`, preserving data for historical invoices.

---

## 5. VALIDATION RULES

### Field Validations

| Field         | Rules                                 | Error Message                      |
| ------------- | ------------------------------------- | ---------------------------------- |
| name          | 2-255 chars, required                 | "Name must be 2-255 characters"    |
| customer_type | 'B2B' or 'B2C', required              | "Customer type must be B2B or B2C" |
| gstin         | 15 chars (B2B only), format validated | "Invalid GSTIN format or checksum" |
| address       | 5-500 chars, required                 | "Address must be 5-500 characters" |
| state         | 2-100 chars, required                 | "State is required"                |
| state_code    | 2 digits, valid code, required        | "Invalid state code"               |
| phone         | Max 15 chars, optional                | "Phone too long (max 15)"          |
| email         | Max 255 chars, optional               | "Email too long (max 255)"         |

### Business Validations

#### 1. B2B Requires GSTIN

```python
if customer_type == "B2B" and not gstin:
    raise ValueError("GSTIN is required for B2B customers")
```

#### 2. B2C Cannot Have GSTIN

```python
if customer_type == "B2C" and gstin:
    raise ValueError("B2C customers cannot have GSTIN")
```

#### 3. GSTIN State Must Match Customer State

```python
gstin_state = gstin[:2]
if gstin_state != customer.state_code:
    raise ValueError(
        f"GSTIN state code ({gstin_state}) does not match "
        f"customer state code ({customer.state_code})"
    )
```

---

## 6. STATE CODES MAPPING

### All Indian States & UTs

```python
STATE_CODES = {
    "01": "Jammu and Kashmir",
    "02": "Himachal Pradesh",
    "03": "Punjab",
    "04": "Chandigarh",
    "05": "Uttarakhand",
    "06": "Haryana",
    "07": "Delhi",
    "08": "Rajasthan",
    "09": "Uttar Pradesh",
    "10": "Bihar",
    "11": "Sikkim",
    "12": "Arunachal Pradesh",
    "13": "Nagaland",
    "14": "Manipur",
    "15": "Mizoram",
    "16": "Tripura",
    "17": "Meghalaya",
    "18": "Assam",
    "19": "West Bengal",
    "20": "Jharkhand",
    "21": "Odisha",
    "22": "Chhattisgarh",
    "23": "Madhya Pradesh",
    "24": "Gujarat",
    "26": "Dadra and Nagar Haveli and Daman and Diu",
    "27": "Maharashtra",
    "29": "Karnataka",
    "30": "Goa",
    "31": "Lakshadweep",
    "32": "Kerala",
    "33": "Tamil Nadu",
    "34": "Puducherry",
    "35": "Andaman and Nicobar Islands",
    "36": "Telangana",
    "37": "Andhra Pradesh",
    "38": "Ladakh"
}
```

---

## 7. INVOICE SNAPSHOT BEHAVIOR

### Problem

Customer details can change after invoice creation. Old invoices must remain legally valid with original data.

### Solution

Invoice items table stores customer snapshot:

```sql
CREATE TABLE invoices (
    ...
    customer_id INTEGER,           -- Reference for reports
    customer_name VARCHAR(255),    -- Snapshot
    customer_gstin VARCHAR(15),    -- Snapshot
    customer_address VARCHAR(500), -- Snapshot
    customer_state VARCHAR(100),   -- Snapshot
    customer_state_code VARCHAR(2),-- Snapshot
    ...
);
```

**When creating invoice:**

```python
invoice = Invoice(
    customer_id=customer.id,              # Reference only
    customer_name=customer.name,          # Snapshot
    customer_gstin=customer.gstin,        # Snapshot
    customer_address=customer.address,    # Snapshot
    customer_state=customer.state,        # Snapshot
    customer_state_code=customer.state_code  # Snapshot
)
```

**Result:**

- Changing customer GSTIN later doesn't affect old invoices
- Historical invoices remain legally compliant
- Audit trail preserved for tax purposes

---

## 8. UI IMPLEMENTATION

### Customer Form Fields

#### Required Fields

1. **Customer Name** (text input)

   - Placeholder: "e.g., ABC Trading Pvt Ltd, John Doe"
   - Validation: 2-255 characters

2. **Customer Type** (radio buttons)

   - Options: B2B (Business) | B2C (Consumer)
   - Default: B2C
   - On change: Toggles GSTIN field

3. **GSTIN** (text input)

   - Enabled only for B2B
   - Pattern: `[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}`
   - Auto-uppercase input
   - Real-time format validation
   - Adjacent button: "🔍 Verify on GST Portal"

4. **Address** (textarea)

   - Placeholder: "Complete address with building, street, area"
   - Validation: 5-500 characters

5. **State** (dropdown)

   - All 38 Indian states/UTs
   - Format: "Karnataka (29)"
   - On change: Auto-fills state code

6. **State Code** (read-only)
   - Auto-filled from state selection
   - 2-digit display

#### Optional Fields

- **Phone** (tel input, max 15 chars)
- **Email** (email input, max 255 chars)

### "Verify on GST Portal" Button

**Visibility:**

- Hidden for B2C customers
- Shown only for B2B customers

**Behavior:**

```javascript
onclick = "verifyOnGSTPortal()";

function verifyOnGSTPortal() {
  const gstin = document.getElementById("gstin").value.trim();

  // Validate format
  if (!gstin || gstin.length !== 15) {
    alert("Please enter valid GSTIN");
    return;
  }

  // Open GST portal
  window.open(
    `https://services.gst.gov.in/services/searchtp?gstin=${gstin}`,
    "_blank"
  );
}
```

**Disclaimer (displayed below GSTIN field for B2B):**

```
ℹ️ GSTIN format is validated by the system.
   Final verification is done on the GST portal.
```

### Customer List View

**Table Columns:**

1. Name + Address (truncated)
2. Type (B2B/B2C badge)
3. GSTIN (monospace, or "—" for B2C)
4. State (with code)
5. Contact (phone + email)
6. Status (Active/Inactive badge)
7. Actions (Edit | Deactivate/Activate)

**Features:**

- Search by name or GSTIN
- Filter by customer type (B2B/B2C)
- Filter by active/inactive status
- Color coding: B2B (blue badge), B2C (gray badge)

---

## 9. GST TAX CALCULATION LOGIC

### IGST vs CGST/SGST Decision

**Based on seller and buyer state codes:**

```python
def determine_gst_type(seller_state: str, buyer_state: str) -> str:
    """
    Determine if IGST or CGST+SGST applies

    Returns: 'INTRA' (CGST+SGST) or 'INTER' (IGST)
    """
    if seller_state == buyer_state:
        return 'INTRA'  # CGST + SGST
    else:
        return 'INTER'  # IGST
```

**Example:**

- Seller in Karnataka (29) → Buyer in Karnataka (29) = **CGST + SGST**
- Seller in Karnataka (29) → Buyer in Delhi (07) = **IGST**

### Tax Calculation

**Intra-State (CGST + SGST):**

```python
total_gst_rate = 18%
cgst_rate = 18% / 2 = 9%
sgst_rate = 18% / 2 = 9%

cgst_amount = (taxable_value * 9) / 100
sgst_amount = (taxable_value * 9) / 100
total_tax = cgst_amount + sgst_amount
```

**Inter-State (IGST):**

```python
igst_rate = 18%
igst_amount = (taxable_value * 18) / 100
total_tax = igst_amount
```

---

## 10. TESTING CHECKLIST

### Backend Tests

- [ ] Create B2B customer with valid GSTIN
- [ ] Create B2C customer without GSTIN
- [ ] Reject B2B customer without GSTIN
- [ ] Reject B2C customer with GSTIN
- [ ] Reject invalid GSTIN format
- [ ] Reject invalid GSTIN checksum
- [ ] Reject GSTIN state mismatch
- [ ] Update customer details
- [ ] Deactivate customer (soft delete)
- [ ] List active customers only
- [ ] Filter by customer type

### Frontend Tests

- [ ] Add B2B customer via form
- [ ] Add B2C customer via form
- [ ] GSTIN field enabled for B2B
- [ ] GSTIN field disabled for B2C
- [ ] "Verify on GST Portal" button shown for B2B only
- [ ] Button opens GST portal in new tab
- [ ] State dropdown populates correctly
- [ ] State code auto-fills on state selection
- [ ] Real-time GSTIN validation (green/red border)
- [ ] Search by name works
- [ ] Search by GSTIN works
- [ ] Filter by B2B/B2C works
- [ ] Edit existing customer
- [ ] Deactivate customer

### Integration Tests

- [ ] Create customer → appears in invoice form
- [ ] Deactivate customer → hidden from invoice form
- [ ] Change customer GSTIN → old invoices unaffected
- [ ] Intra-state customer → CGST+SGST invoice
- [ ] Inter-state customer → IGST invoice

---

## 11. EXAMPLE USAGE

### Create B2B Customer

```bash
curl -X POST http://127.0.0.1:8001/api/customers/ \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "ABC Trading Pvt Ltd",
    "customer_type": "B2B",
    "gstin": "29ABCDE1234F1Z5",
    "address": "123 MG Road, Jayanagar",
    "state": "Karnataka",
    "state_code": "29",
    "phone": "+91 9876543210",
    "email": "contact@abctrading.com"
  }'
```

### Create B2C Customer

```bash
curl -X POST http://127.0.0.1:8001/api/customers/ \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "John Doe",
    "customer_type": "B2C",
    "gstin": null,
    "address": "456 Residency Road",
    "state": "Karnataka",
    "state_code": "29",
    "phone": "+91 8765432109"
  }'
```

### Verify GSTIN on Portal

```
https://services.gst.gov.in/services/searchtp?gstin=29ABCDE1234F1Z5
```

---

## 12. PHASE-1 EXCLUSIONS

❌ **Out of Scope:**

- Credit limit tracking
- Payment terms
- Customer groups/categories
- Price lists per customer
- Customer ledger/accounting
- Outstanding balance tracking
- Credit notes/debit notes
- Customer statements
- Multi-contact management
- Shipping vs billing address
- Customer portal login
- Auto-verification of GSTIN status

---

## 13. FILES CREATED/MODIFIED

### Backend

- ✅ `backend/app/models/customer.py` - Updated with customer_type field
- ✅ `backend/app/schemas/customer.py` - Enhanced validation with B2B/B2C rules
- ✅ `backend/app/api/customers.py` - Added PATCH /deactivate endpoint
- ✅ `backend/app/utils/validators.py` - GSTIN validation (already exists)

### Frontend

- ✅ **`frontend/customers.html`** - Complete customer management UI (CREATED)

### Documentation

- ✅ **`CUSTOMER_MODULE_SPEC.md`** - This specification document (CREATED)

---

## 14. SECURITY & COMPLIANCE

### Security Measures

1. **Authentication:** All write operations require Bearer token
2. **Input Validation:** Server-side validation for all fields
3. **SQL Injection:** SQLAlchemy ORM prevents injection
4. **XSS Prevention:** Frontend escapes HTML in customer data
5. **GSTIN Privacy:** No external API calls, local validation only

### GST Compliance

1. **Local Validation:** GSTIN format and checksum verified locally
2. **Manual Verification:** User verifies on official GST portal
3. **No Automation:** No CAPTCHA bypass or automated verification
4. **Audit Trail:** All customer changes timestamped
5. **Invoice Integrity:** Snapshot behavior preserves historical data

### Legal Disclaimer

```
This system validates GSTIN format only.
Final verification must be done on the official GST portal.
The application does not verify GSTIN status with GSTN servers.
```

---

## 15. NEXT STEPS (POST PHASE-1)

1. Customer analytics dashboard
2. Export customer list to CSV/Excel
3. Bulk import via CSV
4. Customer merge functionality
5. Credit limit warnings
6. Outstanding balance tracking
7. Customer communication log
8. Multiple delivery addresses

---

**Document Version:** 1.0  
**Last Updated:** 2025-12-25  
**Author:** GitHub Copilot  
**Compliance:** Indian GST Act 2017, GSTN Guidelines
