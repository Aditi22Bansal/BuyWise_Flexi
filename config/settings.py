import os
from dataclasses import dataclass
from typing import Dict, List


@dataclass
class ProcurementCriteria:
    price_weight: float = 0.25
    quality_weight: float = 0.20
    review_weight: float = 0.15
    warranty_weight: float = 0.10
    delivery_weight: float = 0.15
    reliability_weight: float = 0.10
    budget_weight: float = 0.05

    def __post_init__(self):
        total = (
            self.price_weight
            + self.quality_weight
            + self.review_weight
            + self.warranty_weight
            + self.delivery_weight
            + self.reliability_weight
            + self.budget_weight
        )
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"Criteria weights must sum to 1.0, got {total}")


@dataclass
class Settings:
    negotiation_max_rounds: int = 3
    negotiation_target_discount: float = 0.10  # 10% target
    auto_approve_threshold: float = 0.85
    vendor_response_delay_seconds: float = 0.5
    negotiation_channel: str = "simulated_api"  # simulated_api | email | portal
    criteria: ProcurementCriteria = None

    def __post_init__(self):
        if self.criteria is None:
            self.criteria = ProcurementCriteria()


SETTINGS = Settings()