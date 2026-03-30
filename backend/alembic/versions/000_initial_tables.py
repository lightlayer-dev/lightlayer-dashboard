"""create initial tables (users, sites, scans, check_results, api_keys)

Revision ID: 000_initial_tables
Revises:
Create Date: 2026-03-30
"""

from alembic import op
import sqlalchemy as sa

revision = "000_initial_tables"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # ── users ────────────────────────────────────────────────────────────
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("email", sa.String(255), unique=True, index=True, nullable=False),
        sa.Column("hashed_password", sa.String(255), nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── sites ────────────────────────────────────────────────────────────
    op.create_table(
        "sites",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), index=True, nullable=True),
        sa.Column("url", sa.String(2048), unique=True, index=True, nullable=False),
        sa.Column("name", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── scans ────────────────────────────────────────────────────────────
    op.create_table(
        "scans",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("site_id", sa.Integer(), sa.ForeignKey("sites.id"), index=True, nullable=False),
        sa.Column("overall_score", sa.Float(), nullable=False),
        sa.Column("source", sa.String(50), nullable=False, server_default="api"),
        sa.Column("commit_sha", sa.String(40), nullable=True),
        sa.Column("branch", sa.String(255), nullable=True),
        sa.Column("raw_json", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

    # ── check_results ────────────────────────────────────────────────────
    op.create_table(
        "check_results",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("scan_id", sa.Integer(), sa.ForeignKey("scans.id"), index=True, nullable=False),
        sa.Column("check_name", sa.String(50), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("findings_json", sa.Text(), nullable=True),
        sa.Column("details_json", sa.Text(), nullable=True),
    )

    # ── api_keys ─────────────────────────────────────────────────────────
    op.create_table(
        "api_keys",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.Integer(), sa.ForeignKey("users.id"), index=True, nullable=True),
        sa.Column("key_hash", sa.String(255), unique=True, index=True, nullable=False),
        sa.Column("key_prefix", sa.String(10), nullable=False),
        sa.Column("name", sa.String(255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("api_keys")
    op.drop_table("check_results")
    op.drop_table("scans")
    op.drop_table("sites")
    op.drop_table("users")
