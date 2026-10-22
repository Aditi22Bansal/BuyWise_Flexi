from pydantic import BaseModel, Field, validator
from typing import List, Optional, Dict, Any
from datetime import datetime
from decimal import Decimal


# --- Procurement Request ---

class ProcurementRequestCreate(BaseModel):
    product_name: str = Field(..., min_length=1, max_length=200)
    category: str = Field(..., min_length=1, max_length=100)
    description: Optional[str] = Field(default="", max_length=2000)
    quantity: int = Field(..., ge=1, le=100000)
    max_budget: float = Field(..., gt=0, le=100000000)
    currency: str = Field(default="USD", min_length=3, max_length=3)
    required_features: List[str] = Field(default_factory=list)
    warranty_months: int = Field(default=12, ge=1, le=120)
    delivery_needed_by: Optional[str] = None
    preferred_vendors: List[str] = Field(default_factory=list)

    @validator("currency")
    def uppercase_currency(cls, v):
        return v.upper()


class ProcurementRequestResponse(BaseModel):
    id: str
    product_name: str
    category: str
    description: Optional[str]
    quantity: int
    max_budget: float
    currency: str
    required_features: List[str]
    warranty_months: int
    delivery_needed_by: Optional[str]
    preferred_vendors: List[str]
    status: str
    current_stage: Optional[str]
    created_at: datetime
    updated_at: Optional[datetime]
    completed_at: Optional[datetime]

    @validator("required_features", pre=True)
    def parse_required_features(cls, v):
        if isinstance(v, str):
            import json as _json
            try:
                return _json.loads(v)
            except Exception:
                return []
        return v or []

    @validator("preferred_vendors", pre=True)
    def parse_preferred_vendors(cls, v):
        if isinstance(v, str):
            import json as _json
            try:
                return _json.loads(v)
            except Exception:
                return []
        return v or []

    class Config:
        from_attributes = True


# --- Product ---

class ProductResponse(BaseModel):
    id: str
    name: str
    category: str
    description: Optional[str]
    base_price: float
    quality_score: float
    review_score: float
    features: List[str]
    warranty_months: int
    manufacturer: Optional[str]
    datasheet_url: Optional[str]

    @validator("features", pre=True)
    def parse_features(cls, v):
        if isinstance(v, str):
            import json as _json
            try:
                return _json.loads(v)
            except Exception:
                return []
        return v or []

    class Config:
        from_attributes = True


# --- Vendor ---

class VendorResponse(BaseModel):
    id: str
    name: str
    contact_email: str
    contact_phone: Optional[str]
    portal_url: Optional[str]
    reliability_score: float
    average_delivery_days: int
    payment_terms: Optional[str]
    min_order_quantity: int
    active: bool

    class Config:
        from_attributes = True


# --- Quote ---

class QuoteItemResponse(BaseModel):
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    total_price: float
    warranty_months: int
    delivery_days: int
    notes: Optional[str]


class QuoteResponse(BaseModel):
    id: str
    vendor_id: str
    vendor_name: str
    total_amount: float
    status: str
    valid_until: Optional[str]
    terms: Optional[str]
    discount_percent: float
    negotiation_round: int
    created_at: Optional[str]
    items: List[QuoteItemResponse]
    is_revised: bool = False
    parent_quote_id: Optional[str] = None

    @validator("items", pre=True)
    def parse_items(cls, v):
        if isinstance(v, str):
            import json as _json
            try:
                return _json.loads(v)
            except Exception:
                return []
        return v or []

    class Config:
        from_attributes = True


# --- Evaluation ---

class EvaluationResponse(BaseModel):
    id: str
    vendor_id: str
    vendor_name: str
    quote_id: str
    total_score: float
    price_score: float
    quality_score: float
    review_score: float
    warranty_score: float
    delivery_score: float
    reliability_score: float
    budget_score: float
    total_cost: float
    savings_vs_budget: float
    details: Optional[Dict[str, Any]]
    reevaluated: bool

    @validator("details", pre=True)
    def parse_details(cls, v):
        if isinstance(v, str):
            import json as _json
            try:
                return _json.loads(v)
            except Exception:
                return None
        return v or None

    class Config:
        from_attributes = True


# --- Negotiation ---

class NegotiationResponse(BaseModel):
    id: str
    vendor_id: str
    vendor_name: str
    original_quote_id: str
    revised_quote_id: Optional[str]
    rounds: int
    final_discount_percent: float
    final_total_amount: float
    savings_achieved: float
    agreed_terms: Optional[str]
    success: bool
    transcript: Optional[List[Dict[str, Any]]]

    class Config:
        from_attributes = True


# --- Decision ---

class DecisionResponse(BaseModel):
    id: str
    recommended_vendor_id: Optional[str]
    recommended_vendor_name: Optional[str]
    recommended_quote_id: Optional[str]
    final_total_amount: float
    total_score: float
    decision: str
    reasoning: str
    requires_human_approval: bool
    created_at: Optional[str]

    class Config:
        from_attributes = True


# --- Approval ---

class ApprovalResponse(BaseModel):
    id: str
    request_id: Optional[str] = None
    product_name: Optional[str] = None
    final_total_amount: Optional[float] = None
    total_score: Optional[float] = None
    status: str
    decision: Optional[str]
    reviewer_id: Optional[str]
    reviewer_name: Optional[str]
    reason: Optional[str]
    decided_at: Optional[str]
    created_at: Optional[str]

    class Config:
        from_attributes = True


class ApprovalAction(BaseModel):
    decision: str  # "approve", "reject", "changes_requested"
    reviewer_name: str = Field(..., min_length=1, max_length=100)
    reviewer_id: Optional[str] = None
    reason: Optional[str] = Field(default=None, max_length=1000)


# --- Agent Execution ---

class AgentExecutionResponse(BaseModel):
    id: str
    agent_name: str
    status: str
    started_at: Optional[str]
    completed_at: Optional[str]
    output_summary: Optional[str]
    error_message: Optional[str]
    execution_order: int

    class Config:
        from_attributes = True


class ProcurementRequestDetailResponse(ProcurementRequestResponse):
    """Full request payload including everything produced by the agent pipeline."""

    products: List[ProductResponse] = Field(default_factory=list)
    vendors: List[VendorResponse] = Field(default_factory=list)
    quotes: List[QuoteResponse] = Field(default_factory=list)
    evaluations: List[EvaluationResponse] = Field(default_factory=list)
    decision: Optional[DecisionResponse] = None
    approval: Optional[ApprovalResponse] = None
    agent_executions: List[AgentExecutionResponse] = Field(default_factory=list)

    class Config:
        from_attributes = True


# --- Audit Log ---

class AuditLogResponse(BaseModel):
    id: str
    request_id: Optional[str]
    event_type: str
    event_description: str
    actor: Optional[str]
    metadata: Optional[Dict[str, Any]]
    created_at: datetime

    class Config:
        from_attributes = True


# --- Evaluation Weights ---

class EvaluationWeight(BaseModel):
    criterion: str
    weight: float


class EvaluationWeightsUpdate(BaseModel):
    weights: Dict[str, float] = Field(..., description="Criterion weight mappings")


class EvaluationWeightsResponse(BaseModel):
    weights: Dict[str, float]


# --- Health ---

class HealthResponse(BaseModel):
    status: str
    service: str
    version: str
    database: str