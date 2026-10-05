"""Severity and Materiality evaluation for detected anomalies."""

import math
from typing import Tuple

from app.database.models.anomalies import AnomalySeverity


class SeverityEvaluator:
    """Evaluates statistical deviation, business materiality, and assigns explainable severity levels."""

    @classmethod
    def evaluate(
        cls,
        anomaly_score: float,
        deviation: float,
        deviation_pct: float,
        expected_value: float,
        recency_idx: int = 0,
        total_points: int = 1,
    ) -> Tuple[AnomalySeverity, float]:
        """Compute severity level and materiality priority score.

        Rules:
        - Critical: Score >= 4.5 or (|deviation_pct| >= 50% with absolute deviation >= 500.0)
        - High: Score >= 3.5 or (|deviation_pct| >= 30% with absolute deviation >= 100.0)
        - Medium: Score >= 2.5 or |deviation_pct| >= 15%
        - Low: Score >= 1.5 or |deviation_pct| >= 5%
        - Info: Minor deviation below thresholds
        """
        abs_dev = abs(deviation)
        abs_pct = abs(deviation_pct)

        # 1. Base statistical severity
        if anomaly_score >= 4.5 or (abs_pct >= 50.0 and abs_dev >= 500.0):
            severity = AnomalySeverity.CRITICAL
        elif anomaly_score >= 3.5 or (abs_pct >= 30.0 and abs_dev >= 100.0):
            severity = AnomalySeverity.HIGH
        elif anomaly_score >= 2.5 or abs_pct >= 15.0:
            severity = AnomalySeverity.MEDIUM
        elif anomaly_score >= 1.5 or abs_pct >= 5.0:
            severity = AnomalySeverity.LOW
        else:
            severity = AnomalySeverity.INFO

        # 2. Materiality Priority Score: Combines statistical score with log-scaled magnitude & recency
        # Avoids tiny $2 items dominating over $100k revenue shifts
        magnitude_factor = math.log10(max(10.0, abs_dev))
        recency_weight = 1.0 + 0.5 * (float(recency_idx) / max(1.0, float(total_points)))
        priority_score = round(float(anomaly_score * magnitude_factor * recency_weight), 2)

        return severity, priority_score
