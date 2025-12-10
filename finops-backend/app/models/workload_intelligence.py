"""
Models for workload intelligence - tracks business context that informs
commitment decisions.
"""
from datetime import datetime, date
from sqlalchemy import (
    Column, Integer, String, Float, Date, DateTime, 
    Boolean, ForeignKey, Text, Enum, JSON
)
from sqlalchemy.orm import relationship
from app.models.cost_history import Base
import enum


class WorkloadStatus(enum.Enum):
    ACTIVE = "active"
    GROWTH = "growth"
    STABLE = "stable"
    DECLINING = "declining"
    SUNSET = "sunset"
    MIGRATING = "migrating"
    EVALUATING = "evaluating"


class CommitmentAction(enum.Enum):
    APPROVE = "approve"
    MODIFY = "modify"
    HOLD = "hold"
    BLOCK = "block"


class EvaluationStatus(enum.Enum):
    PLANNED = "planned"
    EVALUATING = "evaluating"
    POC = "poc"
    PILOT = "pilot"
    APPROVED = "approved"
    REJECTED = "rejected"
    DEFERRED = "deferred"


# ============ WORKLOAD REGISTRY ============

class Workload(Base):
    """
    A logical grouping of Azure resources representing a business application.
    """
    __tablename__ = "workloads"
    
    id = Column(Integer, primary_key=True)
    
    # Identity
    name = Column(String(255), nullable=False, unique=True)
    description = Column(Text)
    owner_name = Column(String(255))
    owner_email = Column(String(255))
    cost_center = Column(String(50))
    department = Column(String(100))
    
    # Azure Resource Matching (how we link Azure resources to this workload)
    resource_group_patterns = Column(JSON)     # ["rg-analytics-*", "rg-dwh-*"]
    subscription_ids = Column(JSON)            # ["sub-id-1", "sub-id-2"]
    tag_filters = Column(JSON)                 # {"app": "synapse", "env": "prod"}
    
    # Business Status
    status = Column(Enum(WorkloadStatus), default=WorkloadStatus.ACTIVE)
    criticality = Column(String(20), default="standard")  # mission-critical, business-critical, standard
    
    # Lifecycle
    expected_end_date = Column(Date, nullable=True)
    migration_target = Column(String(255), nullable=True)
    migration_confidence_pct = Column(Float, default=0)
    
    # Commitment Guidance (manual settings)
    max_commitment_term_months = Column(Integer, default=36)
    commitment_notes = Column(Text)
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255))
    
    # Relationships
    evaluations = relationship("TechnologyEvaluation", back_populates="workload")
    context_notes = relationship("WorkloadContext", back_populates="workload")
    documents = relationship("WorkloadDocument", back_populates="workload")


class WorkloadContext(Base):
    """
    Free-text context notes added by users to inform AI analysis.
    """
    __tablename__ = "workload_context"
    
    id = Column(Integer, primary_key=True)
    workload_id = Column(Integer, ForeignKey('workloads.id'), nullable=False)
    
    content = Column(Text, nullable=False)
    added_by = Column(String(255))
    added_at = Column(DateTime, default=datetime.utcnow)
    
    workload = relationship("Workload", back_populates="context_notes")


class WorkloadDocument(Base):
    """
    Documents uploaded to provide context (Word docs, PDFs, Excel).
    """
    __tablename__ = "workload_documents"
    
    id = Column(Integer, primary_key=True)
    workload_id = Column(Integer, ForeignKey('workloads.id'), nullable=False)
    
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50))  # docx, pdf, xlsx
    file_size_bytes = Column(Integer)
    
    # Extracted content for AI
    extracted_text = Column(Text)
    extraction_status = Column(String(50), default="pending")  # pending, completed, failed
    
    uploaded_by = Column(String(255))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    workload = relationship("Workload", back_populates="documents")


# ============ TECHNOLOGY EVALUATIONS ============

class TechnologyEvaluation(Base):
    """
    Tracks SaaS/vendor evaluations that might replace Azure workloads.
    """
    __tablename__ = "technology_evaluations"
    
    id = Column(Integer, primary_key=True)
    
    # What's being evaluated
    name = Column(String(255), nullable=False)  # "Snowflake Enterprise"
    vendor = Column(String(255))                # "Snowflake Inc."
    evaluation_type = Column(String(50))        # saas_replacement, platform_migration, vendor_switch
    
    # What it affects
    workload_id = Column(Integer, ForeignKey('workloads.id'), nullable=False)
    affected_azure_services = Column(JSON)      # ["Synapse Analytics", "Data Factory"]
    estimated_monthly_spend_affected = Column(Float)
    
    # Timeline
    started_date = Column(Date)
    decision_date = Column(Date)                # When decision will be made
    implementation_date = Column(Date, nullable=True)
    full_migration_date = Column(Date, nullable=True)
    
    # Current Status
    status = Column(Enum(EvaluationStatus), default=EvaluationStatus.EVALUATING)
    adoption_probability_pct = Column(Float, default=50)
    
    # Decision (once made)
    decision = Column(String(50), nullable=True)  # go, no_go, deferred
    decision_date_actual = Column(Date, nullable=True)
    decision_notes = Column(Text)
    decision_made_by = Column(String(255))
    
    # POC/Pilot Details
    poc_success_score = Column(Float, nullable=True)  # 0-100
    poc_notes = Column(Text)
    executive_sponsor = Column(String(255))
    
    # Commitment Impact
    hold_commitments = Column(Boolean, default=True)
    hold_expires = Column(Date)  # Auto-release hold if no decision by this date
    
    # Metadata
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    created_by = Column(String(255))
    
    # Relationships
    workload = relationship("Workload", back_populates="evaluations")
    documents = relationship("EvaluationDocument", back_populates="evaluation")
    agent_analyses = relationship("AgentAnalysis", back_populates="evaluation")


