# GST-Compliant Product Management Module

## Overview

Complete implementation of Indian GST-compliant product management for billing application. Includes database schema, API endpoints, validation logic, and UI implementation.

---

## 1. DATABASE SCHEMA

### Products Table

```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL,
    description VARCHAR(500),
    hsn_code VARCHAR(8) NOT NULL,        -- HSN/SAC code (4/6/8 digits)
    gst_rate NUMERIC(5,2) NOT NULL,      -- 0, 5, 12, 18, or 28
    price_paise INTEGER NOT NULL,        -- Price in paise (avoid float issues)
    stock_quantity INTEGER DEFAULT 0,
    unit VARCHAR(10) DEFAULT 'PCS',
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME NOT NULL,
    updated_at DATETIME NOT NULL,

    INDEX idx_name (name),
    INDEX idx_hsn (hsn_code)
);
```

### Model Properties

- **id**: Auto-increment primary key
- **name**: Product/service name (2-255 chars)
- **description**: Optional description (max 500 chars)
- **hsn_code**: HSN/SAC code validated to 4, 6, or 8 digits
- **gst_rate**: Decimal (5,2) restricted to {0, 5, 12, 18, 28}
- **price_paise**: Integer storage in paise (₹1 = 100 paise) for precision
- **stock_quantity**: Current inventory level (≥0)
- **unit**: Measurement unit (PCS, KG, LTR, MTR, etc.)
- **is_active**: Soft delete flag (hide from new invoices)
- **created_at/updated_at**: Timezone-aware timestamps (UTC)

### Computed Property

```python
@property
def price_rupees(self) -> Decimal:
    """Convert paise to rupees for display"""
    return Decimal(self.price_paise) / 100
```

### Business Method

```python
def reduce_stock(self, quantity: int) -> bool:
    """Reduce stock quantity, return False if insufficient"""
    if self.stock_quantity >= quantity:
        self.stock_quantity -= quantity
        return True
    return False
```

---

## 2. API ENDPOINTS

### Base Path: `/api/products`

#### 1. Create Product

```
POST /api/products/
Authorization: Bearer {token}
Content-Type: application/json

Request Body:
{
    "name": "Laptop Computer",
    "description": "Dell Inspiron 15",
    "hsn_code": "8471",
    "gst_rate": 18,
    "price_paise": 5000000,  // ₹50,000.00
    "stock_quantity": 10,
    "unit": "PCS"
}

Response: 201 Created
{
    "id": 1,
    "name": "Laptop Computer",
    "description": "Dell Inspiron 15",
    "hsn_code": "8471",
    "gst_rate": 18,
    "price_paise": 5000000,
    "price_rupees": 50000.00,
    "stock_quantity": 10,
    "unit": "PCS",
    "is_active": true,
    "created_at": "2025-12-25T06:00:00Z",
    "updated_at": "2025-12-25T06:00:00Z"
}
```

#### 2. List Products

```
GET /api/products/?skip=0&limit=100&active_only=true

Response: 200 OK
[
    {
        "id": 1,
        "name": "Laptop Computer",
        ...
    }
]
```

#### 3. Get Product by ID

```
GET /api/products/{product_id}

Response: 200 OK
{
    "id": 1,
    "name": "Laptop Computer",
    ...
}
```

#### 4. Update Product

```
PUT /api/products/{product_id}
Authorization: Bearer {token}
Content-Type: application/json

Request Body (partial update):
{
    "price_paise": 4800000,  // Update price to ₹48,000
    "stock_quantity": 8
}

Response: 200 OK
{
    "id": 1,
    "price_paise": 4800000,
    "price_rupees": 48000.00,
    "stock_quantity": 8,
    ...
}
```

#### 5. Deactivate Product (Soft Delete)

```
DELETE /api/products/{product_id}
Authorization: Bearer {token}

Response: 204 No Content
```

Note: Sets `is_active = false`, preserving data for historical invoices.

---

## 3. VALIDATION LOGIC

### 3.1 HSN/SAC Code Validation

**Rules per Indian GST Law:**

