"""report engine

Revision ID: 0006_report_engine
Revises: 0005_policy_strategy
"""
from alembic import op
import sqlalchemy as sa

revision = '0006_report_engine'
down_revision = '0005_policy_strategy'
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        'report_runs',
        sa.Column('id', sa.String(length=64), primary_key=True),
        sa.Column('case_id', sa.String(length=64), sa.ForeignKey('cases.id', ondelete='CASCADE'), nullable=False),
        sa.Column('created_by', sa.String(length=64), sa.ForeignKey('users.id', ondelete='CASCADE'), nullable=False),
        sa.Column('report_type', sa.String(length=40), nullable=False),
        sa.Column('audience', sa.String(length=60), nullable=False),
        sa.Column('depth', sa.String(length=24), nullable=False),
        sa.Column('language', sa.String(length=16), nullable=False),
        sa.Column('citation_level', sa.String(length=24), nullable=False),
        sa.Column('version', sa.Integer(), nullable=False),
        sa.Column('selected_sections', sa.JSON(), nullable=False),
        sa.Column('figure_keys', sa.JSON(), nullable=False),
        sa.Column('snapshot_json', sa.JSON(), nullable=False),
        sa.Column('validation_json', sa.JSON(), nullable=False),
        sa.Column('status', sa.String(length=32), nullable=False),
        sa.Column('docx_storage_key', sa.String(length=1200), nullable=True),
        sa.Column('pdf_storage_key', sa.String(length=1200), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index('ix_report_runs_case_id','report_runs',['case_id'])
    op.create_index('ix_report_runs_created_by','report_runs',['created_by'])


def downgrade():
    op.drop_index('ix_report_runs_created_by', table_name='report_runs')
    op.drop_index('ix_report_runs_case_id', table_name='report_runs')
    op.drop_table('report_runs')
