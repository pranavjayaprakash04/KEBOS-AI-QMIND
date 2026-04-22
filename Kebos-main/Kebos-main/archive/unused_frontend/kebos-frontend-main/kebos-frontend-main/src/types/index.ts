// Common types used throughout the application

export interface User {
  id: string;
  username: string;
  email: string;
  role: UserRole;
  permissions: string[];
  created_at: string;
  last_login?: string;
  is_active: boolean;
}

export enum UserRole {
  ADMIN = 'admin',
  ANALYST = 'analyst',
  VIEWER = 'viewer',
  OPERATOR = 'operator'
}

export interface AuthState {
  user: User | null;
  token: string | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

// Threat Detection Types
export interface ThreatDetection {
  id: string;
  timestamp: string;
  threat_type: ThreatType;
  severity: ThreatSeverity;
  source_ip: string;
  destination_ip: string;
  protocol: string;
  payload: any;
  confidence_score: number;
  status: DetectionStatus;
  description: string;
  recommendations?: string[];
}

export enum ThreatType {
  MALWARE = 'malware',
  PHISHING = 'phishing',
  INTRUSION = 'intrusion',
  DDoS = 'ddos',
  DATA_EXFILTRATION = 'data_exfiltration',
  VULNERABILITY_EXPLOIT = 'vulnerability_exploit',
  ANOMALY = 'anomaly'
}

export enum ThreatSeverity {
  LOW = 'low',
  MEDIUM = 'medium',
  HIGH = 'high',
  CRITICAL = 'critical'
}

export enum DetectionStatus {
  ACTIVE = 'active',
  INVESTIGATING = 'investigating',
  RESOLVED = 'resolved',
  FALSE_POSITIVE = 'false_positive'
}

export interface ThreatMetrics {
  total_detections: number;
  critical_threats: number;
  high_threats: number;
  medium_threats: number;
  low_threats: number;
  detection_accuracy: number;
  false_positive_rate: number;
  avg_response_time: number;
  threats_by_type: Record<ThreatType, number>;
}

// GenAI Assistant Types
export interface ChatMessage {
  id: string;
  content: string;
  role: 'user' | 'assistant';
  timestamp: string;
  message_type?: MessageType;
  metadata?: MessageMetadata;
}

export enum MessageType {
  QUERY = 'query',
  THREAT_ANALYSIS = 'threat_analysis',
  RECOMMENDATION = 'recommendation',
  ALERT = 'alert',
  REPORT = 'report'
}

export interface MessageMetadata {
  query_type?: string;
  processing_time?: number;
  confidence?: number;
  sources?: string[];
  related_threats?: string[];
}

export interface AssistantMetrics {
  total_queries: number;
  avg_response_time: number;
  user_satisfaction: number;
  query_types: Record<string, number>;
  conversation_length: number;
}

export interface ThreatNarrative {
  id: string;
  title: string;
  content: string;
  threat_id: string;
  generated_at: string;
  template_used: string;
  parameters: Record<string, any>;
}

// Audit Types
export interface AuditLog {
  id: string;
  timestamp: string;
  user_id: string;
  user_email: string;
  action: AuditAction;
  resource_type: string;
  resource_id?: string;
  details: Record<string, any>;
  ip_address: string;
  user_agent: string;
  status: 'success' | 'failure';
}

export enum AuditAction {
  LOGIN = 'login',
  LOGOUT = 'logout',
  CREATE = 'create',
  READ = 'read',
  UPDATE = 'update',
  DELETE = 'delete',
  EXPORT = 'export',
  IMPORT = 'import',
  CONFIGURE = 'configure'
}

export interface AuditMetrics {
  total_actions: number;
  successful_actions: number;
  failed_actions: number;
  unique_users: number;
  actions_by_type: Record<AuditAction, number>;
  actions_by_hour: number[];
}

// Job Management Types
export interface Job {
  id: string;
  name: string;
  type: JobType;
  status: JobStatus;
  priority: JobPriority;
  created_at: string;
  started_at?: string;
  completed_at?: string;
  progress: number;
  result?: any;
  error_message?: string;
  parameters: Record<string, any>;
  estimated_duration?: number;
  actual_duration?: number;
}

export enum JobType {
  THREAT_SCAN = 'threat_scan',
  DATA_ANALYSIS = 'data_analysis',
  REPORT_GENERATION = 'report_generation',
  SYSTEM_BACKUP = 'system_backup',
  MODEL_TRAINING = 'model_training',
  DATA_EXPORT = 'data_export'
}

export enum JobStatus {
  PENDING = 'pending',
  RUNNING = 'running',
  COMPLETED = 'completed',
  FAILED = 'failed',
  CANCELLED = 'cancelled'
}

export enum JobPriority {
  LOW = 'low',
  NORMAL = 'normal',
  HIGH = 'high',
  URGENT = 'urgent'
}

export interface JobMetrics {
  total_jobs: number;
  running_jobs: number;
  completed_jobs: number;
  failed_jobs: number;
  avg_execution_time: number;
  job_queue_length: number;
  jobs_by_type: Record<JobType, number>;
  success_rate: number;
}

// Chart and Visualization Types
export interface ChartData {
  labels: string[];
  datasets: ChartDataset[];
}

export interface ChartDataset {
  label: string;
  data: number[];
  backgroundColor?: string | string[];
  borderColor?: string | string[];
  borderWidth?: number;
  fill?: boolean;
}

export interface ChartOptions {
  responsive: boolean;
  maintainAspectRatio: boolean;
  plugins?: {
    legend?: {
      display: boolean;
      position?: 'top' | 'bottom' | 'left' | 'right';
    };
    title?: {
      display: boolean;
      text: string;
    };
  };
  scales?: {
    [key: string]: {
      display?: boolean;
      title?: {
        display: boolean;
        text: string;
      };
    };
  };
}

// Dashboard Types
export interface DashboardMetrics {
  threat_metrics: ThreatMetrics;
  assistant_metrics: AssistantMetrics;
  audit_metrics: AuditMetrics;
  job_metrics: JobMetrics;
  system_health: SystemHealth;
}

export interface SystemHealth {
  overall_status: 'healthy' | 'warning' | 'critical';
  services: ServiceStatus[];
  uptime: number;
  last_update: string;
}

export interface ServiceStatus {
  name: string;
  status: 'online' | 'offline' | 'degraded';
  response_time?: number;
  last_check: string;
  url?: string;
}

// API Response Types
export interface ApiResponse<T = any> {
  success: boolean;
  data?: T;
  message?: string;
  error?: string;
  timestamp: string;
}

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  per_page: number;
  pages: number;
  has_next: boolean;
  has_prev: boolean;
}

