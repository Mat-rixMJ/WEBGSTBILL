# WebGST Backend

GST-compliant billing API built with FastAPI.

## Setup

1. **Install dependencies**:

   ```bash
   pip install -r requirements.txt
   ```

2. **Configure environment**:

   ```bash
   copy .env.example .env
   # Edit .env with your settings
   ```

3. **Run migrations**:

   ```bash
   alembic upgrade head
   ```

4. **Start development server**:

   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

5. **Access API docs**:
   - Swagger UI: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc

## Scripts

- `dev`: Start development server
- `test`: Run test suite
- `migrate`: Run database migrations
- `seed`: Seed database with sample data

## Project Structure

```
app/
├── main.py              # FastAPI application
├── config.py            # Configuration
├── database.py          # Database setup
├── models/              # SQLAlchemy models
├── schemas/             # Pydantic schemas
├── api/                 # API routes
├── services/            # Business logic
├── utils/               # Helpers & validators
└── templates/           # PDF templates
```

## Testing

```bash
pytest
```

## PDF rendering (WeasyPrint) on Windows

WeasyPrint requires GTK/Cairo/Fontconfig/Pango. Install once per machine before generating PDFs:

1. Download and install the GTK3 runtime (includes Cairo/Pango/Fontconfig) from https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases (use the latest 64-bit). Accept default path (e.g., `C:\Program Files\GTK3-Runtime Win64`).
2. Add the `bin` folder to `PATH`, e.g., `C:\Program Files\GTK3-Runtime Win64\bin`.
3. Reopen terminal and verify: `python -c "import weasyprint; print(weasyprint.__version__)"` should print the version without Fontconfig errors.
4. If fonts are missing, install core Windows fonts or point `FONTCONFIG_FILE` to a valid config; default config should load once GTK is installed.

## Production Deployment

1. Set `DEBUG=False` in `.env`
2. Use PostgreSQL: `DATABASE_URL=postgresql://...`
3. Generate strong `SECRET_KEY`
4. Run migrations: `alembic upgrade head`
5. Start with gunicorn: `gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker`
