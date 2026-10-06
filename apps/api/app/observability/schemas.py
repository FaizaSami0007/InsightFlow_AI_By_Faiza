"""Pydantic V2 Schemas for Phase 19 Observability, Telemetry & Performance APIs."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class LatencyPercentiles(BaseModel):
    p50: float
    p90: float
    p95: float
    p99: float
    avg: float
    min: float
    max: float


class EndpointMetric(BaseModel):
    endpoint: str
    request_count: int
    p50_ms: float
    p95_ms: float
    avg_ms: float


class SystemTelemetryResponse(BaseModel):
    timestamp: str
    uptime_seconds: float
    total_requests: int
    total_errors: int
    error_rate_percent: float
    requests_per_second: float
    latency_ms: LatencyPercentiles
    memory_usage_mb: float
    cpu_usage_percent: float
    ai_tokens_consumed: int
    status_distribution: Dict[str, int]
    top_endpoints: List[EndpointMetric]


class SLOStatusItem(BaseModel):
    id: str
    name: str
    category: str
    target: str
    current_value: float
    metric_type: str
    is_compliant: bool
    status: str


class SystemAlertItem(BaseModel):
    id: str
    severity: str
    category: str
    title: str
    message: str
    triggered_at: str
    resolved: bool


class WorkloadDefinition(BaseModel):
    tier: str
    label: str
    dataset_rows: int
    document_count: int
    concurrent_users: int
    target_p95_ms: float
    description: str


class BenchmarkReport(BaseModel):
    tier: str
    simulated_scale_multiplier: int
    total_duration_ms: float
    operations: Dict[str, float]
    p50_latency_ms: float
    p95_latency_ms: float
    throughput_ops_per_sec: float
    tested_at: str
    status: str


class CacheStats(BaseModel):
    total_keys: int
    max_capacity: int
    hits: int
    misses: int
    total_lookups: int
    hit_ratio_percent: float
    evictions: int


class DistributedTraceSpan(BaseModel):
    name: str
    span_id: str
    trace_id: str
    parent_span_id: Optional[str] = None
    duration_ms: float
    status: str
    error: Optional[str] = None
    tags: Optional[Dict[str, Any]] = None
