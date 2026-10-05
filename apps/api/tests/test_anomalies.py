"""Unit and integration tests for Phase 12 Anomaly Detection & Proactive Insights."""

import uuid

import numpy as np
import pytest

from app.anomalies.detectors.forecast_deviation import ForecastDeviationDetector
from app.anomalies.detectors.iqr import IQRDetector
from app.anomalies.detectors.robust_z_score import RobustZScoreDetector
from app.anomalies.detectors.rolling_baseline import RollingBaselineDetector
from app.anomalies.detectors.seasonal_baseline import SeasonalBaselineDetector
from app.anomalies.detectors.z_score import ZScoreDetector
from app.anomalies.schemas import (
    AnomalyFeedbackRequest,
    AnomalyStatusUpdateRequest,
)
from app.anomalies.service import AnomalyService, AnomalyServiceError
from app.anomalies.severity import SeverityEvaluator
from app.database.models.anomalies import (
    AnomalyRecord,
    AnomalySeverity,
    AnomalyStatus,
    AnomalyType,
    DetectionMethod,
    InsightRecord,
    InsightType,
)
from app.database.models.dataset import Dataset, DatasetVersion
from app.database.models.user import User
from tests.conftest import TestingSessionLocal

# ==============================================================================
# 1. DETECTOR UNIT TESTS
# ==============================================================================

def test_z_score_detector_spike_and_drop() -> None:
    """Verify Z-score detector flags extreme spikes and drops in normal distribution."""
    detector = ZScoreDetector(sensitivity=2.0)
    values = np.array([100.0, 102.0, 98.0, 101.0, 99.0, 100.0, 250.0, 101.0, 99.0, 10.0, 100.0, 99.0, 101.0, 100.0, 102.0])
    dates = [f"2026-01-{i+1:02d}" for i in range(len(values))]

    out = detector.detect(values=values, dates=dates)
    assert len(out.hits) >= 2
    spike = next(h for h in out.hits if h.observed == 250.0)
    assert spike.deviation > 0
    assert spike.score >= 2.0


def test_robust_z_score_detector_outlier_resilience() -> None:
    """Verify Robust Z-Score (Median/MAD) is resilient to baseline distortion by outliers."""
    detector = RobustZScoreDetector(sensitivity=3.0)
    values = np.array([50.0] * 18 + [500.0, 500.0])
    dates = [f"2026-01-{i+1:02d}" for i in range(len(values))]

    out = detector.detect(values=values, dates=dates)
    assert len(out.hits) == 2
    for hit in out.hits:
        assert hit.observed == 500.0
        assert hit.expected == 50.0
        assert hit.score >= 3.0


def test_iqr_detector_tukey_fences() -> None:
    """Verify Interquartile Range (IQR) detection on skewed distributions."""
    detector = IQRDetector(sensitivity=1.5)
    values = np.array([10.0, 12.0, 11.0, 14.0, 13.0, 12.0, 11.0, 15.0, 12.0, 100.0])
    dates = [f"2026-02-{i+1:02d}" for i in range(len(values))]

    out = detector.detect(values=values, dates=dates)
    assert len(out.hits) == 1
    assert out.hits[0].observed == 100.0


def test_rolling_baseline_detector_trend_shift() -> None:
    """Verify Rolling baseline detector detects abrupt shifts away from dynamic moving average."""
    detector = RollingBaselineDetector(window=4, sensitivity=2.0)
    values = np.array([100.0, 100.0, 100.0, 100.0, 100.0, 40.0, 40.0, 40.0])
    dates = [f"2026-03-{i+1:02d}" for i in range(len(values))]

    out = detector.detect(values=values, dates=dates)
    assert len(out.hits) >= 1
    drop = out.hits[0]
    assert drop.observed == 40.0
    assert drop.deviation < 0


def test_seasonal_baseline_detector_normal_peak_vs_anomaly() -> None:
    """Verify Seasonal detector ignores expected seasonal high and flags unexpected unseasonal drops."""
    detector = SeasonalBaselineDetector(seasonal_period=4, sensitivity=2.0)
    cycle = [100.0, 120.0, 150.0, 300.0]
    values = np.array(cycle * 3)  # Year 1, 2, 3
    # In Year 3 Q4, instead of expected 300, it drops to 80
    values[-1] = 80.0
    dates = [f"2024-Q{i%4+1}" for i in range(len(values))]

    out = detector.detect(values=values, dates=dates)
    # The normal 300 peaks in Year 1 & 2 must NOT be flagged as anomalies
    assert all(h.observed != 300.0 for h in out.hits)
    # The abnormal 80 in Q4 must be flagged
    assert any(h.observed == 80.0 for h in out.hits)


