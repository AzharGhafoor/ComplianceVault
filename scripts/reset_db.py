import sys
import os
import shutil

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from app.models import Base, User, Organization, UserRole, OrganizationSettings
from app.auth import get_password_hash
from app.config import settings

def reset_database():
    print("Starting database cleanup...")
    
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # 1. Clear tables (Order matters for Foreign Keys)
        tables_to_clear = [
            "evidence",
            "comments",
            "evaluations",
            "change_history",
            "sessions",
            "security_logs",
            "rate_limit_tracker",
            "information_assets",
            "bia_processes",
            "organization_settings",
            "users",
            "organizations"
        ]
        
        # Enable FK for deletion consistency if supported
        db.execute(text("PRAGMA foreign_keys = ON"))
        
        for table in tables_to_clear:
            print(f"Clearing table: {table}")
            try:
                db.execute(text(f"DELETE FROM {table}"))
            except Exception as e:
                print(f"Warning: Could not clear {table}: {e}")
        
        db.commit()
        
        # 2. Re-create default Admin and Organization
        print("Creating default admin account...")
        
        org = Organization(
            name="Default Organization",
            sector="Public Sector",
            size="Enterprise"
        )
        db.add(org)
        db.flush() # Get org.id
        
        # Default BIA settings
        org_settings = OrganizationSettings(organization_id=org.id)
        db.add(org_settings)
        
        admin_user = User(
            email="admin@compliancevault.pro",
            password_hash=get_password_hash("Admin123!"),
            first_name="System",
            last_name="Administrator",
            role=UserRole.ADMIN.value,
            organization_id=org.id,
            status="active"
        )
        db.add(admin_user)
        db.commit()
        
        # 3. Clean uploads directory
        if "RAILWAY_VOLUME_MOUNT_PATH" in os.environ:
            uploads_dir = os.path.join(os.environ.get("RAILWAY_VOLUME_MOUNT_PATH"), "uploads")
        else:
            uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
        if os.path.exists(uploads_dir):
            print("Cleaning uploads directory...")
            for filename in os.listdir(uploads_dir):
                file_path = os.path.join(uploads_dir, filename)
                try:
                    if os.path.isfile(file_path) or os.path.islink(file_path):
                        os.unlink(file_path)
                    elif os.path.isdir(file_path):
                        shutil.rmtree(file_path)
                except Exception as e:
                    print(f"Failed to delete {file_path}. Reason: {e}")
        
        print("\nCleanup successful!")
        print("-" * 30)
        print("Default Account Credentials:")
        print("Email: admin@compliancevault.pro")
        print("Password: Admin123!")
        print("-" * 30)
        print("NOTE: The 'controls' table was preserved.")
        
    except Exception as e:
        db.rollback()
        print(f"Error during cleanup: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    reset_database()
