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

// Phase 11 Predictive Analytics & Forecasting Types
export type ForecastModelType =
  | "AUTO"
  | "NAIVE"
  | "SEASONAL_NAIVE"
  | "MOVING_AVERAGE"
  | "EXPONENTIAL_SMOOTHING"
  | "ARIMA"
  | "SARIMA";

export type ForecastStatus =
  | "PENDING"
  | "TRAINING"
  | "VALIDATING"
  | "FORECASTING"
  | "COMPLETED"
  | "FAILED"
  | "STALE";

export interface ForecastPoint {
  date: string;
  forecast: number;
  lower: number;
  upper: number;
}

export interface HistoricalPoint {
  date: string;
  actual: number;
}

export interface ForecastMetrics {
  mae: number;
  rmse: number;
  mape: number;
  smape: number;
  baseline_mae: number;
  relative_improvement_pct: number;
}

export interface ForecastDiagnostics {
  frequency_detected: string;
  observations_count: number;
  missing_periods_imputed: number;
  outliers_detected: number;
  seasonality_detected: boolean;
  seasonality_period?: number | null;
  stationarity_is_stationary: boolean;
  parameters: Record<string, unknown>;
  transformations: string[];
}

export interface ForecastResponse {
  id: string;
  dataset_id: string;
  dataset_version_id: string;
  target_field: string;
  time_field: string;
  frequency: string;
  forecast_horizon: number;
  confidence_level: number;
  requested_model_type: ForecastModelType;
  selected_model_name: string;
  status: ForecastStatus;
  metrics: ForecastMetrics;
  predictions: ForecastPoint[];
  historical_points: HistoricalPoint[];
  diagnostics: ForecastDiagnostics;
  provenance: Record<string, unknown>;
  error_message?: string | null;
  execution_time_ms: number;
  created_at: string;
}

export interface ForecastRunRequest {
  dataset_id: string;
  dataset_version_id?: string | null;
  target_field: string;
  time_field: string;
  frequency?: string | null;
  forecast_horizon?: number;
  confidence_level?: number;
  model_type?: ForecastModelType;
  allow_negative?: boolean;
  filters?: Array<{ field: string; operator: string; value: unknown }>;
}

export interface ForecastListResponse {
  items: ForecastResponse[];
  total: number;
}

// Phase 12 Anomaly Detection & Proactive Insight Intelligence Types
export type AnomalySeverity = "INFO" | "LOW" | "MEDIUM" | "HIGH" | "CRITICAL";
export type AnomalyType = "POINT" | "TREND" | "SEASONAL" | "MAGNITUDE" | "DISTRIBUTION" | "GROUP";
export type AnomalyStatus = "DETECTED" | "ACKNOWLEDGED" | "DISMISSED" | "RESOLVED";
export type DetectionMethod =
  | "Z_SCORE"
  | "ROBUST_Z_SCORE"
  | "IQR"
  | "ROLLING_BASELINE"
  | "SEASONAL_BASELINE"
  | "FORECAST_DEVIATION";
export type InsightType =
  | "ANOMALY"
  | "TREND_CHANGE"
  | "FORECAST_DEVIATION"
  | "CONTRIBUTION"
  | "DATA_QUALITY";

export interface RootCauseContributor {
  dimension_field: string;
  dimension_value: string;
  observed_value: number;
  baseline_value: number;
  delta: number;
  contribution_pct: number;
  narrative: string;
}

export interface AnomalyPoint {
  id: string;
  dataset_id: string;
  dataset_version_id: string;
  metric_field: string;
  dimension_field?: string | null;
  dimension_value?: string | null;
  period: string;
  observed_value: number;
  expected_value: number;
  deviation: number;
  deviation_pct: number;
  anomaly_score: number;
  severity: AnomalySeverity;
  anomaly_type: AnomalyType;
  detection_method: DetectionMethod;
  status: AnomalyStatus;
  root_causes: RootCauseContributor[];
  evidence: Record<string, unknown>;
  dedup_key: string;
  provenance: Record<string, unknown>;
  created_at: string;
}

