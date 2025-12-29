"""
Check user login credentials
"""
from app.database import SessionLocal
from app.models.user import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

db = SessionLocal()

# Try common test passwords
test_passwords = ["testpassword", "testpassword123", "password", "password123"]

users = db.query(User).all()

for user in users:
    print(f"\n👤 Username: {user.username}")
    print(f"   Email: {user.email}")
    
    # Try common passwords
    for pwd in test_passwords:
        if pwd_context.verify(pwd, user.hashed_password):
            print(f"   ✅ Password: {pwd}")
            break
    else:
        print(f"   ⚠️  Password: Not in common list")

db.close()
