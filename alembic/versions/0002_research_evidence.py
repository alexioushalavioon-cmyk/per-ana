"""research and evidence engine

Revision ID: 0002_research_evidence
Revises: 0001_initial
Create Date: 2026-10-15
"""
from typing import Sequence, Union
import sqlalchemy as sa
from alembic import op

revision: str = "0002_research_evidence"
down_revision: Union[str, None] = "0001_initial"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "research_plans",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("case_id", sa.String(64), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_by", sa.String(64), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("objective", sa.Text(), nullable=False),
        sa.Column("queries", sa.JSON(), nullable=False),
        sa.Column("source_types", sa.JSON(), nullable=False),
        sa.Column("priority_actors", sa.JSON(), nullable=False),
        sa.Column("processing_level", sa.String(32), nullable=False),
        sa.Column("max_sources", sa.Integer(), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_research_plans_case_id", "research_plans", ["case_id"])
    op.create_index("ix_research_plans_created_by", "research_plans", ["created_by"])

    op.create_table(
        "sources",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("case_id", sa.String(64), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("research_plan_id", sa.String(64), sa.ForeignKey("research_plans.id", ondelete="SET NULL")),
        sa.Column("added_by", sa.String(64), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("source_type", sa.String(48), nullable=False),
        sa.Column("title", sa.String(700), nullable=False),
        sa.Column("url", sa.String(2000)),
        sa.Column("canonical_url", sa.String(2000)),
        sa.Column("publisher", sa.String(500)),
        sa.Column("published_at", sa.DateTime(timezone=True)),
        sa.Column("retrieved_at", sa.DateTime(timezone=True)),
        sa.Column("access_method", sa.String(48), nullable=False),
        sa.Column("reliability", sa.String(24), nullable=False),
        sa.Column("raw_text", sa.Text()),
        sa.Column("content_hash", sa.String(64)),
        sa.Column("duplicate_of_id", sa.String(64), sa.ForeignKey("sources.id", ondelete="SET NULL")),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    for name, cols in [
        ("ix_sources_case_id", ["case_id"]), ("ix_sources_research_plan_id", ["research_plan_id"]),
        ("ix_sources_added_by", ["added_by"]), ("ix_sources_source_type", ["source_type"]),
        ("ix_sources_canonical_url", ["canonical_url"]), ("ix_sources_content_hash", ["content_hash"]),
        ("ix_sources_duplicate_of_id", ["duplicate_of_id"]),
    ]:
        op.create_index(name, "sources", cols)

    op.create_table(
        "evidence",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("case_id", sa.String(64), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_id", sa.String(64), sa.ForeignKey("sources.id", ondelete="CASCADE"), nullable=False),
        sa.Column("created_by", sa.String(64), sa.ForeignKey("users.id", ondelete="RESTRICT"), nullable=False),
        sa.Column("claim_text", sa.Text(), nullable=False),
        sa.Column("evidence_type", sa.String(48), nullable=False),
        sa.Column("claim_key", sa.String(240)),
        sa.Column("stance", sa.String(24), nullable=False),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("source_locator", sa.String(500)),
        sa.Column("date_context", sa.DateTime(timezone=True)),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("metadata_json", sa.JSON()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    for name, cols in [
        ("ix_evidence_case_id", ["case_id"]), ("ix_evidence_source_id", ["source_id"]),
        ("ix_evidence_created_by", ["created_by"]), ("ix_evidence_evidence_type", ["evidence_type"]),
        ("ix_evidence_claim_key", ["claim_key"]), ("ix_evidence_stance", ["stance"]),
    ]:
        op.create_index(name, "evidence", cols)

    op.create_table(
        "evidence_actor_mentions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("evidence_id", sa.String(64), sa.ForeignKey("evidence.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_label", sa.String(500), nullable=False),
        sa.Column("actor_type", sa.String(80)),
        sa.Column("mention_role", sa.String(80)),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_evidence_actor_mentions_evidence_id", "evidence_actor_mentions", ["evidence_id"])
    op.create_index("ix_evidence_actor_mentions_actor_label", "evidence_actor_mentions", ["actor_label"])

    op.create_table(
        "contradictions",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("case_id", sa.String(64), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("claim_key", sa.String(240), nullable=False),
        sa.Column("evidence_ids", sa.JSON(), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("severity", sa.String(24), nullable=False),
        sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_contradictions_case_id", "contradictions", ["case_id"])
    op.create_index("ix_contradictions_claim_key", "contradictions", ["claim_key"])


def downgrade() -> None:
    op.drop_table("contradictions")
    op.drop_table("evidence_actor_mentions")
    op.drop_table("evidence")
    op.drop_table("sources")
    op.drop_table("research_plans")
