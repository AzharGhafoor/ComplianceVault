"""
Initialize the database schema for Railway deployment
Run this once to set up tables
"""
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, Base
from app.models import *

def init_database():
    print("Creating database tables...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully!")

if __name__ == "__main__":
    init_database()
