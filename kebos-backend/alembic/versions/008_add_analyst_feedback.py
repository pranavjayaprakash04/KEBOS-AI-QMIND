"""Add analyst_feedback table for CatBoost retraining loop

Revision ID: 008_add_analyst_feedback
Revises: 007_add_fido2_to_users
Create Date: 2024-01-01
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


revision = '008_add_analyst_feedback'
down_revision = '007_add_fido2_to_users'
branch_labels = None
depends_on = None


def upgrade():
    # Create analyst_feedback table
    op.create_table(
        'analyst_feedback',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('tenant_id', sa.String(), nullable=False),
        sa.Column('indicator_value', sa.Text(), nullable=False),
        sa.Column('predicted_category', sa.String(), nullable=True),
        sa.Column('corrected_category', sa.String(), nullable=False),
        sa.Column('analyst_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow, nullable=False),
        sa.Column('used_for_training', sa.Boolean(), default=False, nullable=False),
    )
    
    # Create indexes
    op.create_index('ix_analyst_feedback_tenant_id', 'analyst_feedback', ['tenant_id'])
    op.create_index('ix_analyst_feedback_used_for_training', 'analyst_feedback', ['used_for_training'])
    
    # Enable Row Level Security
    op.execute("ALTER TABLE analyst_feedback ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY analyst_feedback_tenant_isolation ON analyst_feedback
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant', true))
    """)


def downgrade():
    # Drop RLS policy
    op.execute("DROP POLICY IF EXISTS analyst_feedback_tenant_isolation ON analyst_feedback")
    
    # Disable RLS
    op.execute("ALTER TABLE analyst_feedback DISABLE ROW LEVEL SECURITY")
    
    # Drop indexes
    op.drop_index('ix_analyst_feedback_used_for_training', 'analyst_feedback')
    op.drop_index('ix_analyst_feedback_tenant_id', 'analyst_feedback')
    
    # Drop table
    op.drop_table('analyst_feedback')
