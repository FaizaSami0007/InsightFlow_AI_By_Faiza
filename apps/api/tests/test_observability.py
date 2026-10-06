"""Tests for Observability: PerformanceMetricsCollector, Prometheus export, Tracing, and SLO evaluation."""

import pytest
from httpx import ASGITransport, AsyncClient

from app.database.models.user import User
from app.main import app
from app.observability.alerts import alert_manager, SLOMonitor
from app.observability.metrics import PerformanceMetricsCollector
from app.observability.tracing import DistributedTracer, Span
from app.users.security import create_access_token
from tests.conftest import TestingSessionLocal


def test_metrics_collector_latency_percentiles():
    collector = PerformanceMetricsCollector(window_size=100)
    # Record 100 requests with ascending latencies 1..100ms
    for i in range(1, 101):
        collector.record_request(endpoint="/api/v1/analytics/query", duration_ms=float(i), status_code=200)

    telemetry = collector.get_system_telemetry()
    assert telemetry["total_requests"] == 100
    assert telemetry["total_errors"] == 0
    assert telemetry["error_rate_percent"] == 0.0

    lat = telemetry["latency_ms"]
    assert lat["p50"] == 51.0
    assert lat["p90"] == 91.0
    assert lat["p95"] == 96.0
    assert lat["p99"] == 100.0


def test_metrics_collector_prometheus_output():
    collector = PerformanceMetricsCollector(window_size=50)
    collector.record_request("/health", 15.0, 200)
    collector.record_ai_tokens(1500)

    prom = collector.get_prometheus_metrics()
    assert "insightflow_uptime_seconds" in prom
    assert "insightflow_requests_total" in prom
    assert "insightflow_ai_tokens_total 1500" in prom


def test_distributed_tracer_spans():
    tracer = DistributedTracer(max_traces=10)
    with Span("duckdb_aggregation_query", tags={"dataset_id": "ds-123"}) as span:
        # Simulate work
        sum(i for i in range(1000))

    tracer.record_span(span)
    traces = tracer.get_recent_traces(limit=5)
    assert len(traces) >= 1
    assert traces[-1]["name"] == "duckdb_aggregation_query"
    assert traces[-1]["duration_ms"] >= 0.0
    assert traces[-1]["status"] == "OK"


def test_slo_monitor_evaluation():
    slos = SLOMonitor.evaluate_slos()
    assert len(slos) == 6
    slo_ids = [s["id"] for s in slos]
    assert "slo_api_availability" in slo_ids
    assert "slo_analytics_latency" in slo_ids
    assert "slo_rag_latency" in slo_ids
    assert "slo_ingestion_success" in slo_ids
    assert "slo_sync_freshness" in slo_ids
    assert "slo_forecasting_latency" in slo_ids


def test_alert_manager_triggering():
    alert = alert_manager.trigger_alert(
        title="High Latency Warning",
        message="Analytics P95 exceeded 500ms threshold.",
        severity="WARNING",
    )
    assert alert["id"] is not None
    assert alert["title"] == "High Latency Warning"
    assert alert["resolved"] is False


@pytest.mark.asyncio
async def test_observability_api_endpoints():
    async with TestingSessionLocal() as db_session:
        user = User(
            id="test-obs-user-1",
            email="obs@test.com",
            password_hash="fakehash",
            full_name="Observability Admin",
            role="admin",
            is_active=True,
        )
        db_session.add(user)
        await db_session.commit()

    token = create_access_token({"sub": "test-obs-user-1", "email": "obs@test.com"})
    headers = {"Authorization": f"Bearer {token}"}

    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as client:
        # 1. Telemetry metrics
        res_m = await client.get("/api/v1/observability/metrics", headers=headers)
        assert res_m.status_code == 200
        data_m = res_m.json()
        assert "latency_ms" in data_m
        assert "uptime_seconds" in data_m

        # 2. Prometheus
        res_p = await client.get("/api/v1/observability/prometheus")
        assert res_p.status_code == 200
        assert "insightflow_requests_total" in res_p.text

        # 3. SLOs
        res_s = await client.get("/api/v1/observability/slos", headers=headers)
        assert res_s.status_code == 200
        assert len(res_s.json()) == 6

        # 4. Traces
        res_t = await client.get("/api/v1/observability/traces", headers=headers)
        assert res_t.status_code == 200
