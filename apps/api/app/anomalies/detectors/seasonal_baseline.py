"""Seasonal Cycle Baseline Anomaly Detector."""

from typing import Any, Dict, List, Optional

import numpy as np

from app.anomalies.detectors.base import AnomalyHit, BaseAnomalyDetector, DetectorOutput
from app.database.models.anomalies import DetectionMethod


class SeasonalBaselineDetector(BaseAnomalyDetector):
    """Compares observations against corresponding historical seasonal cycle slots (e.g. Month-of-Year, Day-of-Week)."""

    def __init__(self, seasonal_period: int = 12, sensitivity: float = 2.5) -> None:
        super().__init__(method=DetectionMethod.SEASONAL_BASELINE, sensitivity=sensitivity)
        self.seasonal_period = max(2, seasonal_period)

    def detect(
        self,
        values: np.ndarray,
        dates: Optional[List[str]] = None,
        seasonal_period: Optional[int] = None,
        **kwargs: Any,
    ) -> DetectorOutput:
        y = np.asarray(values, dtype=float)
        s = seasonal_period or self.seasonal_period
        hits: List[AnomalyHit] = []

        if len(y) < 2 * s:
            # Fallback to standard baseline if insufficient cycles exist
            return DetectorOutput(
                method=self.method,
                hits=[],
                baseline_summary={"seasonal_period": s, "reason": "Requires at least 2 complete seasonal cycles"},
            )

        # Compute seasonal slot medians and MADs
        slots: Dict[int, List[float]] = {k: [] for k in range(s)}
        for i, val in enumerate(y):
            slots[i % s].append(float(val))

        slot_medians: Dict[int, float] = {}
        slot_stds: Dict[int, float] = {}

        for k in range(s):
            slot_vals = np.array(slots[k])
            med = float(np.median(slot_vals))
            slot_medians[k] = med
            mad = float(np.median(np.abs(slot_vals - med)))
            slot_stds[k] = 1.4826 * mad if mad > 1e-4 else float(np.std(slot_vals)) or 1.0

        for i, val in enumerate(y):
            slot_idx = i % s
            exp = slot_medians[slot_idx]
            sigma = slot_stds[slot_idx]
            z = abs(val - exp) / sigma

            if z >= self.sensitivity:
                dev = float(val - exp)
                denom = abs(exp) if abs(exp) > 1e-4 else 1.0
                dev_pct = float((dev / denom) * 100.0)

                hits.append(
                    AnomalyHit(
                        index=i,
                        observed=float(val),
                        expected=round(exp, 2),
                        deviation=round(dev, 2),
                        deviation_pct=round(dev_pct, 2),
                        score=round(float(z), 2),
                        evidence={
                            "seasonal_slot": slot_idx,
                            "seasonal_period": s,
                            "slot_expected_median": round(exp, 2),
                            "slot_std": round(sigma, 2),
                            "seasonal_z_score": round(float(z), 3),
                            "threshold": self.sensitivity,
                        },
                    )
                )

        return DetectorOutput(
            method=self.method,
            hits=hits,
            baseline_summary={"seasonal_period": s, "slots_modeled": len(slot_medians)},
        )
