"""Add honeytokens and threats tables

Revision ID: 002_add_honeytokens
Revises: 001_add_totp_encrypted
Create Date: 2024-01-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_honeytokens'
down_revision = '001_add_totp_encrypted'
branch_labels = None
depends_on = None


def upgrade():
    # Tables already created in base migration - no-op
    pass


def downgrade():
    pass
