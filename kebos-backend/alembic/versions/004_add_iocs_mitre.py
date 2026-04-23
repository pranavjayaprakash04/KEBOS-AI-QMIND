"""Add IOCs table with MITRE techniques

Revision ID: 004_add_iocs_mitre
Revises: 003_add_tenant_isolation
Create Date: 2026-04-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid


# revision identifiers
revision = '004_add_iocs_mitre'
down_revision = '003_add_tenant_isolation'
branch_labels = None
depends_on = None


def upgrade():
    # Create iocs table
    op.create_table(
        'iocs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('indicator_value', sa.Text(), nullable=False),
        sa.Column('indicator_type', sa.String(), nullable=False),
        sa.Column('lead_category', sa.String(), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False),
        sa.Column('first_seen', sa.DateTime(timezone=True), nullable=False),
        sa.Column('last_seen', sa.DateTime(timezone=True), nullable=False),
        sa.Column('source', sa.String(), nullable=False),
        sa.Column('mitre_techniques', postgresql.ARRAY(sa.String()), nullable=True),
        sa.Column('threat_actor', sa.String(), nullable=True),
        sa.Column('dilithium_signature', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('NOW()'), nullable=True),
    )
    
    # Create indexes
    op.create_index('ix_iocs_tenant_id', 'iocs', ['tenant_id'])
    op.create_index('ix_iocs_indicator_value', 'iocs', ['indicator_value'])
    op.create_index('ix_iocs_indicator_type', 'iocs', ['indicator_type'])
    op.create_index('ix_iocs_lead_category', 'iocs', ['lead_category'])
    op.create_index('ix_iocs_source', 'iocs', ['source'])
    
    # Enable RLS
    op.execute("ALTER TABLE iocs ENABLE ROW LEVEL SECURITY")
    
    # Create RLS policy for tenant isolation
    op.execute("""
        CREATE POLICY iocs_tenant_policy ON iocs
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
    """)


def downgrade():
    op.drop_table('iocs')
