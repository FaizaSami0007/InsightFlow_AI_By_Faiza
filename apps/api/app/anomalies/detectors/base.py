"""Abstract Base Class and Protocol for Statistical Anomaly Detectors."""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np

from app.database.models.anomalies import DetectionMethod


@dataclass
class AnomalyHit:
    """Statistical outcome for a single anomalous point."""

    index: int
    observed: float
    expected: float
    deviation: float
    deviation_pct: float
    score: float
    evidence: Dict[str, Any]


@dataclass
class DetectorOutput:
    """Complete collection of detected anomalies and detector metadata."""

    method: DetectionMethod
    hits: List[AnomalyHit]
    baseline_summary: Dict[str, Any]


class BaseAnomalyDetector(ABC):
    """Abstract interface governing all statistical anomaly detection strategies."""

    def __init__(self, method: DetectionMethod, sensitivity: float = 3.0) -> None:
        self.method = method
        self.sensitivity = max(1.0, float(sensitivity))

    @abstractmethod
    def detect(
        self,
        values: np.ndarray,
        dates: Optional[List[str]] = None,
        seasonal_period: Optional[int] = None,
        **kwargs: Any,
    ) -> DetectorOutput:
        """Execute deterministic statistical anomaly detection across 1D numeric array."""
        pass
