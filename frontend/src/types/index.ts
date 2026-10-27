export type TaskStatus = 
  | 'PENDING'
  | 'RUNNING'
  | 'PAUSED_FOR_INTERVENTION'
  | 'VERIFYING'
  | 'COMPLETED'
  | 'PARTIAL_COMPLETION'
  | 'FAILED'
  | 'CANCELLED';

export type TaskType = 
  | 'SEARCH_ONLY'
  | 'RESEARCH'
  | 'COMPARISON'
  | 'NAVIGATION'
  | 'EXTRACTION'
  | 'GENERAL';

export interface PerformanceMetrics {
  total_duration_seconds: number;
  search_duration_seconds: number;
  navigation_duration_seconds: number;
  extraction_duration_seconds: number;
  rag_duration_seconds: number;
  llm_duration_seconds: number;
  step_count: number;
  pages_visited: number;
  actions_retried: number;
}

export interface ExtractedEvidence {
  url: string;
  title: string;
  content: string;
  structured_data: Record<string, any>;
  observed_at: string;
  relevance_score: number;
  source_quality: string;
}

export interface VerificationReport {
  is_successful: boolean;
  confidence_score: number;
  evidence_coverage: number;
  reasons: string[];
  missing_information: string[];
  limitations: string[];
  status_verdict: TaskStatus;
}

export interface Action {
  id: string;
  action_type: string;
  description: string;
  params: Record<string, any>;
  status: string;
  retry_count: number;
}

export interface TaskState {
  task_id: string;
  query?: string;
  original_query: string;
  start_url?: string;
  max_depth?: number;
  max_pages?: number;
  task_type: TaskType;
  status: TaskStatus;
  current_step_index: number;
  visited_urls: string[];
  search_results?: any[];
  evidence_items?: ExtractedEvidence[];
  evidence?: ExtractedEvidence[];
  extracted_records?: Record<string, any>[];
  navigation_graph?: Array<{ from_url: string; to_url: string; depth: number; reason: string }>;
  interventions?: Array<{ obstacle: string; url: string; timestamp: number; resolved?: boolean }>;
  action_history?: Action[];
  logs: string[];
  final_answer?: string;
  verification_report?: VerificationReport;
  metrics: PerformanceMetrics;
  screenshot_path?: string;
  is_finished?: boolean;
  created_at: number;
  updated_at: number;
}

export interface MetricsSummary {
  total_tasks: number;
  successful_tasks: number;
  failed_tasks: number;
  partial_tasks: number;
  success_rate: number;
  failure_rate: number;
  avg_duration_seconds: number;
  total_pages_visited: number;
  avg_pages_per_task: number;
  total_retries: number;
  recovery_rate: number;
  evidence_coverage_avg: number;
  verification_pass_rate: number;
  captcha_count: number;
  recent_trends: Array<{ date: string; total: number; success: number; failed: number; avg_duration: number }>;
  task_types: Record<string, number>;
}

export interface ExperienceEntry {
  id: number;
  domain_or_topic: string;
  strategy_type: string;
  outcome: string;
  details: Record<string, any>;
  usage_count: number;
  last_observed: string;
}

export interface KnowledgeDocument {
  doc_id: string;
  title: string;
  source_type: 'local_document' | 'webpage' | 'experience';
  chunk_count: number;
  source_path_or_url: string;
  created_at: string;
}

export interface KnowledgeSearchResult {
  chunk_id: string;
  title: string;
  url: string;
  text: string;
  chunk_index: number;
  relevance_score: number;
  source_type: string;
  metadata: Record<string, any>;
}

export interface SafetyStatus {
  read_only_mode: boolean;
  block_private_ips: boolean;
  require_human_confirmation_on_high_risk: boolean;
  allowed_schemes: string[];
  blocked_schemes: string[];
  tracking_parameters_filtered: string[];
  consequential_action_triggers: string[];
  sensitive_form_input_keywords: string[];
  captcha_detection_active: boolean;
  is_paused_for_intervention: boolean;
}

export interface InterventionRequest {
  obstacle_type: string;
  url: string;
  message: string;
  timestamp: number;
  resolved: boolean;
  details: Record<string, any>;
}

export interface SystemHealth {
  status: string;
  app_name: string;
  version: string;
  uptime_seconds: number;
  database_connected: boolean;
  vector_store_ready: boolean;
  llm_provider: string;
  llm_available: boolean;
  browser_headless: boolean;
}
