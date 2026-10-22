from typing import List, Dict, Any
from ..core.agent import BaseAgent, AgentContext
from ..models.data import Product, Vendor
from ..config import SETTINGS


class ReviewQualityAgent(BaseAgent):
    """Evaluates product quality, reviews, and overall value."""

    def __init__(self):
        super().__init__("Review & Quality Agent")

    def execute(self, context: AgentContext) -> AgentContext:
        products: List[Product] = context.products
        self.log(context, f"Evaluating quality for {len(products)} products")

        for product in products:
            # Composite value score: weighted blend of quality and reviews
            quality = product.quality_score
            reviews = product.review_score
            value_score = round(0.6 * quality + 0.4 * reviews, 4)

            product.metadata["quality_assessment"] = {
                "quality_score": quality,
                "review_score": reviews,
                "value_score": value_score,
                "assessed_by": self.name,
                "assessed_at": __import__("datetime").datetime.utcnow().isoformat(),
            }
            self.log(
                context,
                f"  {product.name}: quality={quality}, review={reviews}, value={value_score}",
            )

        self._emit(
            context,
            recipient="Comparison Agent",
            action="quality_evaluated",
            payload={"product_ids": [p.id for p in products],
                     "vendor_ids": [v.id for v in context.vendors]},
        )
        return context