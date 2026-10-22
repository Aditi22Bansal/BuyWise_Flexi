from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Dict, Any
from enum import Enum


class RequirementStatus(Enum):
    PENDING = "pending"
    IN_PROGRESS = "in_progress"
    COMPLETED = "completed"
    REJECTED = "rejected"


class QuoteStatus(Enum):
    DRAFT = "draft"
    SUBMITTED = "submitted"
    NEGOTIATED = "negotiated"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


@dataclass
class ProductRequirement:
    id: str
    product_name: str
    category: str
    description: str
    quantity: int
    max_budget: float
    required_features: List[str] = field(default_factory=list)
    warranty_months: int = 12
    delivery_needed_by: Optional[str] = None
    preferred_vendors: List[str] = field(default_factory=list)
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    status: RequirementStatus = RequirementStatus.PENDING


@dataclass
class Product:
    id: str
    name: str
    category: str
    description: str
    base_price: float
    quality_score: float  # 0-1
    review_score: float  # 0-1
    features: List[str] = field(default_factory=list)
    warranty_months: int = 12
    manufacturer: str = ""
    datasheet_url: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Vendor:
    id: str
    name: str
    contact_email: str
    contact_phone: Optional[str] = None
    portal_url: Optional[str] = None
    reliability_score: float = 0.5  # 0-1
    average_delivery_days: int = 7
    payment_terms: str = "net30"
    min_order_quantity: int = 1
    active: bool = True
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QuoteItem:
    product_id: str
    product_name: str
    quantity: int
    unit_price: float
    total_price: float
    warranty_months: int
    delivery_days: int
    notes: str = ""


@dataclass
class Quote:
    id: str
    vendor_id: str
    vendor_name: str
    items: List[QuoteItem]
    total_amount: float
    status: QuoteStatus = QuoteStatus.DRAFT
    valid_until: Optional[str] = None
    terms: str = ""
    discount_percent: float = 0.0
    negotiation_round: int = 0
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    metadata: Dict[str, Any] = field(default_factory=dict)

    @property
    def item_count(self) -> int:
        return len(self.items)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "vendor_id": self.vendor_id,
            "vendor_name": self.vendor_name,
            "total_amount": self.total_amount,
            "status": self.status.value,
            "discount_percent": self.discount_percent,
            "negotiation_round": self.negotiation_round,
            "items": [
                {
                    "product_id": it.product_id,
                    "product_name": it.product_name,
                    "quantity": it.quantity,
                    "unit_price": it.unit_price,
                    "total_price": it.total_price,
                    "warranty_months": it.warranty_months,
                    "delivery_days": it.delivery_days,
                    "notes": it.notes,
                }
                for it in self.items
            ],
        }


@dataclass
class EvaluationResult:
    vendor_id: str
    vendor_name: str
    quote_id: str
    total_score: float  # 0-1
    price_score: float
    quality_score: float
    review_score: float
    warranty_score: float
    delivery_score: float
    reliability_score: float
    budget_score: float
    total_cost: float
    savings_vs_budget: float
    details: Dict[str, Any] = field(default_factory=dict)


@dataclass
class NegotiationResult:
    vendor_id: str
    vendor_name: str
    original_quote_id: str
    revised_quote_id: Optional[str]
    rounds: int
    final_discount_percent: float
    final_total_amount: float
    savings_achieved: float
    agreed_terms: str
    success: bool
    transcript: List[Dict[str, Any]] = field(default_factory=list)


@dataclass
class ProcurementDecision:
    requirement_id: str
    recommended_vendor_id: Optional[str]
    recommended_vendor_name: Optional[str]
    recommended_quote_id: Optional[str]
    final_total_amount: float
    total_score: float
    decision: str  # "approve", "negotiate", "reject", "escalate"
    reasoning: str
    evaluation_results: List[EvaluationResult] = field(default_factory=list)
    negotiation_results: List[NegotiationResult] = field(default_factory=list)
    requires_human_approval: bool = True
    created_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())