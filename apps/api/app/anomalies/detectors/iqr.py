"""Interquartile Range (IQR Tukey Fence) Anomaly Detector."""

from typing import Any, List, Optional

import numpy as np

from app.anomalies.detectors.base import AnomalyHit, BaseAnomalyDetector, DetectorOutput
from app.database.models.anomalies import DetectionMethod


class IQRDetector(BaseAnomalyDetector):
    """Detects values falling outside [Q1 - k*IQR, Q3 + k*IQR] fences."""

    def __init__(self, sensitivity: float = 1.5) -> None:
        super().__init__(method=DetectionMethod.IQR, sensitivity=sensitivity)

    def detect(
        self,
        values: np.ndarray,
        dates: Optional[List[str]] = None,
        seasonal_period: Optional[int] = None,
        **kwargs: Any,
    ) -> DetectorOutput:
        y = np.asarray(values, dtype=float)
        hits: List[AnomalyHit] = []

        if len(y) < 4:
            return DetectorOutput(
                method=self.method,
                hits=[],
                baseline_summary={"q25": 0.0, "q75": 0.0, "iqr": 0.0},
            )

        q25, q75 = np.percentile(y, [25, 75])
        iqr_val = q75 - q25
        med_val = float(np.median(y))

        k = self.sensitivity  # standard 1.5 or 3.0
        lower_fence = float(q25 - k * iqr_val)
        upper_fence = float(q75 + k * iqr_val)

        for i, val in enumerate(y):
            if val < lower_fence or val > upper_fence:
                dev = float(val - med_val)
                denom = abs(med_val) if abs(med_val) > 1e-4 else 1.0
                dev_pct = float((dev / denom) * 100.0)

                # Distance relative to fence
                dist = abs(val - upper_fence) if val > upper_fence else abs(lower_fence - val)
                score = round(float(1.0 + (dist / (iqr_val if iqr_val > 0 else 1.0))), 2)

                hits.append(
                    AnomalyHit(
                        index=i,
                        observed=float(val),
                        expected=med_val,
                        deviation=dev,
                        deviation_pct=round(dev_pct, 2),
                        score=score,
                        evidence={
                            "lower_fence": round(lower_fence, 2),
                            "upper_fence": round(upper_fence, 2),
                            "q25": round(float(q25), 2),
                            "q75": round(float(q75), 2),
                            "iqr": round(float(iqr_val), 2),
                            "multiplier": k,
                        },
                    )
                )

        return DetectorOutput(
            method=self.method,
            hits=hits,
            baseline_summary={
                "q25": round(float(q25), 2),
                "q75": round(float(q75), 2),
                "iqr": round(float(iqr_val), 2),
                "lower_fence": round(lower_fence, 2),
                "upper_fence": round(upper_fence, 2),
            },
        )
