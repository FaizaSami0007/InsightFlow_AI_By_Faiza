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
