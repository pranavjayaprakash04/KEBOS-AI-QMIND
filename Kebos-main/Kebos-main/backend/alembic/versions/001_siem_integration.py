"""Add SIEM Integration Tables

Revision ID: 001_siem_integration
Revises: 
Create Date: 2024-01-01 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '001_siem_integration'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    """Add SIEM integration tables"""
    
    # SIEM Configurations table
    op.create_table(
        'siem_configs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text),
        sa.Column('siem_type', sa.String(50), nullable=False),
        sa.Column('base_url', sa.String(500), nullable=False),
        sa.Column('auth_type', sa.String(50), nullable=False),
        sa.Column('auth_config', postgresql.JSONB),
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('timeout_seconds', sa.Integer, default=30),
        sa.Column('max_retries', sa.Integer, default=3),
        sa.Column('retry_delay_seconds', sa.Integer, default=5),
        sa.Column('query_batch_size', sa.Integer, default=1000),
        sa.Column('enable_real_time', sa.Boolean, default=False),
        sa.Column('webhook_url', sa.String(500)),
        sa.Column('custom_headers', postgresql.JSONB),
        sa.Column('api_version', sa.String(20)),
        sa.Column('enable_ssl_verify', sa.Boolean, default=True),
        sa.Column('created_by', sa.String(255)),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        sa.Index('idx_siem_configs_type', 'siem_type'),
        sa.Index('idx_siem_configs_active', 'is_active'),
    )
    
    # SIEM Events table
    op.create_table(
        'siem_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('event_id', sa.String(255), nullable=False),
        sa.Column('siem_config_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('timestamp', sa.DateTime, nullable=False),
        sa.Column('event_type', sa.String(100)),
        sa.Column('severity', sa.String(20)),
        sa.Column('category', sa.String(100)),
        sa.Column('source_ip', sa.String(45)),  # IPv6 compatible
        sa.Column('destination_ip', sa.String(45)),
        sa.Column('source_port', sa.Integer),
        sa.Column('destination_port', sa.Integer),
        sa.Column('protocol', sa.String(20)),
        sa.Column('source_hostname', sa.String(255)),
        sa.Column('destination_hostname', sa.String(255)),
        sa.Column('user', sa.String(255)),
        sa.Column('asset', sa.String(255)),
        sa.Column('title', sa.String(500)),
        sa.Column('description', sa.Text),
        sa.Column('signature', sa.String(500)),
        sa.Column('geo_location', postgresql.JSONB),
        sa.Column('threat_intelligence', postgresql.JSONB),
        sa.Column('correlation_id', sa.String(255)),
        sa.Column('parent_event_id', sa.String(255)),
        sa.Column('raw_data', postgresql.JSONB),
        sa.Column('normalized_data', postgresql.JSONB),
        sa.Column('processing_notes', sa.Text),
        sa.Column('ingested_at', sa.DateTime, default=sa.func.now()),
        sa.Column('processed_at', sa.DateTime),
        sa.Column('is_processed', sa.Boolean, default=False),
        sa.Column('processing_status', sa.String(50), default='pending'),
        sa.ForeignKeyConstraint(['siem_config_id'], ['siem_configs.id'], ondelete='CASCADE'),
        sa.Index('idx_siem_events_config', 'siem_config_id'),
        sa.Index('idx_siem_events_timestamp', 'timestamp'),
        sa.Index('idx_siem_events_severity', 'severity'),
        sa.Index('idx_siem_events_type', 'event_type'),
        sa.Index('idx_siem_events_source_ip', 'source_ip'),
        sa.Index('idx_siem_events_processed', 'is_processed'),
        sa.Index('idx_siem_events_event_id', 'event_id'),
    )
    
    # SIEM Queries table
    op.create_table(
        'siem_queries',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('siem_config_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('query_text', sa.Text, nullable=False),
        sa.Column('query_type', sa.String(50)),
        sa.Column('query_parameters', postgresql.JSONB),
        sa.Column('start_time', sa.DateTime),
        sa.Column('end_time', sa.DateTime),
        sa.Column('created_by', sa.String(255)),
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('status', sa.String(20), default='pending'),
        sa.Column('execution_time_seconds', sa.Float),
        sa.Column('result_count', sa.Integer),
        sa.Column('error_message', sa.Text),
        sa.Column('completed_at', sa.DateTime),
        sa.ForeignKeyConstraint(['siem_config_id'], ['siem_configs.id'], ondelete='CASCADE'),
        sa.Index('idx_siem_queries_config', 'siem_config_id'),
        sa.Index('idx_siem_queries_status', 'status'),
        sa.Index('idx_siem_queries_created', 'created_at'),
    )
    
    # SIEM Health Logs table
    op.create_table(
        'siem_health_logs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('siem_config_id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('status', sa.String(20), nullable=False),
        sa.Column('auth_success', sa.Boolean, default=False),
        sa.Column('api_success', sa.Boolean, default=False),
        sa.Column('connectivity_info', postgresql.JSONB),
        sa.Column('error_message', sa.Text),
        sa.Column('checked_at', sa.DateTime, default=sa.func.now()),
        sa.ForeignKeyConstraint(['siem_config_id'], ['siem_configs.id'], ondelete='CASCADE'),
        sa.Index('idx_siem_health_config', 'siem_config_id'),
        sa.Index('idx_siem_health_status', 'status'),
        sa.Index('idx_siem_health_checked', 'checked_at'),
    )
    
    # SIEM Webhooks table
    op.create_table(
        'siem_webhooks',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('siem_source', sa.String(255), nullable=False),
        sa.Column('event_type', sa.String(100)),
        sa.Column('payload', postgresql.JSONB),
        sa.Column('signature', sa.String(500)),
        sa.Column('received_at', sa.DateTime, default=sa.func.now()),
        sa.Column('processed_at', sa.DateTime),
        sa.Column('processing_status', sa.String(20), default='pending'),
        sa.Column('error_message', sa.Text),
        sa.Index('idx_siem_webhooks_source', 'siem_source'),
        sa.Index('idx_siem_webhooks_status', 'processing_status'),
        sa.Index('idx_siem_webhooks_received', 'received_at'),
    )


def downgrade():
    """Remove SIEM integration tables"""
    op.drop_table('siem_webhooks')
    op.drop_table('siem_health_logs')
    op.drop_table('siem_queries')
    op.drop_table('siem_events')
    op.drop_table('siem_configs')
