# SUPPLIER MODULE CONTRACT SPECIFICATION

## Version: 1.0.0

## Date: 2025-12-25

## Purpose: Single Source of Truth for Supplier (Vendor) Management

---

## ⚠️ CRITICAL: CONTRACT COMPLIANCE

This contract defines the **EXACT** field names, types, and validation rules that MUST be used by:

- Backend API endpoints
- Database models
- Pydantic schemas
- Frontend forms and JavaScript
- All future integrations

**DO NOT rename fields or change validation without updating this contract.**

---

## 📋 SUPPLIER DATA CONTRACT

```json
{
  "name": "string (required, 2-255 chars)",
  "supplier_type": "REGISTERED | UNREGISTERED (required)",
  "gstin": "string | null (15 chars, required for REGISTERED)",
  "address": "string (required, 5-500 chars)",
  "state": "string (required, full state name)",
  "state_code": "string (required, 2-digit code, derived from state)",
  "phone": "string | null (optional, max 15 chars)",
  "email": "string | null (optional, max 255 chars)"
}
```

### Response Contract (includes system fields):

```json
{
  "id": "integer",
  "name": "string",
  "supplier_type": "REGISTERED | UNREGISTERED",
  "gstin": "string | null",
  "address": "string",
  "state": "string",
  "state_code": "string",
  "phone": "string | null",
  "email": "string | null",
  "is_active": "boolean",
  "created_at": "datetime (ISO 8601)",
  "updated_at": "datetime (ISO 8601)"
}
```

---

## ✅ VALIDATION RULES (MANDATORY)

### Rule 1: Supplier Type Validation

- **MUST** be exactly `"REGISTERED"` or `"UNREGISTERED"` (case-sensitive)
- **NO** variations like "Registered", "registered", "reg", etc.
- Backend enforces via regex: `^(REGISTERED|UNREGISTERED)$`

### Rule 2: GSTIN Requirements

- **REGISTERED suppliers:**
  - GSTIN is **REQUIRED** (cannot be null or empty)
  - MUST match format: `^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z]{1}[1-9A-Z]{1}Z[0-9A-Z]{1}$`
  - MUST validate checksum (if `gstin_checksum_enforced=True` in config)
- **UNREGISTERED suppliers:**
  - GSTIN **MUST NOT** be provided (must be null)
  - If provided, API returns `400 Bad Request`

### Rule 3: State Code Matching

- If GSTIN is provided:

  - First 2 digits of GSTIN (state code) **MUST** match `state_code` field
  - Example: GSTIN `27ABC...` requires `state_code="27"` (Maharashtra)
  - Mismatch returns `400 Bad Request`

- State and state_code must be consistent:
  - If `state="Maharashtra"`, then `state_code="27"`
  - Backend validates using `STATE_CODES` mapping

### Rule 4: State Code Validation

- **MUST** be valid 2-digit Indian state code
- Valid codes: `01-38` (not all numbers, see `STATE_CODES` in validators.py)
- Invalid code returns `400 Bad Request`

### Rule 5: Field Length Constraints

| Field         | Min Length | Max Length | Type                   |
| ------------- | ---------- | ---------- | ---------------------- |
| name          | 2          | 255        | string                 |
| supplier_type | -          | -          | enum                   |
| gstin         | 15         | 15         | string (when provided) |
| address       | 5          | 500        | string                 |
| state         | 2          | 100        | string                 |
| state_code    | 2          | 2          | string                 |
| phone         | -          | 15         | string (when provided) |
| email         | -          | 255        | string (when provided) |

---

## 🔐 API ENDPOINTS

### 1. Create Supplier

```
POST /api/suppliers
Content-Type: application/json
Authorization: Bearer <token>

Request Body: SupplierCreate (see contract above)
Response: 201 Created + SupplierResponse
Error: 400 Bad Request (validation failure)
       401 Unauthorized (missing/invalid token)
```

### 2. List Suppliers

```
GET /api/suppliers?skip=0&limit=100&active_only=true
Authorization: Bearer <token>

Response: 200 OK + List[SupplierResponse]
Error: 401 Unauthorized
```

### 3. Get Supplier by ID

```
GET /api/suppliers/{id}
Authorization: Bearer <token>

Response: 200 OK + SupplierResponse
Error: 404 Not Found
       401 Unauthorized
```

### 4. Update Supplier

```
PUT /api/suppliers/{id}
Content-Type: application/json
Authorization: Bearer <token>

Request Body: SupplierUpdate (all fields optional)
Response: 200 OK + SupplierResponse
Error: 400 Bad Request (validation failure)
       404 Not Found
       401 Unauthorized

Note: Editing supplier does NOT affect past purchase invoices.
```

