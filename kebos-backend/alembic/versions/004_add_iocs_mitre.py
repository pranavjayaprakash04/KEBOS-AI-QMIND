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
    # Table already created in base migration - no-op
    pass


def downgrade():
    pass
