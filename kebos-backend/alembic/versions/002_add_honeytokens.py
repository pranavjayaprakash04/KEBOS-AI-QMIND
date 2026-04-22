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
    # Create honeytokens table
    op.create_table(
        'honeytokens',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('token_type', sa.String(), nullable=False),
        sa.Column('value', sa.String(), nullable=False, unique=True),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('deployed_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deployment_target', sa.String(), nullable=True),
        sa.Column('last_triggered', sa.DateTime(timezone=True), nullable=True),
        sa.Column('trigger_count', sa.Integer(), default=0),
        sa.Column('is_active', sa.Boolean(), default=True),
    )
    
    # Create threats table
    op.create_table(
        'threats',
        sa.Column('id', sa.String(), primary_key=True),
        sa.Column('ioc_value', sa.String(), nullable=True),
        sa.Column('ioc_type', sa.String(), nullable=True),
        sa.Column('category', sa.String(), nullable=True),
        sa.Column('confidence', sa.Float(), nullable=True),
        sa.Column('source_type', sa.String(), nullable=True),
        sa.Column('is_proactive', sa.Boolean(), default=False),
        sa.Column('qmind_category', sa.String(), nullable=True),
        sa.Column('qmind_confidence', sa.Float(), nullable=True),
        sa.Column('qmind_decayed_confidence', sa.Float(), nullable=True),
        sa.Column('supplier_trust', sa.Float(), nullable=True),
        sa.Column('adversarial_stability', sa.Float(), nullable=True),
        sa.Column('qmind_feed_source', sa.String(), nullable=True),
        sa.Column('qmind_enriched_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('priority', sa.String(), default='medium'),
        sa.Column('auto_block', sa.Boolean(), default=False),
        sa.Column('status', sa.String(), default='pending'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
    )


def downgrade():
    op.drop_table('threats')
    op.drop_table('honeytokens')
