"""Workflow service bridging the existing BuyWise orchestrator with the FastAPI backend.

Handles durable job execution, SSE progress streaming, and persistence of
agent results to PostgreSQL.
"""

import asyncio
import json
import uuid
import traceback
from datetime import datetime, timezone
from typing import Dict, List, Optional, Any
from sqlalchemy.orm import Session

from app.db.session import SessionLocal
from app.models import database as db_models
from app.schemas import procurement as schemas

# Import existing BuyWise orchestration engine
import sys
import os
import types
# Add the repository root so the existing orchestration packages can be imported.
_PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
if _PROJECT_ROOT not in sys.path:
    sys.path.insert(0, _PROJECT_ROOT)

if "buywise" not in sys.modules:
    buywise_package = types.ModuleType("buywise")
    buywise_package.__path__ = [_PROJECT_ROOT]
    buywise_package.__package__ = "buywise"
    sys.modules["buywise"] = buywise_package

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
from buywise.config import SETTINGS as BUYWISE_SETTINGS
from buywise.models.data import ProductRequirement


AGENT_ORDER = [
    ("Product Research Agent", ProductResearchAgent, 1),
    ("Vendor Research Agent", VendorResearchAgent, 2),
    ("Review & Quality Agent", ReviewQualityAgent, 3),
    ("Comparison Agent", ComparisonAgent, 4),
    ("Decision Agent", DecisionAgent, 5),
    ("Negotiation Agent", NegotiationAgent, 6),
    ("Re-evaluation Agent", ReevaluationAgent, 7),
    ("Approval Agent", ApprovalAgent, 8),
]

WORKFLOW_TIMEOUT_SECONDS = 300


class WorkflowJob:
    """In-memory registry of running workflow jobs keyed by request_id."""

    def __init__(self):
        self._jobs: Dict[str, dict] = {}

    def create(self, request_id: str) -> dict:
        job = {
            "request_id": request_id,
            "status": "pending",
            "progress": 0,
            "current_agent": None,
            "agent_states": {},  # agent_name -> {status, output, error, started_at, completed_at}
            "logs": [],
            "result": None,
            "error": None,
            "started_at": None,
            "completed_at": None,
            "task": None,
            "sse_queue": asyncio.Queue(),
        }
        self._jobs[request_id] = job
        return job

    def get(self, request_id: str) -> Optional[dict]:
        return self._jobs.get(request_id)

    def update(self, request_id: str, **kwargs):
        job = self._jobs.get(request_id)
        if not job:
            return
        job.update(kwargs)

    def sse_put(self, request_id: str, event: dict):
        job = self._jobs.get(request_id)
        if job:
            job["sse_queue"].put_nowait(event)


workflow_registry = WorkflowJob()


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def _parse_json(text: Optional[str]) -> Any:
    if not text:
        return None
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return text


def _serialize_dataclass(obj: Any) -> Any:
    """Convert a dataclass instance to a dict for JSON serialization."""
    if obj is None:
        return None
    if hasattr(obj, "__dataclass_fields__"):
        result = {}
        for field_name in obj.__dataclass_fields__:
            value = getattr(obj, field_name)
            result[field_name] = _serialize_value(value)
        return result
    if isinstance(obj, list):
        return [_serialize_value(v) for v in obj]
    if isinstance(obj, dict):
        return {k: _serialize_value(v) for k, v in obj.items()}
    return obj


def _serialize_value(value: Any) -> Any:
    if hasattr(value, "__dataclass_fields__"):
        return _serialize_dataclass(value)
    if isinstance(value, list):
        return [_serialize_value(v) for v in value]
    if isinstance(value, dict):
        return {k: _serialize_value(v) for k, v in value.items()}
    if isinstance(value, datetime):
        return value.isoformat()
    return value


