"""admin governance and guardrails

Revision ID: 0007_admin_guardrails
Revises: 0006_report_engine
"""
from alembic import op
import sqlalchemy as sa

revision = "0007_admin_guardrails"
down_revision = "0006_report_engine"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("users", sa.Column("platform_role", sa.String(length=40), nullable=False, server_default="user"))
    op.add_column("users", sa.Column("account_status", sa.String(length=32), nullable=False, server_default="active"))
    op.add_column("users", sa.Column("accepted_policy_version", sa.String(length=32), nullable=True))
    op.create_index("ix_users_platform_role", "users", ["platform_role"])
    op.create_index("ix_users_account_status", "users", ["account_status"])

    op.create_table(
        "usage_policy_versions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("version", sa.String(32), nullable=False, unique=True),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("summary_fa", sa.Text(), nullable=False),
        sa.Column("rules_json", sa.JSON(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_usage_policy_versions_version", "usage_policy_versions", ["version"])

    op.create_table(
        "guardrail_events",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("case_id", sa.String(64), sa.ForeignKey("cases.id", ondelete="SET NULL"), nullable=True),
        sa.Column("category", sa.String(80), nullable=False),
        sa.Column("decision", sa.String(32), nullable=False),
        sa.Column("confidence", sa.String(16), nullable=False, server_default="medium"),
        sa.Column("input_excerpt", sa.Text(), nullable=False),
        sa.Column("reason_code", sa.String(120), nullable=False),
        sa.Column("repeated_pattern", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("reviewer_status", sa.String(32), nullable=False, server_default="unreviewed"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_guardrail_events_user_id", "guardrail_events", ["user_id"])
    op.create_index("ix_guardrail_events_case_id", "guardrail_events", ["case_id"])
    op.create_index("ix_guardrail_events_category", "guardrail_events", ["category"])
    op.create_index("ix_guardrail_events_decision", "guardrail_events", ["decision"])

    op.create_table(
        "privileged_access_requests",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("requester_user_id", sa.String(64), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("target_user_id", sa.String(64), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("scope", sa.String(64), nullable=False, server_default="full_user"),
        sa.Column("status", sa.String(32), nullable=False, server_default="approved"),
        sa.Column("approved_by_user_id", sa.String(64), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("export_storage_key", sa.String(800), nullable=True),
        sa.Column("export_sha256", sa.String(64), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_privileged_access_requests_requester", "privileged_access_requests", ["requester_user_id"])
    op.create_index("ix_privileged_access_requests_target", "privileged_access_requests", ["target_user_id"])

    op.create_table(
        "account_enforcements",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("user_id", sa.String(64), sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("action", sa.String(32), nullable=False),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column("applied_by_user_id", sa.String(64), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("details", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_account_enforcements_user_id", "account_enforcements", ["user_id"])


def downgrade() -> None:
    op.drop_table("account_enforcements")
    op.drop_table("privileged_access_requests")
    op.drop_table("guardrail_events")
    op.drop_table("usage_policy_versions")
    op.drop_index("ix_users_account_status", table_name="users")
    op.drop_index("ix_users_platform_role", table_name="users")
    op.drop_column("users", "accepted_policy_version")
    op.drop_column("users", "account_status")
    op.drop_column("users", "platform_role")
