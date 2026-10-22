"""Align persisted metadata column names with ORM models."""

from alembic import op


revision = "0002"
down_revision = "0001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.alter_column("products", "metadata", new_column_name="extra_data")
    op.alter_column("vendors", "metadata", new_column_name="extra_data")
    op.alter_column("audit_logs", "metadata", new_column_name="extra_data")


def downgrade() -> None:
    op.alter_column("audit_logs", "extra_data", new_column_name="metadata")
    op.alter_column("vendors", "extra_data", new_column_name="metadata")
    op.alter_column("products", "extra_data", new_column_name="metadata")
