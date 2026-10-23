from fastapi import APIRouter, Depends, HTTPException, Query, BackgroundTasks
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from sqlalchemy import desc, func, or_
from typing import List, Optional
import json
import uuid
from datetime import datetime

from app.db.session import get_db
from app.models import database as db_models
from app.schemas import procurement as schemas
from app.core.auth import get_current_user, require_roles
from app.services.workflow import (
    workflow_registry, run_workflow, get_workflow_status, stream_events,
)

router = APIRouter(dependencies=[Depends(get_current_user)])


# --- Procurement Requests ---

@router.post("/procurement-requests", response_model=schemas.ProcurementRequestResponse, tags=["Procurement"])
def create_procurement_request(
    payload: schemas.ProcurementRequestCreate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("admin", "requester", "officer")),
):
    """Create a procurement request. Does NOT start the pipeline.
    The Officer must explicitly start it via POST /procurement-requests/{id}/start.
    """
    request_id = f"REQ-{uuid.uuid4().hex[:12].upper()}"

    db_req = db_models.ProcurementRequest(
        id=request_id,
        product_name=payload.product_name,
        category=payload.category,
        description=payload.description,
        quantity=payload.quantity,
        max_budget=payload.max_budget,
        currency=payload.currency,
        required_features=json.dumps(payload.required_features),
        warranty_months=payload.warranty_months,
        delivery_needed_by=payload.delivery_needed_by,
        preferred_vendors=json.dumps(payload.preferred_vendors),
        status=db_models.ProcurementStatus.PENDING,
    )
    db.add(db_req)

    # Audit log (best-effort — never blocks request creation)
    try:
        db.add(db_models.AuditLog(
            id=str(uuid.uuid4()),
            request_id=request_id,
            event_type="request_created",
            event_description=f"Procurement request created for {payload.product_name}",
            actor=current_user["username"],
            extra_data=json.dumps({
                "product_name": payload.product_name,
                "category": payload.category,
                "budget": payload.max_budget,
                "currency": payload.currency,
            }),
        ))
    except Exception:
        pass

    db.commit()
    db.refresh(db_req)

    return db_req


@router.post("/demo", response_model=schemas.ProcurementRequestResponse, tags=["Procurement"])
def run_demo(
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("admin", "officer")),
):
    """Officer-only: creates a sample request AND starts the pipeline immediately."""
    payload = schemas.ProcurementRequestCreate(
        product_name="Dell Latitude 7450 Business Laptops",
        category="IT Hardware",
        description="Refresh 40 business laptops for the sales team with docking stations.",
        quantity=40,
        max_budget=52000,
        currency="USD",
        required_features=["16GB RAM", "512GB SSD", "Wi-Fi 6E", "3-year warranty"],
        warranty_months=36,
        delivery_needed_by="2026-12-15",
        preferred_vendors=["Dell", "HP", "Lenovo"],
    )
    request_id = f"REQ-{uuid.uuid4().hex[:12].upper()}"
    db_req = db_models.ProcurementRequest(
        id=request_id,
        product_name=payload.product_name,
        category=payload.category,
        description=payload.description,
        quantity=payload.quantity,
        max_budget=payload.max_budget,
        currency=payload.currency,
        required_features=json.dumps(payload.required_features),
        warranty_months=payload.warranty_months,
        delivery_needed_by=payload.delivery_needed_by,
        preferred_vendors=json.dumps(payload.preferred_vendors),
        status=db_models.ProcurementStatus.PENDING,
    )
    db.add(db_req)
    db.commit()
    db.refresh(db_req)

    workflow_registry.create(request_id)
    background_tasks.add_task(run_workflow, request_id, payload.model_dump())
    return db_req


