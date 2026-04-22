from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON, Boolean, Text
from sqlalchemy.orm import relationship
import datetime
from .db import Base
from pydantic import BaseModel, EmailStr, ConfigDict
from typing import Optional, List


# --- Global Regulatory Mapping ORM Model ---
class RegulatoryMappingORM(Base):
    __tablename__ = "regulatory_mappings"
    id = Column(Integer, primary_key=True, index=True)
    jurisdiction = Column(String)  # e.g., 'EU', 'US', 'CN', etc.
    regulation = Column(String)    # e.g., 'GDPR', 'PIPL', 'DPDPA', etc.
    control = Column(String)       # e.g., 'Data Privacy', 'Risk Assessment', etc.
    last_updated = Column(DateTime, default=datetime.datetime.utcnow)
    notes = Column(String)


# --- Certification-Ready Processes ORM Model ---
class EvidenceRecordORM(Base):
    __tablename__ = "evidence_records"
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=True)
    checklist_item = Column(String)  # e.g., ISO 42001, EU AIA, etc.
    evidence_type = Column(String)  # e.g., document, screenshot, log
    file_path = Column(String)
    description = Column(String)
    uploaded_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    model = relationship("ModelORM")
    user = relationship("UserORM")

# --- Human Oversight & Accountability ORM Model ---
class OversightLogORM(Base):
    __tablename__ = "oversight_logs"
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    action = Column(String)  # e.g., 'signoff', 'override', 'review', etc.
    comment = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    model = relationship("ModelORM")
    user = relationship("UserORM")

# --- Transparency & Impact Assessment ORM Model ---
class ImpactAssessmentORM(Base):
    __tablename__ = "impact_assessments"
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    assessment_type = Column(String)  # e.g., 'AI RMF', 'algorithmic', etc.
    summary = Column(String)
    details = Column(JSON)
    exported_report_path = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    model = relationship("ModelORM")
# --- Security & Resilience ORM Model ---

# --- Security & Resilience ORM Model ---
class SecurityEventORM(Base):
    __tablename__ = "security_events"
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=True)
    event_type = Column(String)  # e.g., 'incident', 'vuln_scan', 'policy_violation'
    event_details = Column(JSON)
    detected_at = Column(DateTime, default=datetime.datetime.utcnow)
    severity = Column(String)  # e.g., 'low', 'medium', 'high', 'critical'
    resolved = Column(String, default="no")
    model = relationship("ModelORM")

# --- Security & Threat Detection ORM Models ---

class ThreatLogORM(Base):
    __tablename__ = "threat_logs"
    id = Column(Integer, primary_key=True, index=True)
    threat_type = Column(String)
    source_ip = Column(String)
    target_ip = Column(String)
    severity = Column(String)
    description = Column(JSON)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)

class SecurityAssessmentORM(Base):
    __tablename__ = "security_assessments"
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    assessment_type = Column(String)  # e.g., vulnerability, penetration_test
    findings = Column(JSON)
    risk_level = Column(String)  # e.g., low/medium/high/critical
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    model = relationship("ModelORM")

# --- Ensure all required SQLAlchemy imports are present for new models ---
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
import datetime
from .db import Base

# --- Automated Risk & Metadata Models ---
class ModelMetadataORM(Base):
    __tablename__ = "model_metadata"
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    use_case = Column(String)
    data_sensitivity = Column(String)  # e.g., 'low', 'medium', 'high'
    owner = Column(String)
    region = Column(String)
    additional_info = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    model = relationship("ModelORM")

class UsageLogORM(Base):
    __tablename__ = "usage_logs"
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    event_type = Column(String)  # e.g., 'inference', 'drift_detected', etc.
    event_details = Column(JSON)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    model = relationship("ModelORM")

class RiskAssessmentORM(Base):
    __tablename__ = "risk_assessments"
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=False)
    risk_level = Column(String)  # e.g., 'low', 'medium', 'high', 'unknown'
    score = Column(Integer)
    reasons = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    model = relationship("ModelORM")



# Adversarial Attack Results ORM
from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, JSON
from sqlalchemy.orm import relationship
import datetime
from .db import Base
from pydantic import BaseModel, EmailStr
from typing import Optional, List

class AttackResultORM(Base):
    __tablename__ = "attack_results"
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"))
    model_id = Column(Integer, ForeignKey("models.id"))
    attack_type = Column(String)
    metrics = Column(JSON)
    result_path = Column(String)
    timestamp = Column(DateTime, default=datetime.datetime.utcnow)
    user = relationship("UserORM")
    model = relationship("ModelORM")

