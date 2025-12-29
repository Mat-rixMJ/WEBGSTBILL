# Quick Start Guide for WebGST

## Windows Setup (5 Minutes)

### 1. Install Python 3.11+

Download from: https://www.python.org/downloads/windows/

### 2. Run Startup Script

```powershell
.\start.ps1
```

This will:

- Create virtual environment
- Install dependencies
- Initialize database
- Start backend server

### 3. Open Frontend

Open `frontend/index.html` in your web browser

### 4. Create First User

1. Click "Register" on login page
2. Create account with:
   - Username: admin
   - Email: admin@example.com
   - Password: (your secure password)

### 5. Setup Business Profile

1. Login with your account
2. Go to "Business" section
3. Enter your:
   - Business name
   - GSTIN (15 characters)
   - Address details
   - Invoice prefix (e.g., "INV")

### 6. Add Products

1. Go to "Products"
2. Add products with:
   - Name
   - HSN code (4/6/8 digits)
   - GST rate (0, 5, 12, 18, or 28)
   - Price
   - Stock quantity

### 7. Add Customers

1. Go to "Customers"
2. Add customers with:
   - Name
   - State code
   - Address
   - GSTIN (optional, required for B2B)

### 8. Create Invoice

1. Go to "Invoices"
2. Click "Create Invoice"
3. Select customer
4. Add products with quantities
5. GST will be calculated automatically
6. Stock will be reduced automatically

### 9. View Reports

1. Go to "Reports"
2. View:
   - Sales Register
   - Monthly GST Summary
3. Export to CSV/Excel

## API Testing (Optional)

Visit http://localhost:8000/docs for interactive API documentation.

## Production Checklist

Before deploying to production:

- [ ] Change SECRET_KEY in `.env`
- [ ] Set DEBUG=False
- [ ] Use PostgreSQL instead of SQLite
- [ ] Enable HTTPS
- [ ] Restrict /api/auth/register endpoint
- [ ] Setup backup automation
- [ ] Configure firewall rules
- [ ] Enable rate limiting

## Support

For issues or questions, check:

- README.md in root directory
- backend/README.md for API details
- frontend/README.md for UI guide

## Compliance Notes

✅ GSTIN validation with checksum
✅ HSN code validation (4/6/8 digits)
✅ Intra-state: CGST + SGST
✅ Inter-state: IGST
✅ Money stored in paise (no float precision issues)
✅ Immutable invoice numbers
✅ Customer/Business data snapshots in invoices
✅ Stock auto-reduction
✅ Cancel invoices (soft delete)

---

**Important**: This is for personal/self-hosted use only. NOT for public distribution or SaaS.
