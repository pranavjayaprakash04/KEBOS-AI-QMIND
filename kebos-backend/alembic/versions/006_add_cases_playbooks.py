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
    # Tables already created in base migration - no-op
    pass


def downgrade():
    pass