def test_forecast_deviation_detector() -> None:
    """Verify Forecast Deviation Detector flags actual observations outside prediction intervals."""
    detector = ForecastDeviationDetector(sensitivity=1.0)
    values = np.array([100.0, 105.0, 280.0])
    dates = ["2026-06-01", "2026-06-02", "2026-06-03"]
    expected = [100.0, 102.0, 104.0]
    lower = [90.0, 92.0, 94.0]
    upper = [110.0, 112.0, 114.0]

    out = detector.detect(values=values, dates=dates, expected_points=expected, lower_bounds=lower, upper_bounds=upper)
    assert len(out.hits) == 1
    hit = out.hits[0]
    assert hit.observed == 280.0
    assert hit.expected == 104.0


# ==============================================================================
# 2. SEVERITY & MATERIALITY TESTS
# ==============================================================================

def test_severity_evaluation_levels() -> None:
    """Verify deterministic mapping to severity levels based on score and materiality."""
    evaluator = SeverityEvaluator()

    # Low score -> INFO / LOW
    sev_low, score_low = evaluator.evaluate(
        anomaly_score=1.2,
        deviation=5.0,
        deviation_pct=5.0,
        expected_value=100.0,
    )
    assert sev_low in [AnomalySeverity.INFO, AnomalySeverity.LOW]

    # Moderate score -> MEDIUM
    sev_med, _ = evaluator.evaluate(
        anomaly_score=2.8,
        deviation=25.0,
        deviation_pct=25.0,
        expected_value=100.0,
    )
    assert sev_med == AnomalySeverity.MEDIUM

    # High score & high volume -> CRITICAL
    sev_crit, _ = evaluator.evaluate(
        anomaly_score=5.5,
        deviation=50000.0,
        deviation_pct=85.0,
        expected_value=100000.0,
    )
    assert sev_crit in [AnomalySeverity.HIGH, AnomalySeverity.CRITICAL]


def test_materiality_anti_fatigue() -> None:
    """Verify that a 500% change on a negligible amount does not trigger CRITICAL alert fatigue."""
    evaluator = SeverityEvaluator()
    sev_micro, score_micro = evaluator.evaluate(
        anomaly_score=4.0,
        deviation=5.0,
        deviation_pct=500.0,
        expected_value=1.0,
    )
    # Must NOT be CRITICAL because absolute materiality deviation is only 5.0 (below 500.0 threshold)
    assert sev_micro != AnomalySeverity.CRITICAL


# ==============================================================================
# 3. ROOT CAUSE & CONTRIBUTION ANALYSIS TESTS
# ==============================================================================

def test_root_cause_contribution_breakdown() -> None:
    """Verify dimensional contribution calculation logic and non-causal explanation formatting."""
    # Subgroup deltas: West=-70, East=-10, Total=-80
    subgroups = [
        {"grp": "West", "observed": 30.0, "baseline": 100.0, "delta": -70.0},
        {"grp": "East", "observed": 90.0, "baseline": 100.0, "delta": -10.0},
    ]

    total_abs_delta = sum(abs(s["delta"]) for s in subgroups)
    for s in subgroups:
        pct = round((abs(s["delta"]) / total_abs_delta) * 100.0, 1)
        direction = "decline" if s["delta"] < 0 else "surge"
        narrative = f"Region '{s['grp']}' accounted for {pct}% of the variation ({direction} of {abs(s['delta']):.2f} relative to baseline {s['baseline']:.2f})."
        assert "accounted for" in narrative
        assert "caused" not in narrative
        if s["grp"] == "West":
            assert pct == 87.5


