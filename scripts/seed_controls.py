
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
        # Check if data exists - if so, we need to UPDATE or REPLACE because the previous seed was broken or incomplete
        existing_count = db.query(Control).count()
        if existing_count > 0:
            print(f"Found {existing_count} existing controls. Clearing to re-seed with FULL DATASET...")
            db.query(Control).delete()
            db.commit()

        # Load controls from JSON export
        json_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "niap_controls.json")
        if not os.path.exists(json_path):
            print(f"Error: Seed file not found at {json_path}")
            return
            
        with open(json_path, 'r', encoding='utf-8') as f:
            controls_data = json.load(f)

        print(f"Loading {len(controls_data)} Controls from JSON...")
        
        for c in controls_data:
            # Create control object
            # Filter out 'id' and 'created_at' to let DB handle them
            c.pop('id', None)
            c.pop('created_at', None)
            
            # Ensure mapped fields are present if they were missing in source
            if not c.get('control_statement') and c.get('control_description'):
                 c['control_statement'] = c['control_description']
            
            if not c.get('control_summary') and c.get('control_description'):
                 c['control_summary'] = c['control_description']

            control = Control(**c)
            db.add(control)
        
        db.commit()
        print("✅ Database successfully seeded with FULL DATASET!")

    except Exception as e:
        db.rollback()
        print(f"Error seeding database: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    seed_controls()
