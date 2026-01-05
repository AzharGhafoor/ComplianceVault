from sqlalchemy import Column, String, Text, Boolean, Integer, DateTime, ForeignKey, Enum as SQLEnum
from sqlalchemy.orm import relationship
from datetime import datetime
import uuid
import enum

from .database import Base

def generate_uuid():
    return str(uuid.uuid4())

class UserRole(str, enum.Enum):
    ADMIN = "admin"
    AUDITOR = "auditor"
    COMMENTER = "commenter"
    VIEWER = "viewer"

class EvaluationStatus(str, enum.Enum):
    NOT_EVALUATED = "not_evaluated"
    FULLY_APPLIED = "fully_applied"
    PARTIALLY_APPLIED = "partially_applied"
    LOW_APPLIED = "low_applied"  # NEW: 25% credit
    NOT_APPLIED = "not_applied"

# ============== Organization Model ==============
class Organization(Base):
    __tablename__ = "organizations"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    name = Column(String(255), nullable=False)
    description = Column(Text)
    country = Column(String(100), default="Qatar")
    sector = Column(String(100))
    size = Column(String(50))  # small, medium, large, enterprise
    logo_url = Column(String(500))
    contact_email = Column(String(255))
    contact_phone = Column(String(50))
    domain = Column(String(255))
    status = Column(String(20), default="active")
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    users = relationship("User", back_populates="organization")
    evaluations = relationship("Evaluation", back_populates="organization")
    change_history = relationship("ChangeHistory", back_populates="organization")
    settings = relationship("OrganizationSettings", uselist=False, back_populates="organization", cascade="all, delete-orphan")

# ============== User Model ==============
class User(Base):
    __tablename__ = "users"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    first_name = Column(String(100))
    last_name = Column(String(100))
    organization_id = Column(String(36), ForeignKey("organizations.id"))
    role = Column(String(20), default=UserRole.VIEWER.value)
    status = Column(String(20), default="active")
    reset_token = Column(String(255))
    reset_token_expires = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="users")
    evaluations = relationship("Evaluation", back_populates="auditor")
    comments = relationship("Comment", back_populates="user")
    uploaded_evidence = relationship("Evidence", back_populates="uploader")
    
    @property
    def full_name(self):
        return f"{self.first_name or ''} {self.last_name or ''}".strip() or self.email

# ============== Control Model ==============
class Control(Base):
    __tablename__ = "controls"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    nia_version = Column(String(10))
    section = Column(String(255))
    domain = Column(String(255))
    domain_objective = Column(Text)
    domain_code = Column(String(10), index=True)
    control_code = Column(String(20), unique=True, index=True)
    
    # Types
    type_deter = Column(Boolean, default=False)
    type_avoid = Column(Boolean, default=False)
    type_prevent = Column(Boolean, default=False)
    type_detect = Column(Boolean, default=False)
    type_react = Column(Boolean, default=False)
    type_recover = Column(Boolean, default=False)
    
    # Objectives
    obj_confidentiality = Column(Boolean, default=False)
    obj_integrity = Column(Boolean, default=False)
    obj_availability = Column(Boolean, default=False)
    
    # Baseline/Applicable
    is_baseline = Column(Boolean, default=False)
    is_applicable = Column(Boolean, default=False)
    
    # Control content
    control_statement = Column(Text)  # Control GM
    control_summary = Column(Text)
    control_description = Column(Text)  # Control Description GM
    
    # Framework mappings
    iso27001_2013 = Column(Text)
    pci_dss_v31 = Column(Text)
    sp_800_53_rev4 = Column(Text)
    qscf_process_phases = Column(Text)
    qscf_activities_controls = Column(Text)
    qscf_niap2_controls = Column(Text)
    qscf_nics_standard_v30 = Column(Text)
    qscf_csc = Column(Text)
    qscf_isa_62443_2_1_2009 = Column(Text)
    qscf_isa_62443_3_3_2013 = Column(Text)
    qscf_iso_iec_27001_2013 = Column(Text)
    qscf_nist_sp_800_53_rev4 = Column(Text)
    qscf_pci_dss_32 = Column(Text)
    qscf_hipaa = Column(Text)
    qscf_ccm_v301 = Column(Text)
    qscf_gdpr = Column(Text)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    evaluations = relationship("Evaluation", back_populates="control")

# ============== Evaluation Model ==============
class Evaluation(Base):
    __tablename__ = "evaluations"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    control_id = Column(Integer, ForeignKey("controls.id"), nullable=False, index=True)
    
    status = Column(String(30), default=EvaluationStatus.NOT_EVALUATED.value)
    is_applicable = Column(Boolean, default=None)  # Organization-specific override
    feedback = Column(Text)
    
    auditor_id = Column(String(36), ForeignKey("users.id"))
    evaluated_at = Column(DateTime)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="evaluations")
    control = relationship("Control", back_populates="evaluations")
    auditor = relationship("User", back_populates="evaluations")
    evidence = relationship("Evidence", back_populates="evaluation", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="evaluation", cascade="all, delete-orphan")

