import json
import traceback
from datetime import datetime
from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)

try:
    # Login to get token
    login_resp = client.post(
        "/api/auth/login",
        data={"username": "testuser1", "password": "Test@12345"},
        headers={"Content-Type": "application/x-www-form-urlencoded"},
    )
    assert login_resp.status_code == 200, f"login failed: {login_resp.status_code} {login_resp.text}"
    token = login_resp.json()["access_token"]

    # Build purchase payload
    payload = {
        "supplier_id": 3,
        "supplier_invoice_no": "TS-001",
        "supplier_invoice_date": "2025-12-26T00:00:00",
        "purchase_date": "2025-12-26T00:00:00",
        "items": [
            {
                "item_name": "Steel Rod",
                "hsn_code": "7214",
                "quantity": 10,
                "rate": 50000,
                "gst_rate": 18,
            }
        ],
    }

    # POST purchase (this will raise if server throws)
    resp = client.post(
        "/api/purchases",
        headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"},
        data=json.dumps(payload),
    )
    print("Status:", resp.status_code)
    print("Body:", resp.text)
except Exception:
    print("\n\n=== TRACEBACK ===")
    traceback.print_exc()
