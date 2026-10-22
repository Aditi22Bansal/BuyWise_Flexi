from sqlalchemy import (
    Column, Integer, String, Float, DateTime, Text, Boolean, ForeignKey, Enum
)
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func
import enum

Base = declarative_base()


class ProcurementStatus(str, enum.Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    AWAITING_APPROVAL = "awaiting_approval"
    COMPLETED = "completed"
    REJECTED = "rejected"
    FAILED = "failed"


class AgentStatus(str, enum.Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class ApprovalStatus(str, enum.Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    CHANGES_REQUESTED = "changes_requested"


class ProcurementRequest(Base):
    __tablename__ = "procurement_requests"

    id = Column(String, primary_key=True, index=True)
    product_name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    quantity = Column(Integer, nullable=False)
    max_budget = Column(Float, nullable=False)
    currency = Column(String, default="USD")
    required_features = Column(Text, nullable=True)  # JSON array
    warranty_months = Column(Integer, default=12)
    delivery_needed_by = Column(String, nullable=True)
    preferred_vendors = Column(Text, nullable=True)  # JSON array
    status = Column(Enum(ProcurementStatus), default=ProcurementStatus.PENDING)
    current_stage = Column(String, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)

    # Relationships
    products = relationship("ProductRecord", back_populates="request", cascade="all, delete-orphan")
    vendors = relationship("VendorRecord", back_populates="request", cascade="all, delete-orphan")
    quotes = relationship("QuoteRecord", back_populates="request", cascade="all, delete-orphan")
    evaluations = relationship("EvaluationRecord", back_populates="request", cascade="all, delete-orphan")
    negotiation_results = relationship("NegotiationRecord", back_populates="request", cascade="all, delete-orphan")
    decision = relationship("DecisionRecord", back_populates="request", uselist=False, cascade="all, delete-orphan")
    approval = relationship("ApprovalRecord", back_populates="request", uselist=False, cascade="all, delete-orphan")
    agent_executions = relationship("AgentExecution", back_populates="request", cascade="all, delete-orphan")
    audit_logs = relationship("AuditLog", back_populates="request", cascade="all, delete-orphan")


class ProductRecord(Base):
    __tablename__ = "products"

    id = Column(String, primary_key=True)
    request_id = Column(String, ForeignKey("procurement_requests.id"), nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    description = Column(Text, nullable=True)
    base_price = Column(Float, nullable=False)
    quality_score = Column(Float, nullable=False)
    review_score = Column(Float, nullable=False)
    features = Column(Text, nullable=True)  # JSON array
    warranty_months = Column(Integer, default=12)
    manufacturer = Column(String, nullable=True)
    datasheet_url = Column(String, nullable=True)
    extra_data = Column(Text, nullable=True)  # JSON

    request = relationship("ProcurementRequest", back_populates="products")


class VendorRecord(Base):
    __tablename__ = "vendors"

    id = Column(String, primary_key=True)
    request_id = Column(String, ForeignKey("procurement_requests.id"), nullable=False)
    name = Column(String, nullable=False)
    contact_email = Column(String, nullable=False)
    contact_phone = Column(String, nullable=True)
    portal_url = Column(String, nullable=True)
    reliability_score = Column(Float, nullable=False)
    average_delivery_days = Column(Integer, nullable=False)
    payment_terms = Column(String, nullable=True)
    min_order_quantity = Column(Integer, default=1)
    active = Column(Boolean, default=True)
    extra_data = Column(Text, nullable=True)  # JSON

    request = relationship("ProcurementRequest", back_populates="vendors")


class QuoteRecord(Base):
    __tablename__ = "quotes"

    id = Column(String, primary_key=True)
    request_id = Column(String, ForeignKey("procurement_requests.id"), nullable=False)
    vendor_id = Column(String, ForeignKey("vendors.id"), nullable=False)
    vendor_name = Column(String, nullable=False)
    total_amount = Column(Float, nullable=False)
    status = Column(String, nullable=False)
    valid_until = Column(String, nullable=True)
    terms = Column(String, nullable=True)
    discount_percent = Column(Float, default=0.0)
    negotiation_round = Column(Integer, default=0)
    created_at = Column(String, nullable=True)
    items = Column(Text, nullable=True)  # JSON array
    parent_quote_id = Column(String, nullable=True)
    is_revised = Column(Boolean, default=False)

    request = relationship("ProcurementRequest", back_populates="quotes")
    vendor = relationship("VendorRecord")


class EvaluationRecord(Base):
    __tablename__ = "evaluations"

    id = Column(String, primary_key=True)
    request_id = Column(String, ForeignKey("procurement_requests.id"), nullable=False)
    vendor_id = Column(String, nullable=False)
    vendor_name = Column(String, nullable=False)
    quote_id = Column(String, nullable=False)
    total_score = Column(Float, nullable=False)
    price_score = Column(Float, nullable=False)
    quality_score = Column(Float, nullable=False)
    review_score = Column(Float, nullable=False)
    warranty_score = Column(Float, nullable=False)
    delivery_score = Column(Float, nullable=False)
    reliability_score = Column(Float, nullable=False)
    budget_score = Column(Float, nullable=False)
    total_cost = Column(Float, nullable=False)
    savings_vs_budget = Column(Float, nullable=False)
    details = Column(Text, nullable=True)  # JSON
    reevaluated = Column(Boolean, default=False)

    request = relationship("ProcurementRequest", back_populates="evaluations")


class NegotiationRecord(Base):
    __tablename__ = "negotiations"

    id = Column(String, primary_key=True)
    request_id = Column(String, ForeignKey("procurement_requests.id"), nullable=False)
    vendor_id = Column(String, nullable=False)
    vendor_name = Column(String, nullable=False)
    original_quote_id = Column(String, nullable=False)
    revised_quote_id = Column(String, nullable=True)
    rounds = Column(Integer, nullable=False)
    final_discount_percent = Column(Float, nullable=False)
    final_total_amount = Column(Float, nullable=False)
    savings_achieved = Column(Float, nullable=False)
    agreed_terms = Column(String, nullable=True)
    success = Column(Boolean, nullable=False)
    transcript = Column(Text, nullable=True)  # JSON array

    request = relationship("ProcurementRequest", back_populates="negotiation_results")


class DecisionRecord(Base):
    __tablename__ = "decisions"

    id = Column(String, primary_key=True)
    request_id = Column(String, ForeignKey("procurement_requests.id"), nullable=False)
    recommended_vendor_id = Column(String, nullable=True)
    recommended_vendor_name = Column(String, nullable=True)
    recommended_quote_id = Column(String, nullable=True)
    final_total_amount = Column(Float, nullable=False)
    total_score = Column(Float, nullable=False)
    decision = Column(String, nullable=False)
    reasoning = Column(Text, nullable=False)
    requires_human_approval = Column(Boolean, default=True)
    created_at = Column(String, nullable=True)

    request = relationship("ProcurementRequest", back_populates="decision")


class ApprovalRecord(Base):
    __tablename__ = "approvals"

    id = Column(String, primary_key=True)
    request_id = Column(String, ForeignKey("procurement_requests.id"), nullable=False)
    status = Column(Enum(ApprovalStatus), default=ApprovalStatus.PENDING)
    decision = Column(String, nullable=True)
    reviewer_id = Column(String, nullable=True)
    reviewer_name = Column(String, nullable=True)
    reason = Column(Text, nullable=True)
    decided_at = Column(String, nullable=True)
    created_at = Column(String, nullable=True)

    request = relationship("ProcurementRequest", back_populates="approval")


class AgentExecution(Base):
    __tablename__ = "agent_executions"

    id = Column(String, primary_key=True)
    request_id = Column(String, ForeignKey("procurement_requests.id"), nullable=False)
    agent_name = Column(String, nullable=False)
    status = Column(Enum(AgentStatus), default=AgentStatus.PENDING)
    started_at = Column(String, nullable=True)
    completed_at = Column(String, nullable=True)
    output_summary = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    execution_order = Column(Integer, nullable=False)

    request = relationship("ProcurementRequest", back_populates="agent_executions")


class AuditLog(Base):
    __tablename__ = "audit_logs"

    id = Column(String, primary_key=True)
    request_id = Column(String, ForeignKey("procurement_requests.id"), nullable=True)
    event_type = Column(String, nullable=False)
    event_description = Column(Text, nullable=False)
    actor = Column(String, nullable=True)
    extra_data = Column(Text, nullable=True)  # JSON
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    request = relationship("ProcurementRequest", back_populates="audit_logs")


class EvaluationWeight(Base):
    __tablename__ = "evaluation_weights"

    id = Column(Integer, primary_key=True, autoincrement=True)
    criterion = Column(String, nullable=False, unique=True)
    weight = Column(Float, nullable=False)
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    updated_by = Column(String, nullable=True)