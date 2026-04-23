"""
Create base tables - users, tenants, threat_events, honeytokens, iocs, ueba, cases, playbooks, analyst_feedback, cert_in_reports
Base migration for Kebos AI platform.
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
from sqlalchemy.dialects import postgresql
import uuid


revision = '000_create_base_tables'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Create tenants table
    op.create_table(
        'tenants',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('tenant_type', sa.String(50), nullable=False, default='enterprise'),
        sa.Column('created_at', sa.DateTime(timezone=True), default=datetime.utcnow, nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
    )
    
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('username', sa.String(255), nullable=False, unique=True),
        sa.Column('email', sa.String(255), nullable=False, unique=True),
        sa.Column('password_hash', sa.String(255), nullable=False),
        sa.Column('role', sa.String(50), nullable=False, default='analyst'),
        sa.Column('is_active', sa.Boolean(), default=True, nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), default=datetime.utcnow, nullable=False),
        sa.Column('totp_secret_encrypted', sa.Text(), nullable=True),
        sa.Column('tenant_type', sa.String(), nullable=True, default='enterprise'),
        sa.Column('fido2_credential_id', sa.String(255), nullable=True),
        sa.Column('fido2_public_key', sa.Text(), nullable=True),
        sa.Column('fido2_sign_count', sa.Integer(), nullable=True, default=0),
    )
    
    # Create threat_events table
    op.create_table(
        'threat_events',
        sa.Column('id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('event_type', sa.String(100), nullable=False),
        sa.Column('source_ip', sa.String(50), nullable=True),
        sa.Column('destination_ip', sa.String(50), nullable=True),
        sa.Column('severity', sa.String(20), nullable=False),
        sa.Column('status', sa.String(50), nullable=False, default='open'),
        sa.Column('qmind_confidence', sa.Float(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), default=datetime.utcnow, nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), default=datetime.utcnow, nullable=False),
    )
    
    # Create honeytokens table
    op.create_table(
        'honeytokens',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('tenant_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('token_type', sa.String(), nullable=False),
        sa.Column('value', sa.String(), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('deployed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deployment_target', sa.String(), nullable=True),
        sa.Column('last_triggered', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trigger_count', sa.Integer(), default=0),
        sa.Column('is_active', sa.Boolean(), default=True),
    )
    
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
    
    # Create cases table
    op.create_table(
        'cases',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('case_number', sa.String(50), nullable=False, unique=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), default='open'),
        sa.Column('severity', sa.String(50), default='medium'),
        sa.Column('assigned_to', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('threat_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow, nullable=False),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow, nullable=False),
        sa.Column('five_hour_alert_sent', sa.Boolean(), default=False),
        sa.Column('cert_in_status', sa.String(50), default='pending'),
    )
    
    # Create playbooks table
    op.create_table(
        'playbooks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('steps', sa.JSON(), nullable=True),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow, nullable=False),
    )
    
    # Create analyst_feedback table
    op.create_table(
        'analyst_feedback',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('indicator_value', sa.String(255), nullable=False),
        sa.Column('predicted_category', sa.String(50), nullable=False),
        sa.Column('corrected_category', sa.String(50), nullable=True),
        sa.Column('analyst_id', postgresql.UUID(as_uuid=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
        sa.Column('used_for_training', sa.Boolean(), default=False),
    )
    
    # Create cert_in_reports table
    op.create_table(
        'cert_in_reports',
        sa.Column('report_id', sa.String(255), primary_key=True),
        sa.Column('incident_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('incident_type', sa.String(100), nullable=False),
        sa.Column('severity', sa.String(50), nullable=False),
        sa.Column('affected_assets', sa.Text(), nullable=False),
        sa.Column('timeline', sa.Text(), nullable=False),
        sa.Column('iocs', sa.JSON(), nullable=False),
        sa.Column('mitigation_steps', sa.Text(), nullable=False),
        sa.Column('signature', sa.Text(), nullable=True),
        sa.Column('pubkey_ref', sa.String(255), nullable=False),
        sa.Column('report_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('NOW()'), nullable=False),
    )
    
    # Create indexes
    op.create_index('ix_users_tenant_id', 'users', ['tenant_id'])
    op.create_index('ix_users_username', 'users', ['username'])
    op.create_index('ix_threat_events_tenant_id', 'threat_events', ['tenant_id'])
    op.create_index('ix_threat_events_status', 'threat_events', ['status'])
    op.create_index('ix_honeytokens_tenant_id', 'honeytokens', ['tenant_id'])
    op.create_index('ix_honeytokens_value', 'honeytokens', ['value'])
    op.create_index('ix_iocs_tenant_id', 'iocs', ['tenant_id'])
    op.create_index('ix_iocs_indicator_value', 'iocs', ['indicator_value'])
    op.create_index('ix_iocs_indicator_type', 'iocs', ['indicator_type'])
    op.create_index('ix_iocs_lead_category', 'iocs', ['lead_category'])
    op.create_index('ix_iocs_source', 'iocs', ['source'])
    op.create_index('ix_ueba_events_user_id', 'ueba_events', ['user_id'])
    op.create_index('ix_ueba_events_tenant_id', 'ueba_events', ['tenant_id'])
    op.create_index('ix_ueba_events_timestamp', 'ueba_events', ['timestamp'])
    op.create_index('ix_ueba_baselines_tenant_id', 'ueba_baselines', ['tenant_id'])
    op.create_index('ix_cases_tenant_id', 'cases', ['tenant_id'])
    op.create_index('ix_cases_status', 'cases', ['status'])
    op.create_index('ix_playbooks_tenant_id', 'playbooks', ['tenant_id'])
    op.create_index('ix_analyst_feedback_tenant_id', 'analyst_feedback', ['tenant_id'])
    
    # Enable Row Level Security on all tenant-scoped tables
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE threat_events ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE honeytokens ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE iocs ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE ueba_events ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE ueba_baselines ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE cases ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE playbooks ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE analyst_feedback ENABLE ROW LEVEL SECURITY")
    
    # RLS policies for tenant isolation
    op.execute("""
        CREATE POLICY users_tenant_policy ON users
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
    """)
    
    op.execute("""
        CREATE POLICY threat_events_tenant_policy ON threat_events
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
    """)
    
    op.execute("""
        CREATE POLICY honeytokens_tenant_policy ON honeytokens
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
    """)
    
    op.execute("""
        CREATE POLICY iocs_tenant_policy ON iocs
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
    """)
    
    op.execute("""
        CREATE POLICY ueba_events_tenant_policy ON ueba_events
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
    """)
    
    op.execute("""
        CREATE POLICY ueba_baselines_tenant_policy ON ueba_baselines
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
    """)
    
    op.execute("""
        CREATE POLICY cases_tenant_policy ON cases
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
    """)
    
    op.execute("""
        CREATE POLICY playbooks_tenant_policy ON playbooks
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
    """)
    
    op.execute("""
        CREATE POLICY analyst_feedback_tenant_policy ON analyst_feedback
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
    """)


def downgrade():
    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS users_tenant_policy ON users")
    op.execute("DROP POLICY IF EXISTS threat_events_tenant_policy ON threat_events")
    op.execute("DROP POLICY IF EXISTS honeytokens_tenant_policy ON honeytokens")
    op.execute("DROP POLICY IF EXISTS iocs_tenant_policy ON iocs")
    op.execute("DROP POLICY IF EXISTS ueba_events_tenant_policy ON ueba_events")
    op.execute("DROP POLICY IF EXISTS ueba_baselines_tenant_policy ON ueba_baselines")
    op.execute("DROP POLICY IF EXISTS cases_tenant_policy ON cases")
    op.execute("DROP POLICY IF EXISTS playbooks_tenant_policy ON playbooks")
    op.execute("DROP POLICY IF EXISTS analyst_feedback_tenant_policy ON analyst_feedback")
    
    # Disable RLS
    op.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE threat_events DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE honeytokens DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE iocs DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE ueba_events DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE ueba_baselines DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE cases DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE playbooks DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE analyst_feedback DISABLE ROW LEVEL SECURITY")
    
    # Drop indexes
    op.drop_index('ix_analyst_feedback_tenant_id', 'analyst_feedback')
    op.drop_index('ix_playbooks_tenant_id', 'playbooks')
    op.drop_index('ix_cases_status', 'cases')
    op.drop_index('ix_cases_tenant_id', 'cases')
    op.drop_index('ix_ueba_baselines_tenant_id', 'ueba_baselines')
    op.drop_index('ix_ueba_events_timestamp', 'ueba_events')
    op.drop_index('ix_ueba_events_tenant_id', 'ueba_events')
    op.drop_index('ix_ueba_events_user_id', 'ueba_events')
    op.drop_index('ix_iocs_source', 'iocs')
    op.drop_index('ix_iocs_lead_category', 'iocs')
    op.drop_index('ix_iocs_indicator_type', 'iocs')
    op.drop_index('ix_iocs_indicator_value', 'iocs')
    op.drop_index('ix_iocs_tenant_id', 'iocs')
    op.drop_index('ix_honeytokens_value', 'honeytokens')
    op.drop_index('ix_honeytokens_tenant_id', 'honeytokens')
    op.drop_index('ix_threat_events_status', 'threat_events')
    op.drop_index('ix_threat_events_tenant_id', 'threat_events')
    op.drop_index('ix_users_username', 'users')
    op.drop_index('ix_users_tenant_id', 'users')
    
    # Drop tables
    op.drop_table('cert_in_reports')
    op.drop_table('analyst_feedback')
    op.drop_table('playbooks')
    op.drop_table('cases')
    op.drop_table('ueba_baselines')
    op.drop_table('ueba_events')
    op.drop_table('iocs')
    op.drop_table('honeytokens')
    op.drop_table('threat_events')
    op.drop_table('users')
    op.drop_table('tenants')