async def run_workflow(request_id: str, requirement_data: dict):
    """Execute the BuyWise orchestrator in the background and persist results."""

    job = workflow_registry.get(request_id)
    if not job:
        return

    db: Session = SessionLocal()
    req = None

    try:
        # Update job status
        job["status"] = "running"
        job["started_at"] = _now_iso()
        workflow_registry.sse_put(request_id, {
            "type": "workflow_started",
            "request_id": request_id,
            "timestamp": job["started_at"],
        })

        # Remove artifacts from a previous run so re-running is idempotent
        _clear_previous_results(db, request_id)

        # Persist request status
        req = db.query(db_models.ProcurementRequest).filter_by(id=request_id).first()
        if req:
            req.status = db_models.ProcurementStatus.IN_PROGRESS
            req.current_stage = "Product Research Agent"
            req.completed_at = None
            db.commit()

        _audit_log(db, request_id, "workflow_started",
                   "BuyWise orchestration workflow started", actor="system")

        # Build requirement from API data
        requirement = ProductRequirement(
            id=request_id,
            product_name=requirement_data["product_name"],
            category=requirement_data["category"],
            description=requirement_data.get("description", ""),
            quantity=requirement_data["quantity"],
            max_budget=requirement_data["max_budget"],
            required_features=requirement_data.get("required_features", []),
            warranty_months=requirement_data.get("warranty_months", 12),
            delivery_needed_by=requirement_data.get("delivery_needed_by"),
            preferred_vendors=requirement_data.get("preferred_vendors", []),
            currency=requirement_data.get("currency", "USD"),
        )

        context = AgentContext(requirement=requirement, settings=BUYWISE_SETTINGS)
        channel = SimulatedVendorChannel(seed=42, base_delay=0.1)

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

        total_agents = len(agents)
        completed_agents = 0

        for agent in agents:
            agent_name = agent.name
            execution_order = completed_agents + 1

            # Create agent execution record
            agent_exec = db_models.AgentExecution(
                id=str(uuid.uuid4()),
                request_id=request_id,
                agent_name=agent_name,
                status=db_models.AgentStatus.RUNNING,
                started_at=_now_iso(),
                execution_order=execution_order,
            )
            db.add(agent_exec)
            db.commit()

            # Update job
            job["current_agent"] = agent_name
            job["progress"] = int((completed_agents / total_agents) * 100)
            job["agent_states"][agent_name] = {
                "status": "running",
                "started_at": agent_exec.started_at,
            }
            workflow_registry.sse_put(request_id, {
                "type": "agent_started",
                "agent_name": agent_name,
                "execution_order": execution_order,
                "timestamp": agent_exec.started_at,
            })

            # Persist to DB
            if req:
                req.current_stage = agent_name
                db.commit()

            # Emit agent start audit log
            _audit_log(db, request_id, "agent_started",
                       f"Agent {agent_name} started execution", actor="system")

            error_message = None
            output_summary = None

            try:
                # Execute the agent in a thread pool to avoid blocking the event loop
                context = await asyncio.to_thread(agent.execute, context)

                # Capture output summary based on agent type
                output_summary = _capture_agent_output(agent, context)

                agent_exec.status = db_models.AgentStatus.COMPLETED
                agent_exec.completed_at = _now_iso()
                agent_exec.output_summary = output_summary
                db.commit()

                job["agent_states"][agent_name] = {
                    "status": "completed",
                    "started_at": agent_exec.started_at,
                    "completed_at": agent_exec.completed_at,
                    "output_summary": output_summary,
                }

                completed_agents += 1
                job["progress"] = int((completed_agents / total_agents) * 100)

                workflow_registry.sse_put(request_id, {
                    "type": "agent_completed",
                    "agent_name": agent_name,
                    "execution_order": execution_order,
                    "output_summary": output_summary,
                    "timestamp": agent_exec.completed_at,
                    "progress": job["progress"],
                })

                _audit_log(db, request_id, "agent_completed",
                           f"Agent {agent_name} completed successfully", actor="system")

            except Exception as exc:
                error_message = str(exc)
                agent_exec.status = db_models.AgentStatus.FAILED
                agent_exec.completed_at = _now_iso()
                agent_exec.error_message = error_message
                db.commit()

                job["agent_states"][agent_name] = {
                    "status": "failed",
                    "started_at": agent_exec.started_at,
                    "completed_at": agent_exec.completed_at,
                    "error_message": error_message,
                }

                workflow_registry.sse_put(request_id, {
                    "type": "agent_failed",
                    "agent_name": agent_name,
                    "execution_order": execution_order,
                    "error_message": error_message,
                    "timestamp": agent_exec.completed_at,
                })

                _audit_log(db, request_id, "agent_failed",
                           f"Agent {agent_name} failed: {error_message}", actor="system")

                # Continue to next agent or stop? We continue but mark workflow as having errors
                completed_agents += 1

        # Persist all context results to database
        _persist_context(db, request_id, context)
        _audit_log(db, request_id, "results_persisted",
                   "Agent results persisted to database", actor="system")

        # Create the human approval record for the recommendation
        _create_approval_record(db, request_id, context)
        _audit_log(db, request_id, "approval_record_created",
                   "Pending approval record created for human review", actor="system")

        # The workflow is finished, but the request still needs a human decision
        if req:
            req.status = db_models.ProcurementStatus.AWAITING_APPROVAL
            req.current_stage = "Awaiting human approval"
            db.commit()

        job["status"] = "awaiting_approval"
        job["completed_at"] = _now_iso()
        job["progress"] = 100
        job["result"] = _build_result_payload(context)

        _audit_log(db, request_id, "workflow_completed",
                   "BuyWise orchestration workflow completed; awaiting human approval",
                   actor="system")

        workflow_registry.sse_put(request_id, {
            "type": "workflow_completed",
            "request_id": request_id,
            "result": job["result"],
            "timestamp": job["completed_at"],
        })

    except Exception as exc:
        tb = traceback.format_exc()
        job["status"] = "failed"
        job["error"] = str(exc)
        job["completed_at"] = _now_iso()

        if req:
            req.status = db_models.ProcurementStatus.FAILED
            db.commit()

        _audit_log(db, request_id, "workflow_failed",
                   f"Workflow failed: {str(exc)}", actor="system")

        workflow_registry.sse_put(request_id, {
            "type": "workflow_failed",
            "request_id": request_id,
            "error": str(exc),
            "traceback": tb,
            "timestamp": job["completed_at"],
        })

    finally:
        db.close()


