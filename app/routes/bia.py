from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import json

from ..database import get_db
from ..models import BIAProcess, InformationAsset, OrganizationSettings, Organization, User, UserRole
from ..schemas import (
    BIAProcessCreate, BIAProcessUpdate, BIAProcessResponse,
    InformationAssetCreate, InformationAssetUpdate, InformationAssetResponse,
    OrganizationSettingsUpdate, OrganizationSettingsResponse
)
from ..auth import get_current_user, require_admin

router = APIRouter(prefix="/api/bia", tags=["Business Impact Analysis"])

# Helper to calculate criticality score
def calculate_criticality(process: BIAProcess, settings: OrganizationSettings) -> int:
    # Impact ratings are 0-4
    # Weights are 1-4
    # Formula: 1.25 * sum(weight_i * impact_i)
    
    score = 1.25 * (
        (process.impact_reputation * settings.weight_reputation) +
        (process.impact_external * settings.weight_external) +
        (process.impact_internal * settings.weight_internal) +
        (process.impact_legal * settings.weight_legal) +
        (process.impact_economic * settings.weight_economic)
    )
    
    return int(min(score, 100)) # Cap at 100, though formula might exceed it naturally?
    # Max possible: 1.25 * (4*4 * 5) = 1.25 * 80 = 100. Perfect.

# Helper to calculate security level
def calculate_security_level(asset: InformationAsset) -> str:
    # Logic: Max of C, I, A ratings determines level (NIA Policy v2.0)
    # C: 0-3 (Public, Internal, Limited Access, Restricted)
    # I: 0-3 (Not Important, Identifiable, Checked, Provable)
    # A: 0-3 (Not Important, 90%, 99%, 99.9%)
    # Aggregate Security Level:
    # 0-1 -> Low
    # 2 -> Medium
    # >=3 -> High
    
    max_rating = max(asset.c_rating, asset.i_rating, asset.a_rating)
    
    if max_rating >= 3:
        return "High"
    elif max_rating == 2:
        return "Medium"
    else:
        return "Low"

# ============== Settings Endpoints ==============
@router.get("/settings", response_model=OrganizationSettingsResponse)
async def get_settings(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    settings = db.query(OrganizationSettings).filter(
        OrganizationSettings.organization_id == current_user.organization_id
    ).first()
    
    if not settings:
        # Create default settings
        settings = OrganizationSettings(organization_id=current_user.organization_id)
        db.add(settings)
        db.commit()
        db.refresh(settings)
        
    return settings

@router.put("/settings", response_model=OrganizationSettingsResponse)
async def update_settings(
    settings_data: OrganizationSettingsUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin) # Only admin can change weights
):
    settings = db.query(OrganizationSettings).filter(
        OrganizationSettings.organization_id == current_user.organization_id
    ).first()
    
    if not settings:
        settings = OrganizationSettings(organization_id=current_user.organization_id)
        db.add(settings)
    
    for key, value in settings_data.model_dump(exclude_unset=True).items():
        setattr(settings, key, value)
    
    # Recalculate all process scores since weights changed
    processes = db.query(BIAProcess).filter(
        BIAProcess.organization_id == current_user.organization_id
    ).all()
    
    for proc in processes:
        proc.criticality_score = calculate_criticality(proc, settings)
    
    db.commit()
    db.refresh(settings)
    return settings