export interface InsightResponse {
  id: string;
  dataset_id: string;
  anomaly_id?: string | null;
  insight_type: InsightType;
  title: string;
  summary: string;
  severity: AnomalySeverity;
  status: AnomalyStatus;
  evidence: Record<string, unknown>;
  dedup_key: string;
  feedback?: string | null;
  created_at: string;
}

export interface AnomalyDetectionRequest {
  dataset_id: string;
  dataset_version_id?: string | null;
  metric_fields?: string[];
  time_field?: string | null;
  dimension_fields?: string[];
  method?: DetectionMethod;
  sensitivity?: number;
  min_severity?: AnomalySeverity;
  allow_negative?: boolean;
}

export interface AnomalyDetectionResponse {
  dataset_id: string;
  dataset_version_id: string;
  anomalies: AnomalyPoint[];
  insights: InsightResponse[];
  total_anomalies_count: number;
  critical_count: number;
  high_count: number;
  medium_count: number;
  low_count: number;
  execution_time_ms: number;
  created_at: string;
}

export interface AnomalyListResponse {
  items: AnomalyPoint[];
  total: number;
}

export interface InsightListResponse {
  items: InsightResponse[];
  total: number;
}

// ==========================================
// Phase 13 — Decision Intelligence & Scenario Simulation Types
// ==========================================

export type ScenarioStatus =
  | "DRAFT"
  | "VALIDATED"
  | "RUNNING"
  | "COMPLETED"
  | "FAILED"
  | "EXPIRED";

export type ScenarioType =
  | "SINGLE_VARIABLE"
  | "MULTI_VARIABLE"
  | "SENSITIVITY"
  | "COMPARISON";

export type AssumptionOperation =
  | "PERCENTAGE_CHANGE"
  | "ABSOLUTE_CHANGE"
  | "MULTIPLICATIVE_FACTOR"
  | "SET_VALUE";

export interface AssumptionSpec {
  variable: string;
  operation: AssumptionOperation;
  value: number;
  unit?: string | null;
  description?: string | null;
}

export interface ScenarioProvenance {
  scenario_id: string;
  dataset_id: string;
  dataset_version_id: string;
  dataset_version_num?: number | null;
  baseline_source: string;
  engine_version: string;
  calculated_at: string;
  is_simulation: boolean;
  isolation_context: string;
}

export interface ScenarioResultResponse {
  id: string;
  name: string;
  description?: string | null;
  scenario_type: ScenarioType;
  status: ScenarioStatus;
  dataset_id: string;
  dataset_version_id: string;
  target_metric: string;
  baseline_source?: string;
  baseline_value: number;
  scenario_value: number;
  absolute_change: number;
  percentage_change?: number | null;
  assumptions: AssumptionSpec[];
  steps?: SensitivityStep[];
  comparisons?: ScenarioComparisonItem[];
  engine_version?: string;
  provenance: ScenarioProvenance | Record<string, unknown>;
  narrative?: string | null;
  reliability_notes?: string[];
  execution_time_ms?: number;
  created_at: string;
}

export interface SensitivityStep {
  step_index: number;
  variable: string;
  delta_pct?: number | null;
  delta_abs?: number | null;
  simulated_driver_value: number;
  outcome_value: number;
  absolute_change: number;
  percentage_change?: number | null;
}

export interface ScenarioComparisonItem {
  branch_name: string;
  is_baseline: boolean;
  assumptions: AssumptionSpec[];
  outcome_value: number;
  absolute_change: number;
  percentage_change?: number | null;
  narrative?: string | null;
}

export interface WhatIfScenarioRequest {
  dataset_id: string;
  dataset_version_id?: string | null;
  name?: string;
  description?: string | null;
  target_metric: string;
  assumptions: AssumptionSpec[];
  allow_negative?: boolean;
}

export interface SensitivityAnalysisRequest {
  dataset_id: string;
  dataset_version_id?: string | null;
  name?: string;
  target_metric: string;
  sweep_variable: string;
  min_pct?: number;
  max_pct?: number;
  step_pct?: number;
  allow_negative?: boolean;
}

