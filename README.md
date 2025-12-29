# WebGST - Complete GST Billing System

Production-ready Indian GST billing application built with FastAPI + SQLAlchemy.

## 🚀 Quick Start (Windows)

### 1. Install Python 3.11+

Download from https://www.python.org/downloads/

### 2. Setup Backend

```powershell
cd backend
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### 3. Configure Environment

```powershell
# Edit .env file with your settings
copy .env.example .env
```

### 4. Initialize Database

```powershell
# Tables are auto-created on first run
python -c "from app.database import Base, engine; Base.metadata.create_all(bind=engine)"
```

### 5. Create First User

```powershell
# Start the server first
uvicorn app.main:app --reload --port 8000

# Then register via API:
# POST http://localhost:8000/api/auth/register
# {
#   "username": "admin",
#   "email": "admin@example.com",
#   "password": "your-secure-password"
# }
```

### 6. Access Application

- **API Docs**: http://localhost:8000/docs
- **Frontend**: Open `frontend/index.html` in browser

## 📂 Project Structure

```
WEBGST/
├── backend/           # FastAPI backend
│   ├── app/
│   │   ├── api/       # Route handlers
│   │   ├── models/    # SQLAlchemy models
│   │   ├── schemas/   # Pydantic schemas
│   │   ├── services/  # Business logic
│   │   └── utils/     # Helpers & validators
│   └── tests/         # Unit tests
└── frontend/          # Simple HTML + Tailwind UI
```

## ✅ Features

### Phase-1 (Complete)

✅ **Business Setup** - Single business with GSTIN, invoice numbering  
✅ **Product Management** - HSN, GST rates, stock tracking  
✅ **Customer Management** - B2B/B2C with GSTIN validation  
✅ **Invoice Engine** - Auto GST calculation, sequential numbers, immutable after save  
✅ **GST Logic** - Intra-state (CGST+SGST), Inter-state (IGST), accurate rounding  
✅ **Reports** - Sales register, monthly GST summary  
✅ **Authentication** - JWT-based secure access

## 🔧 API Endpoints

### Authentication

- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login (get JWT token)
- `GET /api/auth/me` - Get current user

### Business

- `POST /api/business/` - Create business profile
- `GET /api/business/` - Get business profile
- `PUT /api/business/` - Update business profile

### Products

- `POST /api/products/` - Create product
- `GET /api/products/` - List products
- `GET /api/products/{id}` - Get product
- `PUT /api/products/{id}` - Update product
- `DELETE /api/products/{id}` - Soft delete product

### Customers

- `POST /api/customers/` - Create customer
- `GET /api/customers/` - List customers
- `GET /api/customers/{id}` - Get customer
- `PUT /api/customers/{id}` - Update customer
- `DELETE /api/customers/{id}` - Soft delete customer

### Invoices

- `POST /api/invoices/` - Create invoice (auto GST + stock reduction)
- `GET /api/invoices/` - List invoices
- `GET /api/invoices/{id}` - Get invoice details
- `GET /api/invoices/number/{number}` - Get by invoice number
- `POST /api/invoices/{id}/cancel` - Cancel invoice

### Reports

- `GET /api/reports/sales-register` - Sales register
- `GET /api/reports/gst-summary` - Monthly GST summary

## 🧪 Testing

```powershell
cd backend
pytest
```

## 🔐 Security Notes

- Change `SECRET_KEY` in `.env` before production
- Use PostgreSQL for production (not SQLite)
- Enable HTTPS in production
- Restrict `/api/auth/register` to admin only

## 📝 Compliance

- **GSTIN Validation**: Format + checksum
- **HSN Codes**: 4/6/8 digits based on turnover
- **GST Calculation**: Intra-state (CGST+SGST), Inter-state (IGST)
- **Invoice Numbering**: Immutable, sequential
- **Money Storage**: Stored in paise (integers) to avoid float precision issues
- **Audit Trail**: All invoices preserve snapshots of customer/business data

## 🚀 Production Deployment

1. Set `DEBUG=False` in `.env`
2. Use PostgreSQL: `DATABASE_URL=postgresql://user:pass@host/dbname`
3. Generate strong `SECRET_KEY`: `openssl rand -hex 32`
4. Run with Gunicorn: `gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000`
5. Setup reverse proxy (Nginx/Caddy) with HTTPS
6. Enable firewall and rate limiting

## 📄 License

Private/Self-hosted use only. NOT for public distribution or SaaS.
