# Supplier & Purchase Module Contract

**Date:** December 25, 2025  
**Status:** ✅ Aligned & Validated

## Summary

This document confirms that the supplier and purchase modules are now fully aligned between backend and frontend per the shared contract specification.

---

## Supplier Module

### Contract

**Request (Create/Update):**

```json
{
  "name": "string (required)",
  "supplier_type": "REGISTERED | UNREGISTERED",
  "gstin": "string | null",
  "address": "string (required)",
  "state": "string (required)",
  "phone": "string | null",
  "email": "string | null"
}
```

**Response:**

```json
{
  "id": "int",
  "name": "string",
  "supplier_type": "Registered | Unregistered",
  "gstin": "string | null",
  "address": "string",
  "state": "string",
  "state_code": "string (derived)",
  "phone": "string | null",
  "email": "string | null",
  "is_active": "boolean",
  "created_at": "ISO-8601",
  "updated_at": "ISO-8601"
}
```

### Validation Rules

✅ **GSTIN Required for REGISTERED suppliers**

- Frontend validates format: `^[0-9]{2}[A-Z]{5}[0-9]{4}[A-Z][1-9A-Z]Z[0-9A-Z]$`
- Frontend validates state code match (first 2 digits = state code)
- Frontend validates checksum (modulo-36 algorithm)
- Backend enforces same validations

✅ **GSTIN Must NOT be provided for UNREGISTERED suppliers**

- Frontend clears and disables GSTIN field when UNREGISTERED selected
- Backend rejects GSTIN for UNREGISTERED

✅ **State Code Derived Server-Side**

- Frontend does NOT send `state_code`
- Backend derives from `state` using `STATE_CODE_MAP`

### API Endpoints

| Method | Endpoint                         | Purpose                                     |
| ------ | -------------------------------- | ------------------------------------------- |
| POST   | `/api/suppliers`                 | Create supplier                             |
| GET    | `/api/suppliers`                 | List suppliers (returns `{ value, Count }`) |
| GET    | `/api/suppliers/{id}`            | Get single supplier                         |
| PUT    | `/api/suppliers/{id}`            | Update supplier                             |
| PATCH  | `/api/suppliers/{id}/deactivate` | Soft delete                                 |

### Frontend Changes

- ✅ Changed supplier type values to uppercase (`REGISTERED`, `UNREGISTERED`)
- ✅ Added STATE_CODE_MAP matching backend
- ✅ Implemented GSTIN checksum validation
- ✅ Switched deactivation to PATCH endpoint
- ✅ Normalize GSTIN to uppercase before submit

**Files:** [frontend/suppliers.html](frontend/suppliers.html)

### Backend Changes

- ✅ Accept uppercase supplier_type and normalize to canonical form
- ✅ Added PATCH `/api/suppliers/{id}/deactivate` endpoint

**Files:** [backend/app/schemas/supplier.py](backend/app/schemas/supplier.py), [backend/app/api/suppliers.py](backend/app/api/suppliers.py)

---

## Purchase Module

### Contract

**Request (Create):**

```json
{
  "supplier_id": "int",
  "supplier_invoice_number": "string",
  "supplier_invoice_date": "date (ISO-8601)",
  "purchase_date": "date (ISO-8601)",
  "items": [
    {
      "item_name": "string",
      "hsn_code": "string (4/6/8 digits, numeric)",
      "quantity": "number (> 0)",
      "unit_rate": "int (paise, > 0)",
      "gst_rate": "0 | 5 | 12 | 18 | 28"
    }
  ]
}
```

**Response:**

```json
{
  "id": "int",
  "supplier_id": "int",
  "supplier_invoice_number": "string",
  "supplier_invoice_date": "ISO-8601",
  "purchase_date": "ISO-8601",
  "place_of_supply": "string (derived from supplier)",
  "place_of_supply_code": "string",
  "total_quantity": "number",
  "subtotal_value": "int (paise)",
  "cgst_amount": "int (paise)",
  "sgst_amount": "int (paise)",
  "igst_amount": "int (paise)",
  "total_gst": "int (paise)",
  "total_amount": "int (paise)",
  "status": "Draft | Finalized | Cancelled",
  "items": [
    {
      "id": "int",
      "item_name": "string",
      "hsn_code": "string",
      "quantity": "number",
      "unit_rate": "int (paise)",
      "gst_rate": "int",
      "subtotal": "int (paise)",
      "cgst_amount": "int (paise)",
      "sgst_amount": "int (paise)",
      "igst_amount": "int (paise)",
      "total_amount": "int (paise)",
      "tax_type": "CGST_SGST | IGST"
    }
  ]
}
```

### GST Calculation Logic

**Same State (Supplier state = Business state):**

```
Input CGST = (subtotal × gst_rate ÷ 2) ÷ 100
Input SGST = (subtotal × gst_rate ÷ 2) ÷ 100
Input IGST = 0
tax_type = "CGST_SGST"
```

**Different State:**

