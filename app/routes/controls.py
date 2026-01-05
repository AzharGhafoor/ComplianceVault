from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from ..database import get_db
from ..models import Control
from ..schemas import ControlResponse, ControlListResponse, DomainResponse
from ..auth import get_current_user

router = APIRouter(prefix="/api/controls", tags=["Controls"])

@router.get("", response_model=List[ControlListResponse])
async def list_controls(
    domain_code: Optional[str] = Query(None, description="Filter by domain code"),
    section: Optional[str] = Query(None, description="Filter by section"),
    is_baseline: Optional[bool] = Query(None, description="Filter baseline controls"),
    type_filter: Optional[str] = Query(None, description="Filter by type: deter,avoid,prevent,detect,react,recover"),
    objective_filter: Optional[str] = Query(None, description="Filter by objective: confidentiality,integrity,availability"),
    search: Optional[str] = Query(None, description="Search in control code or summary"),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """List all controls with filters"""
    query = db.query(Control)
    
    if domain_code:
        query = query.filter(Control.domain_code == domain_code)
    
    if section:
        query = query.filter(Control.section == section)
    
    if is_baseline is not None:
        query = query.filter(Control.is_baseline == is_baseline)
    
    if type_filter:
        type_map = {
            "deter": Control.type_deter,
            "avoid": Control.type_avoid,
            "prevent": Control.type_prevent,
            "detect": Control.type_detect,
            "react": Control.type_react,
            "recover": Control.type_recover
        }
        if type_filter in type_map:
            query = query.filter(type_map[type_filter] == True)
    
    if objective_filter:
        obj_map = {
            "confidentiality": Control.obj_confidentiality,
            "integrity": Control.obj_integrity,
            "availability": Control.obj_availability
        }
        if objective_filter in obj_map:
            query = query.filter(obj_map[objective_filter] == True)
    
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Control.control_code.ilike(search_term)) |
            (Control.control_summary.ilike(search_term))
        )
    
    controls = query.order_by(Control.domain_code, Control.control_code).offset(skip).limit(limit).all()
    
    return [ControlListResponse.model_validate(c) for c in controls]

@router.get("/count")
async def get_controls_count(
    domain_code: Optional[str] = None,
    is_baseline: Optional[bool] = None,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get total count of controls with optional filters"""
    query = db.query(func.count(Control.id))
    
    if domain_code:
        query = query.filter(Control.domain_code == domain_code)
    if is_baseline is not None:
        query = query.filter(Control.is_baseline == is_baseline)
    
    count = query.scalar()
    return {"count": count}

@router.get("/domains", response_model=List[DomainResponse])
async def list_domains(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get all domains with metadata"""
    # Get domain aggregates
    domains = db.query(
        Control.domain_code,
        Control.domain,
        Control.domain_objective,
        Control.section,
        func.count(Control.id).label("control_count"),
        func.sum(func.cast(Control.is_baseline, Integer)).label("baseline_count")
    ).group_by(
        Control.domain_code,
        Control.domain,
        Control.domain_objective,
        Control.section
    ).order_by(Control.section, Control.domain_code).all()
    
    return [
        DomainResponse(
            domain_code=d.domain_code,
            domain=d.domain,
            domain_objective=d.domain_objective,
            section=d.section,
            control_count=d.control_count,
            baseline_count=d.baseline_count or 0
        )
        for d in domains
    ]

@router.get("/{control_code}", response_model=ControlResponse)
async def get_control(
    control_code: str,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    """Get a specific control by code"""
    control = db.query(Control).filter(Control.control_code == control_code).first()
    
    if not control:
        from fastapi import HTTPException, status
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Control not found"
        )
    
    return ControlResponse.model_validate(control)

# Need to import Integer for casting
from sqlalchemy import Integer