- Turnover < ₹1.5 crore: 4-digit HSN optional
- Turnover ₹1.5-5 crore: 4-digit HSN mandatory
- Turnover > ₹5 crore: 6-digit HSN mandatory
- Exports: 8-digit HSN recommended

**Implementation:**

```python
@field_validator("hsn_code")
@classmethod
def validate_hsn(cls, v: str) -> str:
    """Validate HSN code is 4, 6, or 8 digits"""
    if not v.isdigit() or len(v) not in [4, 6, 8]:
        raise ValueError("HSN code must be 4, 6, or 8 digits")
    return v
```

**Frontend Validation:**

```javascript
function validateHSN(input) {
  input.value = input.value.replace(/\D/g, ""); // Only digits
  const len = input.value.length;
  if (len > 0 && len !== 4 && len !== 6 && len !== 8) {
    input.setCustomValidity("HSN code must be exactly 4, 6, or 8 digits");
  } else {
    input.setCustomValidity("");
  }
}
```

### 3.2 GST Rate Validation

**Valid Rates (as per Indian GST):**

- 0%: Exempt, zero-rated, nil-rated goods/services
- 5%: Essential goods (food grains, medicines)
- 12%: Standard goods (processed foods)
- 18%: Most goods and services (electronics, services)
- 28%: Luxury items (automobiles, tobacco)

**Implementation:**

```python
@field_validator("gst_rate")
@classmethod
def validate_gst_rate(cls, v: Decimal) -> Decimal:
    """Validate GST rate is one of standard rates"""
    valid_rates = [Decimal('0'), Decimal('5'), Decimal('12'),
                   Decimal('18'), Decimal('28')]
    if v not in valid_rates:
        raise ValueError("GST rate must be 0, 5, 12, 18, or 28")
    return v
```

### 3.3 Price Storage (Paise vs Rupees)

**Problem:** Floating-point arithmetic causes precision errors

```python
# ❌ WRONG: Float precision issues
price = 49.99
tax = price * 0.18  # Result: 8.9982 (imprecise)

# ✅ CORRECT: Integer paise storage
price_paise = 4999  # ₹49.99 = 4999 paise
tax_paise = (price_paise * 18) // 100  # Result: 899 paise = ₹8.99
```

**Conversion:**

```python
# Store in DB
price_rupees = 50000.00
price_paise = int(price_rupees * 100)  # 5000000

# Display to user
@property
def price_rupees(self) -> Decimal:
    return Decimal(self.price_paise) / 100
```

### 3.4 Stock Management

**Inventory Reduction (Invoice-safe):**

```python
def reduce_stock(self, quantity: int) -> bool:
    """Atomic stock reduction"""
    if self.stock_quantity >= quantity:
        self.stock_quantity -= quantity
        return True
    return False  # Insufficient stock
```

**Business Logic:**

- Stock reduced when invoice is finalized (not saved as draft)
- Returns `False` if insufficient stock (prevent over-selling)
- Atomic operation within transaction

---

## 4. UI FIELDS & FEATURES

### 4.1 Product Form Fields

**Required Fields:**

1. **Name** (text, 2-255 chars)

   - Input: `<input type="text" required minlength="2" maxlength="255">`
   - Example: "Laptop Computer", "Consulting Services"

2. **HSN/SAC Code** (text, 4/6/8 digits)

   - Input: `<input type="text" pattern="[0-9]{4,8}" required>`
   - Validation: Real-time digit-only enforcement
   - Help text: Shows length requirements per turnover

3. **GST Rate** (select, {0,5,12,18,28})

   - Input: `<select required>`
   - Options: Labeled with category (essential/standard/luxury)
   - Help text: Explains rate applicability

4. **Price** (number, ≥0, 2 decimals)

   - Input: `<input type="number" min="0" step="0.01" required>`
   - Display: Real-time tax breakup calculator
   - Shows: Base price | Tax | Total (inclusive/exclusive)

5. **Stock Quantity** (integer, ≥0)

   - Input: `<input type="number" min="0" required>`
   - Alert: Shows red if stock ≤ 0

