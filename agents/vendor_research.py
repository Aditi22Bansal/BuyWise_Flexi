from typing import List, Dict, Any
from ..core.agent import BaseAgent, AgentContext
from ..models.data import Product, Vendor, ProductRequirement
from ..config import SETTINGS


class VendorResearchAgent(BaseAgent):
    """Identifies vendors and collects pricing, delivery, warranty, reliability,
    and payment information."""

    def __init__(self):
        super().__init__("Vendor Research Agent")

    def execute(self, context: AgentContext) -> AgentContext:
        req: ProductRequirement = context.requirement
        products: List[Product] = context.products
        self.log(context, f"Researching vendors for {len(products)} products")

        vendors: List[Vendor] = []
        vendor_catalog = self._get_vendor_catalog()

        for v in vendor_catalog:
            vendor = Vendor(
                id=f"{req.id}:{v['id']}",
                name=v["name"],
                contact_email=v["contact_email"],
                contact_phone=v.get("contact_phone"),
                portal_url=v.get("portal_url"),
                reliability_score=v["reliability_score"],
                average_delivery_days=v["average_delivery_days"],
                payment_terms=v.get("payment_terms", "net30"),
                min_order_quantity=v.get("min_order_quantity", 1),
                active=v.get("active", True),
                metadata=v.get("metadata", {}),
            )
            vendors.append(vendor)

        context.vendors = vendors
        self.log(context, f"Identified {len(vendors)} active vendors")

        self._emit(
            context,
            recipient="Review & Quality Agent",
            action="vendors_identified",
            payload={"vendor_ids": [v.id for v in vendors],
                     "product_ids": [p.id for p in products],
                     "requirement_id": req.id},
        )
        return context

    def _get_vendor_catalog(self) -> List[Dict[str, Any]]:
        """Simulated vendor directory. In production this integrates with
        vendor portals / procurement databases."""
        return [
            {
                "id": "V-001",
                "name": "Alpha Supply Co.",
                "contact_email": "sales@alphasupply.example.com",
                "contact_phone": "+1-555-0101",
                "portal_url": "https://portal.alphasupply.example.com",
                "reliability_score": 0.88,
                "average_delivery_days": 5,
                "payment_terms": "net30",
                "min_order_quantity": 1,
            },
            {
                "id": "V-002",
                "name": "Beta Distributors",
                "contact_email": "orders@betadist.example.com",
                "contact_phone": "+1-555-0102",
                "portal_url": "https://portal.betadist.example.com",
                "reliability_score": 0.75,
                "average_delivery_days": 8,
                "payment_terms": "net15",
                "min_order_quantity": 5,
            },
            {
                "id": "V-003",
                "name": "Gamma Direct",
                "contact_email": "procurement@gammadirect.example.com",
                "contact_phone": "+1-555-0103",
                "portal_url": None,
                "reliability_score": 0.62,
                "average_delivery_days": 12,
                "payment_terms": "prepaid",
                "min_order_quantity": 1,
            },
            {
                "id": "V-004",
                "name": "Delta Wholesale",
                "contact_email": "sales@deltawholesale.example.com",
                "contact_phone": "+1-555-0104",
                "portal_url": "https://portal.deltawholesale.example.com",
                "reliability_score": 0.91,
                "average_delivery_days": 3,
                "payment_terms": "net45",
                "min_order_quantity": 2,
            },
        ]