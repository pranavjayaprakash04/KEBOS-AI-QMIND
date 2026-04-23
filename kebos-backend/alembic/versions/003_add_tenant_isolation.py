"""
Add tenant isolation with Row Level Security (RLS) for all tenant-scoped tables.

Tables:
- threats (threat_events): Add tenant_id, enable RLS
- honeytokens: Add tenant_id, enable RLS
- users: Add tenant_id, enable RLS
- cases: Create with tenant_id, enable RLS
- iocs: Create with tenant_id, enable RLS
- tenants: Create (master table, no RLS needed)
- playbooks: Create with tenant_id, enable RLS

Revision ID: 003_add_tenant_isolation
Revises: 002_add_honeytokens
Create Date: 2024-01-01
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


revision = '003_add_tenant_isolation'
down_revision = '002_add_honeytokens'
branch_labels = None
depends_on = None


def upgrade():
    # Add tenant_id to threats table
    op.add_column('threats', sa.Column('tenant_id', sa.Integer(), nullable=True))
    
    # Add tenant_id to honeytokens table
    op.add_column('honeytokens', sa.Column('tenant_id', sa.Integer(), nullable=True))
    
    # Add tenant_id to users table
    op.add_column('users', sa.Column('tenant_id', sa.Integer(), nullable=True))
    
    # Create cases table
    op.create_table(
        'cases',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('case_number', sa.String(50), nullable=False, unique=True),
        sa.Column('title', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('status', sa.String(50), default='open'),
        sa.Column('severity', sa.String(50), default='medium'),
        sa.Column('assigned_to', sa.Integer(), nullable=True),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow, nullable=False),
        sa.Column('updated_at', sa.DateTime(), default=datetime.utcnow, nullable=False),
    )
    
    # Create iocs table
    op.create_table(
        'iocs',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('ioc_value', sa.String(255), nullable=False),
        sa.Column('ioc_type', sa.String(50), nullable=False),
        sa.Column('case_id', sa.Integer(), nullable=True),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow, nullable=False),
    )
    
    # Create tenants table (master table, no RLS)
    op.create_table(
        'tenants',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False, unique=True),
        sa.Column('tenant_type', sa.String(50), default='enterprise'),
        sa.Column('brand_patterns', sa.JSON(), nullable=True),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow, nullable=False),
    )
    
    # Create playbooks table
    op.create_table(
        'playbooks',
        sa.Column('id', sa.Integer(), primary_key=True),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('steps', sa.JSON(), nullable=True),
        sa.Column('tenant_id', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), default=True),
        sa.Column('created_at', sa.DateTime(), default=datetime.utcnow, nullable=False),
    )
    
    # Create indexes for tenant_id on all tables
    op.create_index('ix_threats_tenant_id', 'threats', ['tenant_id'])
    op.create_index('ix_honeytokens_tenant_id', 'honeytokens', ['tenant_id'])
    op.create_index('ix_users_tenant_id', 'users', ['tenant_id'])
    op.create_index('ix_cases_tenant_id', 'cases', ['tenant_id'])
    op.create_index('ix_iocs_tenant_id', 'iocs', ['tenant_id'])
    op.create_index('ix_playbooks_tenant_id', 'playbooks', ['tenant_id'])
    
    # Enable Row Level Security on threats table
    op.execute("ALTER TABLE threats ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY threats_tenant_isolation ON threats
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant', true)::int)
    """)
    
    # Enable Row Level Security on honeytokens table
    op.execute("ALTER TABLE honeytokens ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY honeytokens_tenant_isolation ON honeytokens
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant', true)::int)
    """)
    
    # Enable Row Level Security on users table
    op.execute("ALTER TABLE users ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY users_tenant_isolation ON users
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant', true)::int)
    """)
    
    # Enable Row Level Security on cases table
    op.execute("ALTER TABLE cases ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY cases_tenant_isolation ON cases
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant', true)::int)
    """)
    
    # Enable Row Level Security on iocs table
    op.execute("ALTER TABLE iocs ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY iocs_tenant_isolation ON iocs
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant', true)::int)
    """)
    
    # Enable Row Level Security on playbooks table
    op.execute("ALTER TABLE playbooks ENABLE ROW LEVEL SECURITY")
    op.execute("""
        CREATE POLICY playbooks_tenant_isolation ON playbooks
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant', true)::int)
    """)
    
    # Note: tenants table does NOT have RLS as it's the master table


def downgrade():
    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS threats_tenant_isolation ON threats")
    op.execute("DROP POLICY IF EXISTS honeytokens_tenant_isolation ON honeytokens")
    op.execute("DROP POLICY IF EXISTS users_tenant_isolation ON users")
    op.execute("DROP POLICY IF EXISTS cases_tenant_isolation ON cases")
    op.execute("DROP POLICY IF EXISTS iocs_tenant_isolation ON iocs")
    op.execute("DROP POLICY IF EXISTS playbooks_tenant_isolation ON playbooks")
    
    # Disable RLS
    op.execute("ALTER TABLE threats DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE honeytokens DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE users DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE cases DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE iocs DISABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE playbooks DISABLE ROW LEVEL SECURITY")
    
    # Drop indexes
    op.drop_index('ix_threats_tenant_id', 'threats')
    op.drop_index('ix_honeytokens_tenant_id', 'honeytokens')
    op.drop_index('ix_users_tenant_id', 'users')
    op.drop_index('ix_cases_tenant_id', 'cases')
    op.drop_index('ix_iocs_tenant_id', 'iocs')
    op.drop_index('ix_playbooks_tenant_id', 'playbooks')
    
    # Drop tables
    op.drop_table('playbooks')
    op.drop_table('tenants')
    op.drop_table('iocs')
    op.drop_table('cases')
    
    # Drop tenant_id columns
    op.drop_column('users', 'tenant_id')
    op.drop_column('honeytokens', 'tenant_id')
    op.drop_column('threats', 'tenant_id')