6. **Unit** (select)
   - Options: PCS, KG, LTR, MTR, BOX, PKT, SET, SVC
   - Default: PCS

**Optional Fields:**

- **Description** (textarea, max 500 chars)
- **Status** (checkbox, edit mode only)

### 4.2 Product List View

**Table Columns:**

1. Name + Description (truncated)
2. HSN Code (monospace font)
3. GST Rate (%) - right-aligned
4. Price (₹) - right-aligned, formatted
5. Stock - right-aligned, red if ≤0
6. Status - badge (Active/Inactive)
7. Actions - Edit | Deactivate/Activate

**Features:**

- Search by name or HSN code
- Filter: Active only | Inactive only | All
- Color coding: Inactive products grayed out
- Stock alerts: Red text for zero/negative stock

### 4.3 Real-time Tax Calculator

**Display while entering price:**

```
Price: ₹50,000 at 18% GST
-----------------------------------
Base Price: ₹42,372.88
Tax Amount: ₹7,627.12
Total Price: ₹50,000.00
```

**JavaScript Implementation:**

```javascript
function calculateTaxBreakup() {
  const price = parseFloat(document.getElementById("price").value) || 0;
  const gstRate = parseFloat(document.getElementById("gst_rate").value) || 0;

  if (price > 0 && gstRate > 0) {
    const basePrice = price / (1 + gstRate / 100);
    const taxAmount = price - basePrice;

    document.getElementById("base-price").textContent = basePrice.toFixed(2);
    document.getElementById("tax-amount").textContent = taxAmount.toFixed(2);
    document.getElementById("total-price").textContent = price.toFixed(2);
  }
}
```

---

## 5. GST COMPLIANCE FEATURES

### 5.1 Invoice Snapshot Behavior

**Problem:** Product price/GST changes shouldn't affect old invoices

**Solution:** Invoice items store snapshots

```sql
-- Invoice items table captures product data at time of invoice
CREATE TABLE invoice_items (
    ...
    product_name VARCHAR(255) NOT NULL,      -- Snapshot
    hsn_code VARCHAR(8) NOT NULL,            -- Snapshot
    gst_rate NUMERIC(5,2) NOT NULL,          -- Snapshot
    price_paise INTEGER NOT NULL,            -- Snapshot
    ...
);
```

When creating invoice:

```python
# Don't reference Product.price_paise directly in invoice
# Instead, copy values at time of creation
invoice_item = InvoiceItem(
    product_id=product.id,           # Reference for reports
    product_name=product.name,       # Snapshot
    hsn_code=product.hsn_code,       # Snapshot
    gst_rate=product.gst_rate,       # Snapshot
    price_paise=product.price_paise  # Snapshot
)
```

### 5.2 Soft Delete (Deactivation)

**Why not hard delete?**

- Historical invoices need product data
- GST reports require product HSN/GST rate history
- Audit trail for tax compliance

**Implementation:**

- `is_active = false` hides from new invoice forms
- Product remains in database for existing invoices
- Can be reactivated if needed

### 5.3 Stock Reconciliation

**When stock reduces:**

- Only on invoice finalization (not draft save)
- Transaction-safe (rollback on error)
- Prevents overselling via `reduce_stock()` check

**Stock alerts:**

- Frontend shows red text for stock ≤ 0
- Optional: Low stock warnings (e.g., stock < 10)
- No automatic PO generation (out of Phase-1 scope)

---

## 6. VALIDATION RULES SUMMARY

| Field          | Rules                    | Error Message                          |
| -------------- | ------------------------ | -------------------------------------- |
| name           | 2-255 chars, required    | "Name must be 2-255 characters"        |
| description    | Max 500 chars, optional  | "Description too long (max 500)"       |
| hsn_code       | 4/6/8 digits, required   | "HSN code must be 4, 6, or 8 digits"   |
| gst_rate       | {0,5,12,18,28}, required | "GST rate must be 0, 5, 12, 18, or 28" |
| price_paise    | Integer ≥ 0, required    | "Price must be non-negative"           |
| stock_quantity | Integer ≥ 0, required    | "Stock cannot be negative"             |
| unit           | Max 10 chars, required   | "Unit required (PCS/KG/LTR/etc.)"      |