// WebSocket Types
export interface WebSocketMessage<T = any> {
  type: string;
  data: T;
  timestamp: string;
  id?: string;
}

export interface ThreatAlert extends WebSocketMessage<ThreatDetection> {
  type: 'threat_alert';
}

export interface JobUpdate extends WebSocketMessage<Job> {
  type: 'job_update';
}

export interface SystemUpdate extends WebSocketMessage<SystemHealth> {
  type: 'system_update';
}

// Form Types
export interface LoginForm {
  username: string;
  password: string;
  remember_me?: boolean;
}

export interface ThreatConfigForm {
  detection_sensitivity: number;
  alert_threshold: number;
  notification_email: string;
  auto_response_enabled: boolean;
  blocked_ips: string[];
}

export interface JobConfigForm {
  name: string;
  type: JobType;
  priority: JobPriority;
  schedule?: string;
  parameters: Record<string, any>;
  notification_enabled: boolean;
}

// Navigation Types
export interface NavigationItem {
  id: string;
  label: string;
  path: string;
  icon: string;
  permission?: string;
  children?: NavigationItem[];
}

// Theme Types
export interface ThemeState {
  primaryColor: string;
  sidebarCollapsed: boolean;
  isSidebarOpen: boolean;
}

// Error Types
export interface AppError {
  code: string;
  message: string;
  details?: any;
  timestamp: string;
}

// Settings Types
export interface UserSettings {
  theme: 'light' | 'dark' | 'auto';
  notifications: {
    email: boolean;
    push: boolean;
    threat_alerts: boolean;
    job_updates: boolean;
  };
  dashboard: {
    refresh_interval: number;
    default_time_range: string;
    auto_refresh: boolean;
  };
  language: string;
  timezone: string;
}
