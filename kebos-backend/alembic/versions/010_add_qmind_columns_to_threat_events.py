"""
Add QMind columns to threat_events table
Adds indicator_value, lead_category, category_scores, and reversibility columns
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '010_add_qmind_columns_to_threat_events'
down_revision = '009_add_audit_entries'
branch_labels = None
depends_on = None


def upgrade():
    # Add missing columns to threat_events table
    op.add_column('threat_events', sa.Column('indicator_value', sa.Text(), nullable=True))
    op.add_column('threat_events', sa.Column('lead_category', sa.String(50), nullable=True))
    op.add_column('threat_events', sa.Column('category_scores', postgresql.JSON(), nullable=True))
    op.add_column('threat_events', sa.Column('reversibility', sa.String(50), nullable=True))
    
    # Add index for indicator_value
    op.create_index('ix_threat_events_indicator_value', 'threat_events', ['indicator_value'])


def downgrade():
    # Drop index
    op.drop_index('ix_threat_events_indicator_value', 'threat_events')
    
    # Drop columns
    op.drop_column('threat_events', 'reversibility')
    op.drop_column('threat_events', 'category_scores')
    op.drop_column('threat_events', 'lead_category')
    op.drop_column('threat_events', 'indicator_value')
