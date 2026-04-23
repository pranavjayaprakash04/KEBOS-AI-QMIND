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
    # Tables already created in base migration - no-op
    pass


def downgrade():
    pass
