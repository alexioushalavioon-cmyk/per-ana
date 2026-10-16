"""analysis engine
Revision ID: 0004_analysis_engine
Revises: 0003_actor_intelligence
"""
from alembic import op
import sqlalchemy as sa
revision='0004_analysis_engine'; down_revision='0003_actor_intelligence'; branch_labels=None; depends_on=None

def upgrade():
    op.add_column('actor_objectives', sa.Column('objective_key', sa.String(length=160), nullable=True))
    op.add_column('actor_objectives', sa.Column('stance', sa.Integer(), nullable=True))
    op.create_index('ix_actor_objectives_objective_key','actor_objectives',['objective_key'])
    op.create_table('analysis_runs',
        sa.Column('id',sa.String(64),primary_key=True), sa.Column('case_id',sa.String(64),sa.ForeignKey('cases.id',ondelete='CASCADE'),nullable=False),
        sa.Column('created_by',sa.String(64),sa.ForeignKey('users.id',ondelete='CASCADE'),nullable=False), sa.Column('status',sa.String(32),nullable=False),
        sa.Column('primary_method',sa.String(80),nullable=False), sa.Column('supporting_methods',sa.JSON(),nullable=False), sa.Column('analytical_question',sa.String(120),nullable=False),
        sa.Column('input_snapshot',sa.JSON(),nullable=False), sa.Column('output_json',sa.JSON(),nullable=False), sa.Column('confidence',sa.Float(),nullable=False),
        sa.Column('created_at',sa.DateTime(timezone=True),nullable=False), sa.Column('updated_at',sa.DateTime(timezone=True),nullable=False))
    op.create_index('ix_analysis_runs_case_id','analysis_runs',['case_id']); op.create_index('ix_analysis_runs_created_by','analysis_runs',['created_by'])

def downgrade():
    op.drop_table('analysis_runs'); op.drop_index('ix_actor_objectives_objective_key',table_name='actor_objectives'); op.drop_column('actor_objectives','stance'); op.drop_column('actor_objectives','objective_key')
