"""policy strategy engine

Revision ID: 0005_policy_strategy
Revises: 0004_analysis_engine
"""
from alembic import op
import sqlalchemy as sa

revision = '0005_policy_strategy'
down_revision = '0004_analysis_engine'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table('policy_options',
        sa.Column('id',sa.String(64),primary_key=True), sa.Column('case_id',sa.String(64),sa.ForeignKey('cases.id',ondelete='CASCADE'),nullable=False),
        sa.Column('created_by',sa.String(64),sa.ForeignKey('users.id',ondelete='CASCADE'),nullable=False), sa.Column('policy_key',sa.String(160),nullable=False),
        sa.Column('title',sa.String(300),nullable=False), sa.Column('description',sa.Text(),nullable=False), sa.Column('goal',sa.Text(),nullable=False),
        sa.Column('instruments',sa.JSON(),nullable=False), sa.Column('assumptions',sa.JSON(),nullable=False), sa.Column('constraints',sa.JSON(),nullable=False),
        sa.Column('status',sa.String(32),nullable=False), sa.Column('created_at',sa.DateTime(timezone=True),nullable=False), sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False))
    op.create_index('ix_policy_options_case_id','policy_options',['case_id']); op.create_index('ix_policy_options_created_by','policy_options',['created_by']); op.create_index('ix_policy_options_policy_key','policy_options',['policy_key'])
    op.create_table('policy_actor_impacts',
        sa.Column('id',sa.String(64),primary_key=True),sa.Column('policy_option_id',sa.String(64),sa.ForeignKey('policy_options.id',ondelete='CASCADE'),nullable=False),sa.Column('actor_id',sa.String(64),sa.ForeignKey('actors.id',ondelete='CASCADE'),nullable=False),
        sa.Column('direction',sa.String(24),nullable=False),sa.Column('magnitude',sa.String(24),nullable=False),sa.Column('dimensions',sa.JSON(),nullable=False),sa.Column('rationale',sa.Text(),nullable=False),sa.Column('evidence_ids',sa.JSON(),nullable=False),sa.Column('confidence',sa.Float(),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False))
    op.create_index('ix_policy_actor_impacts_policy_option_id','policy_actor_impacts',['policy_option_id']);op.create_index('ix_policy_actor_impacts_actor_id','policy_actor_impacts',['actor_id'])
    op.create_table('actor_reactions',
        sa.Column('id',sa.String(64),primary_key=True),sa.Column('policy_option_id',sa.String(64),sa.ForeignKey('policy_options.id',ondelete='CASCADE'),nullable=False),sa.Column('actor_id',sa.String(64),sa.ForeignKey('actors.id',ondelete='CASCADE'),nullable=False),sa.Column('expected_position',sa.String(40),nullable=False),sa.Column('expected_reaction',sa.String(80),nullable=False),sa.Column('trigger',sa.Text()),sa.Column('motivation',sa.Text()),sa.Column('capability',sa.String(24),nullable=False),sa.Column('expected_impact',sa.String(24),nullable=False),sa.Column('evidence_ids',sa.JSON(),nullable=False),sa.Column('confidence',sa.Float(),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False))
    op.create_index('ix_actor_reactions_policy_option_id','actor_reactions',['policy_option_id']);op.create_index('ix_actor_reactions_actor_id','actor_reactions',['actor_id'])
    op.create_table('strategic_leverages',
        sa.Column('id',sa.String(64),primary_key=True),sa.Column('policy_option_id',sa.String(64),sa.ForeignKey('policy_options.id',ondelete='CASCADE'),nullable=False),sa.Column('actor_id',sa.String(64),sa.ForeignKey('actors.id',ondelete='CASCADE'),nullable=False),sa.Column('leverage_type',sa.String(80),nullable=False),sa.Column('description',sa.Text(),nullable=False),sa.Column('basis',sa.Text(),nullable=False),sa.Column('evidence_ids',sa.JSON(),nullable=False),sa.Column('confidence',sa.Float(),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False))
    op.create_index('ix_strategic_leverages_policy_option_id','strategic_leverages',['policy_option_id']);op.create_index('ix_strategic_leverages_actor_id','strategic_leverages',['actor_id'])
    op.create_table('strategy_recommendations',
        sa.Column('id',sa.String(64),primary_key=True),sa.Column('policy_option_id',sa.String(64),sa.ForeignKey('policy_options.id',ondelete='CASCADE'),nullable=False),sa.Column('target_actor_id',sa.String(64),sa.ForeignKey('actors.id',ondelete='SET NULL')),sa.Column('action',sa.Text(),nullable=False),sa.Column('problem_addressed',sa.Text(),nullable=False),sa.Column('actor_logic',sa.Text(),nullable=False),sa.Column('expected_effect',sa.Text(),nullable=False),sa.Column('risks',sa.JSON(),nullable=False),sa.Column('tradeoffs',sa.JSON(),nullable=False),sa.Column('evidence_ids',sa.JSON(),nullable=False),sa.Column('priority',sa.String(24),nullable=False),sa.Column('confidence',sa.Float(),nullable=False),sa.Column('validation_status',sa.String(32),nullable=False),sa.Column('critique',sa.JSON(),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False))
    op.create_index('ix_strategy_recommendations_policy_option_id','strategy_recommendations',['policy_option_id']);op.create_index('ix_strategy_recommendations_target_actor_id','strategy_recommendations',['target_actor_id'])
    op.create_table('strategy_runs',
        sa.Column('id',sa.String(64),primary_key=True),sa.Column('case_id',sa.String(64),sa.ForeignKey('cases.id',ondelete='CASCADE'),nullable=False),sa.Column('policy_option_id',sa.String(64),sa.ForeignKey('policy_options.id',ondelete='CASCADE'),nullable=False),sa.Column('created_by',sa.String(64),sa.ForeignKey('users.id',ondelete='CASCADE'),nullable=False),sa.Column('status',sa.String(32),nullable=False),sa.Column('processing_mode',sa.String(32),nullable=False),sa.Column('output_json',sa.JSON(),nullable=False),sa.Column('confidence',sa.Float(),nullable=False),sa.Column('validated',sa.Boolean(),nullable=False),sa.Column('created_at',sa.DateTime(timezone=True),nullable=False),sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False))
    op.create_index('ix_strategy_runs_case_id','strategy_runs',['case_id']);op.create_index('ix_strategy_runs_policy_option_id','strategy_runs',['policy_option_id']);op.create_index('ix_strategy_runs_created_by','strategy_runs',['created_by'])


def downgrade():
    for t in ['strategy_runs','strategy_recommendations','strategic_leverages','actor_reactions','policy_actor_impacts','policy_options']:
        op.drop_table(t)
