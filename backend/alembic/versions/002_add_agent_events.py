"""Add agent_events table.

Revision ID: 002
Revises: 001
"""

from alembic import op
import sqlalchemy as sa

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "agent_events",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("site_id", sa.Integer(), sa.ForeignKey("sites.id"), nullable=False, index=True),
        sa.Column("agent_name", sa.String(100), nullable=False, index=True),
        sa.Column("user_agent", sa.String(1024), nullable=False),
        sa.Column("method", sa.String(10), nullable=False),
        sa.Column("path", sa.String(2048), nullable=False),
        sa.Column("status_code", sa.Integer(), nullable=False),
        sa.Column("duration_ms", sa.Float(), nullable=False),
        sa.Column("content_type", sa.String(255), nullable=True),
        sa.Column("response_size", sa.Integer(), nullable=True),
        sa.Column("event_timestamp", sa.DateTime(timezone=True), nullable=False, index=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade() -> None:
    op.drop_table("agent_events")