export interface ScenarioBranchSpec {
  branch_name: string;
  assumptions: AssumptionSpec[];
}

export interface ScenarioComparisonRequest {
  dataset_id: string;
  dataset_version_id?: string | null;
  name?: string;
  target_metric: string;
  branches: ScenarioBranchSpec[];
  allow_negative?: boolean;
}

export interface ScenarioListResponse {
  items: ScenarioResultResponse[];
  total: number;
}

// ==========================================
// Phase 14 — Knowledge Intelligence & RAG Types
// ==========================================

export type DocumentProcessingStatus =
  | "UPLOADED"
  | "EXTRACTING"
  | "CHUNKED"
  | "EMBEDDED"
  | "INDEXED"
  | "READY"
  | "FAILED"
  | "STALE";

export type DocumentType =
  | "PDF"
  | "DOCX"
  | "TXT"
  | "MARKDOWN"
  | "CSV_REFERENCE"
  | "OTHER";

export type KnowledgeType =
  | "GENERAL_POLICY"
  | "KPI_DEFINITION"
  | "METRIC_FORMULA"
  | "BUSINESS_RULE"
  | "SOP"
  | "GLOSSARY"
  | "DOMAIN_GUIDE";

export interface KnowledgeCollectionResponse {
  id: string;
  user_id: string;
  name: string;
  description?: string | null;
  is_system: boolean;
  document_count: number;
  metadata_json: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeCollectionCreateRequest {
  name: string;
  description?: string | null;
  metadata?: Record<string, unknown>;
}

export interface KnowledgeDocumentResponse {
  id: string;
  collection_id?: string | null;
  collection_name?: string | null;
  user_id: string;
  title: string;
  filename: string;
  file_type: DocumentType;
  file_size_bytes: number;
  checksum: string;
  knowledge_type: KnowledgeType;
  status: DocumentProcessingStatus;
  current_version_num: number;
  chunk_count: number;
  error_message?: string | null;
  metadata: Record<string, unknown>;
  created_at: string;
  updated_at: string;
}

export interface KnowledgeDocumentListResponse {
  items: KnowledgeDocumentResponse[];
  total: number;
}

export interface KnowledgeChunkResponse {
  id: string;
  document_id: string;
  document_version_id: string;
  chunk_index: number;
  content: string;
  token_count: number;
  page_number?: number | null;
  section_heading?: string | null;
  has_embedding: boolean;
  metadata: Record<string, unknown>;
  created_at: string;
}

export interface KnowledgeDocumentVersionResponse {
  id: string;
  document_id: string;
  version_number: number;
  storage_reference: string;
  checksum: string;
  extracted_text_length: number;
  chunk_count: number;
  is_ocr: boolean;
  ocr_confidence?: number | null;
  status: DocumentProcessingStatus;
  created_at: string;
}

export interface KnowledgeSearchRequest {
  query: string;
  collection_id?: string | null;
  document_ids?: string[] | null;
  dataset_id?: string | null;
  knowledge_types?: KnowledgeType[] | null;
  top_k?: number;
  min_similarity?: number;
  include_full_chunks?: boolean;
}

export interface KnowledgeCitation {
  citation_index: number;
  document_id: string;
  document_title: string;
  document_version_id: string;
  version_number: number;
  page_number?: number | null;
  section_heading?: string | null;
  chunk_id: string;
  source_snippet: string;
  similarity_score: number;
}

export interface KnowledgeSearchResultItem {
  chunk_id: string;
  document_id: string;
  document_title: string;
  document_version_id: string;
  version_number: number;
  chunk_index: number;
  content: string;
  page_number?: number | null;
  section_heading?: string | null;
  similarity_score: number;
  citation_label: string;
  metadata: Record<string, unknown>;
}

export interface KnowledgeSearchResponse {
  query: string;
  results_count: number;
  execution_time_ms: number;
  results: KnowledgeSearchResultItem[];
  citations: KnowledgeCitation[];
  has_sufficient_evidence: boolean;
  notice?: string | null;
}

export interface DatasetKnowledgeLinkRequest {
  dataset_id: string;
  dataset_version_id?: string | null;
  document_id?: string | null;
  collection_id?: string | null;
  relationship_nature?: string;
}

export interface DatasetKnowledgeLinkResponse {
  id: string;
  dataset_id: string;
  dataset_version_id?: string | null;
  document_id?: string | null;
  document_title?: string | null;
  collection_id?: string | null;
  collection_name?: string | null;
  relationship_nature: string;
  created_at: string;
}

// Phase 15 Multi-Agent Intelligence Types
export type AgentID =
  | "supervisor"
  | "data_analyst"
  | "knowledge_agent"
  | "forecasting_agent"
  | "anomaly_agent"
  | "scenario_agent"
  | "visualization_agent"
  | "reporting_agent"
  | "critic_agent";

export type AITaskStatus =
  | "PENDING"
  | "RUNNING"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED"
  | "SKIPPED";

export type TaskType =
  | "PLANNING"
  | "DATA_ANALYSIS"
  | "KNOWLEDGE_RETRIEVAL"
  | "FORECAST"
  | "ANOMALY_DETECTION"
  | "SCENARIO_SIMULATION"
  | "VISUALIZATION_GENERATION"
  | "REPORT_GENERATION"
  | "VALIDATION"
  | "SYNTHESIS";

export type EvidenceType =
  | "DATA_FACT"
  | "KNOWLEDGE_FACT"
  | "CALCULATION"
  | "INTERPRETATION"
  | "ASSUMPTION";

export type ClaimType =
  | "METRIC_VALUE"
  | "BUSINESS_RULE"
  | "TREND_ASSERTION"
  | "ANOMALY_ASSERTION"
  | "SCENARIO_PROJECTION"
  | "CORRELATION";

export type ValidationStatus = "VERIFIED" | "CONTRADICTED" | "UNVERIFIED" | "INSUFFICIENT_EVIDENCE";

export interface EvidenceItem {
  id: string;
  evidence_type: EvidenceType;
  source_type: "DATASET" | "KNOWLEDGE_DOC" | "ENGINE_RESULT" | "CALCULATION" | "USER_INPUT";
  source_id: string;
  statement: string;
  confidence_score: number;
  data_payload?: Record<string, unknown>;
  citation_label?: string;
  created_at: string;
}

export interface ClaimItem {
  claim_id: string;
  claim_type: ClaimType;
  text: string;
  supporting_evidence_ids: string[];
  confidence: number;
}

export interface ValidationFinding {
  claim_id: string;
  status: ValidationStatus;
  evidence_id?: string;
  reason: string;
}

export interface ValidationReport {
  is_valid: boolean;
  overall_status: ValidationStatus;
  findings: ValidationFinding[];
  summary: string;
  verified_claims_count: number;
  unverified_claims_count: number;
  contradicted_claims_count: number;
}

export interface AgentMetadataResponse {
  agent_id: AgentID;
  name: string;
  description: string;
  system_role: string;
  capabilities: string[];
  allowed_tools: string[];
  max_token_budget: number;
  timeout_seconds: number;
}

export interface AITaskResponse {
  id: string;
  conversation_id: string;
  message_id?: string | null;
  agent_id: AgentID;
  task_type: TaskType;
  status: AITaskStatus;
  task_name: string;
  objective?: string | null;
  depends_on_task_ids: string[];
  execution_order: number;
  duration_ms?: number | null;
  tokens_used?: number | null;
  error_message?: string | null;
  validation_report?: ValidationReport | null;
  created_at: string;
}

// ==============================================================================
// Phase 16 MLOps & Model Monitoring Types
// ==============================================================================

export type MLModelType =
  | "FORECASTING"
  | "ANOMALY_DETECTION"
  | "CLASSIFICATION"
  | "REGRESSION"
  | "CLUSTERING"
  | "RECOMMENDATION"
  | "EMBEDDING"
  | "LLM_ADAPTER";

export type MLModelVersionStatus =
  | "DRAFT"
  | "VALIDATING"
  | "VALIDATED"
  | "STAGED"
  | "PRODUCTION"
  | "DEPRECATED"
  | "RETIRED"
  | "FAILED";

export type MLDeploymentEnvironment = "DEVELOPMENT" | "STAGING" | "PRODUCTION";
export type MLDeploymentStatus = "ACTIVE" | "INACTIVE" | "ROLLED_BACK";
export type MLAlertSeverity = "INFO" | "WARNING" | "CRITICAL";

export interface MLModelResponse {
  id: string;
  user_id: string;
  workspace_id?: string | null;
  name: string;
  description?: string | null;
  model_type: MLModelType;
  task_type: string;
  framework: string;
  provider: string;
  status: string;
  owner: string;
  tags: string[];
  metadata_json: Record<string, any>;
  versions_count: number;
  active_production_version?: string | null;
  health_status: string;
  created_at: string;
  updated_at: string;
}

export interface MLModelListResponse {
  items: MLModelResponse[];
  total: number;
}

export interface MLModelVersionResponse {
  id: string;
  model_id: string;
  model_name?: string | null;
  model_type?: MLModelType | null;
  version: string;
  artifact_location: string;
  checksum: string;
  training_dataset_id?: string | null;
  training_dataset_version_id?: string | null;
  feature_schema: Record<string, any>;
  preprocessing_version: string;
  parameters: Record<string, any>;
  metrics: Record<string, any>;
  baseline_metrics: Record<string, any>;
  status: MLModelVersionStatus;
  approval_record?: Record<string, any> | null;
  health_status: string;
  health_details: Record<string, any>;
  created_at: string;
  updated_at: string;
}

export interface MLModelEvaluationResponse {
  id: string;
  model_version_id: string;
  dataset_id?: string | null;
  dataset_version_id?: string | null;
  evaluation_type: string;
  metrics: Record<string, any>;
  baseline_comparison: Record<string, any>;
  passed_validation: boolean;
  warnings: string[];
  evaluated_at: string;
}

export interface MLModelDriftReportResponse {
  id: string;
  model_version_id: string;
  dataset_id?: string | null;
  dataset_version_id?: string | null;
  drift_detected: boolean;
  data_drift_score: number;
  feature_drift_results: Record<string, any>;
  prediction_drift_results: Record<string, any>;
  concept_drift_results: Record<string, any>;
  data_quality_results: Record<string, any>;
  recommendation: string;
  evaluated_at: string;
}

export interface MLModelAlertResponse {
  id: string;
  model_id: string;
  model_version_id?: string | null;
  model_name?: string | null;
  alert_type: string;
  severity: MLAlertSeverity;
  metric_name: string;
  observed_value: number;
  threshold: number;
  message: string;
  evidence: Record<string, any>;
  is_acknowledged: boolean;
  created_at: string;
}

export interface MLModelAlertListResponse {
  items: MLModelAlertResponse[];
  total: number;
}

export interface MLModelLineageNode {
  id: string;
  node_type: string;
  label: string;
  details: Record<string, any>;
}

export interface MLModelLineageEdge {
  source: string;
  target: string;
  relationship: string;
}

export interface MLModelLineageResponse {
  model_version_id: string;
  nodes: MLModelLineageNode[];
  edges: MLModelLineageEdge[];
}

export interface MLModelHealthDimension {
  score: number;
  status: "HEALTHY" | "WARNING" | "CRITICAL";
  details: Record<string, any>;
}

export interface MLModelHealthResponse {
  overall_health: "GOOD" | "WARNING" | "CRITICAL" | "UNKNOWN";
  overall_score: number;
  retraining_recommended: boolean;
  data_quality: MLModelHealthDimension;
  drift: MLModelHealthDimension;
  performance: MLModelHealthDimension;
  latency: MLModelHealthDimension;
  freshness: MLModelHealthDimension;
  recommendations: string[];
}

// =============================================================================
// PHASE 17 — ENTERPRISE DATA CONNECTORS & REAL-WORLD INGESTION
// =============================================================================

export type ConnectorType =
  | "POSTGRESQL"
  | "MYSQL"
  | "SQLITE"
  | "REST_API"
  | "OBJECT_STORAGE"
  | "GOOGLE_SHEETS"
  | "FILE";

export type ConnectionStatus =
  | "CONFIGURED"
  | "TESTING"
  | "ACTIVE"
  | "INACTIVE"
  | "FAILED"
  | "ERROR";

export type ConnectionHealthStatus = "HEALTHY" | "WARNING" | "ERROR" | "UNKNOWN";

export type SyncType = "FULL_SYNC" | "INCREMENTAL_SYNC";

export type SyncJobStatus =
  | "QUEUED"
  | "RUNNING"
  | "COMPLETED"
  | "FAILED"
  | "CANCELLED";

export interface ConnectorCatalogItem {
  connector_type: ConnectorType;
  name: string;
  category: string;
  description: string;
  supported_auth: string[];
  capabilities: string[];
  required_config: string[];
  is_available: boolean;
}

export interface ConnectorCatalogResponse {
  items: ConnectorCatalogItem[];
  total: number;
}

export interface DataConnection {
  id: string;
  user_id: string;
  workspace_id?: string | null;
  name: string;
  description?: string | null;
  connector_type: ConnectorType;
  status: ConnectionStatus;
  configuration: Record<string, any>;
  credential_reference?: string | null;
  last_tested_at?: string | null;
  last_sync_at?: string | null;
  health_status: ConnectionHealthStatus;
  health_details: Record<string, any>;
  sync_schedule?: string | null;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface ConnectionListResponse {
  items: DataConnection[];
  total: number;
}

export interface ConnectionTestResult {
  success: boolean;
  status: string;
  message: string;
  latency_ms: number;
  discovered_resources_count: number;
  tested_at: string;
}

export interface ResourceColumnSpec {
  name: string;
  data_type: string;
  nullable: boolean;
  is_primary_key: boolean;
}

export interface ResourceSpec {
  resource_id: string;
  name: string;
  resource_type: string;
  schema_name?: string | null;
  estimated_rows?: number | null;
  columns: ResourceColumnSpec[];
}

export interface SchemaDiscoveryResponse {
  connection_id: string;
  resources: ResourceSpec[];
  discovered_at: string;
}

export interface ResourcePreviewResponse {
  resource_id: string;
  columns: string[];
  data_types: Record<string, string>;
  rows: Array<Record<string, any>>;
  total_preview_rows: number;
  estimated_total_rows?: number | null;
}

export interface DataConnectionSyncJob {
  id: string;
  connection_id: string;
  dataset_id?: string | null;
  dataset_version_id?: string | null;
  source_resource: string;
  sync_type: SyncType;
  status: SyncJobStatus;
  started_at?: string | null;
  completed_at?: string | null;
  rows_processed: number;
  rows_added: number;
  rows_updated: number;
  rows_rejected: number;
  error?: string | null;
  sync_metadata: Record<string, any>;
  created_at: string;
}

export interface SchemaDriftReport {
  has_drift: boolean;
  added_columns: string[];
  removed_columns: string[];
  type_changes: Record<string, { previous_type: string; current_type: string }>;
  severity: "NONE" | "WARNING" | "CRITICAL";
  recommendation: string;
}

export interface ConnectionHealthResponse {
  connection_id: string;
  health_status: string;
  health_score: number;
  last_successful_sync?: string | null;
  freshness: {
    freshness_status: string;
    hours_since_sync?: number | null;
    is_stale: boolean;
    message: string;
  };
  drift_status: SchemaDriftReport;
  recommendations: string[];
}

// ==========================================
// Phase 18 — Production Security & Compliance Types
// ==========================================

export type SecurityRole = "owner" | "admin" | "analyst" | "member" | "viewer";
export type SecurityEvaluationStatus = "PASS" | "WARNING" | "FAIL" | "UNKNOWN";

export interface ScorecardDimension {
  id: string;
  name: string;
  status: SecurityEvaluationStatus;
  score: number;
  controls_enforced: string[];
  summary: string;
}

export interface SecurityScorecardResponse {
  overall_status: SecurityEvaluationStatus;
  overall_score: number;
  environment: string;
  config_audit: {
    environment: string;
    is_production_ready: boolean;
    issues: Array<{ category: string; severity: string; message: string }>;
    passed_checks: string[];
    total_checks: number;
  };
  dimensions: ScorecardDimension[];
  total_dimensions: number;
  passed_dimensions: number;
}

export interface ThreatVectorItem {
  id: string;
  profile: string;
  threat_description: string;
  entry_point: string;
  trust_boundary: string;
  mitigation_controls: string[];
  residual_risk: string;
}

export interface ThreatModelResponse {
  platform_name: string;
  updated_at: string;
  total_threat_vectors: number;
  trust_boundaries: string[];
  threat_vectors: ThreatVectorItem[];
}

export interface SecurityAuditLogResponse {
  id: string;
  timestamp: string;
  actor_id?: string | null;
  actor_email?: string | null;
  actor_role?: string | null;
  action: string;
  resource_type: string;
  resource_id?: string | null;
  workspace_id?: string | null;
  status: "success" | "denied" | "failed" | string;
  ip_address?: string | null;
  user_agent?: string | null;
  correlation_id?: string | null;
  details?: Record<string, any> | null;
}

export interface PasswordValidationResponse {
  is_valid: boolean;
  strength_score: number;
  violations: string[];
}

// ==========================================
// Phase 19 — Scalability, Performance & Observability Types
// ==========================================

export interface LatencyPercentiles {
  p50: number;
  p90: number;
  p95: number;
  p99: number;
  avg: number;
  min: number;
  max: number;
}

export interface EndpointMetric {
  endpoint: string;
  request_count: number;
  p50_ms: number;
  p95_ms: number;
  avg_ms: number;
}

export interface SystemTelemetryResponse {
  timestamp: string;
  uptime_seconds: number;
  total_requests: number;
  total_errors: number;
  error_rate_percent: number;
  requests_per_second: number;
  latency_ms: LatencyPercentiles;
  memory_usage_mb: number;
  cpu_usage_percent: number;
  ai_tokens_consumed: number;
  status_distribution: Record<string, number>;
  top_endpoints: EndpointMetric[];
}

export interface SLOStatusItem {
  id: string;
  name: string;
  category: string;
  target: string;
  current_value: number;
  metric_type: string;
  is_compliant: boolean;
  status: "COMPLIANT" | "BREACHED" | string;
}

export interface SystemAlertItem {
  id: string;
  severity: "INFO" | "WARNING" | "CRITICAL" | string;
  category: string;
  title: string;
  message: string;
  triggered_at: string;
  resolved: boolean;
}

export interface WorkloadDefinition {
  tier: "SMALL" | "MEDIUM" | "LARGE" | string;
  label: string;
  dataset_rows: number;
  document_count: number;
  concurrent_users: number;
  target_p95_ms: number;
  description: string;
}

export interface BenchmarkReport {
  tier: string;
  simulated_scale_multiplier: number;
  total_duration_ms: number;
  operations: Record<string, number>;
  p50_latency_ms: number;
  p95_latency_ms: number;
  throughput_ops_per_sec: number;
  tested_at: string;
  status: string;
}

export interface CacheStats {
  total_keys: number;
  max_capacity: number;
  hits: number;
  misses: number;
  total_lookups: number;
  hit_ratio_percent: number;
  evictions: number;
}

export interface DistributedTraceSpan {
  name: string;
  span_id: string;
  trace_id: string;
  parent_span_id?: string | null;
  duration_ms: number;
  status: string;
  error?: string | null;
  tags?: Record<string, any> | null;
}




