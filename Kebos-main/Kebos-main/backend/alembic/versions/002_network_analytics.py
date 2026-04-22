"""Add Network Analytics Tables

Revision ID: 002_network_analytics
Revises: 001_siem_integration
Create Date: 2024-01-02 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = '002_network_analytics'
down_revision = '001_siem_integration'
branch_labels = None
depends_on = None


def upgrade():
    """Add network analytics tables"""
    
    # Network Flows table
    op.create_table(
        'network_flows',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('flow_id', sa.String(255), nullable=False, index=True),
        sa.Column('source_ip', postgresql.INET, nullable=False, index=True),
        sa.Column('destination_ip', postgresql.INET, nullable=False, index=True),
        sa.Column('source_port', sa.Integer, index=True),
        sa.Column('destination_port', sa.Integer, index=True),
        sa.Column('protocol', sa.String(20), nullable=False, index=True),
        sa.Column('direction', sa.String(20), nullable=False, index=True),
        
        # Traffic metrics
        sa.Column('packet_count', sa.Integer, default=0),
        sa.Column('byte_count', sa.Integer, default=0),
        sa.Column('duration_seconds', sa.Float, default=0.0),
        
        # Timing information
        sa.Column('first_seen', sa.DateTime, nullable=False, index=True),
        sa.Column('last_seen', sa.DateTime, nullable=False, index=True),
        
        # Geographic and network context
        sa.Column('source_country', sa.String(10)),
        sa.Column('destination_country', sa.String(10)),
        sa.Column('source_asn', sa.String(20)),
        sa.Column('destination_asn', sa.String(20)),
        
        # Analysis results
        sa.Column('threat_score', sa.Float, default=0.0),
        sa.Column('anomaly_score', sa.Float, default=0.0),
        sa.Column('is_malicious', sa.Boolean, default=False),
        
        # Metadata
        sa.Column('raw_data', postgresql.JSONB),
        sa.Column('processed_data', postgresql.JSONB),
        sa.Column('tags', postgresql.JSONB),
        
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        
        # Indexes
        sa.Index('idx_network_flows_time_range', 'first_seen', 'last_seen'),
        sa.Index('idx_network_flows_ips', 'source_ip', 'destination_ip'),
        sa.Index('idx_network_flows_ports', 'source_port', 'destination_port'),
        sa.Index('idx_network_flows_metrics', 'packet_count', 'byte_count'),
        sa.Index('idx_network_flows_scores', 'threat_score', 'anomaly_score'),
    )
    
    # Traffic Patterns table
    op.create_table(
        'traffic_patterns',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('pattern_id', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('pattern_type', sa.String(50), nullable=False, index=True),
        sa.Column('pattern_name', sa.String(255)),
        sa.Column('description', sa.Text),
        
        # Pattern characteristics
        sa.Column('confidence_score', sa.Float, nullable=False),
        sa.Column('frequency', sa.String(50)),
        sa.Column('duration_minutes', sa.Integer),
        
        # Traffic characteristics
        sa.Column('affected_ips', postgresql.JSONB),
        sa.Column('affected_ports', postgresql.JSONB),
        sa.Column('protocols', postgresql.JSONB),
        sa.Column('traffic_volume', postgresql.JSONB),
        
        # Time information
        sa.Column('first_detected', sa.DateTime, nullable=False, index=True),
        sa.Column('last_detected', sa.DateTime, nullable=False, index=True),
        sa.Column('next_predicted', sa.DateTime),
        
        # Analysis metadata
        sa.Column('detection_algorithm', sa.String(100)),
        sa.Column('parameters', postgresql.JSONB),
        sa.Column('baseline_data', postgresql.JSONB),
        
        # Status
        sa.Column('is_active', sa.Boolean, default=True),
        sa.Column('is_baseline', sa.Boolean, default=False),
        
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        
        # Indexes
        sa.Index('idx_traffic_patterns_type', 'pattern_type'),
        sa.Index('idx_traffic_patterns_confidence', 'confidence_score'),
        sa.Index('idx_traffic_patterns_detection_time', 'first_detected', 'last_detected'),
        sa.Index('idx_traffic_patterns_active', 'is_active'),
    )
    
    # Network Anomalies table
    op.create_table(
        'network_anomalies',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('anomaly_id', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('anomaly_type', sa.String(50), nullable=False, index=True),
        sa.Column('title', sa.String(500)),
        sa.Column('description', sa.Text),
        
        # Anomaly scoring
        sa.Column('severity_score', sa.Float, nullable=False, index=True),
        sa.Column('confidence_score', sa.Float, nullable=False),
        sa.Column('risk_level', sa.String(20), index=True),
        
        # Associated flow
        sa.Column('flow_id', postgresql.UUID(as_uuid=True), sa.ForeignKey('network_flows.id')),
        
        # Detection details
        sa.Column('detection_algorithm', sa.String(100)),
        sa.Column('detection_parameters', postgresql.JSONB),
        sa.Column('baseline_comparison', postgresql.JSONB),
        sa.Column('statistical_measures', postgresql.JSONB),
        
        # Time information
        sa.Column('detected_at', sa.DateTime, nullable=False, index=True),
        sa.Column('start_time', sa.DateTime, index=True),
        sa.Column('end_time', sa.DateTime, index=True),
        
        # Investigation status
        sa.Column('is_investigated', sa.Boolean, default=False),
        sa.Column('is_confirmed', sa.Boolean, default=False),
        sa.Column('is_false_positive', sa.Boolean, default=False),
        sa.Column('investigation_notes', sa.Text),
        
        # Metadata
        sa.Column('tags', postgresql.JSONB),
        sa.Column('additional_context', postgresql.JSONB),
        
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        
        # Indexes
        sa.Index('idx_network_anomalies_type', 'anomaly_type'),
        sa.Index('idx_network_anomalies_severity', 'severity_score'),
        sa.Index('idx_network_anomalies_risk', 'risk_level'),
        sa.Index('idx_network_anomalies_detection_time', 'detected_at'),
        sa.Index('idx_network_anomalies_status', 'is_investigated', 'is_confirmed'),
    )
    
    # Analytics Jobs table
    op.create_table(
        'analytics_jobs',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('job_id', sa.String(255), nullable=False, unique=True, index=True),
        sa.Column('job_type', sa.String(50), nullable=False, index=True),
        sa.Column('job_name', sa.String(255)),
        sa.Column('description', sa.Text),
        
        # Job parameters
        sa.Column('query_parameters', postgresql.JSONB),
        sa.Column('processing_parameters', postgresql.JSONB),
        
        # Status tracking
        sa.Column('status', sa.String(20), nullable=False, default='pending', index=True),
        sa.Column('progress_percentage', sa.Float, default=0.0),
        
        # Timing
        sa.Column('created_at', sa.DateTime, default=sa.func.now(), index=True),
        sa.Column('started_at', sa.DateTime),
        sa.Column('completed_at', sa.DateTime),
        
        # Results
        sa.Column('result_data', postgresql.JSONB),
        sa.Column('result_summary', postgresql.JSONB),
        sa.Column('processing_time_seconds', sa.Float),
        
        # Error handling
        sa.Column('error_message', sa.Text),
        sa.Column('retry_count', sa.Integer, default=0),
        
        # User context
        sa.Column('created_by', sa.String(255)),
        
        # Indexes
        sa.Index('idx_analytics_jobs_type', 'job_type'),
        sa.Index('idx_analytics_jobs_status', 'status'),
        sa.Index('idx_analytics_jobs_created', 'created_at'),
        sa.Index('idx_analytics_jobs_user', 'created_by'),
    )
    
    # Network Topology table
    op.create_table(
        'network_topology',
        sa.Column('id', postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('ip_address', postgresql.INET, nullable=False, unique=True, index=True),
        sa.Column('hostname', sa.String(255), index=True),
        sa.Column('mac_address', sa.String(17)),
        
        # Asset classification
        sa.Column('asset_type', sa.String(50)),
        sa.Column('operating_system', sa.String(100)),
        sa.Column('device_vendor', sa.String(100)),
        sa.Column('device_model', sa.String(100)),
        
        # Network information
        sa.Column('subnet', sa.String(50)),
        sa.Column('vlan_id', sa.Integer),
        sa.Column('network_segment', sa.String(100)),
        
        # Geographic and organizational
        sa.Column('location', sa.String(255)),
        sa.Column('department', sa.String(100)),
        sa.Column('owner', sa.String(255)),
        
        # Discovery information
        sa.Column('first_seen', sa.DateTime, nullable=False, index=True),
        sa.Column('last_seen', sa.DateTime, nullable=False, index=True),
        sa.Column('discovery_method', sa.String(50)),
        
        # Status and metrics
        sa.Column('is_active', sa.Boolean, default=True, index=True),
        sa.Column('is_managed', sa.Boolean, default=False),
        sa.Column('risk_score', sa.Float, default=0.0),
        
        # Open ports and services
        sa.Column('open_ports', postgresql.JSONB),
        sa.Column('running_services', postgresql.JSONB),
        
        # Metadata
        sa.Column('tags', postgresql.JSONB),
        sa.Column('custom_attributes', postgresql.JSONB),
        
        sa.Column('created_at', sa.DateTime, default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, default=sa.func.now(), onupdate=sa.func.now()),
        
        # Indexes
        sa.Index('idx_network_topology_type', 'asset_type'),
        sa.Index('idx_network_topology_subnet', 'subnet'),
        sa.Index('idx_network_topology_active', 'is_active'),
        sa.Index('idx_network_topology_seen', 'first_seen', 'last_seen'),
    )


def downgrade():
    """Remove network analytics tables"""
    op.drop_table('network_topology')
    op.drop_table('analytics_jobs')
    op.drop_table('network_anomalies')
    op.drop_table('traffic_patterns')
    op.drop_table('network_flows')