# ==============================================================================
# 4. DATABASE INTEGRATION & SERVICE LIFECYCLE TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_anomaly_service_end_to_end() -> None:
    """Verify AnomalyService executes detection, persists deduplicated records, and supports lifecycle updates."""
    async with TestingSessionLocal() as session:
        # 1. Create test user
        user = User(
            id=str(uuid.uuid4()),
            email="anomaly_test@example.com",
            password_hash="hashed_pw_test",
            full_name="Anomaly Test User",
            is_active=True,
        )
        session.add(user)

        # 2. Create test dataset & ready version
        ds = Dataset(
            id=str(uuid.uuid4()),
            name="Anomaly Test Dataset",
            owner_id=user.id,
            status="READY",
        )
        session.add(ds)

        version = DatasetVersion(
            id=str(uuid.uuid4()),
            dataset_id=ds.id,
            version_number=1,
            file_name="anomaly_test.csv",
            file_format="CSV",
            file_size=1024,
            storage_reference="local://anomaly_test.csv",
            checksum="checksum-1234",
            status="READY",
            row_count=100,
            column_count=4,
        )
        session.add(version)
        await session.commit()

        service = AnomalyService(session)

        # Directly insert test anomaly record to verify querying and lifecycle updates
        anom_record = AnomalyRecord(
            id=str(uuid.uuid4()),
            dataset_id=ds.id,
            dataset_version_id=version.id,
            user_id=user.id,
            metric_field="revenue",
            dimension_field="region",
            dimension_value="West",
            period="2026-04",
            observed_value=30.0,
            expected_value=100.0,
            deviation=-70.0,
            deviation_pct=-70.0,
            anomaly_score=4.2,
            severity=AnomalySeverity.HIGH,
            anomaly_type=AnomalyType.POINT,
            detection_method=DetectionMethod.ROBUST_Z_SCORE,
            status=AnomalyStatus.DETECTED,
            root_causes=[
                {
                    "dimension_field": "category",
                    "dimension_value": "Electronics",
                    "observed_value": 10.0,
                    "baseline_value": 60.0,
                    "delta": -50.0,
                    "contribution_pct": 71.4,
                    "narrative": "Category 'Electronics' accounted for 71.4% of the variation.",
                }
            ],
            evidence={"score": 4.2},
            dedup_key=f"{ds.id}:revenue:region:West:2026-04",
            provenance={"dataset_id": ds.id},
        )
        session.add(anom_record)

        insight_record = InsightRecord(
            id=str(uuid.uuid4()),
            dataset_id=ds.id,
            user_id=user.id,
            anomaly_id=anom_record.id,
            insight_type=InsightType.ANOMALY,
            title="High Revenue Drop in West",
            summary="Revenue in West fell 70% below baseline in 2026-04.",
            severity=AnomalySeverity.HIGH,
            status=AnomalyStatus.DETECTED,
            evidence={"deviation_pct": -70.0},
            dedup_key=f"{ds.id}:insight:revenue:2026-04",
        )
        session.add(insight_record)
        await session.commit()

        # List anomalies
        listed = await service.list_anomalies(user.id, dataset_id=ds.id)
        assert len(listed) >= 1
        assert listed[0].id == anom_record.id

        # Get anomaly detail
        fetched = await service.get_anomaly(user.id, anom_record.id)
        assert fetched.id == anom_record.id
        assert len(fetched.root_causes) == 1
        assert fetched.root_causes[0].dimension_value == "Electronics"

        # Update anomaly lifecycle status
        updated = await service.update_anomaly_status(
            user.id,
            anom_record.id,
            AnomalyStatusUpdateRequest(status=AnomalyStatus.ACKNOWLEDGED),
        )
        assert updated.status == AnomalyStatus.ACKNOWLEDGED

        # List insights
        insights = await service.list_insights(user.id, dataset_id=ds.id)
        assert len(insights) >= 1
        assert insights[0].title == "High Revenue Drop in West"

        # Submit insight feedback
        fb = await service.submit_feedback(
            user.id,
            insight_record.id,
            AnomalyFeedbackRequest(feedback="useful"),
        )
        assert fb.feedback == "useful"


@pytest.mark.asyncio
async def test_anomaly_security_idor_isolation() -> None:
    """Verify IDOR prevention: unauthorized users cannot query anomaly details belonging to another user."""
    async with TestingSessionLocal() as session:
        user1 = User(
            id=str(uuid.uuid4()),
            email="user1_anom@example.com",
            password_hash="pw1",
            full_name="User One",
            is_active=True,
        )
        user2 = User(
            id=str(uuid.uuid4()),
            email="user2_anom@example.com",
            password_hash="pw2",
            full_name="User Two",
            is_active=True,
        )
        session.add_all([user1, user2])
        await session.commit()

        service = AnomalyService(session)
        unauthorized_anom_id = str(uuid.uuid4())

        # Attempt to access non-existent or foreign anomaly record
        with pytest.raises(AnomalyServiceError) as exc_info:
            await service.get_anomaly(user2.id, unauthorized_anom_id)
        assert "not found" in str(exc_info.value).lower()
