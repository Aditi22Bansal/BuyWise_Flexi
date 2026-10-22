"""Initial migration

Revision ID: 0001
Revises:
Create Date: 2026-10-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "procurement_requests",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("product_name", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("quantity", sa.Integer(), nullable=False),
        sa.Column("max_budget", sa.Float(), nullable=False),
        sa.Column("currency", sa.String(), nullable=True),
        sa.Column("required_features", sa.Text(), nullable=True),
        sa.Column("warranty_months", sa.Integer(), nullable=True),
        sa.Column("delivery_needed_by", sa.String(), nullable=True),
        sa.Column("preferred_vendors", sa.Text(), nullable=True),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("current_stage", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_procurement_requests_id"), "procurement_requests", ["id"], unique=False)

    op.create_table(
        "products",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("request_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("category", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("base_price", sa.Float(), nullable=False),
        sa.Column("quality_score", sa.Float(), nullable=False),
        sa.Column("review_score", sa.Float(), nullable=False),
        sa.Column("features", sa.Text(), nullable=True),
        sa.Column("warranty_months", sa.Integer(), nullable=True),
        sa.Column("manufacturer", sa.String(), nullable=True),
        sa.Column("datasheet_url", sa.String(), nullable=True),
        sa.Column("metadata", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["request_id"], ["procurement_requests.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "vendors",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("request_id", sa.String(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("contact_email", sa.String(), nullable=False),
        sa.Column("contact_phone", sa.String(), nullable=True),
        sa.Column("portal_url", sa.String(), nullable=True),
        sa.Column("reliability_score", sa.Float(), nullable=False),
        sa.Column("average_delivery_days", sa.Integer(), nullable=False),
        sa.Column("payment_terms", sa.String(), nullable=True),
        sa.Column("min_order_quantity", sa.Integer(), nullable=True),
        sa.Column("active", sa.Boolean(), nullable=True),
        sa.Column("metadata", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["request_id"], ["procurement_requests.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "quotes",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("request_id", sa.String(), nullable=False),
        sa.Column("vendor_id", sa.String(), nullable=False),
        sa.Column("vendor_name", sa.String(), nullable=False),
        sa.Column("total_amount", sa.Float(), nullable=False),
        sa.Column("status", sa.String(), nullable=False),
        sa.Column("valid_until", sa.String(), nullable=True),
        sa.Column("terms", sa.String(), nullable=True),
        sa.Column("discount_percent", sa.Float(), nullable=True),
        sa.Column("negotiation_round", sa.Integer(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=True),
        sa.Column("items", sa.Text(), nullable=True),
        sa.Column("parent_quote_id", sa.String(), nullable=True),
        sa.Column("is_revised", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["request_id"], ["procurement_requests.id"], ),
        sa.ForeignKeyConstraint(["vendor_id"], ["vendors.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "evaluations",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("request_id", sa.String(), nullable=False),
        sa.Column("vendor_id", sa.String(), nullable=False),
        sa.Column("vendor_name", sa.String(), nullable=False),
        sa.Column("quote_id", sa.String(), nullable=False),
        sa.Column("total_score", sa.Float(), nullable=False),
        sa.Column("price_score", sa.Float(), nullable=False),
        sa.Column("quality_score", sa.Float(), nullable=False),
        sa.Column("review_score", sa.Float(), nullable=False),
        sa.Column("warranty_score", sa.Float(), nullable=False),
        sa.Column("delivery_score", sa.Float(), nullable=False),
        sa.Column("reliability_score", sa.Float(), nullable=False),
        sa.Column("budget_score", sa.Float(), nullable=False),
        sa.Column("total_cost", sa.Float(), nullable=False),
        sa.Column("savings_vs_budget", sa.Float(), nullable=False),
        sa.Column("details", sa.Text(), nullable=True),
        sa.Column("reevaluated", sa.Boolean(), nullable=True),
        sa.ForeignKeyConstraint(["request_id"], ["procurement_requests.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "negotiations",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("request_id", sa.String(), nullable=False),
        sa.Column("vendor_id", sa.String(), nullable=False),
        sa.Column("vendor_name", sa.String(), nullable=False),
        sa.Column("original_quote_id", sa.String(), nullable=False),
        sa.Column("revised_quote_id", sa.String(), nullable=True),
        sa.Column("rounds", sa.Integer(), nullable=False),
        sa.Column("final_discount_percent", sa.Float(), nullable=False),
        sa.Column("final_total_amount", sa.Float(), nullable=False),
        sa.Column("savings_achieved", sa.Float(), nullable=False),
        sa.Column("agreed_terms", sa.String(), nullable=True),
        sa.Column("success", sa.Boolean(), nullable=False),
        sa.Column("transcript", sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(["request_id"], ["procurement_requests.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "decisions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("request_id", sa.String(), nullable=False),
        sa.Column("recommended_vendor_id", sa.String(), nullable=True),
        sa.Column("recommended_vendor_name", sa.String(), nullable=True),
        sa.Column("recommended_quote_id", sa.String(), nullable=True),
        sa.Column("final_total_amount", sa.Float(), nullable=False),
        sa.Column("total_score", sa.Float(), nullable=False),
        sa.Column("decision", sa.String(), nullable=False),
        sa.Column("reasoning", sa.Text(), nullable=False),
        sa.Column("requires_human_approval", sa.Boolean(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["request_id"], ["procurement_requests.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "approvals",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("request_id", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("decision", sa.String(), nullable=True),
        sa.Column("reviewer_id", sa.String(), nullable=True),
        sa.Column("reviewer_name", sa.String(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("decided_at", sa.String(), nullable=True),
        sa.Column("created_at", sa.String(), nullable=True),
        sa.ForeignKeyConstraint(["request_id"], ["procurement_requests.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "agent_executions",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("request_id", sa.String(), nullable=False),
        sa.Column("agent_name", sa.String(), nullable=False),
        sa.Column("status", sa.String(), nullable=True),
        sa.Column("started_at", sa.String(), nullable=True),
        sa.Column("completed_at", sa.String(), nullable=True),
        sa.Column("output_summary", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("execution_order", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["request_id"], ["procurement_requests.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "audit_logs",
        sa.Column("id", sa.String(), nullable=False),
        sa.Column("request_id", sa.String(), nullable=True),
        sa.Column("event_type", sa.String(), nullable=False),
        sa.Column("event_description", sa.Text(), nullable=False),
        sa.Column("actor", sa.String(), nullable=True),
        sa.Column("metadata", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=True),
        sa.ForeignKeyConstraint(["request_id"], ["procurement_requests.id"], ),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_table(
        "evaluation_weights",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("criterion", sa.String(), nullable=False),
        sa.Column("weight", sa.Float(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("updated_by", sa.String(), nullable=True),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("criterion"),
    )


def downgrade() -> None:
    op.drop_table("evaluation_weights")
    op.drop_table("audit_logs")
    op.drop_table("agent_executions")
    op.drop_table("approvals")
    op.drop_table("decisions")
    op.drop_table("negotiations")
    op.drop_table("evaluations")
    op.drop_table("quotes")
    op.drop_table("vendors")
    op.drop_table("products")
    op.drop_index(op.f("ix_procurement_requests_id"), table_name="procurement_requests")
    op.drop_table("procurement_requests")