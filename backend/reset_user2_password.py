"""Reset user2 password to a known value"""
from app.database import SessionLocal
from app.models.user import User
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

db = SessionLocal()

user2 = db.query(User).filter(User.username == "user2").first()

if user2:
    # Set password to 'user2pass'
    user2.hashed_password = pwd_context.hash("user2pass")
    db.commit()
    print("✅ Password reset successfully!")
    print("Username: user2")
    print("Password: user2pass")
else:
    print("❌ user2 not found")

db.close()
