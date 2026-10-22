from typing import List, Dict, Any
from ..core.agent import BaseAgent, AgentContext
from ..models.data import Product, ProductRequirement
from ..config import SETTINGS


class ProductResearchAgent(BaseAgent):
    """Finds and analyzes suitable products based on purchase requirements."""

    def __init__(self):
        super().__init__("Product Research Agent")

    def execute(self, context: AgentContext) -> AgentContext:
        req: ProductRequirement = context.requirement
        self.log(context, f"Researching products for: {req.product_name}")

        products: List[Product] = []
        # Simulated product catalog lookup based on category/keywords
        catalog = self._search_catalog(req)

        for p in catalog:
            product = Product(
                id=f"{req.id}:{p['id']}",
                name=p["name"],
                category=req.category,
                description=p["description"],
                base_price=p["base_price"],
                quality_score=p["quality_score"],
                review_score=p["review_score"],
                features=p.get("features", []),
                warranty_months=p.get("warranty_months", req.warranty_months),
                manufacturer=p.get("manufacturer", "Generic"),
                datasheet_url=p.get("datasheet_url"),
                metadata=p.get("metadata", {}),
            )
            products.append(product)

        # Filter out products missing required features
        if req.required_features:
            filtered = []
            for product in products:
                product_features_lower = [f.lower() for f in product.features]
                if all(any(rf.lower() in pf for pf in product_features_lower)
                       for rf in req.required_features):
                    filtered.append(product)
            products = filtered if filtered else products

        context.products = products
        self.log(context, f"Found {len(products)} suitable products")

        self._emit(
            context,
            recipient="Vendor Research Agent",
            action="products_researched",
            payload={"product_ids": [p.id for p in products],
                     "requirement_id": req.id},
        )
        return context

    def _search_catalog(self, req: ProductRequirement) -> List[Dict[str, Any]]:
        """Simulated product catalog. In production this hits product APIs/databases."""
        # max_budget is the total budget for the requested quantity, so each
        # candidate's price is expressed per unit.
        unit_budget = req.max_budget / max(req.quantity, 1)
        base = [
            {
                "id": "P-001",
                "name": f"{req.product_name} Pro",
                "description": "Premium grade with full feature set",
                "base_price": unit_budget * 0.90,
                "quality_score": 0.92,
                "review_score": 0.88,
                "features": ["wifi", "bluetooth", "warranty", "fast-delivery"],
                "warranty_months": 24,
                "manufacturer": "TechPrime",
                "datasheet_url": "https://example.com/ds/P-001.pdf",
            },
            {
                "id": "P-002",
                "name": f"{req.product_name} Standard",
                "description": "Balanced price and performance",
                "base_price": unit_budget * 0.65,
                "quality_score": 0.78,
                "review_score": 0.82,
                "features": ["wifi", "warranty"],
                "warranty_months": 12,
                "manufacturer": "CoreSystems",
                "datasheet_url": "https://example.com/ds/P-002.pdf",
            },
            {
                "id": "P-003",
                "name": f"{req.product_name} Lite",
                "description": "Budget-friendly entry model",
                "base_price": unit_budget * 0.40,
                "quality_score": 0.65,
                "review_score": 0.70,
                "features": ["warranty"],
                "warranty_months": 12,
                "manufacturer": "ValueCo",
                "datasheet_url": "https://example.com/ds/P-003.pdf",
            },
            {
                "id": "P-004",
                "name": f"{req.product_name} Enterprise",
                "description": "Enterprise-grade with SLA support",
                "base_price": unit_budget * 1.15,
                "quality_score": 0.96,
                "review_score": 0.91,
                "features": ["wifi", "bluetooth", "warranty", "fast-delivery", "sla"],
                "warranty_months": 36,
                "manufacturer": "EnterpriseTech",
                "datasheet_url": "https://example.com/ds/P-004.pdf",
            },
        ]
        return base