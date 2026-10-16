"""actor intelligence engine

Revision ID: 0003_actor_intelligence
Revises: 0002_research_evidence
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_actor_intelligence"
down_revision = "0002_research_evidence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table("actors",
        sa.Column("id", sa.String(64), primary_key=True),
        sa.Column("case_id", sa.String(64), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("canonical_name", sa.String(500), nullable=False),
        sa.Column("normalized_name", sa.String(500), nullable=False),
        sa.Column("actor_type", sa.String(80), nullable=False, server_default="unknown"),
        sa.Column("status", sa.String(32), nullable=False, server_default="suggested"),
        sa.Column("discovery_type", sa.String(32), nullable=False, server_default="explicit"),
        sa.Column("parent_actor_id", sa.String(64), sa.ForeignKey("actors.id", ondelete="SET NULL"), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("strategic_importance", sa.String(24), nullable=False, server_default="unknown"),
        sa.Column("overall_confidence", sa.Float(), nullable=False, server_default="0.5"),
        sa.Column("is_hidden_candidate", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("merged_into_id", sa.String(64), sa.ForeignKey("actors.id", ondelete="SET NULL"), nullable=True),
        sa.Column("metadata_json", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    for col in ["case_id","canonical_name","normalized_name","actor_type","status","parent_actor_id"]: op.create_index(f"ix_actors_{col}", "actors", [col])

    op.create_table("actor_aliases",
        sa.Column("id", sa.String(64), primary_key=True), sa.Column("case_id", sa.String(64), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("actor_id", sa.String(64), sa.ForeignKey("actors.id", ondelete="CASCADE"), nullable=False), sa.Column("alias", sa.String(500), nullable=False),
        sa.Column("normalized_alias", sa.String(500), nullable=False), sa.Column("alias_type", sa.String(32), nullable=False, server_default="mention"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="0.8"), sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("case_id", "normalized_alias", name="uq_actor_alias_case_normalized"),
    )
    op.create_index("ix_actor_aliases_case_id", "actor_aliases", ["case_id"]); op.create_index("ix_actor_aliases_actor_id", "actor_aliases", ["actor_id"]); op.create_index("ix_actor_aliases_normalized_alias", "actor_aliases", ["normalized_alias"])

    def component_table(name, columns):
        op.create_table(name, sa.Column("id", sa.String(64), primary_key=True), sa.Column("actor_id", sa.String(64), sa.ForeignKey("actors.id", ondelete="CASCADE"), nullable=False), *columns, sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False))
        op.create_index(f"ix_{name}_actor_id", name, ["actor_id"])

    component_table("actor_evidence_links", [sa.Column("evidence_id", sa.String(64), sa.ForeignKey("evidence.id", ondelete="CASCADE"), nullable=False), sa.Column("link_type", sa.String(40), nullable=False, server_default="mention"), sa.Column("confidence", sa.Float(), nullable=False, server_default="0.8"), sa.UniqueConstraint("actor_id","evidence_id", name="uq_actor_evidence")])
    op.create_index("ix_actor_evidence_links_evidence_id", "actor_evidence_links", ["evidence_id"])
    component_table("actor_roles", [sa.Column("role", sa.String(100), nullable=False), sa.Column("confidence", sa.Float(), nullable=False, server_default="0.5"), sa.Column("evidence_ids", sa.JSON(), nullable=False), sa.Column("status", sa.String(32), nullable=False, server_default="inferred")]); op.create_index("ix_actor_roles_role", "actor_roles", ["role"])
    component_table("actor_interests", [sa.Column("interest", sa.Text(), nullable=False), sa.Column("interest_type", sa.String(80), nullable=False), sa.Column("importance", sa.String(24), nullable=False), sa.Column("stated_or_inferred", sa.String(24), nullable=False), sa.Column("confidence", sa.Float(), nullable=False), sa.Column("evidence_ids", sa.JSON(), nullable=False)])
    component_table("actor_objectives", [sa.Column("objective", sa.Text(), nullable=False), sa.Column("importance", sa.String(24), nullable=False), sa.Column("time_horizon", sa.String(40)), sa.Column("stated_or_inferred", sa.String(24), nullable=False), sa.Column("policy_relevance", sa.String(100)), sa.Column("confidence", sa.Float(), nullable=False), sa.Column("evidence_ids", sa.JSON(), nullable=False)])
    component_table("actor_power_dimensions", [sa.Column("dimension", sa.String(80), nullable=False), sa.Column("level", sa.String(24), nullable=False), sa.Column("potential_level", sa.String(24)), sa.Column("exercised_level", sa.String(24)), sa.Column("rationale", sa.Text()), sa.Column("confidence", sa.Float(), nullable=False), sa.Column("evidence_ids", sa.JSON(), nullable=False), sa.UniqueConstraint("actor_id","dimension", name="uq_actor_power_dimension")]); op.create_index("ix_actor_power_dimensions_dimension", "actor_power_dimensions", ["dimension"])
    component_table("actor_positions", [sa.Column("policy_key", sa.String(160), nullable=False), sa.Column("declared_position", sa.String(40)), sa.Column("observed_behaviour", sa.String(120)), sa.Column("inferred_position", sa.String(40), nullable=False), sa.Column("position_behaviour_gap", sa.Boolean(), nullable=False), sa.Column("rationale", sa.Text()), sa.Column("confidence", sa.Float(), nullable=False), sa.Column("evidence_ids", sa.JSON(), nullable=False)]); op.create_index("ix_actor_positions_policy_key", "actor_positions", ["policy_key"])
    component_table("actor_constraints", [sa.Column("constraint_type", sa.String(80), nullable=False), sa.Column("description", sa.Text(), nullable=False), sa.Column("severity", sa.String(24), nullable=False), sa.Column("confidence", sa.Float(), nullable=False), sa.Column("evidence_ids", sa.JSON(), nullable=False)])
    op.create_table("actor_relationships",
        sa.Column("id", sa.String(64), primary_key=True), sa.Column("case_id", sa.String(64), sa.ForeignKey("cases.id", ondelete="CASCADE"), nullable=False),
        sa.Column("source_actor_id", sa.String(64), sa.ForeignKey("actors.id", ondelete="CASCADE"), nullable=False), sa.Column("target_actor_id", sa.String(64), sa.ForeignKey("actors.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relationship_type", sa.String(80), nullable=False), sa.Column("direction", sa.String(24), nullable=False), sa.Column("strength", sa.String(24), nullable=False), sa.Column("formality", sa.String(24), nullable=False),
        sa.Column("rationale", sa.Text()), sa.Column("confidence", sa.Float(), nullable=False), sa.Column("evidence_ids", sa.JSON(), nullable=False), sa.Column("status", sa.String(32), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False), sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    for col in ["case_id","source_actor_id","target_actor_id","relationship_type"]: op.create_index(f"ix_actor_relationships_{col}", "actor_relationships", [col])


def downgrade() -> None:
    for table in ["actor_relationships","actor_constraints","actor_positions","actor_power_dimensions","actor_objectives","actor_interests","actor_roles","actor_evidence_links","actor_aliases","actors"]:
        op.drop_table(table)
