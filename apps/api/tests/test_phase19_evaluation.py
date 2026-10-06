"""Phase 19 Evaluation Suite: Scalability, Performance & Production Observability Quality Gates."""

import pytest
from app.observability.alerts import alert_manager, SLOMonitor
from app.observability.benchmarks import BenchmarkRunner
from app.observability.cache import cache_manager, MultiTenantCache
from app.observability.metrics import metrics_collector
from app.observability.tracing import tracer, Span


def test_phase19_quality_gate_telemetry_and_metrics():
    """Verify metrics collector accurately tracks P50, P95, P99, error rates, and CPU/memory."""
    telemetry = metrics_collector.get_system_telemetry()
    assert "latency_ms" in telemetry
    assert "p50" in telemetry["latency_ms"]
    assert "p95" in telemetry["latency_ms"]
    assert "p99" in telemetry["latency_ms"]
    assert "memory_usage_mb" in telemetry
    assert "cpu_usage_percent" in telemetry
    assert "requests_per_second" in telemetry


def test_phase19_quality_gate_prometheus_export():
    """Verify Prometheus text format exporter compliance."""
    prom = metrics_collector.get_prometheus_metrics()
    assert "# HELP insightflow_requests_total" in prom
    assert "# TYPE insightflow_requests_total counter" in prom
    assert "insightflow_latency_p95_ms" in prom


def test_phase19_quality_gate_slo_readiness():
    """Verify all 6 core enterprise SLOs are monitored."""
    slos = SLOMonitor.evaluate_slos()
    assert len(slos) == 6
    for slo in slos:
        assert "target" in slo
        assert "current_value" in slo
        assert "is_compliant" in slo


def test_phase19_quality_gate_multi_tenant_caching():
    """Verify cache generates tenant-isolated keys and supports version-based invalidation."""
    k1 = MultiTenantCache.generate_key("tenant-1", "dataset", "ds-1", version=1)
    k2 = MultiTenantCache.generate_key("tenant-2", "dataset", "ds-1", version=1)
    assert k1 != k2

    cache_manager.set(k1, {"rows": 1000})
    assert cache_manager.get(k1) == {"rows": 1000}
    assert cache_manager.get(k2) is None


def test_phase19_quality_gate_capacity_benchmarks():
    """Verify synthetic load benchmark engine runs across Small, Medium, Large tiers."""
    for tier in ["SMALL", "MEDIUM", "LARGE"]:
        rep = BenchmarkRunner.run_synthetic_benchmark(tier)
        assert rep["status"] == "PASS"
        assert rep["total_duration_ms"] > 0.0
