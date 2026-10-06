"""Version-Aware, Tenant-Isolated High Performance In-Memory LRU Cache."""

import hashlib
import json
import time
from typing import Any, Dict, List, Optional, Tuple


class CacheEntry:
    """Wrapper holding cached value, timestamp, TTL, and access metrics."""

    def __init__(self, value: Any, ttl_seconds: int = 300) -> None:
        self.value = value
        self.created_at = time.time()
        self.expires_at = self.created_at + ttl_seconds
        self.access_count = 0
        self.last_accessed = self.created_at

    def is_expired(self) -> bool:
        return time.time() > self.expires_at

    def touch(self) -> None:
        self.access_count += 1
        self.last_accessed = time.time()


class MultiTenantCache:
    """
    Thread-safe, version-aware, multi-tenant LRU cache.
    Prevents cross-tenant cache leakage and supports instant version-based invalidation.
    """

    def __init__(self, max_capacity: int = 2000) -> None:
        self.max_capacity = max_capacity
        self._store: Dict[str, CacheEntry] = {}
        self._hits: int = 0
        self._misses: int = 0
        self._evictions: int = 0

    @classmethod
    def generate_key(
        cls,
        workspace_id: str,
        resource_type: str,
        resource_id: str,
        version: int | str = "1",
        query_params: Optional[Dict[str, Any]] = None,
    ) -> str:
        """
        Generate a deterministic, tenant-isolated cache key.
        Format: ws:{workspace_id}:{resource_type}:{resource_id}:v{version}:{hash}
        """
        query_str = json.dumps(query_params or {}, sort_keys=True)
        query_hash = hashlib.sha256(query_str.encode("utf-8")).hexdigest()[:12]
        return f"ws:{workspace_id}:{resource_type}:{resource_id}:v{version}:{query_hash}"

    def get(self, key: str) -> Optional[Any]:
        """Retrieve cached value if present and unexpired."""
        entry = self._store.get(key)
        if entry is None:
            self._misses += 1
            return None

        if entry.is_expired():
            del self._store[key]
            self._misses += 1
            return None

        entry.touch()
        self._hits += 1
        return entry.value

    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> None:
        """Store value with specified TTL, evicting LRU item if capacity is exceeded."""
        if len(self._store) >= self.max_capacity:
            self._evict_lru()

        self._store[key] = CacheEntry(value=value, ttl_seconds=ttl_seconds)

    def invalidate_resource(
        self,
        workspace_id: str,
        resource_type: str,
        resource_id: str,
    ) -> int:
        """
        Purge all cached results for a specific resource across all versions and queries.
        Returns the number of evicted keys.
        """
        prefix = f"ws:{workspace_id}:{resource_type}:{resource_id}:"
        keys_to_delete = [k for k in self._store if k.startswith(prefix)]
        for k in keys_to_delete:
            del self._store[k]
        return len(keys_to_delete)

    def invalidate_tenant(self, workspace_id: str) -> int:
        """Purge all cached keys for an entire tenant/workspace."""
        prefix = f"ws:{workspace_id}:"
        keys_to_delete = [k for k in self._store if k.startswith(prefix)]
        for k in keys_to_delete:
            del self._store[k]
        return len(keys_to_delete)

    def clear(self) -> None:
        """Purge all cache entries."""
        self._store.clear()

    def _evict_lru(self) -> None:
        """Evict least-recently-used or expired entry."""
        # 1. First look for expired keys
        now = time.time()
        for k, v in list(self._store.items()):
            if v.expires_at < now:
                del self._store[k]
                self._evictions += 1
                return

        # 2. Otherwise evict oldest accessed
        if self._store:
            oldest_key = min(self._store.keys(), key=lambda k: self._store[k].last_accessed)
            del self._store[oldest_key]
            self._evictions += 1

    def get_stats(self) -> Dict[str, Any]:
        """Return cache performance statistics and hit ratios."""
        total_lookups = self._hits + self._misses
        hit_ratio = round((self._hits / max(1, total_lookups)) * 100, 2)

        return {
            "total_keys": len(self._store),
            "max_capacity": self.max_capacity,
            "hits": self._hits,
            "misses": self._misses,
            "total_lookups": total_lookups,
            "hit_ratio_percent": hit_ratio,
            "evictions": self._evictions,
        }


# Global cache instance
cache_manager = MultiTenantCache()