def reconcile_stuck_workflows():
    """Repair requests left in an inconsistent state by earlier runs.

    A request that has completed all eight agents but still shows ``in_progress``
    (for example because persistence failed) is moved to ``awaiting_approval``
    and given the missing approval record.
    """
    db: Session = SessionLocal()
    try:
        stuck = (
            db.query(db_models.ProcurementRequest)
            .filter(db_models.ProcurementRequest.status.in_([
                db_models.ProcurementStatus.IN_PROGRESS,
                db_models.ProcurementStatus.AWAITING_APPROVAL,
            ]))
            .all()
        )
        for req in stuck:
            executions = (
                db.query(db_models.AgentExecution)
                .filter_by(request_id=req.id)
                .all()
            )
            completed = [e for e in executions if e.status == db_models.AgentStatus.COMPLETED]
            decision = (
                db.query(db_models.DecisionRecord)
                .filter_by(request_id=req.id)
                .first()
            )
            if len(completed) >= len(AGENT_ORDER) and decision:
                req.status = db_models.ProcurementStatus.AWAITING_APPROVAL
                req.current_stage = "Awaiting human approval"
                approval = (
                    db.query(db_models.ApprovalRecord)
                    .filter_by(request_id=req.id)
                    .first()
                )
                if not approval:
                    db.add(db_models.ApprovalRecord(
                        id=str(uuid.uuid4()),
                        request_id=req.id,
                        status=db_models.ApprovalStatus.PENDING,
                        created_at=_now_iso(),
                    ))
            else:
                # The run never produced a persisted recommendation; reset it so
                # it can be started again cleanly.
                req.status = db_models.ProcurementStatus.PENDING
                req.current_stage = None
                db.query(db_models.ApprovalRecord).filter_by(request_id=req.id).delete(
                    synchronize_session=False
                )
        db.commit()
    except Exception as exc:
        db.rollback()
        print(f"Warning: workflow reconciliation failed: {exc}")
    finally:
        db.close()


def _clear_previous_results(db: Session, request_id: str):
    """Delete artifacts from earlier runs so workflows can be re-executed."""
    for model in (
        db_models.AgentExecution,
        db_models.ApprovalRecord,
        db_models.DecisionRecord,
        db_models.NegotiationRecord,
        db_models.EvaluationRecord,
        db_models.QuoteRecord,
        db_models.VendorRecord,
        db_models.ProductRecord,
    ):
        db.query(model).filter_by(request_id=request_id).delete(synchronize_session=False)
    db.commit()


