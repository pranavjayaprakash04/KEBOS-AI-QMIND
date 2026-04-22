-- Cyber Threat Platform (CTP) Database Initialization
-- TimescaleDB setup for time-series network data and threat analytics

-- Enable TimescaleDB extension
CREATE EXTENSION IF NOT EXISTS timescaledb CASCADE;
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_stat_statements";

-- =============================================================================
-- USERS AND AUTHENTICATION TABLES
-- =============================================================================

CREATE TABLE IF NOT EXISTS users (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    username VARCHAR(50) UNIQUE NOT NULL,
    email VARCHAR(100) UNIQUE NOT NULL,
    hashed_password VARCHAR(255) NOT NULL,
    is_active BOOLEAN DEFAULT true,
    is_superuser BOOLEAN DEFAULT false,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    last_login TIMESTAMPTZ
);

CREATE TABLE IF NOT EXISTS user_roles (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    user_id UUID REFERENCES users(id) ON DELETE CASCADE,
    role_name VARCHAR(50) NOT NULL,
    granted_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    granted_by UUID REFERENCES users(id)
);

-- =============================================================================
-- NETWORK TRAFFIC TABLES (Time-series)
-- =============================================================================

CREATE TABLE IF NOT EXISTS network_packets (
    timestamp TIMESTAMPTZ NOT NULL,
    packet_id UUID DEFAULT uuid_generate_v4(),
    source_ip INET NOT NULL,
    destination_ip INET NOT NULL,
    source_port INTEGER,
    destination_port INTEGER,
    protocol VARCHAR(10) NOT NULL,
    payload_size INTEGER NOT NULL DEFAULT 0,
    packet_hash VARCHAR(64),
    geo_source_country VARCHAR(2),
    geo_source_city VARCHAR(100),
    geo_dest_country VARCHAR(2),
    geo_dest_city VARCHAR(100),
    raw_data BYTEA,
    metadata JSONB
);

