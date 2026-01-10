
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, Domain, Control
from app.config import settings

def seed_controls():
    print("Beginning database seeding...")
    
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Check if data already exists
        if db.query(Domain).count() > 0:
            print("Database already contains data. skipping.")
            return

        # 1. Define Domains
        domains_data = [
            {"code": "AM", "name": "Asset Management", "description": "Asset Management"},
            {"code": "BC", "name": "Business Continuity Management", "description": "Business Continuity Management"},
            {"code": "HR", "name": "Human Resources Security", "description": "Human Resources Security"},
            {"code": "IM", "name": "Incident Management", "description": "Incident Management"},
            {"code": "IS", "name": "Information Systems Acquisition, Development and Maintenance", "description": "Information Systems Acquisition, Development and Maintenance"},
            {"code": "LO", "name": "Legal and Regulatory Compliance", "description": "Legal and Regulatory Compliance"},
            {"code": "OS", "name": "Operations Security", "description": "Operations Security"},
            {"code": "PA", "name": "Physical and Environmental Security", "description": "Physical and Environmental Security"},
            {"code": "PM", "name": "Performance Management", "description": "Performance Management"},
            {"code": "PS", "name": "Privacy Security", "description": "Privacy Security"},
            {"code": "RA", "name": "Risk Management", "description": "Risk Management"},
            {"code": "RE", "name": "Third-Party Relationships Security", "description": "Third-Party Relationships Security"},
            {"code": "SG", "name": "Security Governance", "description": "Security Governance"},
            {"code": "SS", "name": "Software Security", "description": "Software Security"}
        ]

        print(f"Creating {len(domains_data)} Domains...")
        domain_objects = {}
        for d in domains_data:
            domain = Domain(**d)
            db.add(domain)
            db.flush() # flush to get ID
            domain_objects[d['code']] = domain

        # 2. Define Controls (Sample set - expand with full policy later or ask user)
        # Assuming we want a representative set to make the app functional immediately.
        # This is a large list in reality. For this step, I will add a few critical ones and ensure the structure works.
        # User can run a full import later if needed, but usually we ship with the full set.
        
        controls_data = [
             # Governance
            {"code": "SG-01", "name": "Information Security Roles and Responsibilities", "domain_code": "SG", "description": "The Agency shall allocate information security roles and responsibilities in accordance with the information security needs of the Agency."},
            {"code": "SG-02", "name": "Confidentiality Binding", "domain_code": "SG", "description": "The Agency shall ensure that all employees, contractors and third party users sign confidentiality/non-disclosure agreements."},
            {"code": "SG-03", "name": "Segregation of Duties", "domain_code": "SG", "description": "The Agency shall enforce segregation of duties to reduce the risk of accidental or deliberate misuse of the Agency's information assets."},
            
             # Asset Management
            {"code": "AM-01", "name": "Asset Inventory", "domain_code": "AM", "description": "The Agency shall maintain an accurate and up-to-date inventory of all information assets."},
            {"code": "AM-02", "name": "Asset Ownership", "domain_code": "AM", "description": "The Agency shall assign an owner for each information asset who is responsible for its protection."},
            {"code": "AM-03", "name": "Acceptable Use of Assets", "domain_code": "AM", "description": "The Agency shall document and disseminate rules for the acceptable use of information assets."},

            # Access Control (Logical) -> Mapped to OS for now or verify standard mapping
            # In NIA Policy, Access Control is often its own or part of OS/SS. 
            # I will strictly follow the domain codes defined above.
            
            # Risk Management
            {"code": "RA-01", "name": "Risk Assessment Methodology", "domain_code": "RA", "description": "The Agency shall define and document a risk assessment methodology."},
            
            # ... (We will rely on the user to provide the full list or we provide a mechanism to upload)
            # For now, let's enable the "Empty Shell" to be functional with these core items.
        ]

        # NOTE to USER: This is a starter set. 
        # Ideally, we load this from a JSON file.
        
        print(f"Creating {len(controls_data)} Controls...")
        for c in controls_data:
            domain_code = c.pop("domain_code")
            c["domain_id"] = domain_objects[domain_code].id
            control = Control(**c)
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