class User(BaseModel):
    """Pydantic User model for API responses."""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    email: EmailStr
    full_name: Optional[str]
    roles: List[str] = []
    is_active: bool = True

from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey, JSON, Text
from sqlalchemy.orm import relationship
from .db import Base
import datetime

class UserORM(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    full_name = Column(String)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="operator")  # single role
    roles = Column(String)  # comma-separated roles (for backward compatibility)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    last_login = Column(DateTime, nullable=True)
    
    # Relationships
    audit_logs = relationship("AuditLogORM", back_populates="user")

class ModelORM(Base):
    __tablename__ = "models"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    tags = Column(String)
    framework = Column(String)
    version = Column(String)
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    mlflow_id = Column(String)
    file_path = Column(String)
    user = relationship("UserORM")
    
    # Relationships
    audit_logs = relationship("AuditLogORM", back_populates="model")

# Threat Detection ORM Models
class ThreatAlertORM(Base):
    __tablename__ = "threat_alerts"
    id = Column(Integer, primary_key=True, index=True)
    alert_id = Column(String, unique=True, index=True, nullable=False)
    title = Column(String, nullable=False)
    description = Column(Text)
    severity = Column(String, nullable=False)  # critical, high, medium, low
    threat_type = Column(String, nullable=False)
    source = Column(String)
    status = Column(String, default="active")  # active, investigating, resolved, false_positive
    confidence_score = Column(String)  # JSON string for float value
    affected_systems = Column(JSON)
    indicators = Column(JSON)
    mitigations = Column(JSON)
    source_ip = Column(String)
    destination_ip = Column(String)
    attack_vector = Column(String)
    mitre_attack_id = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.datetime.utcnow, onupdate=datetime.datetime.utcnow)
    resolved_at = Column(DateTime, nullable=True)
    resolved_by = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    # Relationships
    resolver = relationship("UserORM", foreign_keys=[resolved_by])

class DatasetORM(Base):
    __tablename__ = "datasets"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(Text)
    uploaded_by = Column(Integer, ForeignKey("users.id"))
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    file_path = Column(String)
    user = relationship("UserORM")

class AuditLogORM(Base):
    """Enhanced audit log model with comprehensive tracking."""
    __tablename__ = "audit_logs"
    
    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True)
    action_type = Column(String(100), nullable=False, index=True)
    resource = Column(String(200), nullable=True, index=True)
    details = Column(JSON, nullable=True)
    ip_address = Column(String(45), nullable=True)  # IPv6 compatible
    user_agent = Column(String(500), nullable=True)
    success = Column(Boolean, default=True, nullable=False, index=True)
    
    # Timestamps
    timestamp = Column(DateTime, default=datetime.datetime.utcnow, nullable=False, index=True)
    created_at = Column(DateTime, default=datetime.datetime.utcnow, nullable=False)
    
    # Legacy fields for backward compatibility
    model_id = Column(Integer, ForeignKey("models.id"), nullable=True)
    result_path = Column(String, nullable=True)
    
    # Relationships
    user = relationship("UserORM", back_populates="audit_logs")
    model = relationship("ModelORM", back_populates="audit_logs")

class ModelExplainabilityORM(Base):
    __tablename__ = "model_explainability"
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"))
    shap_values = Column(JSON)
    lime_explanation = Column(JSON)
    graph_path = Column(String)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    model = relationship("ModelORM")

class ThreatAnalysisORM(Base):
    __tablename__ = "threat_analysis"
    id = Column(Integer, primary_key=True, index=True)
    threat_id = Column(String)
    analysis_type = Column(String)
    severity_score = Column(Integer)
    analysis_results = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)

class AttackPatternORM(Base):
    __tablename__ = "attack_patterns"
    id = Column(Integer, primary_key=True, index=True)
    pattern_name = Column(String)
    mitre_id = Column(String)
    description = Column(String)
    detection_rules = Column(JSON)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    __tablename__ = "prompt_risks"
    id = Column(Integer, primary_key=True, index=True)
    model_id = Column(Integer, ForeignKey("models.id"), nullable=True)
    prompt = Column(Text)
    score = Column(String)
    reasoning = Column(Text)
    created_at = Column(DateTime, default=datetime.datetime.utcnow)
    model = relationship("ModelORM")
