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
  visualization?: VisualizationSpec | null;
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
  message_id: string;
  message: string;
  tool_calls: ChatToolCall[];
  tool_results: ChatToolResult[];
  analysis_ids: string[];
  provenance: Record<string, unknown>[];
  suggested_questions?: string[];
  evidence?: {
    dataset_id: string;
    dataset_name: string;
    dataset_version_id: string;
    version_number: number;
    analysis_ids: string[];
    tool_operations: string[];
    provenance: Record<string, unknown>[];
  } | null;
  visualization?: VisualizationSpec | null;
  needs_clarification: boolean;
  execution_time_ms: number;
  tokens_used: number;
  created_at: string;
}

// Phase 7 Visualization Intelligence Types
export type ChartType =
  | "bar"
  | "horizontal_bar"
  | "line"
  | "area"
  | "pie"
  | "donut"
  | "scatter"
  | "histogram"
  | "boxplot"
  | "kpi"
  | "table";

export interface VisualizationProvenance {
  analysis_id: string;
  dataset_id: string;
  dataset_version_id: string;
  operation: string;
  row_count: number;
  created_at: string;
}

export interface VisualizationSpec {
  chart_type: ChartType;
  title: string;
  subtitle?: string | null;
  x_axis?: string | null;
  y_axis?: string | string[] | null;
  series?: string | null;
  sort?: "asc" | "desc" | "none" | null;
  limit?: number | null;
  format?: string | null;
  cardinality?: number | null;
  options?: Record<string, unknown>;
  provenance?: VisualizationProvenance | null;
  explanation?: string | null;
  is_fallback?: boolean;
  available_chart_types?: ChartType[];
}

export interface VisualizationRecommendRequest {
  analysis_id: string;
  preferred_chart_type?: ChartType | null;
  intent?: string | null;
}

export interface VisualizationValidateRequest {
  analysis_id: string;
  spec: VisualizationSpec;
}

export interface VisualizationValidationResult {
  valid: boolean;
  errors: string[];
  warnings: string[];
  validated_spec?: VisualizationSpec | null;
  fallback_spec?: VisualizationSpec | null;
}

export interface ChartTypeMetadata {
  chart_type: ChartType;
  label: string;
  description: string;
  required_axes: string[];
  max_cardinality?: number | null;
  min_values?: number | null;
  supports_series: boolean;
}

// Phase 8 Dashboard Intelligence Types
export type DashboardStatus = "GENERATING" | "READY" | "PARTIAL" | "FAILED";
export type DashboardWidgetType = "kpi" | "chart" | "table";

export interface DashboardWidget {
  id: string;
  dashboard_id: string;
  analysis_id: string | null;
  widget_type: DashboardWidgetType;
  title: string;
  description?: string | null;
  chart_spec?: VisualizationSpec | null;
  grid_x: number;
  grid_y: number;
  grid_w: number;
  grid_h: number;
  metadata?: Record<string, unknown>;
  analysis_status?: string | null;
  result_data?: {
    columns?: string[];
    rows?: Record<string, unknown>[];
  } | null;
  created_at: string;
  updated_at: string;
}

export interface DashboardFilter {
  id: string;
  dashboard_id: string;
  column_name: string;
  display_name: string;
  filter_type: "categorical" | "temporal" | "numeric";
  operator: string;
  current_value?: unknown;
  allowed_values?: unknown[] | null;
  scope: "global" | "widget";
  target_widget_ids: string[];
  created_at: string;
  updated_at: string;
}

export interface Dashboard {
  id: string;
  name: string;
  description?: string | null;
  dataset_id: string;
  dataset_name?: string | null;
  dataset_version_id: string;
  dataset_version_num?: number | null;
  user_id: string;
  status: DashboardStatus;
  theme: string;
  layout_type: string;
  layout_config: Record<string, unknown>;
  metadata: Record<string, unknown>;
  widgets: DashboardWidget[];
  filters: DashboardFilter[];
  created_at: string;
  updated_at: string;
}

export interface DashboardPlanWidget {
  title: string;
  description?: string | null;
  widget_type: DashboardWidgetType;
  operation: string;
  params: Record<string, unknown>;
  preferred_chart_type?: ChartType | null;
  grid_w: number;
  grid_h: number;
}

export interface DashboardPlan {
  title: string;
  purpose: string;
  dataset_id: string;
  dataset_version_id: string;
  widgets: DashboardPlanWidget[];
  suggested_filters: string[];
  reasoning_summary?: string | null;
}

export interface DashboardPatch {
  op:
    | "ADD_WIDGET"
    | "REMOVE_WIDGET"
    | "MOVE_WIDGET"
    | "RESIZE_WIDGET"
    | "CHANGE_CHART"
    | "CHANGE_METRIC"
    | "CHANGE_FILTER"
    | "RENAME_DASHBOARD";
  widget_id?: string | null;
  params: Record<string, unknown>;
}

export interface DashboardQualityReport {
  overall_score: number;
  valid_widget_ratio: number;
  visual_diversity_score: number;
  redundancy_penalty: number;
  data_coverage_score: number;
  breakdown: Record<string, unknown>;
}

