"""
Add QMind columns to threat_events table
Adds indicator_value, lead_category, category_scores, and reversibility columns
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


revision = '010_qmind_columns'
down_revision = '009_add_audit_entries'
branch_labels = None
depends_on = None


def upgrade():
    # Get connection to check if columns exist
    conn = op.get_bind()
    
    # Check if indicator_value column already exists
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('threat_events')]
    
    # Add missing columns to threat_events table (idempotent)
    if 'indicator_value' not in columns:
        op.add_column('threat_events', sa.Column('indicator_value', sa.Text(), nullable=True))
    
    if 'lead_category' not in columns:
        op.add_column('threat_events', sa.Column('lead_category', sa.String(50), nullable=True))
    
    if 'category_scores' not in columns:
        op.add_column('threat_events', sa.Column('category_scores', postgresql.JSON(), nullable=True))
    
    if 'reversibility' not in columns:
        op.add_column('threat_events', sa.Column('reversibility', sa.String(50), nullable=True))
    
    # Add index for indicator_value (idempotent)
    indexes = inspector.get_indexes('threat_events')
    index_names = [idx['name'] for idx in indexes]
    if 'ix_threat_events_indicator_value' not in index_names:
        op.create_index('ix_threat_events_indicator_value', 'threat_events', ['indicator_value'])


def downgrade():
    # Drop index
    op.drop_index('ix_threat_events_indicator_value', 'threat_events')
    
    # Drop columns
    op.drop_column('threat_events', 'reversibility')
    op.drop_column('threat_events', 'category_scores')
    op.drop_column('threat_events', 'lead_category')
    op.drop_column('threat_events', 'indicator_value')
