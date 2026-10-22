from typing import List, Dict, Any
from ..core.agent import BaseAgent, AgentContext
from ..models.data import Quote, EvaluationResult, NegotiationResult
from ..config import SETTINGS


class NegotiationAgent(BaseAgent):
    """Communicates with vendors and negotiates prices, discounts, warranty,
    and other terms via the configured negotiation channel."""

    def __init__(self, vendor_channel=None):
        super().__init__("Negotiation Agent")
        self.vendor_channel = vendor_channel

    def execute(self, context: AgentContext) -> AgentContext:
        req = context.requirement
        decision = context.decision
        vendor_channel = self.vendor_channel or context.metadata.get("vendor_channel")

        if vendor_channel is None:
            from ..channels.simulated_vendor import SimulatedVendorChannel
            vendor_channel = SimulatedVendorChannel()
            context.metadata["vendor_channel"] = vendor_channel

        self.log(context, "Starting negotiation loop with vendors")

        # Handle missing decision gracefully
        decision = context.decision
        if decision is None:
            self.log(context, "No decision available; skipping negotiation")
            self._emit(
                context,
                recipient="Re-evaluation Agent",
                action="negotiation_complete",
                payload={"decision": "skip", "requirement_id": req.id},
            )
            return context

        # Identify quotes to negotiate: those flagged by Decision Agent
        target_vendor_id = decision.recommended_vendor_id
        target_quote_id = decision.recommended_quote_id

        quote = next((q for q in context.quotes if q.id == target_quote_id), None)
        if quote is None:
            self.log(context, "Target quote not found; skipping negotiation")
            self._emit(
                context,
                recipient="Re-evaluation Agent",
                action="negotiation_complete",
                payload={"decision": decision.decision, "requirement_id": req.id},
            )
            return context

        vendor = next((v for v in context.vendors if v.id == quote.vendor_id), None)
        if vendor is None:
            self.log(context, "Target vendor not found; skipping negotiation")
            self._emit(
                context,
                recipient="Re-evaluation Agent",
                action="negotiation_complete",
                payload={"decision": decision.decision, "requirement_id": req.id},
            )
            return context

        transcript: List[Dict[str, Any]] = []
        current_quote = quote
        rounds = 0
        success = False
        max_rounds = SETTINGS.negotiation_max_rounds
        target_discount = SETTINGS.negotiation_target_discount

        # Track the index of the quote being negotiated so revisions can
        # replace it in-place on every round.
        quote_index = None
        for i, q in enumerate(context.quotes):
            if q.id == quote.id:
                quote_index = i
                break

        while rounds < max_rounds:
            rounds += 1
            self.log(
                context,
                f"  Negotiation round {rounds}/{max_rounds} with {vendor.name}",
            )

            response = vendor_channel.negotiate(
                vendor, current_quote, target_discount, rounds
            )

            transcript.append({
                "round": rounds,
                "vendor": vendor.name,
                "accepted": response.accepted_negotiation,
                "note": response.counter_offer_note,
                "quote_id": response.quote.id,
                "total_amount": response.quote.total_amount,
                "discount_percent": response.quote.discount_percent,
            })

            self.log(
                context,
                f"  Vendor response: {response.counter_offer_note}",
            )

            if response.accepted_negotiation and response.quote.id != current_quote.id:
                current_quote = response.quote
                success = True
                # Replace the quote in context at the tracked index
                if quote_index is not None:
                    context.quotes[quote_index] = current_quote
                self.log(context, f"  Concession accepted in round {rounds}")
                if (current_quote.discount_percent < target_discount
                        and rounds < max_rounds):
                    continue
                break
            else:
                break

        final_discount = current_quote.discount_percent
        final_total = current_quote.total_amount
        original_total = quote.total_amount
        savings_achieved = original_total - final_total

        negotiation_result = NegotiationResult(
            vendor_id=vendor.id,
            vendor_name=vendor.name,
            original_quote_id=quote.id,
            revised_quote_id=current_quote.id if current_quote.id != quote.id else None,
            rounds=rounds,
            final_discount_percent=round(final_discount, 4),
            final_total_amount=round(final_total, 2),
            savings_achieved=round(savings_achieved, 2),
            agreed_terms=current_quote.terms,
            success=success,
            transcript=transcript,
        )
        context.negotiation_results.append(negotiation_result)

        # Update decision with negotiated values
        decision.recommended_quote_id = current_quote.id
        decision.final_total_amount = round(final_total, 2)
        if success:
            decision.reasoning += (
                f" Negotiated {rounds} round(s): additional {final_discount*100:.1f}% "
                f"discount, saving ${savings_achieved:.2f}."
            )
        else:
            decision.reasoning += " No further concession obtained from vendor."

        self.log(
            context,
            f"Negotiation complete: success={success}, rounds={rounds}, "
            f"final total=${final_total:.2f}, savings=${savings_achieved:.2f}",
        )

        self._emit(
            context,
            recipient="Re-evaluation Agent",
            action="negotiation_complete",
            payload={
                "decision": decision.decision,
                "requirement_id": req.id,
                "negotiation_result": negotiation_result.__dict__,
                "revised_quote_id": current_quote.id if success else None,
            },
        )
        return context