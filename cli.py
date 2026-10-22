"""BuyWise - Multi-Agent Procurement Automation System.

Command-line entry point. Runs the full agent pipeline for a single
procurement requirement without n8n.
"""

import argparse
import json
import sys

from buywise.core.agent import AgentContext, Orchestrator
from buywise.agents import (
    ProductResearchAgent,
    VendorResearchAgent,
    ReviewQualityAgent,
    ComparisonAgent,
    DecisionAgent,
    NegotiationAgent,
    ReevaluationAgent,
    ApprovalAgent,
)
from buywise.channels.simulated_vendor import SimulatedVendorChannel
from buywise.config import SETTINGS
from buywise.models.data import ProductRequirement


def build_requirement(args) -> ProductRequirement:
    return ProductRequirement(
        id=args.requirement_id or "REQ-0001",
        product_name=args.product_name,
        category=args.category,
        description=args.description or "",
        quantity=args.quantity,
        max_budget=args.budget,
        required_features=args.features.split(",") if args.features else [],
        warranty_months=args.warranty,
        delivery_needed_by=args.delivery_by,
        preferred_vendors=args.preferred_vendors.split(",") if args.preferred_vendors else [],
    )


def build_orchestrator() -> Orchestrator:
    channel = SimulatedVendorChannel(seed=42, base_delay=SETTINGS.vendor_response_delay_seconds)

    agents = [
        ProductResearchAgent(),
        VendorResearchAgent(),
        ReviewQualityAgent(),
        ComparisonAgent(vendor_channel=channel),
        DecisionAgent(),
        NegotiationAgent(vendor_channel=channel),
        ReevaluationAgent(),
        ApprovalAgent(),
    ]
    return Orchestrator(agents)


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="BuyWise Multi-Agent Procurement Automation"
    )
    parser.add_argument("--requirement-id", default=None, help="Requirement ID")
    parser.add_argument("--product-name", required=True, help="Product name")
    parser.add_argument("--category", required=True, help="Product category")
    parser.add_argument("--description", default="", help="Product description")
    parser.add_argument("--quantity", type=int, default=1, help="Quantity")
    parser.add_argument("--budget", type=float, required=True, help="Max budget")
    parser.add_argument("--features", default="", help="Comma-separated required features")
    parser.add_argument("--warranty", type=int, default=12, help="Required warranty months")
    parser.add_argument("--delivery-by", default=None, help="Required delivery date")
    parser.add_argument("--preferred-vendors", default="", help="Comma-separated preferred vendors")
    parser.add_argument("--no-negotiation", action="store_true",
                        help="Skip negotiation agent (for testing)")
    args = parser.parse_args(argv)

    requirement = build_requirement(args)
    context = AgentContext(requirement=requirement, settings=SETTINGS)

    orchestrator = build_orchestrator()

    if args.no_negotiation:
        # Remove negotiation agent for direct approve path
        orchestrator.agents = [a for a in orchestrator.agents
                               if not isinstance(a, NegotiationAgent)]

    try:
        orchestrator.run(context)
    except KeyboardInterrupt:
        print("\nInterrupted by user.")
        sys.exit(130)

    decision = context.decision
    print("\nPipeline complete.")
    if decision:
        print(f"Final decision: {decision.decision}")
        print(f"Recommended vendor: {decision.recommended_vendor_name}")
        print(f"Final amount: ${decision.final_total_amount:.2f}")

    return 0


if __name__ == "__main__":
    sys.exit(main())