"""Add analyst_feedback table for CatBoost retraining loop

Revision ID: 008_add_analyst_feedback
Revises: 007_add_fido2_to_users
Create Date: 2024-01-01
"""
from alembic import op
import sqlalchemy as sa
from datetime import datetime


revision = '008_add_analyst_feedback'
down_revision = '007_add_fido2_to_users'
branch_labels = None
depends_on = None


def upgrade():
    # Table already created in base migration - no-op
    pass


def downgrade():
    pass
