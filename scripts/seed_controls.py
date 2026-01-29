
import sys
import os

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.models import Base, Control
from app.config import settings

import json

def seed_controls():
    print("Beginning database seeding...")
    
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()

    try:
        # Load controls from JSON file
        json_path = os.path.join(os.path.dirname(__file__), "niap_controls.json")
        if not os.path.exists(json_path):
            print(f"Error: niap_controls.json not found at {json_path}")
            return

        with open(json_path, 'r', encoding='utf-8') as f:
            controls_data = json.load(f)

        existing_count = db.query(Control).count()
        if existing_count > 0:
            print(f"Found {existing_count} existing controls. Clearing to re-seed with full dataset...")
            db.query(Control).delete()
            db.commit()
            
        print(f"Creating {len(controls_data)} Controls...")
        
        controls_to_add = []
        for c in controls_data:
            # Map input keys to Model columns
            control = Control(
                control_code=c["control_code"],
                section=c["section"],
                domain=c["domain"],
                domain_code=c["domain_code"],
                
                control_statement=c.get("control_statement", ""),
                control_summary=c.get("control_summary", ""),
                control_description=c.get("control_description", ""),
                
                is_baseline=c.get("is_baseline", True),
                is_applicable=c.get("is_applicable", True)
            )
            controls_to_add.append(control)
        
        # Batch insert for performance
        db.add_all(controls_to_add)
        db.commit()
        print(f"✅ Database successfully seeded with {len(controls_to_add)} controls!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_controls()
