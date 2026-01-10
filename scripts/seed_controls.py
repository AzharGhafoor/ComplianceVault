
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, Control
from app.config import settings

def seed_controls():
    print("Beginning database seeding...")
    
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Check if data exists - if so, we need to UPDATE or REPLACE because the previous seed was broken
        existing_count = db.query(Control).count()
        if existing_count > 0:
            print(f"Found {existing_count} existing controls. clearing to re-seed with correct data mapping...")
            db.query(Control).delete()
            db.commit()

        # Define Controls with their Domain info embedded
        controls_data = [
             # Governance
            {"code": "SG-01", "name": "Information Security Roles and Responsibilities", "domain_code": "SG", "domain": "Security Governance", "description": "The Agency shall allocate information security roles and responsibilities in accordance with the information security needs of the Agency."},
            {"code": "SG-02", "name": "Confidentiality Binding", "domain_code": "SG", "domain": "Security Governance", "description": "The Agency shall ensure that all employees, contractors and third party users sign confidentiality/non-disclosure agreements."},
            {"code": "SG-03", "name": "Segregation of Duties", "domain_code": "SG", "domain": "Security Governance", "description": "The Agency shall enforce segregation of duties to reduce the risk of accidental or deliberate misuse of the Agency's information assets."},
            
             # Asset Management
            {"code": "AM-01", "name": "Asset Inventory", "domain_code": "AM", "domain": "Asset Management", "description": "The Agency shall maintain an accurate and up-to-date inventory of all information assets."},
            {"code": "AM-02", "name": "Asset Ownership", "domain_code": "AM", "domain": "Asset Management", "description": "The Agency shall assign an owner for each information asset who is responsible for its protection."},
            {"code": "AM-03", "name": "Acceptable Use of Assets", "domain_code": "AM", "domain": "Asset Management", "description": "The Agency shall document and disseminate rules for the acceptable use of information assets."},

            # Risk Management
            {"code": "RA-01", "name": "Risk Assessment Methodology", "domain_code": "RA", "domain": "Risk Management", "description": "The Agency shall define and document a risk assessment methodology."},
        ]
        
        print(f"Creating {len(controls_data)} Controls...")
        for c in controls_data:
            # Map input keys to Model columns
            control = Control(
                control_code=c["code"],
                section=c["name"], # Using name as section/title
                domain=c["domain"],
                domain_code=c["domain_code"],
                
                # FIX: Map description to statement AND summary so it shows in UI
                control_statement=c["description"],
                control_summary=c["description"],
                control_description=c["description"],
                
                # Defaults
                is_baseline=True,
                is_applicable=True
            )
            db.add(control)
        
        db.commit()
        print("✅ Database successfully seeded!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_controls()
