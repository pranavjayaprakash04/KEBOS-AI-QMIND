"""Add cases and playbooks tables

Revision ID: 006_add_cases_playbooks
Revises: 005_add_ueba
Create Date: 2026-04-22
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
from datetime import datetime, timedelta
import uuid


# revision identifiers
revision = '006_add_cases_playbooks'
down_revision = '005_add_ueba'
branch_labels = None
depends_on = None


def upgrade():
    # Create cases table
    op.create_table(
        'cases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('case_number', sa.String(), nullable=False, unique=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('threat_event_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('title', sa.String(), nullable=False),
        sa.Column('status', sa.String(), nullable=False, default='OPEN'),
        sa.Column('severity', sa.String(), nullable=False),
        sa.Column('cert_in_deadline', sa.DateTime(timezone=True), nullable=False),
        sa.Column('cert_in_status', sa.String(), nullable=False, default='PENDING'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.text('NOW()'), nullable=True),
    )
    
    # Create playbooks table
    op.create_table(
        'playbooks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(), nullable=False),
        sa.Column('reversibility', sa.String(), nullable=False),  # REVERSIBLE or IRREVERSIBLE
        sa.Column('actions', sa.JSON(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False, default=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    
    # Create pending_actions table
    op.create_table(
        'pending_actions',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('case_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.JSON(), nullable=False),
        sa.Column('digital_twin_result', sa.JSON(), nullable=True),
        sa.Column('status', sa.String(), nullable=False, default='PENDING'),  # PENDING, APPROVED, REJECTED, BLOCKED
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    
    # Create indexes
    op.create_index('ix_cases_tenant_id', 'cases', ['tenant_id'])
    op.create_index('ix_cases_threat_event_id', 'cases', ['threat_event_id'])
    op.create_index('ix_cases_status', 'cases', ['status'])
    op.create_index('ix_cases_cert_in_deadline', 'cases', ['cert_in_deadline'])
    op.create_index('ix_pending_actions_case_id', 'pending_actions', ['case_id'])
    op.create_index('ix_pending_actions_status', 'pending_actions', ['status'])
    
    # Enable RLS on cases
    op.execute("ALTER TABLE cases ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY cases_tenant_policy ON cases
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
    """)
    
    # Enable RLS on pending_actions (via cases)
    op.execute("ALTER TABLE pending_actions ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY pending_actions_tenant_policy ON pending_actions
        FOR ALL
        USING (
            EXISTS (
                SELECT 1 FROM cases 
                WHERE cases.id = pending_actions.case_id 
                AND cases.tenant_id = current_setting('app.current_tenant', true)::uuid
            )
        )
    """)
    
    # Seed default playbooks
    op.execute("""
        INSERT INTO playbooks (name, description, category, reversibility, actions) VALUES
        ('Block IP', 'Block malicious IP at firewall', 'Network', 'REVERSIBLE', 
         '{"type": "firewall_block", "target": "ip"}'::json),
        ('Isolate Host', 'Isolate compromised host from network', 'Endpoint', 'REVERSIBLE',
         '{"type": "network_isolation", "target": "host"}'::json),
        ('Disable Account', 'Disable compromised user account', 'Identity', 'REVERSIBLE',
         '{"type": "account_disable", "target": "user"}'::json),
        ('Wipe Endpoint', 'Wipe compromised endpoint (destructive)', 'Endpoint', 'IRREVERSIBLE',
         '{"type": "endpoint_wipe", "target": "host"}'::json),
        ('Block Domain', 'Block malicious domain at DNS', 'Network', 'REVERSIBLE',
         '{"type": "dns_block", "target": "domain"}'::json)
    """)


def downgrade():
    op.drop_table('pending_actions')
    op.drop_table('playbooks')
    op.drop_table('cases')
