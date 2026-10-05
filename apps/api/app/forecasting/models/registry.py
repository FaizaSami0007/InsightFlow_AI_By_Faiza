"""Model Registry managing supported forecasting algorithms and hyperparameter factories."""

from typing import Any, Dict, List, Optional

from app.database.models.forecasting import ForecastModelType
from app.forecasting.models.base import BaseForecastModel
from app.forecasting.models.estimators import (
    ARIMAModel,
    ExponentialSmoothingModel,
    MovingAverageModel,
    NaiveModel,
    SARIMAModel,
    SeasonalNaiveModel,
)


class ForecastModelRegistry:
    """Registry and factory for forecasting models."""

    @classmethod
    def get_model(
        cls,
        model_type: ForecastModelType,
        seasonal_period: Optional[int] = None,
    ) -> BaseForecastModel:
        """Instantiate a specific forecasting estimator."""
        s = seasonal_period or 12

        if model_type == ForecastModelType.NAIVE:
            return NaiveModel()
        elif model_type == ForecastModelType.SEASONAL_NAIVE:
            return SeasonalNaiveModel(seasonal_period=s)
        elif model_type == ForecastModelType.MOVING_AVERAGE:
            return MovingAverageModel(window=3)
        elif model_type == ForecastModelType.EXPONENTIAL_SMOOTHING:
            return ExponentialSmoothingModel(seasonal_period=s if seasonal_period else None)
        elif model_type == ForecastModelType.ARIMA:
            return ARIMAModel()
        elif model_type == ForecastModelType.SARIMA:
            return SARIMAModel(seasonal_period=s)
        else:
            # Default to Naive
            return NaiveModel()

    @classmethod
    def get_candidate_models(
        cls,
        seasonal_period: Optional[int] = None,
        is_seasonal: bool = False,
        n_obs: int = 10,
    ) -> List[BaseForecastModel]:
        """Construct candidate models for backtesting and selection."""
        candidates: List[BaseForecastModel] = [
            NaiveModel(),
            MovingAverageModel(window=3),
            ExponentialSmoothingModel(seasonal_period=seasonal_period if is_seasonal else None),
        ]

        if is_seasonal and seasonal_period and seasonal_period >= 2:
            candidates.append(SeasonalNaiveModel(seasonal_period=seasonal_period))

        if n_obs >= 10:
            candidates.append(ARIMAModel())

        if is_seasonal and seasonal_period and n_obs >= 2 * seasonal_period:
            candidates.append(SARIMAModel(seasonal_period=seasonal_period))

        return candidates

    @classmethod
    def list_supported_models(cls) -> List[Dict[str, Any]]:
        """List metadata for all supported algorithm families."""
        return [
            {
                "type": ForecastModelType.AUTO.value,
                "name": "Auto Selection",
                "description": "Cross-validates multiple candidate models via walk-forward backtesting and selects the lowest error model.",
            },
            {
                "type": ForecastModelType.NAIVE.value,
                "name": "Naive Baseline",
                "description": "Projects the last observed historical value forward.",
            },
            {
                "type": ForecastModelType.SEASONAL_NAIVE.value,
                "name": "Seasonal Naive",
                "description": "Projects values from the corresponding season of the previous cycle.",
            },
            {
                "type": ForecastModelType.MOVING_AVERAGE.value,
                "name": "Moving Average",
                "description": "Forecasts using a sliding historical rolling mean.",
            },
            {
                "type": ForecastModelType.EXPONENTIAL_SMOOTHING.value,
                "name": "Exponential Smoothing (Holt-Winters)",
                "description": "Captures level, trend, and seasonal patterns with exponentially decaying weights.",
            },
            {
                "type": ForecastModelType.ARIMA.value,
                "name": "ARIMA",
                "description": "Autoregressive integrated moving average for non-seasonal stationary/differenced series.",
            },
            {
                "type": ForecastModelType.SARIMA.value,
                "name": "SARIMA",
                "description": "Seasonal ARIMA modeling both seasonal and non-seasonal autoregression and moving averages.",
            },
        ]
