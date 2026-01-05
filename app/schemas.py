from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

# ============== Enums ==============
class UserRoleEnum(str, Enum):
    admin = "admin"
    auditor = "auditor"
    commenter = "commenter"
    viewer = "viewer"

class EvaluationStatusEnum(str, Enum):
    not_evaluated = "not_evaluated"
    fully_applied = "fully_applied"
    partially_applied = "partially_applied"
    low_applied = "low_applied"  # NEW: 25% credit
    not_applied = "not_applied"

# ============== Auth Schemas ==============
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: "UserResponse"

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(..., min_length=8)
    first_name: str
    last_name: str
    organization_name: str
    organization_sector: Optional[str] = None
    organization_size: Optional[str] = None
    organization_country: str = "Qatar"
    organization_contact_email: str
    organization_contact_phone: str
    organization_domain: str

class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str = Field(..., min_length=8)

# ============== User Schemas ==============
class UserBase(BaseModel):
    email: EmailStr
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: UserRoleEnum = UserRoleEnum.viewer

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserUpdate(BaseModel):
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[UserRoleEnum] = None
    status: Optional[str] = None

class UserResponse(BaseModel):
    id: str
    email: str
    first_name: Optional[str]
    last_name: Optional[str]
    role: str
    status: str
    organization_id: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============== Organization Schemas ==============
class OrganizationBase(BaseModel):
    name: str
    description: Optional[str] = None
    country: str = "Qatar"
    sector: Optional[str] = None
    size: Optional[str] = None

class OrganizationUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    sector: Optional[str] = None
    size: Optional[str] = None

class OrganizationResponse(BaseModel):
    id: str
    name: str
    description: Optional[str]
    country: str
    sector: Optional[str]
    size: Optional[str]
    status: str
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============== Control Schemas ==============
class ControlResponse(BaseModel):
    id: int
    nia_version: Optional[str]
    section: Optional[str]
    domain: Optional[str]
    domain_objective: Optional[str]
    domain_code: Optional[str]
    control_code: str
    
    type_deter: bool
    type_avoid: bool
    type_prevent: bool
    type_detect: bool
    type_react: bool
    type_recover: bool
    
    obj_confidentiality: bool
    obj_integrity: bool
    obj_availability: bool
    
    is_baseline: bool
    is_applicable: bool
    
    control_statement: Optional[str]
    control_summary: Optional[str]
    control_description: Optional[str]
    
    # Framework mappings
    iso27001_2013: Optional[str]
    pci_dss_v31: Optional[str]
    sp_800_53_rev4: Optional[str]
    
    class Config:
        from_attributes = True

class ControlListResponse(BaseModel):
    id: int
    control_code: str
    domain: Optional[str]
    domain_code: Optional[str]
    control_summary: Optional[str]
    control_statement: Optional[str]
    is_baseline: bool
    is_applicable: bool
    
    class Config:
        from_attributes = True

class DomainResponse(BaseModel):
    domain_code: str
    domain: str
    domain_objective: Optional[str]
    section: Optional[str]
    control_count: int
    baseline_count: int

# ============== BIA & Asset Schemas ==============
class OrganizationSettingsBase(BaseModel):
    weight_reputation: int = Field(3, ge=1, le=4)
    weight_external: int = Field(3, ge=1, le=4)
    weight_internal: int = Field(2, ge=1, le=4)
    weight_legal: int = Field(4, ge=1, le=4)
    weight_economic: int = Field(2, ge=1, le=4)

class OrganizationSettingsUpdate(OrganizationSettingsBase):
    pass

class OrganizationSettingsResponse(OrganizationSettingsBase):
    id: str
    organization_id: str
    updated_at: datetime
    
    class Config:
        from_attributes = True

class InformationAssetBase(BaseModel):
    name: str
    type: str
    description: Optional[str] = None
    c_rating: int = Field(0, ge=0, le=4)
    i_rating: int = Field(0, ge=0, le=3)
    a_rating: int = Field(0, ge=0, le=3)

class InformationAssetCreate(InformationAssetBase):
    process_id: str

class InformationAssetUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    description: Optional[str] = None
    c_rating: Optional[int] = Field(None, ge=0, le=4)
    i_rating: Optional[int] = Field(None, ge=0, le=3)
    a_rating: Optional[int] = Field(None, ge=0, le=3)

class InformationAssetResponse(InformationAssetBase):
    id: str
    organization_id: str
    process_id: str
    security_level: Optional[str]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class BIAProcessBase(BaseModel):
    name: str
    description: Optional[str] = None
    owner: Optional[str] = None
    impact_reputation: int = Field(0, ge=0, le=4)
    impact_external: int = Field(0, ge=0, le=4)
    impact_internal: int = Field(0, ge=0, le=4)
    impact_legal: int = Field(0, ge=0, le=4)
    impact_economic: int = Field(0, ge=0, le=4)

