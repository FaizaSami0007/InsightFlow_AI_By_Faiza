"""Schema Drift & Data Freshness Evaluation Engines for Phase 17 Connectors."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple, Union

from app.connectors.schemas import ResourceSpec, SchemaDriftReport


class ConnectorDriftEngine:
    """Detects schema drift (added, removed, renamed columns, and datatype shifts) across sync intervals."""

    @staticmethod
    def detect_drift(
        old_schema: Union[List[ResourceSpec], Dict[str, Any]],
        new_schema: Union[List[ResourceSpec], Dict[str, Any]],
    ) -> SchemaDriftReport:
        """Detects schema drift between two sets of resource specifications."""
        old_map: Dict[str, Dict[str, str]] = {}
        new_map: Dict[str, Dict[str, str]] = {}

        # Normalize old_schema
        if isinstance(old_schema, list):
            for res in old_schema:
                old_map[res.name] = {c.name: c.data_type for c in res.columns}
        elif isinstance(old_schema, dict):
            for tbl in old_schema.get("tables", []):
                old_map[tbl["name"]] = {c["name"]: c.get("data_type", "TEXT") for c in tbl.get("columns", [])}

        # Normalize new_schema
        if isinstance(new_schema, list):
            for res in new_schema:
                new_map[res.name] = {c.name: c.data_type for c in res.columns}
        elif isinstance(new_schema, dict):
            for tbl in new_schema.get("tables", []):
                new_map[tbl["name"]] = {c["name"]: c.get("data_type", "TEXT") for c in tbl.get("columns", [])}

        added_cols: List[str] = []
        removed_cols: List[str] = []
        type_changes: Dict[str, Dict[str, str]] = {}

        all_tables = set(old_map.keys()).union(set(new_map.keys()))
        for tbl in all_tables:
            old_cols = old_map.get(tbl, {})
            new_cols = new_map.get(tbl, {})

            if not old_cols and new_cols:
                # Entire table added
                for col in new_cols:
                    added_cols.append(f"{tbl}.{col}")
                continue

            if old_cols and not new_cols:
                # Entire table removed
                for col in old_cols:
                    removed_cols.append(f"{tbl}.{col}")
                continue

            for col, dtype in new_cols.items():
                if col not in old_cols:
                    added_cols.append(f"{tbl}.{col}")
                elif dtype.upper() != old_cols[col].upper():
                    type_changes[f"{tbl}.{col}"] = {
                        "previous_type": old_cols[col],
                        "current_type": dtype,
                    }

            for col in old_cols:
                if col not in new_cols:
                    removed_cols.append(f"{tbl}.{col}")

        has_drift = bool(added_cols or removed_cols or type_changes)
        if removed_cols or type_changes:
            severity = "CRITICAL"
            rec = "Critical schema alteration detected. Validate downstream pipelines and dataset schemas."
        elif added_cols:
            severity = "WARNING"
            rec = "Columns added in external source. Update dataset schema to ingest new fields."
        else:
            severity = "NONE"
            rec = "NO_ACTION"

        return SchemaDriftReport(
            has_drift=has_drift,
            added_columns=added_cols,
            removed_columns=removed_cols,
            type_changes=type_changes,
            severity=severity,
            recommendation=rec,
        )

    @classmethod
    def compare_schemas(
        cls,
        previous_schema: Any,
        current_resource: Any,
    ) -> SchemaDriftReport:
        """Compares previous schema with current resource."""
        if isinstance(previous_schema, dict) and isinstance(current_resource, ResourceSpec):
            old_list = [
                ResourceSpec(
                    resource_id=current_resource.resource_id,
                    name=current_resource.name,
                    resource_type=current_resource.resource_type,
                    columns=[
                        type("Col", (), {"name": c["name"], "data_type": c.get("data_type", "TEXT")})()
                        for c in previous_schema.get("columns", [])
                    ],
                )
            ]
            return cls.detect_drift(old_list, [current_resource])
        return cls.detect_drift(previous_schema, current_resource)


class FreshnessEngine:
    """Evaluates data freshness based on last successful sync time and configured sync schedules."""

    SCHEDULE_MAX_INTERVAL_HOURS = {
        "HOURLY": 1.5,
        "0 * * * *": 1.5,
        "EVERY_6_HOURS": 8.0,
        "0 */6 * * *": 8.0,
        "EVERY_12_HOURS": 15.0,
        "0 */12 * * *": 15.0,
        "DAILY": 28.0,
        "0 */24 * * *": 28.0,
        "0 0 * * *": 28.0,
        "WEEKLY": 192.0,
    }

    @classmethod
    def calculate_freshness(
        cls,
        last_sync_at: Optional[datetime],
        sync_schedule: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Calculates freshness dictionary status."""
        if not last_sync_at:
            return {
                "freshness_status": "UNKNOWN",
                "hours_since_sync": None,
                "is_stale": False,
                "message": "Connection has not performed an initial sync.",
            }

        now = datetime.now(timezone.utc)
        if last_sync_at.tzinfo is None:
            sync_time = last_sync_at.replace(tzinfo=timezone.utc)
        else:
            sync_time = last_sync_at

        delta_hours = max(0.0, (now - sync_time).total_seconds() / 3600.0)
        schedule = (sync_schedule or "DAILY").strip()
        max_allowed_hours = cls.SCHEDULE_MAX_INTERVAL_HOURS.get(schedule.upper(), 28.0)
        if schedule in cls.SCHEDULE_MAX_INTERVAL_HOURS:
            max_allowed_hours = cls.SCHEDULE_MAX_INTERVAL_HOURS[schedule]

        if delta_hours <= max_allowed_hours:
            status = "FRESH"
            is_stale = False
            message = f"Data is fresh ({delta_hours:.1f}h since last sync)."
        elif delta_hours <= max_allowed_hours * 1.5:
            status = "STALE"
            is_stale = True
            message = f"Data is stale ({delta_hours:.1f}h elapsed vs {max_allowed_hours}h SLA)."
        else:
            status = "OVERDUE"
            is_stale = True
            message = f"Data sync is critically overdue ({delta_hours:.1f}h elapsed)."

        return {
            "freshness_status": status,
            "hours_since_sync": round(delta_hours, 2),
            "is_stale": is_stale,
            "message": message,
        }

    @classmethod
    def assess_freshness(
        cls,
        last_sync_at: Optional[datetime],
        sync_schedule: Optional[str] = None,
    ) -> Tuple[str, float, List[str]]:
        """Returns (freshness_status, freshness_score, recommendations)."""
        calc = cls.calculate_freshness(last_sync_at, sync_schedule)
        status = calc["freshness_status"]
        hours = calc["hours_since_sync"] or 0.0

        if status == "FRESH":
            score = max(80.0, 100.0 - (hours * 0.5))
            recs = ["Sync cadence is optimal."]
        elif status == "STALE":
            score = max(50.0, 75.0 - (hours * 0.5))
            recs = ["Data freshness is degrading. Trigger synchronization soon."]
        elif status == "OVERDUE":
            score = max(10.0, 40.0 - (hours * 0.2))
            recs = ["Data is critically overdue. Immediate re-synchronization recommended."]
        else:
            score = 50.0
            recs = ["Perform initial data sync."]

        return status, round(score, 1), recs
