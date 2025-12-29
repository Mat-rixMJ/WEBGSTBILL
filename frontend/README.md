# WebGST Frontend

Simple HTML + Tailwind CSS interface for WebGST billing system.

## Pages

- `index.html` - Login/Register
- `dashboard.html` - Dashboard with stats
- `products.html` - Product management
- `customers.html` - Customer management
- `invoices.html` - Invoice creation & listing
- `reports.html` - Sales & GST reports

## Usage

1. Start backend server:

   ```powershell
   cd ../backend
   uvicorn app.main:app --reload --port 8000
   ```

2. Open `index.html` in a web browser

3. Register a new user or login

4. Start creating products, customers, and invoices

## API Configuration

Frontend connects to `http://localhost:8000/api` by default.

To change the API URL, edit the `API_URL` constant in each HTML file.

## Features

- JWT authentication with localStorage
- Responsive Tailwind CSS design
- Real-time API integration
- Form validation
- Error handling

## Production Deployment

For production:

1. Build a proper SPA with React/Vue (optional)
2. Use environment variables for API URL
3. Enable HTTPS
4. Add input sanitization
5. Implement proper error boundaries
