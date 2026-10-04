export type SystemStatus = "healthy" | "degraded" | "unreachable" | "loading";

export interface User {
  id: string;
  email: string;
  full_name: string;
  is_active: boolean;
  created_at: string;
}

export interface TokenResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: User;
}

export interface DatasetVersion {
  id: string;
  dataset_id: string;
  version_number: number;
  file_name: string;
  file_format: "CSV" | "PARQUET";
  file_size: number;
  checksum: string;
  status: "UPLOADING" | "VALIDATING" | "READY" | "FAILED" | "ARCHIVED";
  row_count: number | null;
  column_count: number | null;
  created_at: string;
}

export interface Dataset {
  id: string;
  name: string;
  description: string | null;
  status: "UPLOADING" | "VALIDATING" | "READY" | "FAILED" | "ARCHIVED";
  created_at: string;
  updated_at: string;
  version_count: number;
  latest_version: DatasetVersion | null;
  versions?: DatasetVersion[];
}

export interface DatasetListResponse {
  items: Dataset[];
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

// Phase 3 Profiling & Semantics Types
export type ConceptualType =
  | "STRING"
  | "INTEGER"
  | "FLOAT"
  | "BOOLEAN"
  | "DATE"
  | "DATETIME"
  | "TIME"
  | "UNKNOWN";

export type SemanticRole =
  | "IDENTIFIER"
  | "DIMENSION"
  | "MEASURE"
  | "DATE"
  | "DATETIME"
  | "BOOLEAN"
  | "CATEGORY"
  | "TEXT"
  | "UNKNOWN";

export type ProfileStatus = "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";

export interface NumericStats {
  count: number;
  min: number;
  max: number;
  mean: number;
  median: number;
  std_dev: number;
  variance: number;
  q1: number;
  q2: number;
  q3: number;
  iqr: number;
  lower_bound: number;
  upper_bound: number;
  percentiles: Record<string, number>;
}

export interface CategoricalTopValue {
  value: string;
  count: number;
  percentage: number;
}

export interface CategoricalStats {
  top_values: CategoricalTopValue[];
  cardinality_ratio: number;
}

export interface TemporalStats {
  min_date: string | null;
  max_date: string | null;
}

export interface BooleanStats {
  true_count: number;
  false_count: number;
  null_count: number;
  true_percentage: number;
  false_percentage: number;
}

export interface ColumnProfile {
  id: string;
  column_name: string;
  normalized_name: string;
  ordinal_position: number;
  data_type: string;
  conceptual_type: ConceptualType;
  null_count: number;
  null_percentage: number;
  unique_count: number;
  unique_percentage: number;
  is_constant: boolean;
  is_near_constant: boolean;
  numeric_stats?: NumericStats | null;
  categorical_stats?: CategoricalStats | null;
  temporal_stats?: TemporalStats | null;
  boolean_stats?: BooleanStats | null;
  outlier_count: number;
  outlier_percentage: number;
}

export interface QualityWarning {
  rule: string;
  severity: "ERROR" | "WARNING" | "INFO";
  column?: string;
  message: string;
  details: Record<string, unknown>;
}

export interface DataQualityReport {
  id: string;
  overall_score: number;
  grade: "A" | "B" | "C" | "D" | "F";
  total_issues: number;
  missing_summary: {
    average_null_percentage: number;
    buckets: Record<string, number>;
    columns: Array<{
      column_name: string;
      null_count: number;
      null_percentage: number;
      bucket: string;
    }>;
  };
  duplicate_summary: {
    duplicate_rows: number;
    duplicate_percentage: number;
  };
  constant_columns: string[];
  outlier_summary: {
    numeric_columns_analyzed: number;
    columns_with_outliers: number;
    average_outlier_percentage: number;
    outlier_columns: Array<{
      column_name: string;
      outlier_count: number;
      outlier_percentage: number;
      lower_bound: number;
      upper_bound: number;
    }>;
  };
  warnings: QualityWarning[];
  created_at: string;
}

export interface SemanticColumn {
  id: string;
  column_name: string;
  inferred_role: SemanticRole;
  inferred_confidence: number;
  user_role?: SemanticRole | null;
  is_dimension: boolean;
  is_measure: boolean;
  is_identifier: boolean;
  is_temporal: boolean;
  possible_currency: boolean;
  description?: string | null;
  unit?: string | null;
  format_hint?: string | null;
}

export interface DatasetProfile {
  id: string;
  dataset_version_id: string;
  status: ProfileStatus;
  row_count: number | null;
  column_count: number | null;
  memory_size_bytes: number | null;
  duration_ms: number | null;
  error_message: string | null;
  column_profiles: ColumnProfile[];
  quality_report?: DataQualityReport | null;
  semantic_columns: SemanticColumn[];
  created_at: string;
  updated_at: string;
}

export interface AnalyticalQueryResponse {
  columns: string[];
  rows: unknown[][];
  row_count: number;
  execution_time_ms: number;
  metadata: Record<string, unknown>;
}

export interface ApiHealthResponse {
  status: string;
  service: string;
  environment: string;
  timestamp: string;
  version: string;
}

export interface ApiReadinessResponse {
  status: string;
  service: string;
  timestamp: string;
  checks: {
    database: string;
  };
}

export interface ApiErrorResponse {
  error: {
    code: string;
    message: string;
    details: Record<string, unknown>;
    request_id: string;
  };
}

// Phase 4 Analytics Types
export interface AnalysisProvenance {
  dataset_id: string;
  dataset_version_id: string;
  operation: string;
  parameters: Record<string, unknown>;
  filters?: Record<string, unknown> | null;
  execution_time_ms: number;
  tool_version: string;
  timestamp: string;
}

export interface AnalysisResponse {
  analysis_id: string;
  dataset_id: string;
  dataset_version_id: string;
  operation: string;
  status: "PENDING" | "RUNNING" | "COMPLETED" | "FAILED";
  columns: string[];
  rows: Record<string, unknown>[];
  summary?: Record<string, unknown> | null;
  execution_time_ms: number;
  row_count: number;
  provenance?: AnalysisProvenance | null;
  error_message?: string | null;
  created_at?: string | null;
}

export interface AnalysisToolMetadata {
  name: string;
  display_name: string;
  description: string;
  category: "descriptive" | "aggregation" | "statistical" | "temporal" | "filtering";
  required_params: string[];
  optional_params: string[];
  input_schema: Record<string, unknown>;
  output_schema: Record<string, unknown>;
  semantic_prerequisites: Record<string, unknown>;
}

export interface AnalysisHistoryItem {
  id: string;
  dataset_id: string;
  dataset_version_id: string;
  operation: string;
  status: string;
  execution_time_ms?: number | null;
  row_count?: number | null;
  created_at: string;
  error_message?: string | null;
}

// Phase 5 AI Analyst Types
export type MessageRole = "user" | "assistant" | "system" | "tool";

export interface ChatToolCall {
  id: string;
  name: string;
  arguments: Record<string, unknown>;
}

export interface ChatToolResult {
  tool_call_id: string;
  name: string;
  result: Record<string, unknown>;
  error?: string | null;
}

export interface AIMessageItem {
  id: string;
  role: MessageRole;
  content: string;
  tool_calls?: ChatToolCall[] | null;
  tool_results?: ChatToolResult[] | null;
  analysis_ids?: string[] | null;
  created_at: string;
}

export interface AIConversationSummary {
  id: string;
  title: string;
  dataset_id?: string | null;
  dataset_version_id?: string | null;
  created_at: string;
  updated_at: string;
}

export interface AIConversationDetail {
  id: string;
  title: string;
  dataset_id?: string | null;
  dataset_version_id?: string | null;
  created_at: string;
  updated_at: string;
  messages: AIMessageItem[];
}

export interface AIChatRequest {
  dataset_id?: string | null;
  dataset_version_id?: string | null;
  conversation_id?: string | null;
  message: string;
}

export interface AIChatResponse {
  conversation_id: string;
  message: string;
  tool_calls: ChatToolCall[];
  tool_results: ChatToolResult[];
  analysis_ids: string[];
  execution_steps: string[];
  citations: string[];
  needs_clarification: boolean;
  finish_reason: string;
  usage?: {
    prompt_tokens: number;
    completion_tokens: number;
    total_tokens: number;
  } | null;
}