### 5. Deactivate Supplier

```
PATCH /api/suppliers/{id}/deactivate
Authorization: Bearer <token>

Response: 200 OK + {"message": "..."}
Error: 400 Bad Request (already inactive)
       404 Not Found
       401 Unauthorized

Note: Soft delete - sets is_active=False. Historical data preserved.
```

---

## 📝 EXAMPLE PAYLOADS

### Example 1: Create REGISTERED Supplier

```json
{
  "name": "XYZ Chemicals Pvt Ltd",
  "supplier_type": "REGISTERED",
  "gstin": "27ABCDE1234F1Z5",
  "address": "123 Industrial Area, Pune, Maharashtra - 411001",
  "state": "Maharashtra",
  "state_code": "27",
  "phone": "+919876543210",
  "email": "contact@xyzchemicals.com"
}
```

**Success Response (201):**

```json
{
  "id": 1,
  "name": "XYZ Chemicals Pvt Ltd",
  "supplier_type": "REGISTERED",
  "gstin": "27ABCDE1234F1Z5",
  "address": "123 Industrial Area, Pune, Maharashtra - 411001",
  "state": "Maharashtra",
  "state_code": "27",
  "phone": "+919876543210",
  "email": "contact@xyzchemicals.com",
  "is_active": true,
  "created_at": "2025-12-25T12:00:00Z",
  "updated_at": "2025-12-25T12:00:00Z"
}
```

### Example 2: Create UNREGISTERED Supplier

```json
{
  "name": "Local Hardware Store",
  "supplier_type": "UNREGISTERED",
  "gstin": null,
  "address": "Main Street, Village, Karnataka - 560001",
  "state": "Karnataka",
  "state_code": "29",
  "phone": null,
  "email": null
}
```

**Success Response (201):**

```json
{
  "id": 2,
  "name": "Local Hardware Store",
  "supplier_type": "UNREGISTERED",
  "gstin": null,
  "address": "Main Street, Village, Karnataka - 560001",
  "state": "Karnataka",
  "state_code": "29",
  "phone": null,
  "email": null,
  "is_active": true,
  "created_at": "2025-12-25T12:05:00Z",
  "updated_at": "2025-12-25T12:05:00Z"
}
```

### Example 3: Update Supplier (Partial Update)

```json
{
  "phone": "+919988776655",
  "email": "newemail@supplier.com"
}
```

**Success Response (200):** Full supplier object with updated fields

---

## ❌ ERROR EXAMPLES

### Error 1: GSTIN Missing for REGISTERED Supplier

```json
Request:
{
  "name": "ABC Ltd",
  "supplier_type": "REGISTERED",
  "gstin": null,
  "address": "Address",
  "state": "Delhi",
  "state_code": "07"
}

Response (400):
{
  "detail": "GSTIN is required for REGISTERED suppliers"
}
```

### Error 2: GSTIN Provided for UNREGISTERED Supplier

```json
Request:
{
  "name": "Local Supplier",
  "supplier_type": "UNREGISTERED",
  "gstin": "29ABCDE1234F1Z5",
  "address": "Address",
  "state": "Karnataka",
  "state_code": "29"
}

Response (400):
{
  "detail": "GSTIN must not be provided for UNREGISTERED suppliers"
}
```

### Error 3: GSTIN State Code Mismatch

```json
Request:
{
  "name": "ABC Ltd",
  "supplier_type": "REGISTERED",
  "gstin": "29ABCDE1234F1Z5",
  "address": "Address",
  "state": "Maharashtra",
  "state_code": "27"
}

Response (400):
{
  "detail": "GSTIN state code (29) must match supplier state code (27)"
}
```

### Error 4: Invalid GSTIN Format

```json
Request:
{
  "name": "ABC Ltd",
  "supplier_type": "REGISTERED",
  "gstin": "INVALID123",
  "address": "Address",
  "state": "Delhi",
  "state_code": "07"
}

Response (400):
{
  "detail": "Invalid GSTIN format or checksum"
}
```

### Error 5: Invalid State Code

```json
Request:
{
  "name": "ABC Ltd",
  "supplier_type": "UNREGISTERED",
  "gstin": null,
  "address": "Address",
  "state": "Maharashtra",
  "state_code": "99"
}

Response (400):
{
  "detail": "Invalid state code '99'"
}
```

---

## 🎯 BUSINESS RULES

### Rule 1: Soft Delete Only

