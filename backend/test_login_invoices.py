"""Test login for user2 and fetch invoices"""
import requests
import json

API_BASE = "http://127.0.0.1:8000/api"

# Step 1: Login
print("Step 1: Logging in as user2...")
login_data = {
    "username": "user2",
    "password": "user2pass"
}

response = requests.post(
    f"{API_BASE}/auth/login",
    data=login_data,
    headers={"Content-Type": "application/x-www-form-urlencoded"}
)

if response.status_code == 200:
    token_data = response.json()
    token = token_data["access_token"]
    print(f"✅ Login successful! Token: {token[:20]}...")
else:
    print(f"❌ Login failed: {response.status_code}")
    print(response.text)
    exit(1)

# Step 2: Fetch invoices
print("\nStep 2: Fetching invoices...")
headers = {"Authorization": f"Bearer {token}"}

response = requests.get(
    f"{API_BASE}/invoices/?limit=200",
    headers=headers
)

if response.status_code == 200:
    invoices = response.json()
    print(f"✅ Fetched {len(invoices)} invoices:")
    print(json.dumps(invoices, indent=2))
else:
    print(f"❌ Failed to fetch invoices: {response.status_code}")
    print(response.text)