# ============== Evidence Model ==============
class Evidence(Base):
    __tablename__ = "evidence"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    evaluation_id = Column(String(36), ForeignKey("evaluations.id"), nullable=False)
    
    file_name = Column(String(255))
    file_path = Column(String(500))
    file_type = Column(String(100))
    file_size = Column(Integer)
    
    uploaded_by = Column(String(36), ForeignKey("users.id"))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    evaluation = relationship("Evaluation", back_populates="evidence")
    uploader = relationship("User", back_populates="uploaded_evidence")

# ============== Comment Model ==============
class Comment(Base):
    __tablename__ = "comments"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    evaluation_id = Column(String(36), ForeignKey("evaluations.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    
    content = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    evaluation = relationship("Evaluation", back_populates="comments")
    user = relationship("User", back_populates="comments")

# ============== Change History Model ==============
class ChangeHistory(Base):
    __tablename__ = "change_history"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    
    entity_type = Column(String(50))  # evaluation, evidence, comment, user
    entity_id = Column(String(36))
    action = Column(String(50))  # create, update, delete
    changes = Column(Text)  # JSON string of changes
    
    user_id = Column(String(36), ForeignKey("users.id"))
    user_name = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    organization = relationship("Organization", back_populates="change_history")
# ============== Security Models ==============
class Session(Base):
    '''Secure session management'''
    __tablename__ = 'sessions'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    user_id = Column(String(36), ForeignKey('users.id'), nullable=False, index=True)
    token_jti = Column(String(100), unique=True, nullable=False, index=True)
    refresh_token_jti = Column(String(100), unique=True, index=True)
    ip_address = Column(String(45))
    user_agent = Column(Text)
    device_fingerprint = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    last_activity = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, index=True)
    expires_at = Column(DateTime, nullable=False, index=True)
    is_active = Column(Boolean, default=True, index=True)
    is_revoked = Column(Boolean, default=False, index=True)
    revoked_at = Column(DateTime)
    revoke_reason = Column(String(255))
    user = relationship('User')
    
    def is_valid(self):
        return self.is_active and not self.is_revoked and datetime.utcnow() <= self.expires_at

class SecurityLog(Base):
    '''Security event audit log'''
    __tablename__ = 'security_logs'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    event_type = Column(String(50), nullable=False, index=True)
    user_id = Column(String(36), ForeignKey('users.id'), index=True)
    email = Column(String(255), index=True)
    ip_address = Column(String(45), index=True)
    user_agent = Column(Text)
    request_id = Column(String(100), index=True)
    success = Column(Boolean, index=True)
    failure_reason = Column(Text)
    event_metadata = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    user = relationship('User')

class RateLimitTracker(Base):
    '''Rate limiting tracker'''
    __tablename__ = 'rate_limit_tracker'
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    
# ============== BIA & Asset Models ==============
class OrganizationSettings(Base):
    __tablename__ = "organization_settings"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id"), unique=True, index=True)
    
    # Impact Weights (1-4)
    weight_reputation = Column(Integer, default=3)
    weight_external = Column(Integer, default=3)
    weight_internal = Column(Integer, default=2)
    weight_legal = Column(Integer, default=4)
    weight_economic = Column(Integer, default=2)
    
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    organization = relationship("Organization", back_populates="settings")

class BIAProcess(Base):
    __tablename__ = "bia_processes"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    description = Column(Text)
    owner = Column(String(255))
    
    # Impact Ratings (0-4)
    impact_reputation = Column(Integer, default=0)
    impact_external = Column(Integer, default=0)
    impact_internal = Column(Integer, default=0)
    impact_legal = Column(Integer, default=0)
    impact_economic = Column(Integer, default=0)
    
    criticality_score = Column(Integer, default=0) # 0-100
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    organization = relationship("Organization")
    assets = relationship("InformationAsset", back_populates="process", cascade="all, delete-orphan")

class InformationAsset(Base):
    __tablename__ = "information_assets"
    
    id = Column(String(36), primary_key=True, default=generate_uuid)
    organization_id = Column(String(36), ForeignKey("organizations.id"), nullable=False, index=True)
    process_id = Column(String(36), ForeignKey("bia_processes.id"), nullable=False, index=True)
    
    name = Column(String(255), nullable=False)
    type = Column(String(100)) # Hardware, Software, Data, People, etc.
    description = Column(Text)
    
    # Security Ratings (NIA Policy v2.0)
    # C: 0-3 (C0-Public, C1-Internal, C2-Limited Access, C3-Restricted)
    # I: 0-3 (I0-Not Important, I1-Identifiable, I2-Checked, I3-Provable)
    # A: 0-3 (A0-Not Important, A1-90%, A2-99%, A3-99.9%)
    c_rating = Column(Integer, default=0)
    i_rating = Column(Integer, default=0)
    a_rating = Column(Integer, default=0)
    
    security_level = Column(String(10)) # Low, Medium, High
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    organization = relationship("Organization")
    process = relationship("BIAProcess", back_populates="assets")