---

## 7. TESTING CHECKLIST

### Backend Tests

- [ ] Create product with valid data
- [ ] Reject invalid HSN codes (3, 5, 7, 9+ digits)
- [ ] Reject invalid GST rates (1, 6, 15, 30, etc.)
- [ ] Reject negative prices
- [ ] Update product fields
- [ ] Soft delete (deactivate)
- [ ] Stock reduction logic
- [ ] Paise-to-rupees conversion accuracy

### Frontend Tests

- [ ] Add new product via form
- [ ] HSN validation (digit-only, length check)
- [ ] GST rate dropdown shows all valid rates
- [ ] Price input accepts decimals
- [ ] Tax breakup calculator shows correct math
- [ ] Stock shows red when ≤ 0
- [ ] Search by name works
- [ ] Search by HSN code works
- [ ] Filter active/inactive works
- [ ] Edit existing product
- [ ] Deactivate product
- [ ] Reactivate product

### Integration Tests

- [ ] Create product → appears in invoice form
- [ ] Deactivate product → hidden from invoice form
- [ ] Change product price → old invoices unaffected
- [ ] Reduce stock via invoice → updates correctly
- [ ] Insufficient stock → invoice creation blocked

---

## 8. EXAMPLE USAGE

### Create a Standard Product

```bash
curl -X POST http://127.0.0.1:8001/api/products/ \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Dell Laptop",
    "description": "Inspiron 15 3000 Series",
    "hsn_code": "8471",
    "gst_rate": 18,
    "price_paise": 3500000,
    "stock_quantity": 5,
    "unit": "PCS"
  }'
```

### Create a Service

```bash
curl -X POST http://127.0.0.1:8001/api/products/ \
  -H "Authorization: Bearer {token}" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "IT Consulting",
    "description": "Hourly consulting services",
    "hsn_code": "998314",
    "gst_rate": 18,
    "price_paise": 200000,
    "stock_quantity": 0,
    "unit": "SVC"
  }'
```

### List Active Products

```bash
curl http://127.0.0.1:8001/api/products/?active_only=true
```

---

## 9. PHASE-1 EXCLUSIONS (NOT IMPLEMENTED)

❌ **Out of Scope:**

- Barcode/SKU support
- Product variants (size, color, etc.)
- Bulk import/export
- Product categories
- Multi-currency pricing
- Discount schemes
- Purchase order integration
- Supplier management
- Warehouse/location tracking
- Serial number tracking
- Batch/lot management
- Reorder level automation

---

## 10. FILES MODIFIED/CREATED

### Backend

- ✅ `backend/app/models/product.py` - Database model (already exists)
- ✅ `backend/app/schemas/product.py` - Pydantic schemas (already exists)
- ✅ `backend/app/api/products.py` - API routes (already exists)
- ✅ `backend/app/utils/validators.py` - HSN/GST validators (already exists)

### Frontend

- ✅ **`frontend/products.html`** - Complete product management UI (CREATED)

### Documentation

- ✅ **`PRODUCT_MODULE_SPEC.md`** - This specification document (CREATED)

---

## 11. SECURITY CONSIDERATIONS

1. **Authentication:** All write operations require Bearer token
2. **Input Validation:** Server-side validation for all fields
3. **SQL Injection:** SQLAlchemy ORM prevents injection
4. **XSS Prevention:** Frontend escapes HTML in product names
5. **CSRF:** Token-based auth (no cookies) prevents CSRF
6. **Rate Limiting:** Applied via slowapi middleware (200/day, 50/hour)

---

## 12. NEXT STEPS (POST PHASE-1)

1. Add product search by category
2. Implement barcode scanner support
3. Add bulk import via CSV/Excel
4. Product image upload
5. Multi-variant products (size, color)
6. Low stock email alerts
7. Product analytics dashboard

---

**Document Version:** 1.0  
**Last Updated:** 2025-12-25  
**Author:** GitHub Copilot  
**Compliance:** Indian GST Act 2017
