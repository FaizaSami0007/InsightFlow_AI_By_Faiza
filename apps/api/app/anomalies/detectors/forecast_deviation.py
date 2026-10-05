"""Forecast Deviation Anomaly Detector (Phase 11 Forecast Interval Integration)."""

from typing import Any, List, Optional

import numpy as np

from app.anomalies.detectors.base import AnomalyHit, BaseAnomalyDetector, DetectorOutput
from app.database.models.anomalies import DetectionMethod


class ForecastDeviationDetector(BaseAnomalyDetector):
    """Detects observations that violate backtested forecasting prediction intervals [Lower, Upper]."""

    def __init__(self, sensitivity: float = 1.0) -> None:
        super().__init__(method=DetectionMethod.FORECAST_DEVIATION, sensitivity=sensitivity)

    def detect(
        self,
        values: np.ndarray,
        dates: Optional[List[str]] = None,
        seasonal_period: Optional[int] = None,
        expected_points: Optional[List[float]] = None,
        lower_bounds: Optional[List[float]] = None,
        upper_bounds: Optional[List[float]] = None,
        **kwargs: Any,
    ) -> DetectorOutput:
        y = np.asarray(values, dtype=float)
        hits: List[AnomalyHit] = []

        if not expected_points or len(expected_points) != len(y):
            # Fallback simple exponential smoothing baseline if explicit forecast points not provided
            med = float(np.median(y)) if len(y) > 0 else 0.0
            std = float(np.std(y)) or 1.0
            lower = [med - 2.0 * std] * len(y)
            upper = [med + 2.0 * std] * len(y)
            exp_pts = [med] * len(y)
        else:
            exp_pts = expected_points
            lower = lower_bounds or [e - 0.2 * abs(e) for e in exp_pts]
            upper = upper_bounds or [e + 0.2 * abs(e) for e in exp_pts]

        for i, (val, exp, low, high) in enumerate(zip(y, exp_pts, lower, upper)):
            if val < low or val > high:
                dev = float(val - exp)
                denom = abs(exp) if abs(exp) > 1e-4 else 1.0
                dev_pct = float((dev / denom) * 100.0)

                # Distance outside prediction interval band
                interval_half_width = max(1e-4, (high - low) / 2.0)
                score = round(float(abs(dev) / interval_half_width), 2)

                hits.append(
                    AnomalyHit(
                        index=i,
                        observed=float(val),
                        expected=float(exp),
                        deviation=round(dev, 2),
                        deviation_pct=round(dev_pct, 2),
                        score=score,
                        evidence={
                            "point_forecast_expected": round(float(exp), 2),
                            "prediction_interval_lower": round(float(low), 2),
                            "prediction_interval_upper": round(float(high), 2),
                            "violation_score": score,
                        },
                    )
                )

        return DetectorOutput(
            method=self.method,
            hits=hits,
            baseline_summary={"integrated_forecast_points": len(exp_pts)},
        )
