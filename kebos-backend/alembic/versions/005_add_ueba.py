"""Add UEBA tables for baseline tracking

Revision ID: 005_add_ueba
Revises: 004_add_iocs_mitre
Create Date: 2026-04-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid


# revision identifiers
revision = '005_add_ueba'
down_revision = '004_add_iocs_mitre'
branch_labels = None
depends_on = None


def upgrade():
    # Create ueba_events table
    op.create_table(
        'ueba_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('user_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('features', sa.JSON(), nullable=False),
        sa.Column('anomaly_score', sa.Float(), nullable=True),
        sa.Column('timestamp', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    
    # Create ueba_baselines table
    op.create_table(
        'ueba_baselines',
        sa.Column('user_id', postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('mean_features', sa.JSON(), nullable=False),
        sa.Column('variance_features', sa.JSON(), nullable=False),
        sa.Column('sample_count', sa.Integer(), nullable=False, default=0),
        sa.Column('last_updated', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    
    # Create indexes
    op.create_index('ix_ueba_events_user_id', 'ueba_events', ['user_id'])
    op.create_index('ix_ueba_events_tenant_id', 'ueba_events', ['tenant_id'])
    op.create_index('ix_ueba_events_timestamp', 'ueba_events', ['timestamp'])
    op.create_index('ix_ueba_baselines_tenant_id', 'ueba_baselines', ['tenant_id'])
    
    # Enable RLS on ueba_events
    op.execute("ALTER TABLE ueba_events ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY ueba_events_tenant_policy ON ueba_events
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
    """)
    
    # Enable RLS on ueba_baselines
    op.execute("ALTER TABLE ueba_baselines ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY ueba_baselines_tenant_policy ON ueba_baselines
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
    """)


def downgrade():
    op.drop_table('ueba_baselines')
    op.drop_table('ueba_events')
