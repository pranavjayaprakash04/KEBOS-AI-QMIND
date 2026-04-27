"""
Add audit_entries table with Dilithium-3 signatures.
Phase 2.4 - Audit chain implementation.
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime
import uuid


revision = '009_add_audit_entries'
down_revision = '008_add_analyst_feedback'
branch_labels = None
depends_on = None


def upgrade():
    # Create audit_entries table with UUID fields
    op.create_table(
        'audit_entries',
        sa.Column('entry_id', sa.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('tenant_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('timestamp', sa.DateTime(timezone=True), default=datetime.utcnow, nullable=False),
        sa.Column('actor_id', sa.UUID(as_uuid=True), nullable=False),
        sa.Column('action', sa.String(255), nullable=False),
        sa.Column('resource', sa.String(255), nullable=False),
        sa.Column('metadata', sa.JSON(), nullable=True),
        sa.Column('prev_hash', sa.String(64), nullable=False),
        sa.Column('entry_hash', sa.String(64), nullable=False, unique=True),
        sa.Column('signature', sa.Text(), nullable=True),
        sa.Column('pubkey_ref', sa.String(255), nullable=False),
    )
    
    # Create index on tenant_id for RLS
    op.create_index('ix_audit_entries_tenant_id', 'audit_entries', ['tenant_id'])
    
    # Create index on entry_hash for chain verification
    op.create_index('ix_audit_entries_entry_hash', 'audit_entries', ['entry_hash'])
    
    # Create index on timestamp for time-based queries
    op.create_index('ix_audit_entries_timestamp', 'audit_entries', ['timestamp'])
    
    # Enable Row Level Security
    op.execute("ALTER TABLE audit_entries ENABLE ROW LEVEL SECURITY")
    
    # RLS policy: Users can only see audit entries for their tenant
    op.execute("""
        CREATE POLICY audit_entries_tenant_policy ON audit_entries
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant', true)::uuid)
    """)


def downgrade():
    # Drop RLS policy
    op.execute("DROP POLICY IF EXISTS audit_entries_tenant_policy ON audit_entries")
    
    # Disable RLS
    op.execute("ALTER TABLE audit_entries DISABLE ROW LEVEL SECURITY")
    
    # Drop indexes
    op.drop_index('ix_audit_entries_timestamp', 'audit_entries')
    op.drop_index('ix_audit_entries_entry_hash', 'audit_entries')
    op.drop_index('ix_audit_entries_tenant_id', 'audit_entries')
    
    # Drop table
    op.drop_table('audit_entries')
