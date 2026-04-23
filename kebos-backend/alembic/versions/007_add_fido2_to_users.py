"""Add FIDO2 fields to users table

Revision ID: 007_add_fido2_to_users
Revises: 006_add_cases_playbooks
Create Date: 2026-04-22

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007_add_fido2_to_users'
down_revision = '006_add_cases_playbooks'
branch_labels = None
depends_on = None


def upgrade():
    # Columns already added in base migration - no-op
    pass


def downgrade():
    pass
