"""Rolling Window Dynamic Baseline Anomaly Detector."""

from typing import Any, List, Optional

import numpy as np
import pandas as pd

from app.anomalies.detectors.base import AnomalyHit, BaseAnomalyDetector, DetectorOutput
from app.database.models.anomalies import DetectionMethod


class RollingBaselineDetector(BaseAnomalyDetector):
    """Detects temporal points that deviate from local sliding window mean/median dynamics."""

    def __init__(self, window: int = 5, sensitivity: float = 2.5) -> None:
        super().__init__(method=DetectionMethod.ROLLING_BASELINE, sensitivity=sensitivity)
        self.window = max(3, window)

    def detect(
        self,
        values: np.ndarray,
        dates: Optional[List[str]] = None,
        seasonal_period: Optional[int] = None,
        **kwargs: Any,
    ) -> DetectorOutput:
        y = np.asarray(values, dtype=float)
        hits: List[AnomalyHit] = []

        if len(y) < self.window:
            return DetectorOutput(
                method=self.method,
                hits=[],
                baseline_summary={"window": self.window, "reason": "Insufficient points for rolling window"},
            )

        s = pd.Series(y)
        roll_med = s.rolling(window=self.window, min_periods=2).median().bfill().to_numpy()
        roll_std = s.rolling(window=self.window, min_periods=2).std().bfill().fillna(1.0).to_numpy()

        for i, (val, exp, std_val) in enumerate(zip(y, roll_med, roll_std)):
            sigma = std_val if std_val > 1e-4 else 1.0
            z = abs(val - exp) / sigma

            if z >= self.sensitivity:
                dev = float(val - exp)
                denom = abs(exp) if abs(exp) > 1e-4 else 1.0
                dev_pct = float((dev / denom) * 100.0)

                hits.append(
                    AnomalyHit(
                        index=i,
                        observed=float(val),
                        expected=float(exp),
                        deviation=dev,
                        deviation_pct=round(dev_pct, 2),
                        score=round(float(z), 2),
                        evidence={
                            "rolling_median": round(float(exp), 2),
                            "rolling_std": round(float(sigma), 2),
                            "local_z_score": round(float(z), 3),
                            "window_size": self.window,
                            "threshold": self.sensitivity,
                        },
                    )
                )

        return DetectorOutput(
            method=self.method,
            hits=hits,
            baseline_summary={"window": self.window, "sensitivity": self.sensitivity},
        )