export interface DashboardGenerateRequest {
  dataset_id: string;
  dataset_version_id: string;
  purpose?: string | null;
  intent?: string | null;
  min_widgets?: number;
  max_widgets?: number;
}

// Phase 9 Export & Sharing Types
export type ExportFormat = "pdf" | "png" | "csv" | "json";
export type ExportStatus = "PENDING" | "PROCESSING" | "COMPLETED" | "FAILED" | "EXPIRED";

export interface ExportRequest {
  format?: ExportFormat;
  page_size?: "A4" | "Letter";
  orientation?: "landscape" | "portrait";
  include_provenance?: boolean;
  include_filters?: boolean;
  title_override?: string | null;
  filter_values?: Record<string, unknown> | null;
  widget_id?: string | null;
}

export interface ExportResponse {
  id: string;
  dashboard_id: string;
  user_id: string;
  format: ExportFormat;
  status: ExportStatus;
  title: string;
  file_size_bytes?: number | null;
  content_type: string;
  filter_snapshot: Record<string, unknown>;
  metadata_snapshot: Record<string, unknown>;
  error_message?: string | null;
  download_url: string;
  expires_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ExportListResponse {
  items: ExportResponse[];
  total: number;
}

export interface ShareCreateRequest {
  expires_in_days?: number | null;
  is_snapshot?: boolean;
  allowed_filters?: string[];
}

export interface ShareResponse {
  id: string;
  dashboard_id: string;
  owner_id: string;
  share_token: string;
  share_url: string;
  access_type: string;
  is_active: boolean;
  is_snapshot: boolean;
  allowed_filters: string[];
  view_count: number;
  last_accessed_at?: string | null;
  expires_at?: string | null;
  created_at: string;
  updated_at: string;
}

export interface ShareListResponse {
  items: ShareResponse[];
  total: number;
}

export interface SharedDashboardViewResponse {
  share_token: string;
  dashboard_id: string;
  title: string;
  description?: string | null;
  dataset_id: string;
  dataset_version_id: string;
  is_snapshot: boolean;
  status: string;
  theme: string;
  layout_type: string;
  layout_config: Record<string, unknown>;
  widgets: DashboardWidget[];
  filters: DashboardFilter[];
  allowed_filters: string[];
  created_at: string;
  updated_at: string;
}

export interface SharedFilterRefreshRequest {
  filter_values: Record<string, unknown>;
}

// ==========================================
// Phase 10 — Multi-Dataset & Federation Types
// ==========================================

export type RelationshipType = "ONE_TO_ONE" | "ONE_TO_MANY" | "MANY_TO_ONE" | "MANY_TO_MANY";
export type RelationshipStatus = "PROPOSED" | "VALIDATED" | "REJECTED" | "DISABLED";

export interface DatasetCollectionItem {
  id: string;
  collection_id: string;
  dataset_id: string;
  dataset_version_id?: string | null;
  dataset?: Dataset | null;
  created_at: string;
}

export interface DatasetRelationship {
  id: string;
  collection_id?: string | null;
  user_id: string;
  source_dataset_id: string;
  source_version_id: string;
  source_field: string;
  target_dataset_id: string;
  target_version_id: string;
  target_field: string;
  relationship_type: RelationshipType;
  status: RelationshipStatus;
  coverage_ratio: number;
  source_unique_ratio: number;
  target_unique_ratio: number;
  null_rate: number;
  quality_score: number;
  evidence: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface DatasetCollection {
  id: string;
  name: string;
  description?: string | null;
  user_id: string;
  metadata_json: Record<string, unknown>;
  items: DatasetCollectionItem[];
  relationships: DatasetRelationship[];
  created_at: string;
  updated_at: string;
}

export interface DiscoveredRelationshipCandidate {
  source_dataset_id: string;
  source_dataset_name: string;
  source_field: string;
  target_dataset_id: string;
  target_dataset_name: string;
  target_field: string;
  inferred_type: RelationshipType;
  confidence: number;
  reason: string;
}

export interface DiscoveryResponse {
  candidates: DiscoveredRelationshipCandidate[];
  total: number;
}

export interface FederatedAggregationSpec {
  field: string;
  agg: "SUM" | "AVG" | "COUNT" | "COUNT_DISTINCT" | "MIN" | "MAX";
  alias?: string | null;
}

export interface FederatedFilterSpec {
  field: string;
  operator: "=" | "!=" | ">" | "<" | ">=" | "<=" | "LIKE" | "IN";
  value: unknown;
}

export interface FederatedAnalysisRequest {
  dataset_version_ids: string[];
  dimensions: string[];
  measures: FederatedAggregationSpec[];
  filters?: FederatedFilterSpec[];
  sort_by?: string | null;
  sort_order?: "ASC" | "DESC";
  limit?: number;
}

export interface FederatedAnalysisResponse {
  analysis_id: string;
  columns: string[];
  rows: Record<string, unknown>[];
  row_count: number;
  execution_time_ms: number;
  datasets_involved: Array<{
    dataset_id: string;
    dataset_version_id: string;
    version_num: number;
  }>;
  relationships_used: Array<{
    id: string;
    source: string;
    target: string;
    type: string;
  }>;
  join_path_description: string;
  provenance: Record<string, unknown>;
  warnings: string[];
}



