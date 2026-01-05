from fastapi import APIRouter, Depends, HTTPException, status, UploadFile, File
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import func
from typing import List, Optional
from datetime import datetime
import os
import uuid
import json

from ..database import get_db
from ..models import User, Control, Evaluation, Evidence, Comment, ChangeHistory, EvaluationStatus
from ..schemas import (
    EvaluationUpdate, EvaluationResponse, EvaluationWithControlResponse,
    EvidenceResponse, CommentCreate, CommentResponse, ControlListResponse
)
from ..auth import get_current_user, require_auditor, require_commenter
from ..config import settings

router = APIRouter(prefix="/api/evaluations", tags=["Evaluations"])

def log_change(db: Session, user: User, entity_type: str, entity_id: str, action: str, changes: dict):
    """Log a change to the history"""
    history = ChangeHistory(
        organization_id=user.organization_id,
        entity_type=entity_type,
        entity_id=entity_id,
        action=action,
        changes=json.dumps(changes),
        user_id=user.id,
        user_name=user.full_name
    )
    db.add(history)

@router.get("", response_model=List[EvaluationWithControlResponse])
async def list_evaluations(
    domain_code: Optional[str] = None,
    is_baseline: Optional[bool] = None,
    status_filter: Optional[str] = None,
    search: Optional[str] = None,
    skip: int = 0,
    limit: int = 50,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List all controls with their evaluations for the organization"""
    # Get all controls first
    query = db.query(Control)
    
    if domain_code:
        query = query.filter(Control.domain_code == domain_code)
    if is_baseline is not None:
        query = query.filter(Control.is_baseline == is_baseline)
    if search:
        search_term = f"%{search}%"
        query = query.filter(
            (Control.control_code.ilike(search_term)) |
            (Control.control_summary.ilike(search_term))
        )
    
    controls = query.order_by(Control.domain_code, Control.control_code).offset(skip).limit(limit).all()
    
    # Get evaluations for these controls
    control_ids = [c.id for c in controls]
    evaluations = db.query(Evaluation).filter(
        Evaluation.organization_id == current_user.organization_id,
        Evaluation.control_id.in_(control_ids)
    ).all()
    
    eval_map = {e.control_id: e for e in evaluations}
    
    # Get evidence and comment counts
    evidence_counts = {}
    comment_counts = {}
    eval_ids = [e.id for e in evaluations]
    if eval_ids:
        ev_counts = db.query(
            Evidence.evaluation_id, func.count(Evidence.id)
        ).filter(Evidence.evaluation_id.in_(eval_ids)).group_by(Evidence.evaluation_id).all()
        evidence_counts = {ec[0]: ec[1] for ec in ev_counts}
        
        cm_counts = db.query(
            Comment.evaluation_id, func.count(Comment.id)
        ).filter(Comment.evaluation_id.in_(eval_ids)).group_by(Comment.evaluation_id).all()
        comment_counts = {cc[0]: cc[1] for cc in cm_counts}
    
    result = []
    for control in controls:
        eval_obj = eval_map.get(control.id)
        
        # Apply status filter
        if status_filter:
            if eval_obj and eval_obj.status != status_filter:
                continue
            if not eval_obj and status_filter != "not_evaluated":
                continue
        
        result.append(EvaluationWithControlResponse(
            control=ControlListResponse.model_validate(control),
            evaluation=EvaluationResponse.model_validate(eval_obj) if eval_obj else None,
            evidence_count=evidence_counts.get(eval_obj.id, 0) if eval_obj else 0,
            comment_count=comment_counts.get(eval_obj.id, 0) if eval_obj else 0
        ))
    
    return result

@router.put("/{control_code}", response_model=EvaluationResponse)
async def update_evaluation(
    control_code: str,
    update_data: EvaluationUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auditor)
):
    """Update evaluation for a control (auditor only)"""
    control = db.query(Control).filter(Control.control_code == control_code).first()
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")
    
    # Get or create evaluation
    evaluation = db.query(Evaluation).filter(
        Evaluation.organization_id == current_user.organization_id,
        Evaluation.control_id == control.id
    ).first()
    
    old_status = None
    if evaluation:
        old_status = evaluation.status
    else:
        evaluation = Evaluation(
            organization_id=current_user.organization_id,
            control_id=control.id
        )
        db.add(evaluation)
    
    # Update fields
    evaluation.status = update_data.status.value
    evaluation.feedback = update_data.feedback
    
    # Auto-update is_applicable based on status if not explicitly provided
    if update_data.is_applicable is not None:
        evaluation.is_applicable = update_data.is_applicable
    elif not control.is_baseline:
        # If no explicit applicability setting, infer from status for additional controls
        # If status is NOT_EVALUATED, assume not applicable (reset)
        # If status is anything else (Applied, Partial, etc.), it MUST be applicable
        if update_data.status == EvaluationStatus.NOT_EVALUATED:
            evaluation.is_applicable = False
        else:
            evaluation.is_applicable = True

    evaluation.auditor_id = current_user.id
    evaluation.evaluated_at = datetime.utcnow()
    
    # Log change
    log_change(db, current_user, "evaluation", str(control.id), "update", {
        "control_code": control_code,
        "old_status": old_status,
        "new_status": update_data.status.value,
        "feedback": update_data.feedback
    })
    
    db.commit()
    db.refresh(evaluation)
    
    return EvaluationResponse.model_validate(evaluation)

@router.get("/{control_code}", response_model=EvaluationWithControlResponse)
async def get_evaluation(
    control_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get evaluation for a specific control"""
    control = db.query(Control).filter(Control.control_code == control_code).first()
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")
    
    evaluation = db.query(Evaluation).filter(
        Evaluation.organization_id == current_user.organization_id,
        Evaluation.control_id == control.id
    ).first()
    
    evidence_count = 0
    comment_count = 0
    if evaluation:
        evidence_count = db.query(func.count(Evidence.id)).filter(
            Evidence.evaluation_id == evaluation.id
        ).scalar()
        comment_count = db.query(func.count(Comment.id)).filter(
            Comment.evaluation_id == evaluation.id
        ).scalar()
    
    return EvaluationWithControlResponse(
        control=ControlListResponse.model_validate(control),
        evaluation=EvaluationResponse.model_validate(evaluation) if evaluation else None,
        evidence_count=evidence_count,
        comment_count=comment_count
    )

# ============== Evidence Endpoints ==============
ALLOWED_MIME_TYPES = {
    "image/jpeg",
    "image/png",
    "application/pdf"
}

@router.get("/{control_code}/evidence/{evidence_id}/download")
async def download_evidence(
    control_code: str,
    evidence_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Download an evidence file"""
    from fastapi.responses import FileResponse
    
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    
    # Verify ownership
    evaluation = db.query(Evaluation).filter(
        Evaluation.id == evidence.evaluation_id,
        Evaluation.organization_id == current_user.organization_id
    ).first()
    
    if not evaluation:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Check if file exists
    if not os.path.exists(evidence.file_path):
        raise HTTPException(status_code=404, detail="File not found on server")
    
    return FileResponse(
        path=evidence.file_path,
        filename=evidence.file_name,
        media_type=evidence.file_type
    )

@router.post("/{control_code}/evidence", response_model=EvidenceResponse)
async def upload_evidence(
    control_code: str,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auditor)
):
    """Upload evidence file for a control (jpg, png, pdf only)"""
    # Validate MIME type
    if file.content_type not in ALLOWED_MIME_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type. Only JPG, PNG, and PDF files are allowed. Received: {file.content_type}"
        )
    
    control = db.query(Control).filter(Control.control_code == control_code).first()
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")
    
    # Get or create evaluation
    evaluation = db.query(Evaluation).filter(
        Evaluation.organization_id == current_user.organization_id,
        Evaluation.control_id == control.id
    ).first()
    
    if not evaluation:
        evaluation = Evaluation(
            organization_id=current_user.organization_id,
            control_id=control.id,
            status=EvaluationStatus.NOT_EVALUATED.value
        )
        db.add(evaluation)
        db.flush()
    
    # Save file
    upload_dir = os.path.join(settings.UPLOAD_DIR, current_user.organization_id)
    os.makedirs(upload_dir, exist_ok=True)
    
    file_ext = os.path.splitext(file.filename)[1]
    unique_name = f"{uuid.uuid4()}{file_ext}"
    file_path = os.path.join(upload_dir, unique_name)
    
    content = await file.read()
    with open(file_path, "wb") as f:
        f.write(content)
    
    evidence = Evidence(
        evaluation_id=evaluation.id,
        file_name=file.filename,
        file_path=file_path,
        file_type=file.content_type,
        file_size=len(content),
        uploaded_by=current_user.id
    )
    db.add(evidence)
    
    log_change(db, current_user, "evidence", control_code, "upload", {
        "file_name": file.filename
    })
    
    db.commit()
    db.refresh(evidence)
    
    return EvidenceResponse.model_validate(evidence)


@router.get("/{control_code}/evidence", response_model=List[EvidenceResponse])
async def list_evidence(
    control_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List evidence files for a control"""
    control = db.query(Control).filter(Control.control_code == control_code).first()
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")
    
    evaluation = db.query(Evaluation).filter(
        Evaluation.organization_id == current_user.organization_id,
        Evaluation.control_id == control.id
    ).first()
    
    if not evaluation:
        return []
    
    evidence_list = db.query(Evidence).filter(
        Evidence.evaluation_id == evaluation.id
    ).order_by(Evidence.uploaded_at.desc()).all()
    
    return [EvidenceResponse.model_validate(e) for e in evidence_list]

@router.delete("/{control_code}/evidence/{evidence_id}")
async def delete_evidence(
    control_code: str,
    evidence_id: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_auditor)
):
    """Delete an evidence file"""
    evidence = db.query(Evidence).filter(Evidence.id == evidence_id).first()
    if not evidence:
        raise HTTPException(status_code=404, detail="Evidence not found")
    
    # Verify ownership
    evaluation = db.query(Evaluation).filter(
        Evaluation.id == evidence.evaluation_id,
        Evaluation.organization_id == current_user.organization_id
    ).first()
    
    if not evaluation:
        raise HTTPException(status_code=403, detail="Access denied")
    
    # Restrict deletion to uploader (or admin)
    if evidence.uploaded_by != current_user.id and current_user.role != "admin":
        raise HTTPException(
            status_code=403, 
            detail="You can only delete evidence that you uploaded"
        )
    
    # Delete file
    if os.path.exists(evidence.file_path):
        os.remove(evidence.file_path)
    
    log_change(db, current_user, "evidence", control_code, "delete", {
        "file_name": evidence.file_name
    })
    
    db.delete(evidence)
    db.commit()
    
    return {"message": "Evidence deleted"}

# ============== Comment Endpoints ==============
@router.post("/{control_code}/comments", response_model=CommentResponse)
async def add_comment(
    control_code: str,
    comment_data: CommentCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_commenter)
):
    """Add a comment to a control (commenter role or above)"""
    control = db.query(Control).filter(Control.control_code == control_code).first()
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")
    
    # Get or create evaluation
    evaluation = db.query(Evaluation).filter(
        Evaluation.organization_id == current_user.organization_id,
        Evaluation.control_id == control.id
    ).first()
    
    if not evaluation:
        evaluation = Evaluation(
            organization_id=current_user.organization_id,
            control_id=control.id,
            status=EvaluationStatus.NOT_EVALUATED.value
        )
        db.add(evaluation)
        db.flush()
    
    comment = Comment(
        evaluation_id=evaluation.id,
        user_id=current_user.id,
        content=comment_data.content
    )
    db.add(comment)
    
    log_change(db, current_user, "comment", control_code, "add", {
        "content": comment_data.content[:100]
    })
    
    db.commit()
    db.refresh(comment)
    
    return CommentResponse(
        id=comment.id,
        content=comment.content,
        user_id=comment.user_id,
        user_name=current_user.full_name,
        user_role=current_user.role,
        created_at=comment.created_at
    )

@router.get("/{control_code}/comments", response_model=List[CommentResponse])
async def list_comments(
    control_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """List comments for a control"""
    control = db.query(Control).filter(Control.control_code == control_code).first()
    if not control:
        raise HTTPException(status_code=404, detail="Control not found")
    
    evaluation = db.query(Evaluation).filter(
        Evaluation.organization_id == current_user.organization_id,
        Evaluation.control_id == control.id
    ).first()
    
    if not evaluation:
        return []
    
    comments = db.query(Comment).options(
        joinedload(Comment.user)
    ).filter(
        Comment.evaluation_id == evaluation.id
    ).order_by(Comment.created_at.desc()).all()
    
    return [
        CommentResponse(
            id=c.id,
            content=c.content,
            user_id=c.user_id,
            user_name=c.user.full_name if c.user else None,
            user_role=c.user.role if c.user else None,
            created_at=c.created_at
        )
        for c in comments
    ]
