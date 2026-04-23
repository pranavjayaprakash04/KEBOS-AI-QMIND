"""Add totp_secret_encrypted column to users table

Revision ID: 001_add_totp_encrypted
Revises: 
Create Date: 2024-01-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_add_totp_encrypted'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add totp_secret_encrypted column (NEVER plaintext totp_secret)
    op.add_column(
        'users',
        sa.Column('totp_secret_encrypted', sa.Text(), nullable=True)
    )
    
    # Add tenant_type column for government tenant enforcement
    op.add_column(
        'users',
        sa.Column('tenant_type', sa.String(), nullable=True, default='enterprise')
    )


def downgrade():
    op.drop_column('users', 'tenant_type')
    op.drop_column('users', 'totp_secret_encrypted')
