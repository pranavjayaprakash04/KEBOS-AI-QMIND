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
    # Tables already created with tenant_id and RLS in base migration
    # This is a no-op migration
    pass


def downgrade():
    pass