# ============== Process Endpoints ==============
@router.get("/processes", response_model=List[BIAProcessResponse])
async def list_processes(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    # Ensure settings exist
    settings = db.query(OrganizationSettings).filter(
        OrganizationSettings.organization_id == current_user.organization_id
    ).first()
    if not settings:
        settings = OrganizationSettings(organization_id=current_user.organization_id)
        db.add(settings)
        db.commit()

    processes = db.query(BIAProcess).filter(
        BIAProcess.organization_id == current_user.organization_id
    ).all()
    return processes

@router.post("/processes", response_model=BIAProcessResponse)
async def create_process(
    process_data: BIAProcessCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    settings = db.query(OrganizationSettings).filter(
        OrganizationSettings.organization_id == current_user.organization_id
    ).first()
    if not settings:
        settings = OrganizationSettings(organization_id=current_user.organization_id)
        db.add(settings)
        db.commit()
        
    process = BIAProcess(
        **process_data.model_dump(),
        organization_id=current_user.organization_id
    )
    
    process.criticality_score = calculate_criticality(process, settings)
    
    db.add(process)
    db.commit()
    db.refresh(process)
    return process

@router.put("/processes/{process_id}", response_model=BIAProcessResponse)
async def update_process(
    process_id: str,
    process_data: BIAProcessUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    process = db.query(BIAProcess).filter(
        BIAProcess.id == process_id,
        BIAProcess.organization_id == current_user.organization_id
    ).first()
    
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
        
    for key, value in process_data.model_dump(exclude_unset=True).items():
        setattr(process, key, value)
    
    settings = db.query(OrganizationSettings).filter(
        OrganizationSettings.organization_id == current_user.organization_id
    ).first()
    
    process.criticality_score = calculate_criticality(process, settings)
    
    db.commit()
    db.refresh(process)
    return process

@router.delete("/processes/{process_id}")
async def delete_process(
    process_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    process = db.query(BIAProcess).filter(
        BIAProcess.id == process_id,
        BIAProcess.organization_id == current_user.organization_id
    ).first()
    
    if not process:
        raise HTTPException(status_code=404, detail="Process not found")
        
    db.delete(process)
    db.commit()
    return {"message": "Process deleted"}

# ============== Asset Endpoints ==============
@router.post("/assets", response_model=InformationAssetResponse)
async def create_asset(
    asset_data: InformationAssetCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    try:
        # Verify process ownership
        process = db.query(BIAProcess).filter(
            BIAProcess.id == asset_data.process_id,
            BIAProcess.organization_id == current_user.organization_id
        ).first()
        
        if not process:
            print(f"Process not found: {asset_data.process_id} for org {current_user.organization_id}")
            raise HTTPException(status_code=404, detail="Process not found")
            
        asset = InformationAsset(
            **asset_data.model_dump(),
            organization_id=current_user.organization_id
        )
        
        asset.security_level = calculate_security_level(asset)
        
        db.add(asset)
        db.commit()
        db.refresh(asset)
        return asset
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise e

@router.put("/assets/{asset_id}", response_model=InformationAssetResponse)
async def update_asset(
    asset_id: str,
    asset_data: InformationAssetUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    asset = db.query(InformationAsset).filter(
        InformationAsset.id == asset_id,
        InformationAsset.organization_id == current_user.organization_id
    ).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
        
    for key, value in asset_data.model_dump(exclude_unset=True).items():
        setattr(asset, key, value)
        
    asset.security_level = calculate_security_level(asset)
    
    db.commit()
    db.refresh(asset)
    return asset

@router.delete("/assets/{asset_id}")
async def delete_asset(
    asset_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_admin)
):
    asset = db.query(InformationAsset).filter(
        InformationAsset.id == asset_id,
        InformationAsset.organization_id == current_user.organization_id
    ).first()
    
    if not asset:
        raise HTTPException(status_code=404, detail="Asset not found")
        
    db.delete(asset)
    db.commit()
    return {"message": "Asset deleted"}

@router.get("/compliance-level")
async def get_compliance_level(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Determine the organization's aggregate compliance level target"""
    # Simply High if any High asset exists, else Medium if any Medium, else Low.
    
    has_high = db.query(InformationAsset).filter(
        InformationAsset.organization_id == current_user.organization_id,
        InformationAsset.security_level == "High"
    ).first()
    
    process_count = db.query(BIAProcess).filter(
        BIAProcess.organization_id == current_user.organization_id
    ).count()

    has_medium = db.query(InformationAsset).filter(
        InformationAsset.organization_id == current_user.organization_id,
        InformationAsset.security_level == "Medium"
    ).first()
    
    is_assessed = process_count > 0
    
    if has_high:
        return {"level": "High", "controls": "Baseline + 2+", "is_assessed": is_assessed}
        
    if has_medium:
        return {"level": "Medium", "controls": "Baseline + 1+", "is_assessed": is_assessed}
        
    return {"level": "Low", "controls": "Baseline", "is_assessed": is_assessed}
