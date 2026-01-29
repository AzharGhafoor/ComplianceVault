
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
                # Core Identifiers
                control_code=c.get("control_code"),
                nia_version=c.get("nia_version"),
                section=c.get("section"),
                domain=c.get("domain"),
                domain_code=c.get("domain_code"),
                domain_objective=c.get("domain_objective"),
                
                # Control Content
                control_statement=c.get("control_statement", ""),
                control_summary=c.get("control_summary", ""),
                control_description=c.get("control_description", ""),
                
                # Types (Boolean)
                type_deter=c.get("type_deter", False),
                type_avoid=c.get("type_avoid", False),
                type_prevent=c.get("type_prevent", False),
                type_detect=c.get("type_detect", False),
                type_react=c.get("type_react", False),
                type_recover=c.get("type_recover", False),
                
                # Objectives (Boolean)
                obj_confidentiality=c.get("obj_confidentiality", False),
                obj_integrity=c.get("obj_integrity", False),
                obj_availability=c.get("obj_availability", False),

                # Applicability
                is_baseline=c.get("is_baseline", True),
                is_applicable=c.get("is_applicable", True),

                # Framework Mappings
                iso27001_2013=c.get("iso27001_2013"),
                pci_dss_v31=c.get("pci_dss_v31"),
                sp_800_53_rev4=c.get("sp_800_53_rev4"),
                qscf_process_phases=c.get("qscf_process_phases"),
                qscf_activities_controls=c.get("qscf_activities_controls"),
                qscf_niap2_controls=c.get("qscf_niap2_controls"),
                qscf_nics_standard_v30=c.get("qscf_nics_standard_v30"),
                qscf_csc=c.get("qscf_csc"),
                qscf_isa_62443_2_1_2009=c.get("qscf_isa_62443_2_1_2009"),
                qscf_isa_62443_3_3_2013=c.get("qscf_isa_62443_3_3_2013"),
                qscf_iso_iec_27001_2013=c.get("qscf_iso_iec_27001_2013"),
                qscf_nist_sp_800_53_rev4=c.get("qscf_nist_sp_800_53_rev4"),
                qscf_pci_dss_32=c.get("qscf_pci_dss_32"),
                qscf_hipaa=c.get("qscf_hipaa"),
                qscf_ccm_v301=c.get("qscf_ccm_v301"),
                qscf_gdpr=c.get("qscf_gdpr")
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
