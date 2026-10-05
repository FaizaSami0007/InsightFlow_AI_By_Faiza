"""Deterministic Relationship Discovery & Validation Engine for Multi-Dataset Federation."""

import re
from typing import Any, Dict, List

from app.analytics.duckdb.manager import DuckDBManager
from app.database.models.federation import RelationshipType
from app.database.models.profiling import DatasetProfile
from app.federation.schemas import DiscoveredRelationshipCandidate


class RelationshipEngine:
    """Discovers and rigorously validates dataset relationships with deterministic metrics."""

    @staticmethod
    def _normalize_name(name: str) -> str:
        return re.sub(r"[^a-zA-Z0-9]", "", name.lower())

    @classmethod
    def discover_candidate_relationships(
        cls,
        source_profile: DatasetProfile,
        target_profile: DatasetProfile,
        source_dataset_id: str,
        source_dataset_name: str,
        target_dataset_id: str,
        target_dataset_name: str,
    ) -> List[DiscoveredRelationshipCandidate]:
        """Discover candidate relationships between two profiled datasets based on metadata."""
        if source_dataset_id == target_dataset_id:
            return []

        candidates: List[DiscoveredRelationshipCandidate] = []

        source_cols = {col.column_name: col for col in source_profile.column_profiles}
        target_cols = {col.column_name: col for col in target_profile.column_profiles}

        for s_name, s_col in source_cols.items():
            s_norm = cls._normalize_name(s_name)
            s_type = s_col.data_type.upper()

            for t_name, t_col in target_cols.items():
                t_norm = cls._normalize_name(t_name)
                t_type = t_col.data_type.upper()

                # Basic type compatibility
                type_compatible = (
                    s_type == t_type
                    or (any(x in s_type for x in ["INT", "FLOAT", "NUM", "DEC"]) and any(x in t_type for x in ["INT", "FLOAT", "NUM", "DEC"]))
                    or (any(x in s_type for x in ["VARCHAR", "TEXT", "STR", "CHAR"]) and any(x in t_type for x in ["VARCHAR", "TEXT", "STR", "CHAR"]))
                )

                if not type_compatible:
                    continue

                confidence = 0.0
                reasons: List[str] = []

                # Exact normalized name match (e.g. customer_id == customer_id)
                if s_norm == t_norm:
                    confidence += 0.6
                    reasons.append(f"Matching column name '{s_name}'")
                # ID prefix/suffix match (e.g. customer.id <-> orders.customer_id)
                elif (
                    (s_norm == "id" and t_norm.endswith("id") and cls._normalize_name(source_dataset_name) in t_norm)
                    or (t_norm == "id" and s_norm.endswith("id") and cls._normalize_name(target_dataset_name) in s_norm)
                ):
                    confidence += 0.55
                    reasons.append(f"Primary-to-Foreign key name pattern ('{s_name}' <-> '{t_name}')")
                elif s_norm.endswith("id") and t_norm.endswith("id") and (s_norm in t_norm or t_norm in s_norm):
                    confidence += 0.4
                    reasons.append(f"Related identifier pattern ('{s_name}' <-> '{t_name}')")
                else:
                    continue

                # Uniqueness signal
                s_unique = (s_col.unique_percentage or 0.0) >= 95.0
                t_unique = (t_col.unique_percentage or 0.0) >= 95.0

                if s_unique and not t_unique:
                    inferred_type = RelationshipType.ONE_TO_MANY
                    confidence += 0.25
                    reasons.append("Source field is unique (Primary Key behavior)")
                elif not s_unique and t_unique:
                    inferred_type = RelationshipType.MANY_TO_ONE
                    confidence += 0.25
                    reasons.append("Target field is unique (Foreign Key behavior)")
                elif s_unique and t_unique:
                    inferred_type = RelationshipType.ONE_TO_ONE
                    confidence += 0.2
                    reasons.append("Both fields are highly unique (1:1 link)")
                else:
                    inferred_type = RelationshipType.MANY_TO_ONE
                    confidence += 0.1

                confidence = min(0.99, max(0.1, confidence))

                candidates.append(
                    DiscoveredRelationshipCandidate(
                        source_dataset_id=source_dataset_id,
                        source_dataset_name=source_dataset_name,
                        source_version_id=source_profile.dataset_version_id,
                        source_field=s_name,
                        source_type=s_type,
                        target_dataset_id=target_dataset_id,
                        target_dataset_name=target_dataset_name,
                        target_version_id=target_profile.dataset_version_id,
                        target_field=t_name,
                        target_type=t_type,
                        inferred_type=inferred_type,
                        confidence=round(confidence, 2),
                        reason=", ".join(reasons),
                    )
                )

        return sorted(candidates, key=lambda c: c.confidence, reverse=True)

    @classmethod
    def validate_relationship_data(
        cls,
        duckdb_manager: DuckDBManager,
        source_version_id: str,
        source_file_path: str,
        source_format: str,
        source_field: str,
        target_version_id: str,
        target_file_path: str,
        target_format: str,
        target_field: str,
    ) -> Dict[str, Any]:
        """Execute deterministic DuckDB verification of referential integrity, uniqueness and coverage."""
        source_tbl = duckdb_manager.register_dataset(source_version_id, source_file_path, source_format)
        target_tbl = duckdb_manager.register_dataset(target_version_id, target_file_path, target_format)

        # Sanitize column names for SQL safety
        s_col = f'"{source_field.replace('"', '""')}"'
        t_col = f'"{target_field.replace('"', '""')}"'

        # 1. Compute source & target cardinality & null statistics
        stats_sql = f"""
        SELECT
            (SELECT COUNT(*) FROM {source_tbl}) AS s_count,
            (SELECT COUNT(DISTINCT {s_col}) FROM {source_tbl} WHERE {s_col} IS NOT NULL) AS s_distinct,
            (SELECT COUNT(*) FROM {source_tbl} WHERE {s_col} IS NULL) AS s_nulls,
            (SELECT COUNT(*) FROM {target_tbl}) AS t_count,
            (SELECT COUNT(DISTINCT {t_col}) FROM {target_tbl} WHERE {t_col} IS NOT NULL) AS t_distinct,
            (SELECT COUNT(*) FROM {target_tbl} WHERE {t_col} IS NULL) AS t_nulls
        """
        stats_res = duckdb_manager.execute_federated_query(stats_sql)
        stats_cols = stats_res.get("columns", [])
        stats_row = stats_res["rows"][0] if stats_res.get("rows") else []
        stats = dict(zip(stats_cols, stats_row)) if stats_cols and stats_row else {}

        s_count = int(stats.get("s_count", 0))
        s_distinct = int(stats.get("s_distinct", 0))
        s_nulls = int(stats.get("s_nulls", 0))

        t_count = int(stats.get("t_count", 0))
        t_distinct = int(stats.get("t_distinct", 0))
        t_nulls = int(stats.get("t_nulls", 0))

        # 2. Compute key intersection & coverage
        intersect_sql = f"""
        SELECT COUNT(DISTINCT s.{s_col}) AS matched_keys
        FROM {source_tbl} s
        INNER JOIN {target_tbl} t ON CAST(s.{s_col} AS VARCHAR) = CAST(t.{t_col} AS VARCHAR)
        WHERE s.{s_col} IS NOT NULL AND t.{t_col} IS NOT NULL
        """
        intersect_res = duckdb_manager.execute_federated_query(intersect_sql)
        inter_cols = intersect_res.get("columns", [])
        inter_row = intersect_res["rows"][0] if intersect_res.get("rows") else []
        inter_dict = dict(zip(inter_cols, inter_row)) if inter_cols and inter_row else {}
        matched_keys = int(inter_dict.get("matched_keys", 0))

        # Ratios
        coverage_ratio = matched_keys / max(s_distinct, 1) if s_distinct > 0 else 0.0
        source_unique_ratio = s_distinct / max(s_count, 1) if s_count > 0 else 0.0
        target_unique_ratio = t_distinct / max(t_count, 1) if t_count > 0 else 0.0
        null_rate = (s_nulls + t_nulls) / max(s_count + t_count, 1) if (s_count + t_count) > 0 else 0.0

        # Inferred relationship type
        if source_unique_ratio >= 0.98 and target_unique_ratio >= 0.98:
            rel_type = RelationshipType.ONE_TO_ONE
        elif source_unique_ratio >= 0.98 and target_unique_ratio < 0.98:
            rel_type = RelationshipType.ONE_TO_MANY
        else:
            rel_type = RelationshipType.MANY_TO_ONE

        # Quality score (0 to 100)
        quality_score = round(
            (coverage_ratio * 70.0) + ((1.0 - min(null_rate, 1.0)) * 20.0) + (10.0 if coverage_ratio > 0.5 else 0.0),
            1,
        )

        return {
            "relationship_type": rel_type,
            "coverage_ratio": round(coverage_ratio, 4),
            "source_unique_ratio": round(source_unique_ratio, 4),
            "target_unique_ratio": round(target_unique_ratio, 4),
            "null_rate": round(null_rate, 4),
            "quality_score": min(100.0, max(0.0, quality_score)),
            "evidence": {
                "source_row_count": s_count,
                "source_distinct_keys": s_distinct,
                "source_null_count": s_nulls,
                "target_row_count": t_count,
                "target_distinct_keys": t_distinct,
                "target_null_count": t_nulls,
                "matched_keys_count": matched_keys,
                "referential_coverage_pct": round(coverage_ratio * 100, 2),
            },
        }
