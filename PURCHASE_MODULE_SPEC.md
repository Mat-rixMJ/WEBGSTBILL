# Purchase Module Specification

## Overview

The Purchase Module handles raw material and expense purchases from suppliers, tracking INPUT GST (ITC), and maintaining audit-safe records.

## Database Schema

### Suppliers Table

```sql
CREATE TABLE suppliers (
    id INTEGER PRIMARY KEY,
    name VARCHAR(255) NOT NULL UNIQUE,
    supplier_type VARCHAR(20) NOT NULL,  -- "Registered" or "Unregistered"
    gstin VARCHAR(15),                   -- Required for Registered
    address VARCHAR(500) NOT NULL,
    state VARCHAR(100) NOT NULL,
    state_code VARCHAR(2) NOT NULL,
    phone VARCHAR(15),
    email VARCHAR(255),
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME,
    updated_at DATETIME
)
```

### Purchase Invoices Table

```sql
CREATE TABLE purchase_invoices (
    id INTEGER PRIMARY KEY,
    supplier_id INTEGER NOT NULL,
    supplier_invoice_number VARCHAR(100) NOT NULL,
    supplier_invoice_date DATETIME NOT NULL,
    purchase_date DATETIME NOT NULL,
    place_of_supply VARCHAR(100) NOT NULL,
    place_of_supply_code VARCHAR(2) NOT NULL,
    total_quantity FLOAT NOT NULL,
    subtotal_value INTEGER NOT NULL,  -- in paise
    cgst_amount INTEGER NOT NULL,     -- in paise
    sgst_amount INTEGER NOT NULL,     -- in paise
    igst_amount INTEGER NOT NULL,     -- in paise
    total_gst INTEGER NOT NULL,
    total_amount INTEGER NOT NULL,
    status VARCHAR(20),               -- Draft, Finalized, Cancelled
    cancel_reason TEXT,
    is_active BOOLEAN DEFAULT TRUE,
    created_at DATETIME,
    updated_at DATETIME,
    finalized_at DATETIME,
    cancelled_at DATETIME,
    FOREIGN KEY (supplier_id) REFERENCES suppliers(id)
)
```

### Purchase Items Table

```sql
CREATE TABLE purchase_items (
    id INTEGER PRIMARY KEY,
    invoice_id INTEGER NOT NULL,
    item_name VARCHAR(255) NOT NULL,
    hsn_code VARCHAR(8) NOT NULL,
    quantity FLOAT NOT NULL,
    unit_rate INTEGER NOT NULL,       -- in paise
    gst_rate INTEGER NOT NULL,        -- 0, 5, 12, 18, 28
    subtotal INTEGER NOT NULL,        -- in paise
    cgst_amount INTEGER NOT NULL,
    sgst_amount INTEGER NOT NULL,
    igst_amount INTEGER NOT NULL,
    total_amount INTEGER NOT NULL,
    tax_type VARCHAR(10) NOT NULL,    -- "CGST_SGST" or "IGST"
    created_at DATETIME,
    FOREIGN KEY (invoice_id) REFERENCES purchase_invoices(id)
)
```

## API Endpoints

### Suppliers

- **POST /api/suppliers** - Create supplier
- **GET /api/suppliers** - List suppliers
- **GET /api/suppliers/{id}** - Get supplier details
- **PUT /api/suppliers/{id}** - Update supplier
- **DELETE /api/suppliers/{id}** - Deactivate supplier

### Purchases

- **POST /api/purchases** - Create purchase invoice (Draft status)
- **GET /api/purchases** - List purchase invoices (with optional status filter)
- **GET /api/purchases/{id}** - Get purchase invoice with items
- **POST /api/purchases/{id}/finalize** - Finalize invoice (locks + updates inventory)
- **POST /api/purchases/{id}/cancel** - Cancel invoice (soft delete with reason)

## GST Calculation Rules

### Same State (Supplier state = Business state)

- GST Type: CGST + SGST
- Each = GST Rate / 2
- Example: 18% GST = 9% CGST + 9% SGST

### Different State (Supplier state ≠ Business state)

- GST Type: IGST (Integrated GST)
- IGST = Full GST Rate
- Example: 18% GST = 18% IGST

### Rounding

- Round half up (banker's rounding)
- Applied per item, then summed

## Inventory Impact

### On Finalization

- Stock quantity increased for each item
- Matched by HSN code to products table
- One-way operation (no reversal in Phase-1.5)

### On Cancellation

- Soft delete (status = "Cancelled")
- If finalized, inventory NOT reversed (Phase-1.5 limitation)
- Reason recorded for audit

## Validation Rules

### Supplier

- Name: Required, unique
- Type: Must be "Registered" or "Unregistered"
- GSTIN: Required for Registered, forbidden for Unregistered
- State: Must match valid Indian state
- GSTIN state code must match supplier state code

### Purchase Invoice

- Supplier: Must exist and be active
- At least 1 item required
- Invoice date: Must be datetime
- Purchase date: Must be datetime

### Purchase Item

- HSN: 4, 6, or 8 digits
- Quantity: Must be > 0
- Rate: Must be > 0 (in paise)
- GST Rate: Must be 0, 5, 12, 18, or 28

## Security Rules

- All endpoints require JWT authentication
- Soft deletes only (no hard delete)
- Audit trail: created_at, updated_at, finalized_at, cancelled_at
- Tax snapshot prevents recalculation after save

## Phase-1.5 Limitations

❌ NO:

- GST return filing
- ITC reconciliation (GSTR-2B)
- Bank integration
- Payment settlement
- Reverse inventory on cancellation
- Multi-business support

✅ YES:

- Record purchases
- Track INPUT GST
- Audit-safe immutable data
- Future Phase-2 ready
