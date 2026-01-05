from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session
from typing import List

from ..database import get_db
from ..models import User, ChangeHistory
from ..schemas import ChangeHistoryResponse
from ..auth import get_current_user

router = APIRouter(prefix="/api/history", tags=["Change History"])

@router.get("", response_model=List[ChangeHistoryResponse])
async def get_change_history(
    entity_type: str = Query(None, description="Filter by entity type"),
    limit: int = Query(100, ge=1, le=500),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get change history for the organization"""
    query = db.query(ChangeHistory).filter(
        ChangeHistory.organization_id == current_user.organization_id
    )
    
    if entity_type:
        query = query.filter(ChangeHistory.entity_type == entity_type)
    
    history = query.order_by(ChangeHistory.created_at.desc()).limit(limit).all()
    
    return [ChangeHistoryResponse.model_validate(h) for h in history]