class BIAProcessCreate(BIAProcessBase):
    pass

class BIAProcessUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None
    owner: Optional[str] = None
    impact_reputation: Optional[int] = Field(None, ge=0, le=4)
    impact_external: Optional[int] = Field(None, ge=0, le=4)
    impact_internal: Optional[int] = Field(None, ge=0, le=4)
    impact_legal: Optional[int] = Field(None, ge=0, le=4)
    impact_economic: Optional[int] = Field(None, ge=0, le=4)

class BIAProcessResponse(BIAProcessBase):
    id: str
    organization_id: str
    criticality_score: int
    created_at: datetime
    updated_at: datetime
    assets: List[InformationAssetResponse] = []
    
    class Config:
        from_attributes = True

# ============== Evaluation Schemas ==============
class EvaluationUpdate(BaseModel):
    status: EvaluationStatusEnum
    feedback: Optional[str] = None
    is_applicable: Optional[bool] = None

class EvaluationResponse(BaseModel):
    id: str
    organization_id: str
    control_id: int
    status: str
    is_applicable: Optional[bool]
    feedback: Optional[str]
    auditor_id: Optional[str]
    evaluated_at: Optional[datetime]
    created_at: datetime
    updated_at: datetime
    
    class Config:
        from_attributes = True

class EvaluationWithControlResponse(BaseModel):
    evaluation: Optional[EvaluationResponse]
    control: ControlListResponse
    evidence_count: int = 0
    comment_count: int = 0

# ============== Evidence Schemas ==============
class EvidenceResponse(BaseModel):
    id: str
    file_name: str
    file_type: Optional[str]
    file_size: Optional[int]
    uploaded_by: Optional[str]
    uploaded_at: datetime
    
    class Config:
        from_attributes = True

# ============== Comment Schemas ==============
class CommentCreate(BaseModel):
    content: str

class CommentResponse(BaseModel):
    id: str
    content: str
    user_id: str
    user_name: Optional[str] = None
    user_role: Optional[str] = None
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============== Change History Schemas ==============
class ChangeHistoryResponse(BaseModel):
    id: str
    entity_type: str
    entity_id: str
    action: str
    changes: Optional[str]
    user_id: Optional[str]
    user_name: Optional[str]
    created_at: datetime
    
    class Config:
        from_attributes = True

# ============== Dashboard Schemas ==============
class DomainScoreResponse(BaseModel):
    domain_code: str
    domain: str
    domain_objective: Optional[str] = None
    total_controls: int
    baseline_controls: int
    applicable_controls: int
    fully_applied: int
    partially_applied: int
    low_applied: int = 0  # NEW
    not_applied: int
    not_evaluated: int
    score: float
    baseline_fully_applied: int = 0
    baseline_partially_applied: int = 0 # NEW
    baseline_low_applied: int = 0       # NEW
    additional_applicable: int = 0
    additional_control_target: int = 0 
    additional_fully_applied: int = 0
    additional_partially_applied: int = 0 # NEW
    additional_low_applied: int = 0       # NEW
    status: str  # green, amber, red

class DashboardOverviewResponse(BaseModel):
    overall_score: float
    baseline_score: float
    total_controls: int
    baseline_controls: int
    applicable_controls: int
    evaluated_controls: int
    fully_applied: int
    partially_applied: int
    low_applied: int = 0  # NEW
    not_applied: int
    domain_scores: List[DomainScoreResponse]
    critical_domains: List[dict] = []  # domains with score < 50%
    critical_domains_count: int = 0
    bia_level: Optional[str] = "Low"
    bia_target: Optional[str] = "Baseline Controls"
    target_score: Optional[float] = 0.0
    baseline_fully_applied: int = 0
    baseline_partially_applied: int = 0
    baseline_low_applied: int = 0
    additional_applicable_controls: int = 0
    additional_controls_required: int = 0
    additional_fully_applied: int = 0
    additional_partially_applied: int = 0
    additional_low_applied: int = 0
    # Evidence Coverage
    controls_with_evidence: int = 0
    evidence_coverage_percent: float = 0.0
    is_bia_assessed: bool = False

class PublicStatsResponse(BaseModel):
    total_organizations: int
    organizations_with_full_baseline: int
    organizations_with_additional_controls: int
    total_evaluations: int
    platform_evidence_coverage: float
    average_compliance_score: float
    domain_average_scores: List[dict]

# Update forward references
TokenResponse.model_rebuild()