- Suppliers are **NEVER** hard-deleted from database
- Deactivation sets `is_active=False`
- Inactive suppliers hidden from default listings
- Historical purchase records always retain supplier reference

### Rule 2: Immutable Invoice References

- Editing supplier details does **NOT** update past purchase invoices
- Purchase invoices store supplier snapshot at time of creation
- This ensures audit trail and legal compliance

### Rule 3: Duplicate GSTIN Prevention

- System allows only **ONE active** supplier per GSTIN
- Attempting to create duplicate GSTIN returns `400 Bad Request`
- Inactive suppliers (is_active=False) don't block GSTIN reuse

### Rule 4: No GST Portal Integration

- System validates GSTIN **format and checksum** only
- Does **NOT** verify GSTIN status on GST portal
- Does **NOT** auto-fetch supplier details from government systems
- Manual entry and verification required

---

## 🔄 STATE CODE MAPPING (Reference)

| Code | State Name                               |
| ---- | ---------------------------------------- |
| 01   | Jammu and Kashmir                        |
| 02   | Himachal Pradesh                         |
| 03   | Punjab                                   |
| 04   | Chandigarh                               |
| 05   | Uttarakhand                              |
| 06   | Haryana                                  |
| 07   | Delhi                                    |
| 08   | Rajasthan                                |
| 09   | Uttar Pradesh                            |
| 10   | Bihar                                    |
| 11   | Sikkim                                   |
| 12   | Arunachal Pradesh                        |
| 13   | Nagaland                                 |
| 14   | Manipur                                  |
| 15   | Mizoram                                  |
| 16   | Tripura                                  |
| 17   | Meghalaya                                |
| 18   | Assam                                    |
| 19   | West Bengal                              |
| 20   | Jharkhand                                |
| 21   | Odisha                                   |
| 22   | Chhattisgarh                             |
| 23   | Madhya Pradesh                           |
| 24   | Gujarat                                  |
| 26   | Dadra and Nagar Haveli and Daman and Diu |
| 27   | Maharashtra                              |
| 29   | Karnataka                                |
| 30   | Goa                                      |
| 31   | Lakshadweep                              |
| 32   | Kerala                                   |
| 33   | Tamil Nadu                               |
| 34   | Puducherry                               |
| 35   | Andaman and Nicobar Islands              |
| 36   | Telangana                                |
| 37   | Andhra Pradesh                           |
| 38   | Ladakh                                   |

---

## 🧪 TESTING CHECKLIST

### Backend Tests

- [ ] Create REGISTERED supplier with valid GSTIN succeeds
- [ ] Create UNREGISTERED supplier without GSTIN succeeds
- [ ] Create REGISTERED supplier without GSTIN fails with 400
- [ ] Create UNREGISTERED supplier with GSTIN fails with 400
- [ ] GSTIN state code mismatch fails with 400
- [ ] Invalid GSTIN format fails with 400
- [ ] Invalid state code fails with 400
- [ ] Duplicate GSTIN fails with 400
- [ ] Update supplier with partial data succeeds
- [ ] Deactivate supplier succeeds and sets is_active=False
- [ ] List suppliers filters by active_only correctly
- [ ] Get supplier by ID returns correct data
- [ ] Unauthorized requests fail with 401

### Frontend Tests

- [ ] GSTIN field disabled for UNREGISTERED type
- [ ] GSTIN field enabled and required for REGISTERED type
- [ ] State selection auto-fills state_code
- [ ] GSTIN input auto-selects matching state
- [ ] Client-side validation prevents invalid submissions
- [ ] Error messages display correctly
- [ ] Edit modal pre-fills all fields correctly
- [ ] Deactivate confirmation works
- [ ] Search and filters work correctly
- [ ] Table displays all supplier fields correctly

---

## 📚 IMPLEMENTATION FILES

### Backend

- **Model:** `backend/app/models/supplier.py`
- **Schemas:** `backend/app/schemas/supplier.py`
- **API:** `backend/app/api/suppliers.py`
- **Validators:** `backend/app/utils/validators.py`

### Frontend

- **UI:** `frontend/suppliers.html`

### Documentation

- **Contract:** `SUPPLIER_MODULE_CONTRACT.md` (this file)
- **Purchase Integration:** `SUPPLIER_PURCHASE_CONTRACT.md`

---

## 🔒 CONTRACT VERSION HISTORY

| Version | Date       | Changes                        |
| ------- | ---------- | ------------------------------ |
| 1.0.0   | 2025-12-25 | Initial contract specification |

---

**END OF CONTRACT SPECIFICATION**
