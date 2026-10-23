from typing import List, Dict, Any
from ..core.agent import BaseAgent, AgentContext
from ..models.data import EvaluationResult, ProcurementDecision
from ..config import SETTINGS, currency_symbol


class DecisionAgent(BaseAgent):
    """Determines whether the current offer is suitable or whether negotiation
    can improve the deal."""

    def __init__(self):
        super().__init__("Decision Agent")

    def execute(self, context: AgentContext) -> AgentContext:
        evaluations: List[EvaluationResult] = context.evaluations
        req = context.requirement
        sym = currency_symbol(req.currency)
        self.log(context, f"Evaluating {len(evaluations)} vendor offers for decision")

        if not evaluations:
            self.log(context, "No evaluations available; marking rejected")
            context.decision = ProcurementDecision(
                requirement_id=req.id,
                recommended_vendor_id=None,
                recommended_vendor_name=None,
                recommended_quote_id=None,
                final_total_amount=0.0,
                total_score=0.0,
                decision="reject",
                reasoning="No vendor quotations received.",
                requires_human_approval=True,
            )
            self._emit(
                context,
                recipient="Approval Agent",
                action="decision_made",
                payload={"decision": "reject", "requirement_id": req.id},
            )
            return context

        # Pick best evaluation by total score
        best = max(evaluations, key=lambda e: e.total_score)
        self.log(
            context,
            f"Best offer: {best.vendor_name} (score={best.total_score:.2f}, "
            f"cost={sym}{best.total_cost:.2f})",
        )

        threshold = SETTINGS.auto_approve_threshold

        if best.total_score >= threshold and best.savings_vs_budget >= 0:
            decision = "approve"
            reasoning = (
                f"Best offer from {best.vendor_name} exceeds auto-approve "
                f"threshold ({best.total_score:.2f} >= {threshold}) and is within budget."
            )
        elif best.total_score >= 0.6:
            # Within acceptable range but negotiation may improve terms
            decision = "negotiate"
            reasoning = (
                f"Best offer from {best.vendor_name} (score={best.total_score:.2f}) "
                f"is acceptable but negotiation may improve price/terms. "
                f"Target discount: {SETTINGS.negotiation_target_discount*100:.0f}%."
            )
        else:
            decision = "reject"
            reasoning = (
                f"Best offer from {best.vendor_name} (score={best.total_score:.2f}) "
                f"does not meet minimum quality threshold (0.60)."
            )

        context.decision = ProcurementDecision(
            requirement_id=req.id,
            recommended_vendor_id=best.vendor_id if decision != "reject" else None,
            recommended_vendor_name=best.vendor_name if decision != "reject" else None,
            recommended_quote_id=best.quote_id if decision != "reject" else None,
            final_total_amount=best.total_cost if decision != "reject" else 0.0,
            total_score=best.total_score,
            decision=decision,
            reasoning=reasoning,
            evaluation_results=list(evaluations),
            requires_human_approval=True,
        )

        self.log(context, f"Decision: {decision} — {reasoning}")

        self._emit(
            context,
            recipient="Negotiation Agent" if decision == "negotiate" else "Approval Agent",
            action="decision_made",
            payload={
                "decision": decision,
                "requirement_id": req.id,
                "best_vendor_id": best.vendor_id,
                "best_vendor_name": best.vendor_name,
                "best_quote_id": best.quote_id,
                "best_score": best.total_score,
                "target_discount": SETTINGS.negotiation_target_discount,
            },
        )
        return context