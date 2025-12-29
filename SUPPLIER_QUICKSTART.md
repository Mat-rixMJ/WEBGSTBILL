# SUPPLIER MODULE QUICKSTART GUIDE

## 🚀 Quick Start - Testing Supplier Module

### Prerequisites

- Backend server running on `http://localhost:8000`
- Valid JWT authentication token (login first)
- Database initialized with suppliers table

---

## ⚡ 1-Minute Test

### Step 1: Login to Get Token

```bash
curl -X POST http://localhost:8000/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin"}'
```

Save the token from response.

### Step 2: Create a REGISTERED Supplier

```bash
curl -X POST http://localhost:8000/api/suppliers \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
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
```

**Expected Response:** `201 Created` with supplier object

### Step 3: Create an UNREGISTERED Supplier

```bash
curl -X POST http://localhost:8000/api/suppliers \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer YOUR_TOKEN_HERE" \
  -d '{
    "name": "Local Hardware Store",
    "supplier_type": "UNREGISTERED",
    "gstin": null,
    "address": "Main Street, Village Name, Karnataka - 560001",
    "state": "Karnataka",
    "state_code": "29"
  }'
```

**Expected Response:** `201 Created` with supplier object (gstin=null)

### Step 4: List All Suppliers

```bash
curl -X GET http://localhost:8000/api/suppliers?active_only=true \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

**Expected Response:** `200 OK` with array of suppliers

---

## 🎯 Contract Field Names (Copy-Paste Ready)

### Create Supplier (JSON)

```json
{
  "name": "Supplier Name Here",
  "supplier_type": "REGISTERED",
  "gstin": "27ABCDE1234F1Z5",
  "address": "Complete address here",
  "state": "Maharashtra",
  "state_code": "27",
  "phone": "+919876543210",
  "email": "email@example.com"
}
```

### Field Reference

| Field           | Type         | Required    | Notes                          |
| --------------- | ------------ | ----------- | ------------------------------ |
| `name`          | string       | Yes         | 2-255 chars                    |
| `supplier_type` | string       | Yes         | "REGISTERED" or "UNREGISTERED" |
| `gstin`         | string\|null | Conditional | Required for REGISTERED        |
| `address`       | string       | Yes         | 5-500 chars                    |
| `state`         | string       | Yes         | Full state name                |
| `state_code`    | string       | Yes         | 2-digit code                   |
| `phone`         | string\|null | No          | Max 15 chars                   |
| `email`         | string\|null | No          | Max 255 chars                  |

---

## 🔍 Common Use Cases

### Use Case 1: Raw Material Supplier (Registered)

```json
{
  "name": "XYZ Chemicals Pvt Ltd",
  "supplier_type": "REGISTERED",
  "gstin": "29ABCDE1234F1Z5",
  "address": "Industrial Estate, Bangalore, Karnataka - 560100",
  "state": "Karnataka",
  "state_code": "29",
  "phone": "+919876543210",
  "email": "purchase@xyzchemicals.com"
}
```

### Use Case 2: Local Unregistered Vendor

```json
{
  "name": "Local Stationery Shop",
  "supplier_type": "UNREGISTERED",
  "gstin": null,
  "address": "Shop 5, Main Road, Chennai - 600001",
  "state": "Tamil Nadu",
  "state_code": "33",
  "phone": "+919123456789",
  "email": null
}
```

### Use Case 3: Service Provider (Registered)

```json
{
  "name": "ABC Logistics Services",
  "supplier_type": "REGISTERED",
  "gstin": "07PQRST9876M1Z3",
  "address": "Sector 18, Delhi - 110001",
  "state": "Delhi",
  "state_code": "07",
  "phone": "+911123456789",
  "email": "logistics@abcservices.com"
}
```

---

## ⚠️ Common Mistakes to Avoid

### ❌ Wrong: Using lowercase supplier_type

```json
{
  "supplier_type": "registered" // ❌ Wrong
}
```

### ✅ Correct: Use uppercase

```json
{
  "supplier_type": "REGISTERED" // ✓ Correct
}
```

### ❌ Wrong: Providing GSTIN for UNREGISTERED

```json
{
  "supplier_type": "UNREGISTERED",
  "gstin": "29ABCDE1234F1Z5" // ❌ This will fail
}
```

### ✅ Correct: No GSTIN for UNREGISTERED

```json
{
  "supplier_type": "UNREGISTERED",
  "gstin": null // ✓ Correct
}
```

### ❌ Wrong: GSTIN state code mismatch

```json
{
  "gstin": "29ABCDE1234F1Z5", // Karnataka (29)
  "state": "Maharashtra",
  "state_code": "27" // ❌ Mismatch
}
```

### ✅ Correct: Matching state codes

```json
{
  "gstin": "29ABCDE1234F1Z5", // Karnataka (29)
  "state": "Karnataka",
  "state_code": "29" // ✓ Match
}
```

---

## 🌐 Frontend Quick Test

1. Start backend: `cd backend && python -m app.main`
2. Open `frontend/suppliers.html` in browser
3. Login via `frontend/index.html` first
4. Navigate to Suppliers page
5. Click "+ Add Supplier"
6. Select "REGISTERED" type
7. Enter GSTIN: `29ABCDE1234F1Z5`
8. Watch state auto-select to "Karnataka"
9. Fill other fields and save

---

## 📊 State Code Quick Reference

| Code | State         | Code | State       |
| ---- | ------------- | ---- | ----------- |
| 07   | Delhi         | 27   | Maharashtra |
| 09   | Uttar Pradesh | 29   | Karnataka   |
| 19   | West Bengal   | 33   | Tamil Nadu  |
| 24   | Gujarat       | 36   | Telangana   |

Full list: See `SUPPLIER_MODULE_CONTRACT.md`

---

## 🔗 API Endpoints Summary

| Method | Endpoint                         | Purpose         |
| ------ | -------------------------------- | --------------- |
| POST   | `/api/suppliers`                 | Create supplier |
| GET    | `/api/suppliers`                 | List suppliers  |
| GET    | `/api/suppliers/{id}`            | Get supplier    |
| PUT    | `/api/suppliers/{id}`            | Update supplier |
| PATCH  | `/api/suppliers/{id}/deactivate` | Soft delete     |

---

## 📞 Need Help?

- **Contract:** `SUPPLIER_MODULE_CONTRACT.md`
- **Examples:** `backend/tests/test_supplier_contract_examples.py`
- **Implementation:** `SUPPLIER_IMPLEMENTATION_SUMMARY.md`
- **Purchase Integration:** `SUPPLIER_PURCHASE_CONTRACT.md`

---

## ✅ Validation Checklist

Before creating a supplier, ensure:

- [ ] `supplier_type` is exactly "REGISTERED" or "UNREGISTERED"
- [ ] GSTIN provided ONLY if type is REGISTERED
- [ ] GSTIN format: 15 chars, matches pattern
- [ ] GSTIN state code matches `state_code` field
- [ ] State name matches `state_code`
- [ ] Address is 5-500 chars
- [ ] Name is 2-255 chars

---

**That's it! You're ready to manage suppliers.** 🎉

For production deployment, ensure:

1. Proper authentication configured
2. CORS settings updated
3. Database backups enabled
4. Error logging configured