-- Convert to hypertable for time-series optimization
SELECT create_hypertable('network_packets', 'timestamp', 
    chunk_time_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

-- Create indexes for efficient queries
CREATE INDEX IF NOT EXISTS idx_network_packets_source_ip ON network_packets (source_ip, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_network_packets_dest_ip ON network_packets (destination_ip, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_network_packets_protocol ON network_packets (protocol, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_network_packets_ports ON network_packets (source_port, destination_port);
CREATE INDEX IF NOT EXISTS idx_network_packets_geo ON network_packets (geo_source_country, geo_dest_country);

-- =============================================================================
-- THREAT DETECTION TABLES
-- =============================================================================

CREATE TABLE IF NOT EXISTS anomaly_reports (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL,
    packet_id UUID,
    anomaly_score DECIMAL(5,4) NOT NULL CHECK (anomaly_score >= 0 AND anomaly_score <= 1),
    confidence DECIMAL(5,4) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    features JSONB NOT NULL,
    reconstruction_error DECIMAL(10,6),
    baseline_deviation DECIMAL(10,6),
    detection_method VARCHAR(100) NOT NULL,
    model_version VARCHAR(50),
    CONSTRAINT fk_anomaly_packet FOREIGN KEY (packet_id) REFERENCES network_packets(packet_id)
);

-- Convert to hypertable
SELECT create_hypertable('anomaly_reports', 'timestamp',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS idx_anomaly_reports_score ON anomaly_reports (anomaly_score DESC, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_anomaly_reports_method ON anomaly_reports (detection_method, timestamp DESC);

CREATE TABLE IF NOT EXISTS threat_alerts (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL,
    threat_level VARCHAR(20) NOT NULL CHECK (threat_level IN ('low', 'medium', 'high', 'critical')),
    attack_type VARCHAR(50) NOT NULL,
    confidence_score DECIMAL(5,4) NOT NULL CHECK (confidence_score >= 0 AND confidence_score <= 1),
    
    -- AI Analysis
    threat_description TEXT NOT NULL,
    attack_vector TEXT,
    mitre_attack_id VARCHAR(20),
    recommended_actions TEXT[],
    
    -- Context
    affected_assets TEXT[],
    network_segment VARCHAR(100),
    source_packets_count INTEGER DEFAULT 0,
    anomaly_reports_count INTEGER DEFAULT 0,
    
    -- Metadata
    detection_method VARCHAR(100) NOT NULL,
    processing_time_ms DECIMAL(10,3),
    false_positive_probability DECIMAL(5,4),
    
    -- Status tracking
    status VARCHAR(20) DEFAULT 'open' CHECK (status IN ('open', 'investigating', 'resolved', 'false_positive')),
    assigned_to UUID REFERENCES users(id),
    resolved_at TIMESTAMPTZ,
    resolution_notes TEXT
);

-- Convert to hypertable
SELECT create_hypertable('threat_alerts', 'timestamp',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS idx_threat_alerts_level ON threat_alerts (threat_level, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_threat_alerts_type ON threat_alerts (attack_type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_threat_alerts_status ON threat_alerts (status, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_threat_alerts_confidence ON threat_alerts (confidence_score DESC, timestamp DESC);

-- =============================================================================
-- SIEM INTEGRATION TABLES
-- =============================================================================

CREATE TABLE IF NOT EXISTS siem_configurations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    name VARCHAR(100) NOT NULL,
    siem_type VARCHAR(50) NOT NULL,
    base_url VARCHAR(500) NOT NULL,
    auth_type VARCHAR(50) NOT NULL,
    
    -- Authentication (encrypted)
    encrypted_credentials BYTEA,
    
    -- Configuration
    polling_interval_seconds INTEGER DEFAULT 60,
    max_events_per_poll INTEGER DEFAULT 1000,
    timeout_seconds INTEGER DEFAULT 30,
    default_query TEXT,
    time_field VARCHAR(100) DEFAULT 'timestamp',
    
    -- Webhooks
    webhook_enabled BOOLEAN DEFAULT false,
    webhook_secret_hash VARCHAR(255),
    
    -- Status
    enabled BOOLEAN DEFAULT true,
    last_successful_poll TIMESTAMPTZ,
    last_error TEXT,
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE IF NOT EXISTS siem_events (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL,
    siem_source VARCHAR(100) NOT NULL,
    event_id VARCHAR(255) NOT NULL,
    event_type VARCHAR(100) NOT NULL,
    severity VARCHAR(20) NOT NULL,
    category VARCHAR(100),
    
    -- Network information
    source_ip INET,
    destination_ip INET,
    source_port INTEGER,
    destination_port INTEGER,
    protocol VARCHAR(10),
    
    -- Asset information
    source_hostname VARCHAR(255),
    destination_hostname VARCHAR(255),
    username VARCHAR(100),
    asset VARCHAR(255),
    
    -- Event details
    title TEXT NOT NULL,
    description TEXT,
    signature VARCHAR(500),
    
    -- Raw and enriched data
    raw_event JSONB NOT NULL,
    geo_location JSONB,
    threat_intelligence JSONB,
    
    -- Correlation
    correlation_id UUID,
    parent_event_id UUID,
    
    -- Processing
    processed_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    correlated_threat_alert_id UUID REFERENCES threat_alerts(id)
);

-- Convert to hypertable
SELECT create_hypertable('siem_events', 'timestamp',
    chunk_time_interval => INTERVAL '6 hours',
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS idx_siem_events_source ON siem_events (siem_source, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_siem_events_type ON siem_events (event_type, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_siem_events_severity ON siem_events (severity, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_siem_events_correlation ON siem_events (correlation_id);
CREATE INDEX IF NOT EXISTS idx_siem_events_source_ip ON siem_events (source_ip, timestamp DESC);

-- =============================================================================
-- THREAT INTELLIGENCE TABLES
-- =============================================================================

CREATE TABLE IF NOT EXISTS threat_intelligence (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    ioc_type VARCHAR(50) NOT NULL, -- IP, domain, hash, etc.
    ioc_value VARCHAR(500) NOT NULL,
    threat_type VARCHAR(100) NOT NULL,
    confidence DECIMAL(5,4) NOT NULL CHECK (confidence >= 0 AND confidence <= 1),
    source VARCHAR(100) NOT NULL,
    first_seen TIMESTAMPTZ NOT NULL,
    last_seen TIMESTAMPTZ NOT NULL,
    tags TEXT[],
    metadata JSONB,
    
    -- Tracking
    created_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMPTZ DEFAULT CURRENT_TIMESTAMP,
    
    UNIQUE(ioc_type, ioc_value, source)
);

CREATE INDEX IF NOT EXISTS idx_threat_intel_ioc ON threat_intelligence (ioc_type, ioc_value);
CREATE INDEX IF NOT EXISTS idx_threat_intel_type ON threat_intelligence (threat_type, confidence DESC);
CREATE INDEX IF NOT EXISTS idx_threat_intel_source ON threat_intelligence (source, last_seen DESC);
CREATE INDEX IF NOT EXISTS idx_threat_intel_tags ON threat_intelligence USING GIN (tags);

-- =============================================================================
-- AUDIT AND LOGGING TABLES
-- =============================================================================

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    timestamp TIMESTAMPTZ NOT NULL DEFAULT CURRENT_TIMESTAMP,
    user_id UUID REFERENCES users(id),
    action VARCHAR(100) NOT NULL,
    resource VARCHAR(100) NOT NULL,
    resource_id VARCHAR(255),
    ip_address INET,
    user_agent TEXT,
    details JSONB,
    success BOOLEAN DEFAULT true,
    error_message TEXT
);

-- Convert to hypertable
SELECT create_hypertable('audit_logs', 'timestamp',
    chunk_time_interval => INTERVAL '1 day',
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs (user_id, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_action ON audit_logs (action, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_resource ON audit_logs (resource, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_audit_logs_success ON audit_logs (success, timestamp DESC);

-- =============================================================================
-- SYSTEM METRICS TABLES
-- =============================================================================

CREATE TABLE IF NOT EXISTS system_metrics (
    timestamp TIMESTAMPTZ NOT NULL,
    metric_name VARCHAR(100) NOT NULL,
    metric_value DECIMAL(15,6) NOT NULL,
    tags JSONB,
    source VARCHAR(100) NOT NULL
);

-- Convert to hypertable
SELECT create_hypertable('system_metrics', 'timestamp',
    chunk_time_interval => INTERVAL '1 hour',
    if_not_exists => TRUE
);

CREATE INDEX IF NOT EXISTS idx_system_metrics_name ON system_metrics (metric_name, timestamp DESC);
CREATE INDEX IF NOT EXISTS idx_system_metrics_source ON system_metrics (source, timestamp DESC);

-- =============================================================================
-- DATA RETENTION POLICIES
-- =============================================================================

-- Retain network packets for 30 days
SELECT add_retention_policy('network_packets', INTERVAL '30 days');

-- Retain anomaly reports for 90 days
SELECT add_retention_policy('anomaly_reports', INTERVAL '90 days');

-- Retain threat alerts for 1 year
SELECT add_retention_policy('threat_alerts', INTERVAL '1 year');

-- Retain SIEM events for 180 days
SELECT add_retention_policy('siem_events', INTERVAL '180 days');

-- Retain audit logs for 2 years (compliance)
SELECT add_retention_policy('audit_logs', INTERVAL '2 years');

-- Retain system metrics for 30 days
SELECT add_retention_policy('system_metrics', INTERVAL '30 days');

-- =============================================================================
-- CONTINUOUS AGGREGATES FOR ANALYTICS
-- =============================================================================

-- Hourly network traffic aggregates
CREATE MATERIALIZED VIEW IF NOT EXISTS network_traffic_hourly
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 hour', timestamp) AS bucket,
    source_ip,
    destination_ip,
    protocol,
    COUNT(*) AS packet_count,
    SUM(payload_size) AS total_bytes,
    AVG(payload_size) AS avg_packet_size,
    MIN(timestamp) AS first_packet,
    MAX(timestamp) AS last_packet
FROM network_packets
GROUP BY bucket, source_ip, destination_ip, protocol;

-- Daily threat alert aggregates
CREATE MATERIALIZED VIEW IF NOT EXISTS threat_alerts_daily
WITH (timescaledb.continuous) AS
SELECT 
    time_bucket('1 day', timestamp) AS bucket,
    threat_level,
    attack_type,
    COUNT(*) AS alert_count,
    AVG(confidence_score) AS avg_confidence,
    COUNT(*) FILTER (WHERE status = 'resolved') AS resolved_count,
    COUNT(*) FILTER (WHERE status = 'false_positive') AS false_positive_count
FROM threat_alerts
GROUP BY bucket, threat_level, attack_type;

-- =============================================================================
-- SAMPLE DATA AND DEFAULT USERS
-- =============================================================================

-- Create default admin user (password: admin123 - CHANGE IN PRODUCTION!)
INSERT INTO users (username, email, hashed_password, is_superuser) VALUES
('admin', 'admin@ctp.local', '$2b$12$LQv3c1yqBWVHxkd0LHAkCOYz6TtxMQJqhN8/LewKyNiYagDh.9Wd2', true)
ON CONFLICT (username) DO NOTHING;

-- Create default roles
INSERT INTO user_roles (user_id, role_name) 
SELECT id, 'admin' FROM users WHERE username = 'admin'
ON CONFLICT DO NOTHING;

-- =============================================================================
-- FUNCTIONS AND TRIGGERS
-- =============================================================================

-- Function to update the updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Triggers for updated_at
CREATE TRIGGER update_users_updated_at BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_siem_configurations_updated_at BEFORE UPDATE ON siem_configurations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_threat_intelligence_updated_at BEFORE UPDATE ON threat_intelligence
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- =============================================================================
-- GRANTS AND PERMISSIONS
-- =============================================================================

-- Grant permissions to application user
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO ctp_user;
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ctp_user;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO ctp_user;

-- =============================================================================
-- COMPLETION MESSAGE
-- =============================================================================

DO $$
BEGIN
    RAISE NOTICE 'Cyber Threat Platform database initialization completed successfully!';
    RAISE NOTICE 'TimescaleDB hypertables created for time-series data';
    RAISE NOTICE 'Default admin user created (username: admin, password: admin123)';
    RAISE NOTICE 'IMPORTANT: Change default passwords before production deployment!';
END $$;