def _create_approval_record(db: Session, request_id: str, context: AgentContext):
    """Queue the final recommendation for a human reviewer."""
    approval = db_models.ApprovalRecord(
        id=str(uuid.uuid4()),
        request_id=request_id,
        status=db_models.ApprovalStatus.PENDING,
        created_at=_now_iso(),
    )
    db.add(approval)
    db.commit()


def _capture_agent_output(agent, context: AgentContext) -> str:
    """Capture a human-readable summary of what an agent produced."""
    name = agent.name
    try:
        if name == "Product Research Agent":
            return f"Found {len(context.products)} product candidates"
        if name == "Vendor Research Agent":
            return f"Identified {len(context.vendors)} vendors"
        if name == "Review & Quality Agent":
            return f"Evaluated quality for {len(context.products)} products"
        if name == "Comparison Agent":
            return f"Generated {len(context.quotes)} quotes and {len(context.evaluations)} evaluations"
        if name == "Decision Agent":
            d = context.decision
            return f"Decision: {d.decision} - {d.reasoning[:100]}" if d else "No decision recorded"
        if name == "Negotiation Agent":
            return f"Completed {len(context.negotiation_results)} negotiation(s)"
        if name == "Re-evaluation Agent":
            return f"Re-evaluated {len(context.evaluations)} vendor(s)"
        if name == "Approval Agent":
            d = context.decision
            return f"Final recommendation: {d.decision if d else 'pending'}"
        return "Agent executed"
    except Exception:
        return "Output summary unavailable"


def _persist_context(db: Session, request_id: str, context: AgentContext):
    """Persist orchestrator context results to the database."""

    # Products
    for p in context.products:
        db.add(db_models.ProductRecord(
            id=p.id,
            request_id=request_id,
            name=p.name,
            category=p.category,
            description=p.description,
            base_price=p.base_price,
            quality_score=p.quality_score,
            review_score=p.review_score,
            features=json.dumps(p.features),
            warranty_months=p.warranty_months,
            manufacturer=p.manufacturer,
            datasheet_url=p.datasheet_url,
            extra_data=json.dumps(p.metadata) if p.metadata else None,
        ))

    # Vendors
    for v in context.vendors:
        db.add(db_models.VendorRecord(
            id=v.id,
            request_id=request_id,
            name=v.name,
            contact_email=v.contact_email,
            contact_phone=v.contact_phone,
            portal_url=v.portal_url,
            reliability_score=v.reliability_score,
            average_delivery_days=v.average_delivery_days,
            payment_terms=v.payment_terms,
            min_order_quantity=v.min_order_quantity,
            active=v.active,
            extra_data=json.dumps(v.metadata) if v.metadata else None,
        ))

    # Quotes
    for q in context.quotes:
        db.add(db_models.QuoteRecord(
            id=q.id,
            request_id=request_id,
            vendor_id=q.vendor_id,
            vendor_name=q.vendor_name,
            total_amount=q.total_amount,
            status=q.status.value,
            valid_until=q.valid_until,
            terms=q.terms,
            discount_percent=q.discount_percent,
            negotiation_round=q.negotiation_round,
            created_at=q.created_at,
            items=json.dumps([it.__dict__ for it in q.items]),
            parent_quote_id=q.metadata.get("parent_quote_id") if q.metadata else None,
            is_revised=q.negotiation_round > 0,
        ))

    # Evaluations
    for e in context.evaluations:
        db.add(db_models.EvaluationRecord(
            id=str(uuid.uuid4()),
            request_id=request_id,
            vendor_id=e.vendor_id,
            vendor_name=e.vendor_name,
            quote_id=e.quote_id,
            total_score=e.total_score,
            price_score=e.price_score,
            quality_score=e.quality_score,
            review_score=e.review_score,
            warranty_score=e.warranty_score,
            delivery_score=e.delivery_score,
            reliability_score=e.reliability_score,
            budget_score=e.budget_score,
            total_cost=e.total_cost,
            savings_vs_budget=e.savings_vs_budget,
            details=json.dumps(e.details) if e.details else None,
            reevaluated=e.details.get("reevaluated", False) if e.details else False,
        ))

    # Negotiations
    for n in context.negotiation_results:
        db.add(db_models.NegotiationRecord(
            id=str(uuid.uuid4()),
            request_id=request_id,
            vendor_id=n.vendor_id,
            vendor_name=n.vendor_name,
            original_quote_id=n.original_quote_id,
            revised_quote_id=n.revised_quote_id,
            rounds=n.rounds,
            final_discount_percent=n.final_discount_percent,
            final_total_amount=n.final_total_amount,
            savings_achieved=n.savings_achieved,
            agreed_terms=n.agreed_terms,
            success=n.success,
            transcript=json.dumps(n.transcript) if n.transcript else None,
        ))

    # Decision
    if context.decision:
        d = context.decision
        db.add(db_models.DecisionRecord(
            id=str(uuid.uuid4()),
            request_id=request_id,
            recommended_vendor_id=d.recommended_vendor_id,
            recommended_vendor_name=d.recommended_vendor_name,
            recommended_quote_id=d.recommended_quote_id,
            final_total_amount=d.final_total_amount,
            total_score=d.total_score,
            decision=d.decision,
            reasoning=d.reasoning,
            requires_human_approval=d.requires_human_approval,
            created_at=d.created_at,
        ))

    db.commit()


