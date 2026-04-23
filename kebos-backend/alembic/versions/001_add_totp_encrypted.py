"""Add totp_secret_encrypted column to users table

Revision ID: 001_add_totp_encrypted
Revises: 000_create_base_tables
Create Date: 2024-01-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_add_totp_encrypted'
down_revision = '000_create_base_tables'
branch_labels = None
depends_on = None


def upgrade():
    # Columns already added in base migration - this is a no-op
    pass


def downgrade():
    pass
