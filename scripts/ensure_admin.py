from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import sys
import os

# Add parent dir to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import Base, SessionLocal
from app.models import User, UserRole, Organization
from app.auth import get_password_hash

db = SessionLocal()

# Ensure Org
org = db.query(Organization).filter(Organization.name == "Test Org").first()
if not org:
    org = Organization(name="Test Org")
    db.add(org)
    db.commit()

# Ensure User
user = db.query(User).filter(User.email == "admin@example.com").first()
if not user:
    user = User(
        email="admin@example.com",
        password_hash=get_password_hash("admin123"),
        first_name="Admin",
        last_name="User",
        role=UserRole.ADMIN,
        organization_id=org.id
    )
    db.add(user)
    db.commit()
    print("User created: admin@example.com / admin123")
else:
    # Reset password just in case
    user.password_hash = get_password_hash("admin123")
    db.commit()
    print("User updated: admin@example.com / admin123")

db.close()
