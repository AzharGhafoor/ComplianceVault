from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func
from typing import List, Optional

from ..database import get_db
from ..models import User, Organization, Control, Evaluation, EvaluationStatus, InformationAsset, BIAProcess
from ..schemas import (
    DashboardOverviewResponse, DomainScoreResponse, PublicStatsResponse
)
from ..auth import get_current_user

router = APIRouter(prefix="/api/dashboard", tags=["Dashboard"])

def calculate_score(fully: int, partial: int, low: int, total: int) -> float:
    """Calculate compliance score with weighted credits:
    - Fully Applied: 100% (1.0)
    - Partially Applied: 50% (0.5)
    - Low Applied: 25% (0.25)
    """
    if total == 0:
        return 0.0
    return round((fully + 0.5 * partial + 0.25 * low) / total * 100, 1)

def get_status_color(score: float) -> str:
    """Get status color based on score"""
    if score >= 80:
        return "green"
    elif score >= 50:
        return "amber"
    return "red"

@router.get("/overview", response_model=DashboardOverviewResponse)
async def get_dashboard_overview(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get organization's compliance dashboard overview"""
    org_id = current_user.organization_id

    # Determine BIA Level
    has_high = db.query(InformationAsset).filter(
        InformationAsset.organization_id == org_id,
        InformationAsset.security_level == "High"
    ).first()
    
    has_medium = db.query(InformationAsset).filter(
        InformationAsset.organization_id == org_id,
        InformationAsset.security_level == "Medium"
    ).first()

    process_count = db.query(BIAProcess).filter(BIAProcess.organization_id == org_id).count()
    is_assessed = process_count > 0
    
    # Calculate domain count for target
    domain_count = db.query(Control.domain_code).distinct().count()

    additional_multiplier = 0
    if has_high:
        bia_level = "High"
        bia_target = "Baseline + 2 Controls"
        additional_multiplier = 2
    elif has_medium:
        bia_level = "Medium"
        bia_target = "Baseline + 1 Control"
        additional_multiplier = 1
    else:
        bia_level = "Low"
        bia_target = "Baseline Controls Only" if is_assessed else "Baseline (Default - BIA Required)"
        additional_multiplier = 0

    additional_req_target = domain_count * additional_multiplier

    
    # Get all controls
    controls = db.query(Control).all()
    total_controls = len(controls)
    
    baseline_controls = [c for c in controls if c.is_baseline]
    baseline_count = len(baseline_controls)
    
    # Get evaluations for this org
    evaluations = db.query(Evaluation).filter(
        Evaluation.organization_id == org_id
    ).all()
    eval_map = {e.control_id: e for e in evaluations}
    
    # Calculate overall stats
    fully_applied = 0
    partially_applied = 0
    low_applied = 0  # NEW: track low applied
    not_applied = 0
    evaluated = 0
    
    baseline_fully = 0
    baseline_partial = 0
    baseline_low = 0  # NEW: track low for baseline
    
    additional_applicable = 0
    additional_fully = 0
    additional_partial = 0
    additional_low = 0  # NEW: track low for additional
    
    applicable_count = baseline_count  # Start with baseline
    
    # NEW: Evidence coverage tracking
    controls_with_evidence = 0
    
    # Calculate stats
    for control in controls:
        eval_obj = eval_map.get(control.id)
        
        if not eval_obj or eval_obj.status == EvaluationStatus.NOT_EVALUATED.value:
            continue
        
        evaluated += 1
        
        # Check if this evaluation has evidence
        if eval_obj.evidence and len(eval_obj.evidence) > 0:
            controls_with_evidence += 1
        
        if eval_obj.status == EvaluationStatus.FULLY_APPLIED.value:
            fully_applied += 1
        elif eval_obj.status == EvaluationStatus.PARTIALLY_APPLIED.value:
            partially_applied += 1
        elif eval_obj.status == EvaluationStatus.LOW_APPLIED.value:
            low_applied += 1
        elif eval_obj.status == EvaluationStatus.NOT_APPLIED.value:
            not_applied += 1
        
        if control.is_baseline:
            if eval_obj.status == EvaluationStatus.FULLY_APPLIED.value:
                baseline_fully += 1
            elif eval_obj.status == EvaluationStatus.PARTIALLY_APPLIED.value:
                baseline_partial += 1
            elif eval_obj.status == EvaluationStatus.LOW_APPLIED.value:
                baseline_low += 1
        else:
            # Additional control: check if applicable
            # Consider applicable if explicitly marked OR if it has been applied (retroactive fix)
            is_implicitly_applicable = eval_obj and (
                eval_obj.is_applicable or 
                eval_obj.status in [EvaluationStatus.FULLY_APPLIED.value, EvaluationStatus.PARTIALLY_APPLIED.value, EvaluationStatus.LOW_APPLIED.value]
            )
            
            if is_implicitly_applicable:
                applicable_count += 1
                additional_applicable += 1
                if eval_obj.status == EvaluationStatus.FULLY_APPLIED.value:
                    additional_fully += 1
                elif eval_obj.status == EvaluationStatus.PARTIALLY_APPLIED.value:
                    additional_partial += 1
                elif eval_obj.status == EvaluationStatus.LOW_APPLIED.value:
                    additional_low += 1
    
    # Calculate domain scores
    domain_data = {}
    for control in controls:
        dc = control.domain_code
        if dc not in domain_data:
            domain_data[dc] = {
                "domain": control.domain,
                "domain_objective": control.domain_objective,
                "domain_code": dc,
                "total": 0,
                "baseline": 0,
                "baseline_fully": 0,
                "baseline_partial": 0, # NEW
                "baseline_low": 0,     # NEW
                "applicable": 0,
                "additional_applicable": 0,
                "additional_fully": 0,
                "additional_partial": 0, # NEW
                "additional_low": 0,     # NEW
                "fully": 0,
                "partial": 0,
                "low": 0,
                "not_applied": 0,
                "not_evaluated": 0
            }
        
        domain_data[dc]["total"] += 1
        
        eval_obj = eval_map.get(control.id) # Moved to top of loop

        if control.is_baseline:
            domain_data[dc]["baseline"] += 1
            domain_data[dc]["applicable"] += 1
            if eval_obj:
                if eval_obj.status == EvaluationStatus.FULLY_APPLIED.value:
                    domain_data[dc]["baseline_fully"] += 1
                elif eval_obj.status == EvaluationStatus.PARTIALLY_APPLIED.value:
                    domain_data[dc]["baseline_partial"] += 1
                elif eval_obj.status == EvaluationStatus.LOW_APPLIED.value:
                    domain_data[dc]["baseline_low"] += 1
        else:
            # Check if additional control is applicable (explicit or implicit)
            is_implicitly_applicable = eval_obj and (
                eval_obj.is_applicable or 
                eval_obj.status in [EvaluationStatus.FULLY_APPLIED.value, EvaluationStatus.PARTIALLY_APPLIED.value, EvaluationStatus.LOW_APPLIED.value]
            )
            
            if is_implicitly_applicable:
                domain_data[dc]["additional_applicable"] += 1
                domain_data[dc]["applicable"] += 1
                if eval_obj.status == EvaluationStatus.FULLY_APPLIED.value:
                    domain_data[dc]["additional_fully"] += 1
                elif eval_obj.status == EvaluationStatus.PARTIALLY_APPLIED.value:
                    domain_data[dc]["additional_partial"] += 1
                elif eval_obj.status == EvaluationStatus.LOW_APPLIED.value:
                    domain_data[dc]["additional_low"] += 1

        if not eval_obj or eval_obj.status == EvaluationStatus.NOT_EVALUATED.value:
            domain_data[dc]["not_evaluated"] += 1
        elif eval_obj.status == EvaluationStatus.FULLY_APPLIED.value:
            domain_data[dc]["fully"] += 1
        elif eval_obj.status == EvaluationStatus.PARTIALLY_APPLIED.value:
            domain_data[dc]["partial"] += 1
        elif eval_obj.status == EvaluationStatus.LOW_APPLIED.value:
            domain_data[dc]["low"] += 1
        elif eval_obj.status == EvaluationStatus.NOT_APPLIED.value:
            domain_data[dc]["not_applied"] += 1
    
    domain_scores = []
    for dc, data in domain_data.items():
        # Calculate effective target: Baseline + max(applied, target)
        additional_target_for_domain = max(data["additional_applicable"], additional_multiplier)
        effective_total = data["baseline"] + additional_target_for_domain
        
        score = calculate_score(data["fully"], data["partial"], data["low"], effective_total)
        domain_scores.append(DomainScoreResponse(
            domain_code=dc,
            domain=data["domain"],
            domain_objective=data.get("domain_objective"),
            total_controls=data["total"],
            baseline_controls=data["baseline"],
            applicable_controls=data["applicable"],
            fully_applied=data["fully"],
            partially_applied=data["partial"],
            low_applied=data["low"],  # NEW
            not_applied=data["not_applied"],
            not_evaluated=data["not_evaluated"],
            # New fields
            baseline_fully_applied=data["baseline_fully"],
            baseline_partially_applied=data["baseline_partial"], # NEW
            baseline_low_applied=data["baseline_low"],           # NEW
            additional_applicable=data["additional_applicable"],
            additional_control_target=additional_multiplier, # Target per domain based on BIA
            additional_fully_applied=data["additional_fully"],
            additional_partially_applied=data["additional_partial"], # NEW
            additional_low_applied=data["additional_low"],           # NEW
            score=score,
            status=get_status_color(score)
        ))
    
    # Sort by score ascending to find critical domains
    domain_scores.sort(key=lambda x: x.score)
    critical_domains = [d for d in domain_scores if d.status == "red"]
    
    # Sort by domain code for display
    domain_scores.sort(key=lambda x: x.domain_code)
    
    # Calculate overall effective target
    # Sum of effective total for all domains, or simplified:
    # baseline_count + max(additional_applicable, additional_req_target)
    # Using the same logic as domains ensures consistency
    overall_effective_total = baseline_count + max(additional_applicable, additional_req_target)
    
    overall_score = calculate_score(fully_applied, partially_applied, low_applied, overall_effective_total)
    baseline_score = calculate_score(baseline_fully, baseline_partial, baseline_low, baseline_count)
    
    # Calculate evidence coverage percentage
    evidence_coverage_percent = round((controls_with_evidence / evaluated * 100), 1) if evaluated > 0 else 0.0
    
    return DashboardOverviewResponse(
        overall_score=overall_score,
        baseline_score=baseline_score,
        bia_level=bia_level,
        bia_target=bia_target,
        target_score=baseline_score, # For Low/Default, target is Baseline
        baseline_fully_applied=baseline_fully,
        baseline_partially_applied=baseline_partial,
        baseline_low_applied=baseline_low,  # NEW
        additional_applicable_controls=additional_applicable,
        additional_controls_required=additional_req_target,
        additional_fully_applied=additional_fully,
        additional_partially_applied=additional_partial,
        additional_low_applied=additional_low,  # NEW
        
        total_controls=total_controls,
        baseline_controls=baseline_count,
        applicable_controls=applicable_count,
        evaluated_controls=evaluated,
        fully_applied=fully_applied,
        partially_applied=partially_applied,
        low_applied=low_applied,  # NEW
        not_applied=not_applied,
        
        # NEW: Evidence Coverage
        controls_with_evidence=controls_with_evidence,
        evidence_coverage_percent=evidence_coverage_percent,
        
        domain_scores=domain_scores,
        
        critical_domains_count=len(critical_domains),
        critical_domains=[{
            "domain_code": d.domain_code,
            "domain": d.domain,
            "score": d.score,
            "fully_applied": d.fully_applied,    # Added back
            "total_controls": d.total_controls   # Added back
        } for d in critical_domains[:5]],  # Top 5 worst domains
        
        is_bia_assessed=is_assessed
    )

@router.get("/domain/{domain_code}")
async def get_domain_details(
    domain_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """Get detailed domain compliance info"""
    controls = db.query(Control).filter(Control.domain_code == domain_code).all()
    
    if not controls:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Domain not found")
    
    evaluations = db.query(Evaluation).filter(
        Evaluation.organization_id == current_user.organization_id,
        Evaluation.control_id.in_([c.id for c in controls])
    ).all()
    eval_map = {e.control_id: e for e in evaluations}
    
    control_details = []
    for control in controls:
        eval_obj = eval_map.get(control.id)
        control_details.append({
            "control_code": control.control_code,
            "control_summary": control.control_summary,
            "is_baseline": control.is_baseline,
            "is_applicable": eval_obj.is_applicable if eval_obj else control.is_applicable,
            "status": eval_obj.status if eval_obj else "not_evaluated",
            "feedback": eval_obj.feedback if eval_obj else None
        })
    
    return {
        "domain_code": domain_code,
        "domain": controls[0].domain,
        "domain_objective": controls[0].domain_objective,
        "controls": control_details
    }

@router.get("/public", response_model=PublicStatsResponse)
async def get_public_stats(db: Session = Depends(get_db)):
    """Get aggregated public statistics (no auth required)"""
    # Count organizations
    total_orgs = db.query(func.count(Organization.id)).scalar()
    
    if total_orgs == 0:
        return PublicStatsResponse(
            total_organizations=0,
            organizations_with_full_baseline=0,
            organizations_with_additional_controls=0,
            total_evaluations=0,
            platform_evidence_coverage=0.0,
            average_compliance_score=0,
            domain_average_scores=[]
        )
    
    # Get baseline controls
    baseline_controls = db.query(Control).filter(Control.is_baseline == True).all()
    baseline_ids = [c.id for c in baseline_controls]
    baseline_count = len(baseline_ids)
    
    # Calculate per-org stats
    organizations = db.query(Organization).all()
    
    full_baseline_orgs = 0
    additional_control_orgs = 0
    total_score = 0
    
    domain_scores_sum = {}
    domain_scores_count = {}
    
    for org in organizations:
        evaluations = db.query(Evaluation).filter(
            Evaluation.organization_id == org.id
        ).all()
        
        if not evaluations:
            continue
        
        eval_map = {e.control_id: e for e in evaluations}
        
        # Check baseline completion
        baseline_fully = sum(
            1 for cid in baseline_ids
            if cid in eval_map and eval_map[cid].status == EvaluationStatus.FULLY_APPLIED.value
        )
        
        if baseline_fully == baseline_count and baseline_count > 0:
            full_baseline_orgs += 1
        
        # Check additional controls
        has_additional = any(
            e.is_applicable and e.control_id not in baseline_ids
            for e in evaluations
        )
        if has_additional:
            additional_control_orgs += 1
        
        # Calculate org score
        fully = sum(1 for e in evaluations if e.status == EvaluationStatus.FULLY_APPLIED.value)
        partial = sum(1 for e in evaluations if e.status == EvaluationStatus.PARTIALLY_APPLIED.value)
        low = sum(1 for e in evaluations if e.status == EvaluationStatus.LOW_APPLIED.value)
        org_score = calculate_score(fully, partial, low, len(evaluations))
        total_score += org_score
        
        # Calculate domain scores
        all_controls = db.query(Control).all()
        for control in all_controls:
            dc = control.domain_code
            if dc not in domain_scores_sum:
                domain_scores_sum[dc] = 0
                domain_scores_count[dc] = 0
            
            eval_obj = eval_map.get(control.id)
            if eval_obj:
                if eval_obj.status == EvaluationStatus.FULLY_APPLIED.value:
                    domain_scores_sum[dc] += 100
                elif eval_obj.status == EvaluationStatus.PARTIALLY_APPLIED.value:
                    domain_scores_sum[dc] += 50
                elif eval_obj.status == EvaluationStatus.LOW_APPLIED.value:
                    domain_scores_sum[dc] += 25
                domain_scores_count[dc] += 1

    # Platform-wide totals
    total_evaluations = db.query(func.count(Evaluation.id)).scalar()
    evals_with_evidence = db.query(func.count(Evaluation.id)).filter(Evaluation.evidence != None).scalar()
    platform_evidence_coverage = round((evals_with_evidence / total_evaluations * 100), 1) if total_evaluations > 0 else 0.0
    
    avg_score = total_score / total_orgs if total_orgs > 0 else 0
    
    # Calculate domain averages
    domain_averages = []
    domains = db.query(Control.domain_code, Control.domain).distinct().all()
    for dc, domain_name in domains:
        if dc in domain_scores_count and domain_scores_count[dc] > 0:
            avg = domain_scores_sum[dc] / domain_scores_count[dc]
        else:
            avg = 0
        domain_averages.append({
            "domain_code": dc,
            "domain": domain_name,
            "average_score": round(avg, 1)
        })
    
    domain_averages.sort(key=lambda x: x["domain_code"])
    
    return PublicStatsResponse(
        total_organizations=total_orgs,
        organizations_with_full_baseline=full_baseline_orgs,
        organizations_with_additional_controls=additional_control_orgs,
        total_evaluations=total_evaluations,
        platform_evidence_coverage=platform_evidence_coverage,
        average_compliance_score=round(avg_score, 1),
        domain_average_scores=domain_averages
    )
