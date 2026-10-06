"""Tests for MultiTenantCache, Invalidation, and Synthetic Benchmark Runner."""

import time
import pytest

from app.observability.benchmarks import BenchmarkRunner
from app.observability.cache import MultiTenantCache


def test_multi_tenant_cache_isolation():
    cache = MultiTenantCache(max_capacity=50)

    # Key for Workspace A
    k_a = MultiTenantCache.generate_key(
        workspace_id="ws-tenant-a",
        resource_type="dataset_profile",
        resource_id="ds-100",
        version=1,
    )
    # Key for Workspace B
    k_b = MultiTenantCache.generate_key(
        workspace_id="ws-tenant-b",
        resource_type="dataset_profile",
        resource_id="ds-100",
        version=1,
    )

    cache.set(k_a, {"summary": "Tenant A Sensitive Data"})
    cache.set(k_b, {"summary": "Tenant B Sensitive Data"})

    # Check isolation
    assert cache.get(k_a)["summary"] == "Tenant A Sensitive Data"
    assert cache.get(k_b)["summary"] == "Tenant B Sensitive Data"

    # Invalidate Tenant A
    evicted = cache.invalidate_tenant("ws-tenant-a")
    assert evicted == 1
    assert cache.get(k_a) is None
    assert cache.get(k_b)["summary"] == "Tenant B Sensitive Data"


def test_multi_tenant_cache_version_invalidation():
    cache = MultiTenantCache()

    k_v1 = MultiTenantCache.generate_key("ws-1", "dataset", "ds-alpha", version=1)
    k_v2 = MultiTenantCache.generate_key("ws-1", "dataset", "ds-alpha", version=2)

    cache.set(k_v1, "Data Version 1")
    cache.set(k_v2, "Data Version 2")

    assert cache.get(k_v1) == "Data Version 1"
    assert cache.get(k_v2) == "Data Version 2"

    # Invalidate all versions of ds-alpha
    evicted = cache.invalidate_resource("ws-1", "dataset", "ds-alpha")
    assert evicted == 2
    assert cache.get(k_v1) is None
    assert cache.get(k_v2) is None


def test_multi_tenant_cache_lru_capacity_and_stats():
    cache = MultiTenantCache(max_capacity=5)
    for i in range(10):
        cache.set(f"key_{i}", f"val_{i}")

    stats = cache.get_stats()
    assert stats["total_keys"] == 5
    assert stats["evictions"] == 5
    assert stats["max_capacity"] == 5


def test_benchmark_runner_tiers():
    defs = BenchmarkRunner.get_workload_definitions()
    assert len(defs) == 3
    tiers = [d["tier"] for d in defs]
    assert "SMALL" in tiers
    assert "MEDIUM" in tiers
    assert "LARGE" in tiers


def test_synthetic_benchmark_execution():
    report_small = BenchmarkRunner.run_synthetic_benchmark(tier="SMALL")
    assert report_small["tier"] == "SMALL"
    assert report_small["status"] == "PASS"
    assert report_small["total_duration_ms"] > 0.0
    assert "analytics_aggregation_ms" in report_small["operations"]
    assert "rag_vector_search_ms" in report_small["operations"]

    report_medium = BenchmarkRunner.run_synthetic_benchmark(tier="MEDIUM")
    assert report_medium["tier"] == "MEDIUM"
    assert report_medium["simulated_scale_multiplier"] == 5