class EvaluationDocument(Base):
    """
    Documents related to an evaluation (POC results, vendor proposals, etc).
    """
    __tablename__ = "evaluation_documents"
    
    id = Column(Integer, primary_key=True)
    evaluation_id = Column(Integer, ForeignKey('technology_evaluations.id'), nullable=False)
    
    filename = Column(String(255), nullable=False)
    original_filename = Column(String(255), nullable=False)
    file_path = Column(String(500), nullable=False)
    file_type = Column(String(50))
    file_size_bytes = Column(Integer)
    
    document_type = Column(String(100))  # poc_results, vendor_proposal, tco_analysis, security_review
    extracted_text = Column(Text)
    
    uploaded_by = Column(String(255))
    uploaded_at = Column(DateTime, default=datetime.utcnow)
    
    evaluation = relationship("TechnologyEvaluation", back_populates="documents")


# ============ AI AGENT ANALYSIS ============

class AgentAnalysis(Base):
    """
    Stores AI agent analysis results for evaluations/recommendations.
    """
    __tablename__ = "agent_analyses"
    
    id = Column(Integer, primary_key=True)
    
    # What was analyzed
    evaluation_id = Column(Integer, ForeignKey('technology_evaluations.id'), nullable=True)
    recommendation_id = Column(String(500), nullable=True)  # Azure recommendation ID
    
    # Agent info
    agent_type = Column(String(100))  # saas_evaluator, commitment_advisor, risk_scorer
    agent_version = Column(String(50))
    
    # Analysis Results
    risk_score = Column(Float)  # 0-10
    confidence_score = Column(Float)  # 0-100
    recommended_action = Column(Enum(CommitmentAction))
    
    # Detailed output
    analysis_summary = Column(Text)
    factors_analyzed = Column(JSON)  # [{"factor": "POC success", "score": 8.2, "weight": 0.3}, ...]
    reasoning = Column(Text)
    
    # Input context used
    input_documents = Column(JSON)  # Document IDs used
    input_context = Column(Text)    # Free text context used
    
    # Metadata
    analyzed_at = Column(DateTime, default=datetime.utcnow)
    analysis_duration_ms = Column(Integer)
    tokens_used = Column(Integer)
    model_used = Column(String(100))
    
    evaluation = relationship("TechnologyEvaluation", back_populates="agent_analyses")


# ============ RECOMMENDATION ENRICHMENT ============

class RecommendationIntelligence(Base):
    """
    Cached intelligence for each Azure recommendation.
    Links recommendations to workloads and stores AI analysis.
    """
    __tablename__ = "recommendation_intelligence"
    
    id = Column(Integer, primary_key=True)
    
    # Azure Recommendation Reference
    azure_recommendation_id = Column(String(500), unique=True)
    recommendation_type = Column(String(50))  # RI, SP, Advisor
    resource_id = Column(String(500))
    sku = Column(String(100))
    region = Column(String(50))
    
    # Matched Workload
    workload_id = Column(Integer, ForeignKey('workloads.id'), nullable=True)
    
    # Intelligence Result
    action = Column(Enum(CommitmentAction), default=CommitmentAction.APPROVE)
    action_reason = Column(Text)
    
    # Risk Assessment
    risk_score = Column(Float)  # 0-10
    risk_factors = Column(JSON)
    
    # Modifications (if action = MODIFY)
    original_term_months = Column(Integer)
    recommended_term_months = Column(Integer)
    modification_reason = Column(Text)
    
    # Related Evaluation (if any)
    blocking_evaluation_id = Column(Integer, ForeignKey('technology_evaluations.id'), nullable=True)
    
    # Manual Override
    override_action = Column(Enum(CommitmentAction), nullable=True)
    override_reason = Column(Text)
    override_by = Column(String(255))
    override_at = Column(DateTime)
    override_expires = Column(Date)
    
    # Metadata
    last_analyzed = Column(DateTime, default=datetime.utcnow)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    workload = relationship("Workload")
    blocking_evaluation = relationship("TechnologyEvaluation")