@router.get("/procurement-requests", response_model=List[schemas.ProcurementRequestResponse], tags=["Procurement"])
def list_procurement_requests(
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    status: Optional[str] = Query(None),
    search: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(db_models.ProcurementRequest)
    if status:
        try:
            status_enum = db_models.ProcurementStatus(status.lower())
            query = query.filter(db_models.ProcurementRequest.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    if search:
        query = query.filter(
            or_(
                db_models.ProcurementRequest.product_name.ilike(f"%{search}%"),
                db_models.ProcurementRequest.id.ilike(f"%{search}%"),
                db_models.ProcurementRequest.category.ilike(f"%{search}%"),
            )
        )
    query = query.order_by(desc(db_models.ProcurementRequest.created_at))
    return query.offset(skip).limit(limit).all()


@router.get("/procurement-requests/{request_id}", response_model=schemas.ProcurementRequestDetailResponse, tags=["Procurement"])
def get_procurement_request(request_id: str, db: Session = Depends(get_db)):
    req = db.query(db_models.ProcurementRequest).filter_by(id=request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Procurement request not found")
    return req


@router.post("/procurement-requests/{request_id}/start", tags=["Procurement"])
def start_workflow(
    request_id: str,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("admin", "officer")),
):
    req = db.query(db_models.ProcurementRequest).filter_by(id=request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Procurement request not found")

    if req.status == db_models.ProcurementStatus.IN_PROGRESS:
        raise HTTPException(status_code=409, detail="Workflow already in progress")

    # Reset status
    req.status = db_models.ProcurementStatus.PENDING
    req.current_stage = None
    db.commit()

    workflow_registry.create(request_id)

    payload = schemas.ProcurementRequestCreate(
        product_name=req.product_name,
        category=req.category,
        description=req.description or "",
        quantity=req.quantity,
        max_budget=req.max_budget,
        currency=req.currency,
        required_features=json.loads(req.required_features) if req.required_features else [],
        warranty_months=req.warranty_months,
        delivery_needed_by=req.delivery_needed_by,
        preferred_vendors=json.loads(req.preferred_vendors) if req.preferred_vendors else [],
    )

    background_tasks.add_task(run_workflow, request_id, payload.model_dump())

    return {"request_id": request_id, "status": "started"}


@router.get("/procurement-requests/{request_id}/status", tags=["Procurement"])
async def get_workflow_status_endpoint(request_id: str):
    status = await get_workflow_status(request_id)
    if not status:
        raise HTTPException(status_code=404, detail="Workflow not found")
    return status


@router.get("/procurement-requests/{request_id}/events", tags=["Procurement"])
async def stream_workflow_events(request_id: str):
    """Server-Sent Events stream for real-time workflow progress."""
    return StreamingResponse(
        stream_events(request_id),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
            "X-Accel-Buffering": "no",
        },
    )


# --- Comparison ---

@router.get("/vendor-comparisons", tags=["Comparison"])
def list_vendor_comparisons(db: Session = Depends(get_db)):
    """All vendor evaluations across every request, for the comparison page."""
    evaluations = db.query(db_models.EvaluationRecord).all()
    quotes = {q.id: q for q in db.query(db_models.QuoteRecord).all()}
    requests = {r.id: r for r in db.query(db_models.ProcurementRequest).all()}

    rows = []
    for e in evaluations:
        req = requests.get(e.request_id)
        quote = quotes.get(e.quote_id)
        is_revised = bool(quote.is_revised) if quote else False
        rows.append({
            "evaluation_id": e.id,
            "request_id": e.request_id,
            "product_name": req.product_name if req else None,
            "request_status": req.status.value if req and hasattr(req.status, "value") else None,
            "vendor_id": e.vendor_id,
            "vendor_name": e.vendor_name,
            "quote_id": e.quote_id,
            "total_amount": e.total_cost,
            "original_amount": quote.total_amount if quote else None,
            "discount_percent": quote.discount_percent if quote else 0,
            "negotiation_round": quote.negotiation_round if quote else 0,
            "is_revised": is_revised,
            "total_score": e.total_score,
            "price_score": e.price_score,
            "quality_score": e.quality_score,
            "review_score": e.review_score,
            "warranty_score": e.warranty_score,
            "delivery_score": e.delivery_score,
            "reliability_score": e.reliability_score,
            "budget_score": e.budget_score,
            "savings_vs_budget": e.savings_vs_budget,
            "reevaluated": e.reevaluated,
            "created_at": req.created_at if req else None,
        })

    rows.sort(key=lambda r: (str(r["created_at"] or ""), r["total_score"]), reverse=True)
    return rows


@router.get("/procurement-requests/{request_id}/comparison", tags=["Comparison"])
def get_comparison(request_id: str, db: Session = Depends(get_db)):
    req = db.query(db_models.ProcurementRequest).filter_by(id=request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Procurement request not found")

    vendors = db.query(db_models.VendorRecord).filter_by(request_id=request_id).all()
    quotes = db.query(db_models.QuoteRecord).filter_by(request_id=request_id).all()
    evaluations = db.query(db_models.EvaluationRecord).filter_by(request_id=request_id).all()

    # Build comparison data
    vendor_map = {v.id: v for v in vendors}
    comparison = []

    for e in evaluations:
        quote = next((q for q in quotes if q.id == e.quote_id), None)
        vendor = vendor_map.get(e.vendor_id)
        comparison.append({
            "vendor_id": e.vendor_id,
            "vendor_name": e.vendor_name,
            "quote_id": e.quote_id,
            "original_quote_id": quote.parent_quote_id if quote else None,
            "is_revised": quote.is_revised if quote else False,
            "negotiation_round": quote.negotiation_round if quote else 0,
            "total_amount": e.total_cost,
            "original_amount": quote.total_amount if quote else None,
            "discount_percent": quote.discount_percent if quote else 0,
            "total_score": e.total_score,
            "price_score": e.price_score,
            "quality_score": e.quality_score,
            "review_score": e.review_score,
            "warranty_score": e.warranty_score,
            "delivery_score": e.delivery_score,
            "reliability_score": e.reliability_score,
            "budget_score": e.budget_score,
            "savings_vs_budget": e.savings_vs_budget,
            "delivery_days": None,  # would need to parse quote items
            "warranty_months": None,
            "reevaluated": e.reevaluated,
            "details": json.loads(e.details) if e.details else None,
        })

    comparison.sort(key=lambda x: x["total_score"], reverse=True)

    return {
        "request_id": request_id,
        "criteria_weights": {
            "price": 0.25,
            "quality": 0.20,
            "review": 0.15,
            "warranty": 0.10,
            "delivery": 0.15,
            "reliability": 0.10,
            "budget": 0.05,
        },
        "comparison": comparison,
    }


# --- Negotiations ---

@router.get("/negotiations", tags=["Negotiations"])
def list_negotiations(db: Session = Depends(get_db)):
    """All negotiation records across every request, for the workspace page."""
    negotiations = (
        db.query(db_models.NegotiationRecord)
        .order_by(desc(db_models.NegotiationRecord.id))
        .all()
    )
    requests = {r.id: r for r in db.query(db_models.ProcurementRequest).all()}
    return [
        {
            "id": n.id,
            "request_id": n.request_id,
            "product_name": requests[n.request_id].product_name if n.request_id in requests else None,
            "request_status": (
                requests[n.request_id].status.value
                if n.request_id in requests and hasattr(requests[n.request_id].status, "value")
                else None
            ),
            "vendor_id": n.vendor_id,
            "vendor_name": n.vendor_name,
            "original_quote_id": n.original_quote_id,
            "revised_quote_id": n.revised_quote_id,
            "rounds": n.rounds,
            "final_discount_percent": n.final_discount_percent,
            "final_total_amount": n.final_total_amount,
            "savings_achieved": n.savings_achieved,
            "agreed_terms": n.agreed_terms,
            "success": n.success,
            "transcript": json.loads(n.transcript) if n.transcript else [],
        }
        for n in negotiations
    ]


@router.get("/procurement-requests/{request_id}/negotiations", tags=["Negotiations"])
def get_negotiations(request_id: str, db: Session = Depends(get_db)):
    req = db.query(db_models.ProcurementRequest).filter_by(id=request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Procurement request not found")

    negotiations = (
        db.query(db_models.NegotiationRecord)
        .filter_by(request_id=request_id)
        .order_by(db_models.NegotiationRecord.id)
        .all()
    )

    return [
        {
            "id": n.id,
            "vendor_id": n.vendor_id,
            "vendor_name": n.vendor_name,
            "original_quote_id": n.original_quote_id,
            "revised_quote_id": n.revised_quote_id,
            "rounds": n.rounds,
            "final_discount_percent": n.final_discount_percent,
            "final_total_amount": n.final_total_amount,
            "savings_achieved": n.savings_achieved,
            "agreed_terms": n.agreed_terms,
            "success": n.success,
            "transcript": json.loads(n.transcript) if n.transcript else [],
        }
        for n in negotiations
    ]


# --- Approvals ---

def _approval_payload(db: Session, approval: db_models.ApprovalRecord) -> dict:
    req = db.query(db_models.ProcurementRequest).filter_by(id=approval.request_id).first()
    decision = (
        db.query(db_models.DecisionRecord)
        .filter_by(request_id=approval.request_id)
        .order_by(desc(db_models.DecisionRecord.id))
        .first()
    )
    return {
        "id": approval.id,
        "request_id": approval.request_id,
        "product_name": req.product_name if req else None,
        "final_total_amount": decision.final_total_amount if decision else None,
        "total_score": decision.total_score if decision else None,
        "status": approval.status.value if hasattr(approval.status, "value") else approval.status,
        "decision": approval.decision,
        "reviewer_id": approval.reviewer_id,
        "reviewer_name": approval.reviewer_name,
        "reason": approval.reason,
        "decided_at": approval.decided_at,
        "created_at": approval.created_at,
    }


@router.get("/approvals", response_model=List[schemas.ApprovalResponse], tags=["Approvals"])
def get_approvals(
    status: Optional[str] = Query(None),
    db: Session = Depends(get_db),
):
    query = db.query(db_models.ApprovalRecord)
    if status:
        try:
            status_enum = db_models.ApprovalStatus(status.lower())
            query = query.filter(db_models.ApprovalRecord.status == status_enum)
        except ValueError:
            raise HTTPException(status_code=400, detail=f"Invalid status: {status}")
    approvals = query.order_by(desc(db_models.ApprovalRecord.created_at)).all()
    return [_approval_payload(db, a) for a in approvals]


@router.get("/approvals/{request_id}", response_model=schemas.ApprovalResponse, tags=["Approvals"])
def get_approval_for_request(request_id: str, db: Session = Depends(get_db)):
    approval = db.query(db_models.ApprovalRecord).filter_by(request_id=request_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval record not found")
    return _approval_payload(db, approval)


@router.post("/approvals/{request_id}/approve", tags=["Approvals"])
def approve_request(
    request_id: str,
    action: schemas.ApprovalAction,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("admin", "approver")),
):
    req = db.query(db_models.ProcurementRequest).filter_by(id=request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Procurement request not found")

    if current_user["role"] == "approver":
        decision = (
            db.query(db_models.DecisionRecord)
            .filter_by(request_id=request_id)
            .order_by(desc(db_models.DecisionRecord.id))
            .first()
        )
        limit = current_user.get("approval_limit") or 0
        if decision and decision.final_total_amount > limit:
            raise HTTPException(
                status_code=403,
                detail=(
                    f"Amount exceeds your approval limit of {limit:,.0f}. "
                    "Ask an administrator to approve this request."
                ),
            )

    approval = db.query(db_models.ApprovalRecord).filter_by(request_id=request_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval record not found")

    if approval.status != db_models.ApprovalStatus.PENDING:
        raise HTTPException(status_code=409, detail="Approval already decided")

    approval.status = db_models.ApprovalStatus.APPROVED
    approval.decision = "approve"
    approval.reviewer_name = action.reviewer_name
    approval.reviewer_id = action.reviewer_id
    approval.reason = action.reason
    approval.decided_at = datetime.utcnow().isoformat()

    req.status = db_models.ProcurementStatus.COMPLETED

    # Audit log (best-effort)
    try:
        db.add(db_models.AuditLog(
            id=str(uuid.uuid4()),
            request_id=request_id,
            event_type="approval_granted",
            event_description=f"Request approved by {action.reviewer_name}",
            actor=action.reviewer_name,
            extra_data=json.dumps({"decision": "approve", "reason": action.reason}),
        ))
    except Exception:
        pass

    db.commit()
    db.refresh(approval)

    return approval


@router.post("/approvals/{request_id}/reject", tags=["Approvals"])
def reject_request(
    request_id: str,
    action: schemas.ApprovalAction,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("admin", "approver")),
):
    req = db.query(db_models.ProcurementRequest).filter_by(id=request_id).first()
    if not req:
        raise HTTPException(status_code=404, detail="Procurement request not found")

    approval = db.query(db_models.ApprovalRecord).filter_by(request_id=request_id).first()
    if not approval:
        raise HTTPException(status_code=404, detail="Approval record not found")

    if approval.status != db_models.ApprovalStatus.PENDING:
        raise HTTPException(status_code=409, detail="Approval already decided")

    approval.status = db_models.ApprovalStatus.REJECTED
    approval.decision = "reject"
    approval.reviewer_name = action.reviewer_name
    approval.reviewer_id = action.reviewer_id
    approval.reason = action.reason
    approval.decided_at = datetime.utcnow().isoformat()

    req.status = db_models.ProcurementStatus.REJECTED

    # Audit log (best-effort)
    try:
        db.add(db_models.AuditLog(
            id=str(uuid.uuid4()),
            request_id=request_id,
            event_type="approval_rejected",
            event_description=f"Request rejected by {action.reviewer_name}",
            actor=action.reviewer_name,
            extra_data=json.dumps({"decision": "reject", "reason": action.reason}),
        ))
    except Exception:
        pass

    db.commit()
    db.refresh(approval)

    return approval


# --- Evaluation Weights ---

@router.get("/settings/evaluation-weights", response_model=schemas.EvaluationWeightsResponse, tags=["Settings"])
def get_evaluation_weights(db: Session = Depends(get_db)):
    weights = db.query(db_models.EvaluationWeight).all()
    if not weights:
        # Default weights from BuyWise config
        default_weights = {
            "price": 0.25,
            "quality": 0.20,
            "review": 0.15,
            "warranty": 0.10,
            "delivery": 0.15,
            "reliability": 0.10,
            "budget": 0.05,
        }
        for criterion, weight in default_weights.items():
            db.add(db_models.EvaluationWeight(criterion=criterion, weight=weight))
        db.commit()
        return {"weights": default_weights}
    return {"weights": {w.criterion: w.weight for w in weights}}


@router.put("/settings/evaluation-weights", response_model=schemas.EvaluationWeightsResponse, tags=["Settings"])
def update_evaluation_weights(
    payload: schemas.EvaluationWeightsUpdate,
    db: Session = Depends(get_db),
    current_user: dict = Depends(require_roles("admin")),
):
    weights = payload.weights
    total = sum(weights.values())
    if abs(total - 1.0) > 1e-6:
        raise HTTPException(
            status_code=400,
            detail=f"Weights must sum to 1.0, got {total}",
        )

    for criterion, weight in weights.items():
        if weight < 0 or weight > 1:
            raise HTTPException(
                status_code=400,
                detail=f"Weight for {criterion} must be between 0 and 1",
            )
        existing = db.query(db_models.EvaluationWeight).filter_by(criterion=criterion).first()
        if existing:
            existing.weight = weight
            existing.updated_by = "api_user"
        else:
            db.add(db_models.EvaluationWeight(criterion=criterion, weight=weight))

    db.commit()

    return {"weights": weights}


# --- Audit Logs ---

@router.get("/audit-logs", response_model=List[schemas.AuditLogResponse], tags=["Audit"])
def get_audit_logs(
    request_id: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    query = db.query(db_models.AuditLog)
    if request_id:
        query = query.filter_by(request_id=request_id)
    return query.order_by(desc(db_models.AuditLog.created_at)).offset(skip).limit(limit).all()