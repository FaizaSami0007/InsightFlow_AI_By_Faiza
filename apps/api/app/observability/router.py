"""API router for Phase 19 Observability, Telemetry, SLOs, Benchmarks & Tracing."""

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, Query, Response, status

from app.database.models.user import User
from app.observability.alerts import alert_manager, SLOMonitor
from app.observability.benchmarks import BenchmarkRunner
from app.observability.cache import cache_manager
from app.observability.metrics import metrics_collector
from app.observability.schemas import (
    BenchmarkReport,
    CacheStats,
    DistributedTraceSpan,
    SLOStatusItem,
    SystemAlertItem,
    SystemTelemetryResponse,
    WorkloadDefinition,
)
from app.observability.tracing import tracer
from app.users.dependencies import get_current_user

router = APIRouter(prefix="/observability", tags=["Observability & Performance"])


@router.get("/metrics", response_model=SystemTelemetryResponse, summary="Get Live System Performance Telemetry")
async def get_metrics(
    current_user: User = Depends(get_current_user),
) -> SystemTelemetryResponse:
    """Retrieve real-time latency percentiles, throughput (RPS), memory, CPU, and AI token metrics."""
    telemetry = metrics_collector.get_system_telemetry()
    return SystemTelemetryResponse(**telemetry)


@router.get("/prometheus", summary="Prometheus Exposition Format Metrics")
async def get_prometheus_metrics() -> Response:
    """Export standard Prometheus text-format metrics for scraping."""
    prom_text = metrics_collector.get_prometheus_metrics()
    return Response(content=prom_text, media_type="text/plain; version=0.0.4")


@router.get("/slos", response_model=List[SLOStatusItem], summary="Get Service Level Objectives (SLOs) Status")
async def get_slos(
    current_user: User = Depends(get_current_user),
) -> List[SLOStatusItem]:
    """Retrieve evaluated SLO targets, compliance percentages, and SLA breach indicators."""
    slos = SLOMonitor.evaluate_slos()
    return [SLOStatusItem(**slo) for slo in slos]


@router.get("/alerts", response_model=List[SystemAlertItem], summary="Get System Health & Performance Alerts")
async def get_alerts(
    current_user: User = Depends(get_current_user),
) -> List[SystemAlertItem]:
    """Retrieve active system health alerts and threshold warnings."""
    alerts = alert_manager.get_active_alerts()
    return [SystemAlertItem(**alert) for alert in alerts]


@router.get(
    "/benchmarks/definitions",
    response_model=List[WorkloadDefinition],
    summary="Get Workload Tier Definitions",
)
async def get_workload_definitions(
    current_user: User = Depends(get_current_user),
) -> List[WorkloadDefinition]:
    """Return specifications for Small, Medium, and Large workload categories."""
    defs = BenchmarkRunner.get_workload_definitions()
    return [WorkloadDefinition(**d) for d in defs]


@router.post(
    "/benchmarks/run",
    response_model=BenchmarkReport,
    summary="Run Synthetic Capacity Benchmark Test",
)
async def run_benchmark(
    tier: str = Query("SMALL", description="Workload tier (SMALL, MEDIUM, LARGE)"),
    current_user: User = Depends(get_current_user),
) -> BenchmarkReport:
    """Execute synthetic load micro-benchmarks measuring DuckDB, RAG cosine search, and ingestion throughput."""
    report = BenchmarkRunner.run_synthetic_benchmark(tier=tier)
    return BenchmarkReport(**report)


@router.get("/cache/stats", response_model=CacheStats, summary="Get Multi-Tenant Cache Statistics")
async def get_cache_stats(
    current_user: User = Depends(get_current_user),
) -> CacheStats:
    """Retrieve cache hit ratios, memory key count, and eviction statistics."""
    stats = cache_manager.get_stats()
    return CacheStats(**stats)


@router.post("/cache/clear", summary="Clear In-Memory Cache")
async def clear_cache(
    current_user: User = Depends(get_current_user),
) -> Dict[str, str]:
    """Purge in-memory multi-tenant cache."""
    cache_manager.clear()
    return {"status": "ok", "message": "Cache successfully cleared."}


@router.get("/traces", response_model=List[DistributedTraceSpan], summary="Get Recent Distributed Trace Spans")
async def get_traces(
    limit: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
) -> List[DistributedTraceSpan]:
    """Retrieve recent distributed trace spans and request execution breakdowns."""
    traces = tracer.get_recent_traces(limit=limit)
    return [DistributedTraceSpan(**t) for t in traces]
