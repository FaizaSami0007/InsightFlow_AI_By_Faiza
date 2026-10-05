"""Standard Z-Score (Mean / Standard Deviation) Anomaly Detector."""

from typing import Any, List, Optional

import numpy as np

from app.anomalies.detectors.base import AnomalyHit, BaseAnomalyDetector, DetectorOutput
from app.database.models.anomalies import DetectionMethod


class ZScoreDetector(BaseAnomalyDetector):
    """Detects observations exceeding k standard deviations from the sample mean."""

    def __init__(self, sensitivity: float = 3.0) -> None:
        super().__init__(method=DetectionMethod.Z_SCORE, sensitivity=sensitivity)

    def detect(
        self,
        values: np.ndarray,
        dates: Optional[List[str]] = None,
        seasonal_period: Optional[int] = None,
        **kwargs: Any,
    ) -> DetectorOutput:
        y = np.asarray(values, dtype=float)
        hits: List[AnomalyHit] = []

        if len(y) < 3:
            return DetectorOutput(
                method=self.method,
                hits=[],
                baseline_summary={"mean": float(np.mean(y)) if len(y) > 0 else 0.0, "std": 0.0},
            )

        mean_val = float(np.mean(y))
        std_val = float(np.std(y, ddof=1)) or 1e-6

        z_scores = np.abs((y - mean_val) / std_val)

        for i, (val, z_score) in enumerate(zip(y, z_scores)):
            if z_score >= self.sensitivity:
                dev = float(val - mean_val)
                denom = abs(mean_val) if abs(mean_val) > 1e-4 else 1.0
                dev_pct = float((dev / denom) * 100.0)

                hits.append(
                    AnomalyHit(
                        index=i,
                        observed=float(val),
                        expected=mean_val,
                        deviation=dev,
                        deviation_pct=round(dev_pct, 2),
                        score=round(float(z_score), 2),
                        evidence={
                            "z_score": round(float(z_score), 3),
                            "threshold": self.sensitivity,
                            "sample_mean": round(mean_val, 2),
                            "sample_std": round(std_val, 2),
                        },
                    )
                )

        return DetectorOutput(
            method=self.method,
            hits=hits,
            baseline_summary={"mean": round(mean_val, 2), "std": round(std_val, 2)},
        )
