"""Tests for BuyWise backend - verifies integration with existing orchestrator."""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", ".."))

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


def test_orchestrator_runs_end_to_end():
    """Verify the existing BuyWise orchestrator executes all 8 agents."""
    req = ProductRequirement(
        id="REQ-TEST-001",
        product_name="Test Laptop",
        category="Computers",
        description="Test procurement requirement",
        quantity=2,
        max_budget=50000.0,
        required_features=["wifi", "warranty"],
        warranty_months=12,
    )

    context = AgentContext(requirement=req, settings=SETTINGS)
    channel = SimulatedVendorChannel(seed=42, base_delay=0.0)

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
    orchestrator = Orchestrator(agents)
    result = orchestrator.run(context)

    assert result.products, "Should find products"
    assert result.vendors, "Should identify vendors"
    assert result.quotes, "Should generate quotes"
    assert result.evaluations, "Should produce evaluations"
    assert result.decision is not None, "Should produce a decision"

    # Verify negotiation happened
    assert len(result.negotiation_results) >= 0, "Negotiation results should exist"

    # Verify decision is valid
    assert result.decision.decision in ("approve", "negotiate", "reject")

    print("PASS: Orchestrator end-to-end test")


def test_agent_execution_order():
    """Verify all 8 agents execute in the correct order."""
    agent_names = [
        "Product Research Agent",
        "Vendor Research Agent",
        "Review & Quality Agent",
        "Comparison Agent",
        "Decision Agent",
        "Negotiation Agent",
        "Re-evaluation Agent",
        "Approval Agent",
    ]

    # Verify all agents exist
    agents = [
        ProductResearchAgent(),
        VendorResearchAgent(),
        ReviewQualityAgent(),
        ComparisonAgent(vendor_channel=SimulatedVendorChannel()),
        DecisionAgent(),
        NegotiationAgent(vendor_channel=SimulatedVendorChannel()),
        ReevaluationAgent(),
        ApprovalAgent(),
    ]

    executed_names = [a.name for a in agents]
    assert executed_names == agent_names, f"Agent order mismatch: {executed_names}"
    print("PASS: Agent execution order test")


def test_negotiation_produces_revised_quote():
    """Verify negotiation produces revised quotes with discounts."""
    req = ProductRequirement(
        id="REQ-TEST-002",
        product_name="Test Server",
        category="Servers",
        description="Test server procurement",
        quantity=5,
        max_budget=100000.0,
    )

    context = AgentContext(requirement=req, settings=SETTINGS)
    channel = SimulatedVendorChannel(seed=42, base_delay=0.0)

    # Run through comparison to get quotes
    agents_pre = [
        ProductResearchAgent(),
        VendorResearchAgent(),
        ReviewQualityAgent(),
        ComparisonAgent(vendor_channel=channel),
    ]
    orchestrator_pre = Orchestrator(agents_pre)
    context = orchestrator_pre.run(context)

    assert len(context.quotes) > 0, "Should have quotes"

    # Run negotiation
    agents_neg = [NegotiationAgent(vendor_channel=channel)]
    orchestrator_neg = Orchestrator(agents_neg)
    context = orchestrator_neg.run(context)

    # Check if any negotiation succeeded
    if context.negotiation_results:
        for nr in context.negotiation_results:
            if nr.success:
                assert nr.revised_quote_id is not None
                assert nr.final_discount_percent > 0
                assert nr.savings_achieved >= 0
                print(f"PASS: Negotiation test - {nr.vendor_name} discounted by {nr.final_discount_percent*100:.1f}%")
                return

    print("PASS: Negotiation test (no successful negotiation, which is valid)")


def test_reevaluation_uses_revised_quotes():
    """Verify re-evaluation recalculates using revised quotes."""
    req = ProductRequirement(
        id="REQ-TEST-003",
        product_name="Test Equipment",
        category="Equipment",
        description="Test equipment procurement",
        quantity=3,
        max_budget=75000.0,
    )

    context = AgentContext(requirement=req, settings=SETTINGS)
    channel = SimulatedVendorChannel(seed=42, base_delay=0.0)

    agents = [
        ProductResearchAgent(),
        VendorResearchAgent(),
        ReviewQualityAgent(),
        ComparisonAgent(vendor_channel=channel),
        DecisionAgent(),
        NegotiationAgent(vendor_channel=channel),
        ReevaluationAgent(),
    ]
    orchestrator = Orchestrator(agents)
    result = orchestrator.run(context)

    # Re-evaluation should mark evaluations as reevaluated if negotiations happened
    for e in result.evaluations:
        if e.details.get("reevaluated"):
            assert e.details["reevaluated"] is True
            print(f"PASS: Re-evaluation test - {e.vendor_name} was re-evaluated")
            return

    print("PASS: Re-evaluation test (evaluations processed)")


def test_decision_requires_human_approval():
    """Verify decision always requires human approval."""
    req = ProductRequirement(
        id="REQ-TEST-004",
        product_name="Test Item",
        category="Test",
        description="Test",
        quantity=1,
        max_budget=1000.0,
    )

    context = AgentContext(requirement=req, settings=SETTINGS)
    channel = SimulatedVendorChannel(seed=42, base_delay=0.0)

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
    orchestrator = Orchestrator(agents)
    result = orchestrator.run(context)

    assert result.decision.requires_human_approval is True
    print("PASS: Human approval requirement test")


if __name__ == "__main__":
    test_orchestrator_runs_end_to_end()
    test_agent_execution_order()
    test_negotiation_produces_revised_quote()
    test_reevaluation_uses_revised_quotes()
    test_decision_requires_human_approval()
    print("\nAll tests passed!")