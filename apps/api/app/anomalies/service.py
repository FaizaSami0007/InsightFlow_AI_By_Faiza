"""Service layer orchestrating statistical anomaly detection, root-cause analysis, and insight generation."""

import hashlib
import time
import uuid
from datetime import datetime, timezone
from typing import List, Optional

import pandas as pd
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.duckdb.manager import DuckDBManager
from app.anomalies.detectors.registry import AnomalyDetectorRegistry
from app.anomalies.root_cause import RootCauseAnalyzer
from app.anomalies.schemas import (
    AnomalyDetectionRequest,
    AnomalyDetectionResponse,
    AnomalyFeedbackRequest,
    AnomalyPoint,
    AnomalyStatusUpdateRequest,
    InsightResponse,
    RootCauseContributor,
)
from app.anomalies.severity import SeverityEvaluator
from app.database.models.anomalies import (
    AnomalyRecord,
    AnomalySeverity,
    AnomalyStatus,
    AnomalyType,
    InsightRecord,
    InsightType,
)
from app.database.models.dataset import Dataset, DatasetVersion
from app.datasets.storage import get_storage_provider


class AnomalyServiceError(Exception):
    """Raised when anomaly detection or processing fails."""

    pass


class AnomalyService:
    """Orchestrates anomaly detection pipelines, root-cause investigation, and persistence."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.duckdb_manager = DuckDBManager()

    async def detect_anomalies(
        self,
        user_id: str,
        request: AnomalyDetectionRequest,
    ) -> AnomalyDetectionResponse:
        """Execute validated anomaly detection and proactive insight generation across dataset."""
        t_start = time.perf_counter()

        # 1. Dataset Ownership & Version Validation
        q = select(Dataset).where(Dataset.id == request.dataset_id, Dataset.owner_id == user_id)
        res = await self.db.execute(q)
        dataset = res.scalar_one_or_none()
        if not dataset:
            raise AnomalyServiceError(f"Dataset {request.dataset_id} not found or access denied.")

        version_id = request.dataset_version_id
        if not version_id:
            q_ver = (
                select(DatasetVersion)
                .where(DatasetVersion.dataset_id == dataset.id, DatasetVersion.status == "READY")
                .order_by(DatasetVersion.version_number.desc())
            )
            res_ver = await self.db.execute(q_ver)
            latest_version = res_ver.scalar_one_or_none()
            if not latest_version:
                raise AnomalyServiceError("No READY version found for the requested dataset.")
            version_id = latest_version.id

        table_name = self.duckdb_manager.get_table_name(version_id)
        if not table_name:
            # Register table in DuckDB
            storage = get_storage_provider()
            q_v = select(DatasetVersion).where(DatasetVersion.id == version_id)
            res_v = await self.db.execute(q_v)
            ver = res_v.scalar_one_or_none()
            if not ver:
                raise AnomalyServiceError(f"Version {version_id} not found.")

            ref = ver.storage_reference or ver.file_name
            try:
                file_path = str(storage.get_file_path(ref))
            except Exception:
                file_path = str(getattr(storage, "base_dir", "")) + "/" + str(ref)
            table_name = self.duckdb_manager.register_dataset(
                dataset_version_id=version_id,
                file_path=str(file_path),
                file_format=ver.file_format.value if hasattr(ver.file_format, "value") else str(ver.file_format),
            )

        # 2. Schema Discovery
        schema_info = self.duckdb_manager.get_table_schema(table_name)
        all_cols = [c["name"] for c in schema_info]

        # Determine target metrics
        metrics = request.metric_fields or [
            c["name"]
            for c in schema_info
            if any(t in c["type"].lower() for t in ["int", "double", "float", "decimal", "numeric", "bigint"])
        ]
        if not metrics:
            raise AnomalyServiceError("No numeric measures found or specified for anomaly detection.")

        # Determine time column
        time_col = request.time_field or next(
            (c["name"] for c in schema_info if any(t in c["type"].lower() for t in ["date", "timestamp", "time"])),
            None,
        )

        # Determine dimensions for subgroup breakdown
        dimensions = request.dimension_fields or [
            c["name"]
            for c in schema_info
            if any(t in c["type"].lower() for t in ["varchar", "string", "text"]) and c["name"] != time_col
        ][:3]

        detector = AnomalyDetectorRegistry.get_detector(
            method=request.method,
            sensitivity=request.sensitivity,
        )

        detected_anomalies: List[AnomalyRecord] = []
        generated_insights: List[InsightRecord] = []

        # 3. Detect Anomalies for each metric
        for metric in metrics:
            if metric not in all_cols:
                continue

            clean_m = f'"{metric.replace('"', '""')}"'

            if time_col and time_col in all_cols:
                clean_t = f'"{time_col.replace('"', '""')}"'
                sql = f"""
                SELECT
                    TRY_CAST({clean_t} AS VARCHAR) AS period_str,
                    SUM(TRY_CAST({clean_m} AS DOUBLE)) AS val
                FROM {table_name}
                WHERE {clean_m} IS NOT NULL AND {clean_t} IS NOT NULL
                GROUP BY {clean_t}
                ORDER BY {clean_t} ASC
                """
            else:
                sql = f"""
                SELECT
                    CAST(ROW_NUMBER() OVER () AS VARCHAR) AS period_str,
                    TRY_CAST({clean_m} AS DOUBLE) AS val
                FROM {table_name}
                WHERE {clean_m} IS NOT NULL
                """

            res_data = self.duckdb_manager.execute_federated_query(sql, max_rows=50000)
            rows = res_data.get("rows", [])
            if len(rows) < 3:
                continue

            df = pd.DataFrame(rows, columns=["period_str", "val"]).dropna()
            values_arr = df["val"].to_numpy(dtype=float)
            periods_list = df["period_str"].tolist()

            output = detector.detect(values=values_arr, dates=periods_list)

            for hit in output.hits:
                period_name = periods_list[hit.index] if hit.index < len(periods_list) else str(hit.index)
                severity, priority = SeverityEvaluator.evaluate(
                    anomaly_score=hit.score,
                    deviation=hit.deviation,
                    deviation_pct=hit.deviation_pct,
                    expected_value=hit.expected,
                    recency_idx=hit.index,
                    total_points=len(values_arr),
                )

                # Filter by minimum severity requested
                sev_order = [
                    AnomalySeverity.INFO,
                    AnomalySeverity.LOW,
                    AnomalySeverity.MEDIUM,
                    AnomalySeverity.HIGH,
                    AnomalySeverity.CRITICAL,
                ]
                if sev_order.index(severity) < sev_order.index(request.min_severity):
                    continue

                # 4. Root Cause Contribution Analysis
                root_cause_items: List[RootCauseContributor] = []
                for dim in dimensions:
                    contribs = RootCauseAnalyzer.analyze_contribution(
                        duckdb_manager=self.duckdb_manager,
                        table_name=table_name,
                        metric_col=metric,
                        time_col=time_col,
                        anomalous_period=period_name,
                        dimension_col=dim,
                        overall_observed=hit.observed,
                        overall_expected=hit.expected,
                    )
                    root_cause_items.extend(contribs)

                # Deterministic dedup key
                dedup_raw = f"{dataset.id}:{version_id}:{metric}:none:{period_name}:{request.method.value}"
                dedup_hash = hashlib.sha256(dedup_raw.encode("utf-8")).hexdigest()[:32]

                anomaly_rec = AnomalyRecord(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    dataset_id=dataset.id,
                    dataset_version_id=version_id,
                    metric_field=metric,
                    dimension_field=None,
                    dimension_value=None,
                    period=period_name,
                    observed_value=hit.observed,
                    expected_value=hit.expected,
                    deviation=hit.deviation,
                    deviation_pct=hit.deviation_pct,
                    anomaly_score=hit.score,
                    severity=severity,
                    anomaly_type=AnomalyType.POINT if not time_col else AnomalyType.TREND,
                    detection_method=request.method,
                    status=AnomalyStatus.DETECTED,
                    root_causes=[rc.model_dump() for rc in root_cause_items],
                    evidence={
                        **hit.evidence,
                        **output.baseline_summary,
                        "priority_score": priority,
                    },
                    dedup_key=dedup_hash,
                    provenance={
                        "dataset_id": dataset.id,
                        "dataset_name": dataset.name,
                        "dataset_version_id": version_id,
                        "analysis_timestamp": datetime.now(timezone.utc).isoformat(),
                        "total_observations": len(values_arr),
                    },
                )
                detected_anomalies.append(anomaly_rec)

                # Generate proactive insight summary
                direction_word = "dropped" if hit.deviation < 0 else "surged"
                insight_title = f"{metric.capitalize()} {direction_word} by {abs(hit.deviation_pct):.1f}% in {period_name}"
                top_contributor_text = (
                    f" Top contributor: {root_cause_items[0].narrative}" if root_cause_items else ""
                )
                insight_summary = (
                    f"Observed {hit.observed:.2f} compared to expected baseline {hit.expected:.2f} "
                    f"(deviation of {hit.deviation:.2f}).{top_contributor_text}"
                )

                insight_rec = InsightRecord(
                    id=str(uuid.uuid4()),
                    user_id=user_id,
                    dataset_id=dataset.id,
                    anomaly_id=anomaly_rec.id,
                    insight_type=InsightType.ANOMALY,
                    title=insight_title,
                    summary=insight_summary,
                    severity=severity,
                    status=AnomalyStatus.DETECTED,
                    evidence=anomaly_rec.evidence,
                    dedup_key=dedup_hash,
                )
                generated_insights.append(insight_rec)

        # 5. Persist non-duplicate records to PostgreSQL
        for anom in detected_anomalies:
            q_exist = select(AnomalyRecord).where(
                AnomalyRecord.dataset_id == dataset.id, AnomalyRecord.dedup_key == anom.dedup_key
            )
            res_ex = await self.db.execute(q_exist)
            if not res_ex.scalar_one_or_none():
                self.db.add(anom)

        for ins in generated_insights:
            q_ins = select(InsightRecord).where(
                InsightRecord.dataset_id == dataset.id, InsightRecord.dedup_key == ins.dedup_key
            )
            res_ins = await self.db.execute(q_ins)
            if not res_ins.scalar_one_or_none():
                self.db.add(ins)

        await self.db.commit()

        # Build schema points
        anomaly_points = [
            AnomalyPoint(
                id=a.id,
                dataset_id=a.dataset_id,
                dataset_version_id=a.dataset_version_id,
                metric_field=a.metric_field,
                dimension_field=a.dimension_field,
                dimension_value=a.dimension_value,
                period=a.period,
                observed_value=a.observed_value,
                expected_value=a.expected_value,
                deviation=a.deviation,
                deviation_pct=a.deviation_pct,
                anomaly_score=a.anomaly_score,
                severity=a.severity,
                anomaly_type=a.anomaly_type,
                detection_method=a.detection_method,
                status=a.status,
                root_causes=[RootCauseContributor(**rc) for rc in a.root_causes],
                evidence=a.evidence,
                dedup_key=a.dedup_key,
                provenance=a.provenance,
                created_at=a.created_at or datetime.now(timezone.utc),
            )
            for a in detected_anomalies
        ]

        insight_responses = [
            InsightResponse(
                id=ins.id,
                dataset_id=ins.dataset_id,
                anomaly_id=ins.anomaly_id,
                insight_type=ins.insight_type,
                title=ins.title,
                summary=ins.summary,
                severity=ins.severity,
                status=ins.status,
                evidence=ins.evidence,
                dedup_key=ins.dedup_key,
                feedback=ins.feedback,
                created_at=ins.created_at or datetime.now(timezone.utc),
            )
            for ins in generated_insights
        ]

        t_elapsed = (time.perf_counter() - t_start) * 1000.0

        return AnomalyDetectionResponse(
            dataset_id=dataset.id,
            dataset_version_id=version_id,
            anomalies=anomaly_points,
            insights=insight_responses,
            total_anomalies_count=len(anomaly_points),
            critical_count=sum(1 for a in anomaly_points if a.severity == AnomalySeverity.CRITICAL),
            high_count=sum(1 for a in anomaly_points if a.severity == AnomalySeverity.HIGH),
            medium_count=sum(1 for a in anomaly_points if a.severity == AnomalySeverity.MEDIUM),
            low_count=sum(1 for a in anomaly_points if a.severity in (AnomalySeverity.LOW, AnomalySeverity.INFO)),
            execution_time_ms=round(t_elapsed, 2),
            created_at=datetime.now(timezone.utc),
        )

    async def list_anomalies(
        self,
        user_id: str,
        dataset_id: Optional[str] = None,
        severity: Optional[AnomalySeverity] = None,
        status: Optional[AnomalyStatus] = None,
    ) -> List[AnomalyPoint]:
        """Query historical detected anomalies for user."""
        stmt = select(AnomalyRecord).where(AnomalyRecord.user_id == user_id)
        if dataset_id:
            stmt = stmt.where(AnomalyRecord.dataset_id == dataset_id)
        if severity:
            stmt = stmt.where(AnomalyRecord.severity == severity)
        if status:
            stmt = stmt.where(AnomalyRecord.status == status)

        stmt = stmt.order_by(AnomalyRecord.created_at.desc())
        res = await self.db.execute(stmt)
        records = res.scalars().all()

        return [
            AnomalyPoint(
                id=r.id,
                dataset_id=r.dataset_id,
                dataset_version_id=r.dataset_version_id,
                metric_field=r.metric_field,
                dimension_field=r.dimension_field,
                dimension_value=r.dimension_value,
                period=r.period,
                observed_value=r.observed_value,
                expected_value=r.expected_value,
                deviation=r.deviation,
                deviation_pct=r.deviation_pct,
                anomaly_score=r.anomaly_score,
                severity=r.severity,
                anomaly_type=r.anomaly_type,
                detection_method=r.detection_method,
                status=r.status,
                root_causes=[RootCauseContributor(**rc) for rc in r.root_causes],
                evidence=r.evidence,
                dedup_key=r.dedup_key,
                provenance=r.provenance,
                created_at=r.created_at or datetime.now(timezone.utc),
            )
            for r in records
        ]

    async def get_anomaly(self, user_id: str, anomaly_id: str) -> AnomalyPoint:
        """Fetch a single anomaly by ID with authorization checks."""
        stmt = select(AnomalyRecord).where(AnomalyRecord.id == anomaly_id, AnomalyRecord.user_id == user_id)
        res = await self.db.execute(stmt)
        record = res.scalar_one_or_none()
        if not record:
            raise AnomalyServiceError(f"Anomaly {anomaly_id} not found or unauthorized.")

        return AnomalyPoint(
            id=record.id,
            dataset_id=record.dataset_id,
            dataset_version_id=record.dataset_version_id,
            metric_field=record.metric_field,
            dimension_field=record.dimension_field,
            dimension_value=record.dimension_value,
            period=record.period,
            observed_value=record.observed_value,
            expected_value=record.expected_value,
            deviation=record.deviation,
            deviation_pct=record.deviation_pct,
            anomaly_score=record.anomaly_score,
            severity=record.severity,
            anomaly_type=record.anomaly_type,
            detection_method=record.detection_method,
            status=record.status,
            root_causes=[RootCauseContributor(**rc) for rc in record.root_causes],
            evidence=record.evidence,
            dedup_key=record.dedup_key,
            provenance=record.provenance,
            created_at=record.created_at or datetime.now(timezone.utc),
        )

    async def update_anomaly_status(
        self,
        user_id: str,
        anomaly_id: str,
        req: AnomalyStatusUpdateRequest,
    ) -> AnomalyPoint:
        """Update lifecycle status of an anomaly."""
        stmt = select(AnomalyRecord).where(AnomalyRecord.id == anomaly_id, AnomalyRecord.user_id == user_id)
        res = await self.db.execute(stmt)
        record = res.scalar_one_or_none()
        if not record:
            raise AnomalyServiceError(f"Anomaly {anomaly_id} not found.")

        record.status = req.status
        await self.db.commit()
        await self.db.refresh(record)
        return await self.get_anomaly(user_id, anomaly_id)

    async def list_insights(
        self,
        user_id: str,
        dataset_id: Optional[str] = None,
        min_severity: Optional[AnomalySeverity] = None,
    ) -> List[InsightResponse]:
        """Query proactive insights feed for user."""
        stmt = select(InsightRecord).where(InsightRecord.user_id == user_id)
        if dataset_id:
            stmt = stmt.where(InsightRecord.dataset_id == dataset_id)

        stmt = stmt.order_by(InsightRecord.created_at.desc())
        res = await self.db.execute(stmt)
        records = res.scalars().all()

        return [
            InsightResponse(
                id=r.id,
                dataset_id=r.dataset_id,
                anomaly_id=r.anomaly_id,
                insight_type=r.insight_type,
                title=r.title,
                summary=r.summary,
                severity=r.severity,
                status=r.status,
                evidence=r.evidence,
                dedup_key=r.dedup_key,
                feedback=r.feedback,
                created_at=r.created_at or datetime.now(timezone.utc),
            )
            for r in records
        ]

    async def submit_feedback(
        self,
        user_id: str,
        insight_id: str,
        req: AnomalyFeedbackRequest,
    ) -> InsightResponse:
        """Store user feedback for proactive insight."""
        stmt = select(InsightRecord).where(InsightRecord.id == insight_id, InsightRecord.user_id == user_id)
        res = await self.db.execute(stmt)
        rec = res.scalar_one_or_none()
        if not rec:
            raise AnomalyServiceError(f"Insight {insight_id} not found.")

        rec.feedback = req.feedback
        await self.db.commit()
        await self.db.refresh(rec)

        return InsightResponse(
            id=rec.id,
            dataset_id=rec.dataset_id,
            anomaly_id=rec.anomaly_id,
            insight_type=rec.insight_type,
            title=rec.title,
            summary=rec.summary,
            severity=rec.severity,
            status=rec.status,
            evidence=rec.evidence,
            dedup_key=rec.dedup_key,
            feedback=rec.feedback,
            created_at=rec.created_at or datetime.now(timezone.utc),
        )
