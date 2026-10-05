"""Robust Modified Z-Score (Median / Median Absolute Deviation) Anomaly Detector."""

from typing import Any, List, Optional

import numpy as np

from app.anomalies.detectors.base import AnomalyHit, BaseAnomalyDetector, DetectorOutput
from app.database.models.anomalies import DetectionMethod


class RobustZScoreDetector(BaseAnomalyDetector):
    """Detects anomalies using Median Absolute Deviation (MAD), resilient against severe outlier skew."""

    def __init__(self, sensitivity: float = 3.0) -> None:
        super().__init__(method=DetectionMethod.ROBUST_Z_SCORE, sensitivity=sensitivity)

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
                baseline_summary={"median": float(np.median(y)) if len(y) > 0 else 0.0, "mad": 0.0},
            )

        med_val = float(np.median(y))
        abs_diff = np.abs(y - med_val)
        mad_val = float(np.median(abs_diff))

        if mad_val > 1e-6:
            mod_z_scores = 0.6745 * abs_diff / mad_val
        else:
            # Fallback when >50% of values are identical (MAD=0): use mean absolute deviation
            mean_ad = float(np.mean(abs_diff))
            if mean_ad > 1e-6:
                mod_z_scores = abs_diff / (1.253314 * mean_ad)
            else:
                std_val = float(np.std(y)) or 1.0
                mod_z_scores = abs_diff / std_val

        for i, (val, mod_z) in enumerate(zip(y, mod_z_scores)):
            if mod_z >= self.sensitivity:
                dev = float(val - med_val)
                denom = abs(med_val) if abs(med_val) > 1e-4 else 1.0
                dev_pct = float((dev / denom) * 100.0)

                hits.append(
                    AnomalyHit(
                        index=i,
                        observed=float(val),
                        expected=med_val,
                        deviation=dev,
                        deviation_pct=round(dev_pct, 2),
                        score=round(float(mod_z), 2),
                        evidence={
                            "modified_z_score": round(float(mod_z), 3),
                            "threshold": self.sensitivity,
                            "median": round(med_val, 2),
                            "mad": round(mad_val, 2),
                        },
                    )
                )

        return DetectorOutput(
            method=self.method,
            hits=hits,
            baseline_summary={"median": round(med_val, 2), "mad": round(mad_val, 2)},
        )
