from typing import List, Dict, Any
from ..core.agent import BaseAgent, AgentContext
from ..models.data import ProcurementDecision, NegotiationResult
from ..config import SETTINGS


class ApprovalAgent(BaseAgent):
    """Presents the final recommendation and negotiation results to the
    manager for human approval."""

    def __init__(self):
        super().__init__("Approval Agent")

    def execute(self, context: AgentContext) -> AgentContext:
        req = context.requirement
        decision: ProcurementDecision = context.decision
        negotiations: List[NegotiationResult] = context.negotiation_results

        self.log(context, "Preparing final recommendation for approval")

        recommendation = self._build_recommendation(req, decision, negotiations)

        print("\n" + "=" * 70)
        print("BUYWISE PROCUREMENT RECOMMENDATION")
        print("=" * 70)
        print(recommendation)
        print("=" * 70)

        context.decision.requires_human_approval = True

        # Auto-approve if above threshold and no human override configured
        auto_approve = (
            decision.decision == "approve"
            and decision.total_score >= SETTINGS.auto_approve_threshold
        )

        if auto_approve:
            self.log(context, "Auto-approve threshold met; marking pre-approved")
            decision.metadata = getattr(decision, "metadata", {}) or {}
            decision.metadata["auto_approved"] = True
        else:
            self.log(context, "Awaiting human manager approval")

        self._emit(
            context,
            recipient="Human Manager",
            action="final_recommendation",
            payload={
                "decision": decision.decision,
                "requirement_id": req.id,
                "recommended_vendor": decision.recommended_vendor_name,
                "final_total_amount": decision.final_total_amount,
                "final_score": decision.total_score,
                "requires_human_approval": decision.requires_human_approval,
                "auto_approved": auto_approve,
            },
        )

        return context

    def _build_recommendation(
        self, req, decision: ProcurementDecision,
        negotiations: List[NegotiationResult]
    ) -> str:
        lines: List[str] = []
        lines.append(f"Requirement ID: {req.id}")
        lines.append(f"Product: {req.product_name} ({req.category})")
        lines.append(f"Quantity: {req.quantity}")
        lines.append(f"Max Budget: ${req.max_budget:.2f}")
        lines.append("")
        lines.append(f"Decision: {decision.decision.upper()}")
        lines.append(f"Reasoning: {decision.reasoning}")
        lines.append("")

        if decision.recommended_vendor_name:
            lines.append(f"Recommended Vendor: {decision.recommended_vendor_name}")
            lines.append(f"Final Total Amount: ${decision.final_total_amount:.2f}")
            lines.append(f"Total Score: {decision.total_score:.2f}")
            lines.append(f"Savings vs Budget: ${req.max_budget - decision.final_total_amount:.2f}")
            lines.append("")

        if negotiations:
            lines.append("Negotiation Results:")
            for n in negotiations:
                lines.append(f"  Vendor: {n.vendor_name}")
                lines.append(f"    Rounds: {n.rounds}")
                lines.append(f"    Success: {n.success}")
                lines.append(f"    Final Discount: {n.final_discount_percent*100:.1f}%")
                lines.append(f"    Final Total: ${n.final_total_amount:.2f}")
                lines.append(f"    Savings Achieved: ${n.savings_achieved:.2f}")
                lines.append("")

        lines.append("Evaluation Summary:")
        for e in (decision.evaluation_results or []):
            lines.append(f"  {e.vendor_name}: score={e.total_score:.2f}, "
                         f"cost=${e.total_cost:.2f}, savings=${e.savings_vs_budget:.2f}")

        lines.append("")
        lines.append("Requires Human Approval: "
                     f"{'Yes' if decision.requires_human_approval else 'No'}")
        return "\n".join(lines)