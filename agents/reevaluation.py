from typing import List, Dict, Any
from ..core.agent import BaseAgent, AgentContext
from ..models.data import EvaluationResult, NegotiationResult, ProcurementDecision
from ..config import SETTINGS, currency_symbol


class ReevaluationAgent(BaseAgent):
    """Recalculates scores, costs, and savings after receiving revised quotations."""

    def __init__(self):
        super().__init__("Re-evaluation Agent")

    def execute(self, context: AgentContext) -> AgentContext:
        req = context.requirement
        sym = currency_symbol(req.currency)
        decision = context.decision
        negotiations: List[NegotiationResult] = context.negotiation_results
        evaluations: List[EvaluationResult] = context.evaluations

        self.log(context, "Re-evaluating after negotiation results")

        # Rebuild evaluations using revised quotes where applicable
        revised_evaluations: List[EvaluationResult] = []
        quote_map = {q.id: q for q in context.quotes}

        # Map vendor_id -> revised quote id from successful negotiations
        revised_quote_by_vendor: Dict[str, str] = {}
        for n in negotiations:
            if n.success and n.revised_quote_id:
                revised_quote_by_vendor[n.vendor_id] = n.revised_quote_id

        for eval_result in evaluations:
            # Prefer the revised (negotiated) quote if one exists
            quote_id = revised_quote_by_vendor.get(
                eval_result.vendor_id, eval_result.quote_id
            )
            quote = quote_map.get(quote_id)
            if quote is None:
                revised_evaluations.append(eval_result)
                continue

            # Recompute scores against the (possibly revised) quote
            from ..models.data import EvaluationResult as ER

            c = SETTINGS.criteria
            product_map = {p.id: p for p in context.products}

            price_score = max(0.0, 1.0 - (quote.total_amount / req.max_budget))
            price_score = min(price_score, 1.0)

            best_quality = 0.0
            best_review = 0.0
            best_warranty = 0
            best_delivery = 999
            for item in quote.items:
                p = product_map.get(item.product_id)
                if p:
                    best_quality = max(best_quality, p.quality_score)
                    best_review = max(best_review, p.review_score)
            best_warranty = max((it.warranty_months for it in quote.items),
                                default=req.warranty_months)
            best_delivery = min((it.delivery_days for it in quote.items),
                                default=999)

            quality_score = best_quality if best_quality > 0 else 0.75
            review_score = best_review if best_review > 0 else 0.7
            warranty_score = min(best_warranty / max(req.warranty_months, 1), 1.0)
            delivery_score = max(0.0, 1.0 - (best_delivery / 30.0))

            vendor = next((v for v in context.vendors if v.id == eval_result.vendor_id),
                          None)
            reliability_score = vendor.reliability_score if vendor else 0.5
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

            revised = ER(
                vendor_id=eval_result.vendor_id,
                vendor_name=eval_result.vendor_name,
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
                    "reevaluated": True,
                },
            )
            revised_evaluations.append(revised)

        context.evaluations = revised_evaluations

        # Update decision with re-evaluated best (prefer affordable offers)
        if revised_evaluations:
            affordable = [e for e in revised_evaluations if e.savings_vs_budget >= 0]
            best = max(affordable or revised_evaluations, key=lambda e: e.total_score)
            decision.recommended_vendor_id = best.vendor_id
            decision.recommended_vendor_name = best.vendor_name
            decision.recommended_quote_id = best.quote_id
            decision.final_total_amount = best.total_cost
            decision.total_score = best.total_score
            # Keep existing decision (approve/negotiate) but refresh reasoning
            if decision.decision == "negotiate":
                if best.savings_vs_budget < 0:
                    decision.decision = "reject"
                    decision.reasoning = (
                        f"After re-evaluation, the best offer from {best.vendor_name} "
                        f"(score={best.total_score:.2f}, cost={sym}{best.total_cost:.2f}) still "
                        f"exceeds the budget of {sym}{req.max_budget:.2f}."
                    )
                elif best.total_score >= 0.6:
                    decision.decision = "approve"
                    decision.reasoning = (
                        f"After re-evaluation, {best.vendor_name} (score={best.total_score:.2f}, "
                        f"cost={sym}{best.total_cost:.2f}) is recommended for approval."
                    )
                else:
                    decision.decision = "reject"
                    decision.reasoning = (
                        f"After re-evaluation, the best offer from {best.vendor_name} "
                        f"(score={best.total_score:.2f}) does not meet the minimum quality threshold."
                    )

        context.decision = decision
        self.log(
            context,
            f"Re-evaluation complete: best={best.vendor_name if revised_evaluations else 'none'} "
            f"(score={best.total_score:.2f}, cost={sym}{best.total_cost:.2f})"
            if revised_evaluations else "No evaluations to re-evaluate.",
        )

        self._emit(
            context,
            recipient="Approval Agent",
            action="reevaluation_complete",
            payload={
                "decision": decision.decision,
                "requirement_id": req.id,
                "best_vendor_id": best.vendor_id if revised_evaluations else None,
                "best_vendor_name": best.vendor_name if revised_evaluations else None,
                "best_quote_id": best.quote_id if revised_evaluations else None,
                "final_total_amount": best.total_cost if revised_evaluations else 0.0,
                "final_score": best.total_score if revised_evaluations else 0.0,
                "negotiation_results": [n.__dict__ for n in negotiations],
            },
        )
        return context