def _audit_log(db: Session, request_id: Optional[str], event_type: str,
               description: str, actor: str = "system", metadata: Optional[dict] = None):
    """Write an audit trail entry. Never raises — failures are swallowed so
    the workflow can continue even if the audit table is temporarily
    unavailable or has a stale column name."""
    try:
        audit = db_models.AuditLog(
            id=str(uuid.uuid4()),
            request_id=request_id,
            event_type=event_type,
            event_description=description,
            actor=actor,
            extra_data=json.dumps(metadata) if metadata else None,
        )
        db.add(audit)
        db.commit()
    except Exception:
        try:
            db.rollback()
        except Exception:
            pass
        # Fallback: retry with the legacy column name (pre-0002 migrations)
        try:
            db.execute(
                db.text(
                    "INSERT INTO audit_logs (id, request_id, event_type, "
                    "event_description, actor, metadata, created_at) "
                    "VALUES (:id, :request_id, :event_type, :event_description, "
                    ":actor, :metadata, now())"
                ),
                {
                    "id": str(uuid.uuid4()),
                    "request_id": request_id,
                    "event_type": event_type,
                    "event_description": description,
                    "actor": actor,
                    "metadata": json.dumps(metadata) if metadata else None,
                },
            )
            db.commit()
        except Exception:
            try:
                db.rollback()
            except Exception:
                pass


def _build_result_payload(context: AgentContext) -> dict:
    """Build a JSON-serializable result payload from the final context."""
    return {
        "products": [_serialize_dataclass(p) for p in context.products],
        "vendors": [_serialize_dataclass(v) for v in context.vendors],
        "quotes": [_serialize_dataclass(q) for q in context.quotes],
        "evaluations": [_serialize_dataclass(e) for e in context.evaluations],
        "negotiations": [_serialize_dataclass(n) for n in context.negotiation_results],
        "decision": _serialize_dataclass(context.decision) if context.decision else None,
        "messages": [_serialize_dataclass(m) for m in context.messages],
    }


async def get_workflow_status(request_id: str) -> Optional[dict]:
    """Get the current status of a workflow job."""
    job = workflow_registry.get(request_id)
    if not job:
        return None
    return {
        "request_id": job["request_id"],
        "status": job["status"],
        "progress": job["progress"],
        "current_agent": job["current_agent"],
        "agent_states": job["agent_states"],
        "logs": job["logs"],
        "started_at": job["started_at"],
        "completed_at": job["completed_at"],
        "error": job["error"],
    }


async def stream_events(request_id: str):
    """SSE event stream for a workflow job."""
    job = workflow_registry.get(request_id)
    if not job:
        yield f"data: {json.dumps({'type': 'error', 'message': 'Job not found'})}\n\n"
        return

    # Send initial status
    yield f"data: {json.dumps({'type': 'status', 'status': job['status'], 'progress': job['progress']})}\n\n"

    while True:
        try:
            event = await asyncio.wait_for(job["sse_queue"].get(), timeout=30.0)
            yield f"data: {json.dumps(event)}\n\n"
            if event.get("type") in ("workflow_completed", "workflow_failed"):
                break
        except asyncio.TimeoutError:
            yield f"data: {json.dumps({'type': 'heartbeat'})}\n\n"