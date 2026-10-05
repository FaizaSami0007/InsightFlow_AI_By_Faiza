"""Base Abstract Class and Protocol for Time-Series Forecasting Estimators."""

from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from scipy import stats

from app.database.models.forecasting import ForecastModelType


class BaseForecastModel(ABC):
    """Abstract interface governing all deterministic forecasting estimators."""

    def __init__(self, name: str, model_type: ForecastModelType):
        self.name = name
        self.model_type = model_type
        self.is_fitted = False
        self.fitted_values: np.ndarray = np.array([])
        self.residuals: np.ndarray = np.array([])
        self.residual_std: float = 1.0
        self.last_observation: float = 0.0
        self.params: Dict[str, Any] = {}

    @abstractmethod
    def fit(self, y: np.ndarray, dates: Optional[List[pd.Timestamp]] = None, **kwargs: Any) -> "BaseForecastModel":
        """Fit model on historical 1D numpy array."""
        pass

    @abstractmethod
    def predict(
        self,
        horizon: int,
        confidence_level: float = 0.95,
        allow_negative: bool = False,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """Generate point forecasts with lower and upper prediction intervals (point, lower, upper)."""
        pass

    def get_parameters(self) -> Dict[str, Any]:
        """Return explainable hyperparameter and fit diagnostics."""
        return {
            "name": self.name,
            "model_type": self.model_type.value,
            "residual_std": round(float(self.residual_std), 4),
            **self.params,
        }

    @staticmethod
    def get_z_score(confidence_level: float) -> float:
        """Calculate normal distribution critical value for prediction interval."""
        alpha = (1.0 - confidence_level) / 2.0
        return float(stats.norm.ppf(1.0 - alpha))
