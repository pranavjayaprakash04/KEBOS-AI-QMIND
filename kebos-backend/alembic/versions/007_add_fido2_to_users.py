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
    # Add fido2_enabled column
    op.add_column('users', sa.Column('fido2_enabled', sa.Boolean(), server_default='false', nullable=False))
    
    # Add fido2_credentials column (JSONB)
    op.add_column('users', sa.Column('fido2_credentials', sa.JSON(), server_default='[]', nullable=True))


def downgrade():
    # Remove fido2_credentials column
    op.drop_column('users', 'fido2_credentials')
    
    # Remove fido2_enabled column
    op.drop_column('users', 'fido2_enabled')