```
Input CGST = 0
Input SGST = 0
Input IGST = (subtotal × gst_rate) ÷ 100
tax_type = "IGST"
```

**Implementation:** [backend/app/services/purchase_gst_calculator.py](backend/app/services/purchase_gst_calculator.py)

### Validation Rules

✅ **HSN Code**: Numeric, 4/6/8 digits
✅ **Quantity**: Greater than 0
✅ **Unit Rate**: Positive integer in paise
✅ **GST Rate**: Must be 0, 5, 12, 18, or 28
✅ **Items**: At least one item required

### API Endpoints

| Method | Endpoint                       | Purpose                                     |
| ------ | ------------------------------ | ------------------------------------------- |
| POST   | `/api/purchases`               | Create purchase (Draft)                     |
| GET    | `/api/purchases`               | List purchases (returns `{ value, Count }`) |
| GET    | `/api/purchases/{id}`          | Get single purchase with items              |
| POST   | `/api/purchases/{id}/finalize` | Lock invoice & update stock                 |
| POST   | `/api/purchases/{id}/cancel`   | Cancel with reason                          |

### Frontend Changes

- ✅ Fetch business profile to get state code for GST preview
- ✅ Calculate CGST/SGST vs IGST based on supplier vs business state
- ✅ Convert rupees to paise for `unit_rate` before submit
- ✅ Added HSN validation (numeric, 4/6/8 digits)
- ✅ Bind event handlers for form submission
- ✅ Display tax breakdown in preview summary

**Files:** [frontend/purchases.html](frontend/purchases.html)

### Backend Changes

- ✅ Purchase API already aligned with contract
- ✅ GST calculator uses supplier state vs business state
- ✅ Stores tax snapshot immutably

**Files:** [backend/app/api/purchases.py](backend/app/api/purchases.py), [backend/app/services/purchase_gst_calculator.py](backend/app/services/purchase_gst_calculator.py)

---

## Key Alignment Points

### 1. Type Casing

- Frontend sends: `REGISTERED` / `UNREGISTERED`
- Backend accepts both and normalizes to: `Registered` / `Unregistered`
- Backend stores canonical form

### 2. Money Units

- Frontend displays rupees (₹)
- Frontend converts to paise before submit
- Backend stores and returns paise
- Frontend converts back to rupees for display

### 3. Date Formats

- Frontend sends ISO-8601 datetime strings
- Backend accepts and stores datetime objects
- Backend returns ISO-8601 strings

### 4. List Responses

- Both endpoints return `{ value: [], Count: number }`
- Frontend expects and parses this structure

### 5. State Code Handling

- Frontend has `STATE_CODE_MAP` matching backend
- Frontend never sends `state_code`
- Backend derives from `state` name

### 6. GSTIN Validation

- Frontend validates format, state match, checksum
- Backend validates same rules
- Consistent error messages

### 7. HSN Validation

- Frontend validates numeric and length (4/6/8)
- Backend validates same
- Prevents invalid data from reaching server

---

## Testing Status

### Servers

- ✅ Backend running on http://127.0.0.1:8001
- ✅ Frontend running on http://127.0.0.1:3000
- ✅ Health check passed

### Manual Test Cases

**Supplier Module:**

1. ✅ Create REGISTERED supplier with valid GSTIN
2. ✅ Create UNREGISTERED supplier without GSTIN
3. ✅ Reject REGISTERED supplier without GSTIN
4. ✅ Reject UNREGISTERED supplier with GSTIN
5. ✅ Validate GSTIN state code matches supplier state
6. ✅ Deactivate supplier via PATCH endpoint

**Purchase Module:**

1. ✅ Create purchase with intra-state supplier (CGST+SGST)
2. ✅ Create purchase with inter-state supplier (IGST)
3. ✅ Validate HSN numeric and length
4. ✅ Convert rupees to paise correctly
5. ✅ Preview shows correct tax breakdown
6. ✅ Finalize updates stock for matching HSN products
7. ✅ Cancel records reason without stock reversal

---

## Files Modified

### Backend

- [backend/app/schemas/supplier.py](backend/app/schemas/supplier.py) - Normalize supplier_type
- [backend/app/api/suppliers.py](backend/app/api/suppliers.py) - Add PATCH deactivate endpoint

### Frontend

- [frontend/suppliers.html](frontend/suppliers.html) - Full contract alignment
- [frontend/purchases.html](frontend/purchases.html) - Full contract alignment

---

## Next Steps (Optional Enhancements)

- [ ] Add automated integration tests
- [ ] Add unit tests for GST calculator edge cases
- [ ] Add validation for supplier invoice duplicate detection
- [ ] Add bulk import for suppliers
- [ ] Add purchase edit (if status = Draft)
- [ ] Add stock reversal on cancellation (Phase-1.5+)

---

**Contract Status:** ✅ **FULLY ALIGNED**

Both backend and frontend now follow a single shared contract with identical validation, payload structure, and API behavior. No mismatches remain.
