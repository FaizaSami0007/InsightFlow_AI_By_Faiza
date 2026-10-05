"""Anomaly Detector Registry and Factory."""

from typing import Any, Dict, List, Optional

from app.anomalies.detectors.base import BaseAnomalyDetector
from app.anomalies.detectors.forecast_deviation import ForecastDeviationDetector
from app.anomalies.detectors.iqr import IQRDetector
from app.anomalies.detectors.robust_z_score import RobustZScoreDetector
from app.anomalies.detectors.rolling_baseline import RollingBaselineDetector
from app.anomalies.detectors.seasonal_baseline import SeasonalBaselineDetector
from app.anomalies.detectors.z_score import ZScoreDetector
from app.database.models.anomalies import DetectionMethod


class AnomalyDetectorRegistry:
    """Factory and registry for statistical anomaly detection methods."""

    @classmethod
    def get_detector(
        cls,
        method: DetectionMethod = DetectionMethod.ROBUST_Z_SCORE,
        sensitivity: float = 3.0,
        seasonal_period: Optional[int] = None,
        window: int = 5,
    ) -> BaseAnomalyDetector:
        """Instantiate an anomaly detector based on chosen methodology."""
        if method == DetectionMethod.Z_SCORE:
            return ZScoreDetector(sensitivity=sensitivity)
        elif method == DetectionMethod.ROBUST_Z_SCORE:
            return RobustZScoreDetector(sensitivity=sensitivity)
        elif method == DetectionMethod.IQR:
            return IQRDetector(sensitivity=sensitivity if sensitivity < 3.0 else 1.5)
        elif method == DetectionMethod.ROLLING_BASELINE:
            return RollingBaselineDetector(window=window, sensitivity=sensitivity)
        elif method == DetectionMethod.SEASONAL_BASELINE:
            return SeasonalBaselineDetector(seasonal_period=seasonal_period or 12, sensitivity=sensitivity)
        elif method == DetectionMethod.FORECAST_DEVIATION:
            return ForecastDeviationDetector(sensitivity=sensitivity)
        else:
            return RobustZScoreDetector(sensitivity=sensitivity)

    @classmethod
    def list_supported_methods(cls) -> List[Dict[str, Any]]:
        """List metadata for all supported detection algorithms."""
        return [
            {
                "method": DetectionMethod.ROBUST_Z_SCORE.value,
                "name": "Robust Z-Score (Median / MAD)",
                "description": "Detects outliers using Median Absolute Deviation. Highly resilient to existing extreme outliers.",
            },
            {
                "method": DetectionMethod.Z_SCORE.value,
                "name": "Standard Z-Score (Mean / Std)",
                "description": "Parametric detection measuring distance in standard deviations from the sample mean.",
            },
            {
                "method": DetectionMethod.IQR.value,
                "name": "Interquartile Range (IQR / Boxplot)",
                "description": "Non-parametric detection using Q1 - 1.5*IQR and Q3 + 1.5*IQR Tukey fences.",
            },
            {
                "method": DetectionMethod.ROLLING_BASELINE.value,
                "name": "Rolling Dynamic Baseline",
                "description": "Tracks local moving window statistics to capture evolving trend shifts.",
            },
            {
                "method": DetectionMethod.SEASONAL_BASELINE.value,
                "name": "Seasonal Cycle Baseline",
                "description": "Compares periods directly against identical seasonal slots across recurring cycles.",
            },
            {
                "method": DetectionMethod.FORECAST_DEVIATION.value,
                "name": "Forecast Prediction Interval Deviation",
                "description": "Flags actual observations that break out of backtested time-series prediction bands.",
            },
        ]
