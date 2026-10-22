import itertools
from typing import List, Dict, Any
from ..core.agent import BaseAgent, AgentContext
from ..channels.simulated_vendor import SimulatedVendorChannel
from ..models.data import Product, Vendor, Quote, QuoteItem, QuoteStatus
from ..config import SETTINGS


class ComparisonAgent(BaseAgent):
    """Compares vendors across configurable procurement criteria and requests
    initial quotations."""

    def __init__(self, vendor_channel: SimulatedVendorChannel = None):
        super().__init__("Comparison Agent")
        self.vendor_channel = vendor_channel

    def execute(self, context: AgentContext) -> AgentContext:
        req = context.requirement
        products: List[Product] = context.products
        vendors: List[Vendor] = context.vendors
        channel = self.vendor_channel or context.metadata.get("vendor_channel")

        if channel is None:
            channel = SimulatedVendorChannel()
            context.metadata["vendor_channel"] = channel

        self.log(context, "Requesting quotations from vendors")

        # Vendors are compared on the same specification: the best-quality
        # product candidate that fits within the total budget.
        if not products:
            self.log(context, "No products available; no quotations can be requested")
            return context

        affordable = [
            p for p in products
            if p.base_price * req.quantity <= req.max_budget
        ] or products
        selected_product = max(affordable, key=lambda p: p.quality_score)
        context.metadata["selected_product_id"] = selected_product.id
        self.log(context, f"Selected product for quotation: {selected_product.name}")

        for vendor in vendors:
            if not vendor.active:
                continue
            quote = channel.request_quote(vendor, req, [selected_product])
            context.quotes.append(quote)
            self.log(context, f"  Quote from {vendor.name}: ${quote.total_amount:.2f}")

        # Score each vendor-quote pair across criteria
        evaluations = []
        for quote in context.quotes:
            vendor = next(v for v in vendors if v.id == quote.vendor_id)
            eval_result = self._evaluate(quote, vendor, req, context)
            context.evaluations.append(eval_result)
            evaluations.append(eval_result)
            self.log(
                context,
                f"  {vendor.name}: total_score={eval_result.total_score:.2f}, "
                f"cost=${eval_result.total_cost:.2f}",
            )

        self._emit(
            context,
            recipient="Decision Agent",
            action="comparison_complete",
            payload={
                "quote_ids": [q.id for q in context.quotes],
                "evaluation_ids": [e.vendor_id for e in context.evaluations],
            },
        )
        return context

    def _evaluate(self, quote: Quote, vendor: Vendor, req, context: AgentContext) -> Any:
        from ..models.data import EvaluationResult

        c = SETTINGS.criteria

        # Normalize price score (lower price = higher score)
        price_score = max(0.0, 1.0 - (quote.total_amount / req.max_budget))
        price_score = min(price_score, 1.0)

        # Quality score from product research (use best product in quote)
        product_map = {p.id: p for p in context.products}
        best_quality = 0.0
        for item in quote.items:
            p = product_map.get(item.product_id)
            if p:
                best_quality = max(best_quality, p.quality_score)
        quality_score = best_quality if best_quality > 0 else 0.75

        review_score = 0.0
        for item in quote.items:
            p = product_map.get(item.product_id)
            if p:
                review_score = max(review_score, p.review_score)
        review_score = review_score if review_score > 0 else 0.7

        # Warranty score
        best_warranty = max((it.warranty_months for it in quote.items),
                            default=req.warranty_months)
        warranty_score = min(best_warranty / max(req.warranty_months, 1), 1.0)

        # Delivery score (faster = higher)
        best_delivery = min((it.delivery_days for it in quote.items),
                            default=vendor.average_delivery_days)
        delivery_score = max(0.0, 1.0 - (best_delivery / 30.0))

        reliability_score = vendor.reliability_score

        # Budget score
        budget_score = max(0.0, 1.0 - (quote.total_amount / req.max_budget))

        total_score = (
            c.price_weight * price_score
            + c.quality_weight * quality_score
            + c.review_weight * review_score
            + c.warranty_weight * warranty_score
            + c.delivery_weight * delivery_score
            + c.reliability_weight * reliability_score
            + c.budget_weight * budget_score
        )

        savings = req.max_budget - quote.total_amount

        return EvaluationResult(
            vendor_id=vendor.id,
            vendor_name=vendor.name,
            quote_id=quote.id,
            total_score=round(total_score, 4),
            price_score=round(price_score, 4),
            quality_score=round(quality_score, 4),
            review_score=round(review_score, 4),
            warranty_score=round(warranty_score, 4),
            delivery_score=round(delivery_score, 4),
            reliability_score=round(reliability_score, 4),
            budget_score=round(budget_score, 4),
            total_cost=round(quote.total_amount, 2),
            savings_vs_budget=round(savings, 2),
            details={
                "negotiation_round": quote.negotiation_round,
                "discount_percent": quote.discount_percent,
            },
        )