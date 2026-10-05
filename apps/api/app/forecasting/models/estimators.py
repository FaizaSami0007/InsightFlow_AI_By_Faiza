"""Classical, deterministic time-series estimators adhering to BaseForecastModel."""

from typing import Any, List, Optional, Tuple

import numpy as np
import pandas as pd
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing

from app.database.models.forecasting import ForecastModelType
from app.forecasting.models.base import BaseForecastModel


class NaiveModel(BaseForecastModel):
    """Naive baseline projecting the last observed value forward."""

    def __init__(self) -> None:
        super().__init__(name="Naive (Last Value)", model_type=ForecastModelType.NAIVE)

    def fit(self, y: Any, dates: Optional[List[pd.Timestamp]] = None, **kwargs: Any) -> "NaiveModel":
        y_arr = np.asarray(y, dtype=float)
        self.last_observation = float(y_arr[-1]) if len(y_arr) > 0 else 0.0
        self.fitted_values = np.roll(y_arr, 1)
        if len(y_arr) > 0:
            self.fitted_values[0] = y_arr[0]
        self.residuals = y_arr - self.fitted_values
        self.residual_std = float(np.std(self.residuals[1:])) if len(self.residuals) > 1 else 1.0
        self.is_fitted = True
        return self

    def predict(
        self,
        horizon: int,
        confidence_level: float = 0.95,
        allow_negative: bool = False,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        z = self.get_z_score(confidence_level)
        h_steps = np.arange(1, horizon + 1)
        point = np.full(horizon, self.last_observation, dtype=float)
        # Prediction interval grows with sqrt(h)
        margin = z * self.residual_std * np.sqrt(h_steps)
        lower = point - margin
        upper = point + margin

        if not allow_negative:
            lower = np.maximum(lower, 0.0)
            point = np.maximum(point, 0.0)

        return point, lower, upper


class SeasonalNaiveModel(BaseForecastModel):
    """Seasonal naive baseline repeating observations from the previous full seasonal cycle."""

    def __init__(self, seasonal_period: int = 12) -> None:
        super().__init__(name=f"Seasonal Naive (Period={seasonal_period})", model_type=ForecastModelType.SEASONAL_NAIVE)
        self.seasonal_period = max(seasonal_period, 2)
        self.history: np.ndarray = np.array([])

    def fit(self, y: Any, dates: Optional[List[pd.Timestamp]] = None, **kwargs: Any) -> "SeasonalNaiveModel":
        y_arr = np.asarray(y, dtype=float)
        self.history = np.copy(y_arr)
        self.last_observation = float(y_arr[-1]) if len(y_arr) > 0 else 0.0
        s = self.seasonal_period

        if len(y_arr) > s:
            self.fitted_values = np.roll(y_arr, s)
            self.residuals = y_arr[s:] - self.fitted_values[s:]
            self.residual_std = float(np.std(self.residuals)) if len(self.residuals) > 0 else 1.0
        else:
            self.fitted_values = np.roll(y_arr, 1)
            self.residuals = y_arr[1:] - self.fitted_values[1:]
            self.residual_std = float(np.std(self.residuals)) if len(self.residuals) > 0 else 1.0

        self.params["seasonal_period"] = self.seasonal_period
        self.is_fitted = True
        return self

    def predict(
        self,
        horizon: int,
        confidence_level: float = 0.95,
        allow_negative: bool = False,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        s = self.seasonal_period
        z = self.get_z_score(confidence_level)
        point = np.zeros(horizon, dtype=float)

        for h in range(horizon):
            idx = len(self.history) - s + (h % s)
            point[h] = self.history[idx] if idx >= 0 and idx < len(self.history) else self.last_observation

        # Uncertainty multiplier accounts for multiple seasonal cycles k = floor(h/s) + 1
        k_cycles = np.floor(np.arange(horizon) / s) + 1.0
        margin = z * self.residual_std * np.sqrt(k_cycles)
        lower = point - margin
        upper = point + margin

        if not allow_negative:
            lower = np.maximum(lower, 0.0)
            point = np.maximum(point, 0.0)

        return point, lower, upper


class MovingAverageModel(BaseForecastModel):
    """Rolling window mean forecast."""

    def __init__(self, window: int = 3) -> None:
        super().__init__(name=f"Moving Average (k={window})", model_type=ForecastModelType.MOVING_AVERAGE)
        self.window = window

    def fit(self, y: Any, dates: Optional[List[pd.Timestamp]] = None, **kwargs: Any) -> "MovingAverageModel":
        y_arr = np.asarray(y, dtype=float)
        w = min(self.window, len(y_arr))
        self.last_observation = float(np.mean(y_arr[-w:])) if w > 0 else 0.0
        self.fitted_values = pd.Series(y_arr).rolling(window=w, min_periods=1).mean().to_numpy()
        self.residuals = y_arr - self.fitted_values
        self.residual_std = float(np.std(self.residuals)) or 1.0
        self.params["window"] = w
        self.is_fitted = True
        return self

    def predict(
        self,
        horizon: int,
        confidence_level: float = 0.95,
        allow_negative: bool = False,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        z = self.get_z_score(confidence_level)
        h_steps = np.arange(1, horizon + 1)
        point = np.full(horizon, self.last_observation, dtype=float)
        margin = z * self.residual_std * np.sqrt(1.0 + (h_steps / self.window))
        lower = point - margin
        upper = point + margin

        if not allow_negative:
            lower = np.maximum(lower, 0.0)
            point = np.maximum(point, 0.0)

        return point, lower, upper


class ExponentialSmoothingModel(BaseForecastModel):
    """Holt-Winters Exponential Smoothing with automated trend/seasonality selection."""

    def __init__(self, seasonal_period: Optional[int] = None) -> None:
        super().__init__(name="Exponential Smoothing (Holt-Winters)", model_type=ForecastModelType.EXPONENTIAL_SMOOTHING)
        self.seasonal_period = seasonal_period
        self._fitted_hw = None

    def fit(self, y: Any, dates: Optional[List[pd.Timestamp]] = None, **kwargs: Any) -> "ExponentialSmoothingModel":
        y_arr = np.asarray(y, dtype=float)
        self.last_observation = float(y_arr[-1]) if len(y_arr) > 0 else 0.0
        s = self.seasonal_period

        # Determine trend and seasonal configuration safely
        has_season = bool(s and s >= 2 and len(y_arr) >= 2 * s)
        has_trend = len(y_arr) >= 6

        try:
            model = ExponentialSmoothing(
                y_arr,
                trend="add" if has_trend else None,
                seasonal="add" if has_season else None,
                seasonal_periods=s if has_season else None,
                initialization_method="estimated",
            )
            self._fitted_hw = model.fit(optimized=True)
            self.fitted_values = self._fitted_hw.fittedvalues
            self.residuals = y_arr - self.fitted_values
            self.residual_std = float(np.std(self.residuals)) or 1.0
            self.params = {
                "alpha": round(float(self._fitted_hw.params.get("smoothing_level", 0.0)), 4),
                "beta": round(float(self._fitted_hw.params.get("smoothing_trend", 0.0)), 4) if has_trend else None,
                "gamma": round(float(self._fitted_hw.params.get("smoothing_seasonal", 0.0)), 4) if has_season else None,
                "has_trend": has_trend,
                "has_seasonality": has_season,
            }
        except Exception:
            # Fallback simple exponential smoothing
            alpha = 0.3
            fitted = np.zeros_like(y_arr)
            fitted[0] = y_arr[0] if len(y_arr) > 0 else 0.0
            for t in range(1, len(y_arr)):
                fitted[t] = alpha * y_arr[t - 1] + (1 - alpha) * fitted[t - 1]
            self.fitted_values = fitted
            self.residuals = y_arr - fitted
            self.residual_std = float(np.std(self.residuals)) or 1.0
            self.params = {"alpha": alpha, "fallback": True}

        self.is_fitted = True
        return self

    def predict(
        self,
        horizon: int,
        confidence_level: float = 0.95,
        allow_negative: bool = False,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        z = self.get_z_score(confidence_level)
        h_steps = np.arange(1, horizon + 1)

        if self._fitted_hw is not None:
            try:
                point = np.asarray(self._fitted_hw.forecast(horizon), dtype=float)
            except Exception:
                point = np.full(horizon, self.last_observation, dtype=float)
        else:
            point = np.full(horizon, self.last_observation, dtype=float)

        margin = z * self.residual_std * np.sqrt(h_steps)
        lower = point - margin
        upper = point + margin

        if not allow_negative:
            lower = np.maximum(lower, 0.0)
            point = np.maximum(point, 0.0)

        return point, lower, upper


class ARIMAModel(BaseForecastModel):
    """AutoRegressive Integrated Moving Average ARIMA(p,d,q) with AIC order search."""

    def __init__(self, order: Optional[Tuple[int, int, int]] = None) -> None:
        super().__init__(name="ARIMA", model_type=ForecastModelType.ARIMA)
        self.order = order or (1, 1, 1)
        self._fitted_arima = None

    def fit(self, y: Any, dates: Optional[List[pd.Timestamp]] = None, **kwargs: Any) -> "ARIMAModel":
        y_arr = np.asarray(y, dtype=float)
        self.last_observation = float(y_arr[-1]) if len(y_arr) > 0 else 0.0

        # AIC search over simple bounded orders
        candidate_orders = [
            (1, 1, 1),
            (0, 1, 1),
            (1, 1, 0),
            (1, 0, 1),
            (2, 1, 1),
            (1, 0, 0),
        ]

        best_aic = float("inf")
        best_fit = None
        best_order = (1, 1, 1)

        for ord_tuple in candidate_orders:
            try:
                fit_candidate = ARIMA(y_arr, order=ord_tuple).fit()
                if fit_candidate.aic < best_aic:
                    best_aic = fit_candidate.aic
                    best_fit = fit_candidate
                    best_order = ord_tuple
            except Exception:
                continue

        if best_fit is not None:
            self._fitted_arima = best_fit
            self.order = best_order
            self.fitted_values = np.asarray(best_fit.fittedvalues)
            self.residuals = y_arr - self.fitted_values
            self.residual_std = float(np.std(self.residuals)) or 1.0
            self.name = f"ARIMA{self.order}"
            self.params = {
                "order": self.order,
                "aic": round(float(best_fit.aic), 2),
                "bic": round(float(best_fit.bic), 2),
            }
        else:
            # Fallback Naive
            self.fitted_values = np.roll(y_arr, 1)
            if len(y_arr) > 0:
                self.fitted_values[0] = y_arr[0]
            self.residuals = y_arr - self.fitted_values
            self.residual_std = float(np.std(self.residuals)) or 1.0
            self.params = {"fallback": True}

        self.is_fitted = True
        return self

    def predict(
        self,
        horizon: int,
        confidence_level: float = 0.95,
        allow_negative: bool = False,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        z = self.get_z_score(confidence_level)
        alpha = 1.0 - confidence_level

        if self._fitted_arima is not None:
            try:
                forecast_res = self._fitted_arima.get_forecast(steps=horizon)
                point = np.asarray(forecast_res.predicted_mean, dtype=float)
                conf_int = forecast_res.conf_int(alpha=alpha)
                lower = np.asarray(conf_int[:, 0], dtype=float)
                upper = np.asarray(conf_int[:, 1], dtype=float)
            except Exception:
                point = np.full(horizon, self.last_observation, dtype=float)
                margin = z * self.residual_std * np.sqrt(np.arange(1, horizon + 1))
                lower = point - margin
                upper = point + margin
        else:
            point = np.full(horizon, self.last_observation, dtype=float)
            margin = z * self.residual_std * np.sqrt(np.arange(1, horizon + 1))
            lower = point - margin
            upper = point + margin

        if not allow_negative:
            lower = np.maximum(lower, 0.0)
            point = np.maximum(point, 0.0)

        return point, lower, upper


class SARIMAModel(BaseForecastModel):
    """Seasonal ARIMA(p,d,q)x(P,D,Q)s estimator."""

    def __init__(self, seasonal_period: int = 12) -> None:
        super().__init__(name=f"SARIMA (s={seasonal_period})", model_type=ForecastModelType.SARIMA)
        self.seasonal_period = seasonal_period
        self._fitted_sarima = None

    def fit(self, y: Any, dates: Optional[List[pd.Timestamp]] = None, **kwargs: Any) -> "SARIMAModel":
        y_arr = np.asarray(y, dtype=float)
        self.last_observation = float(y_arr[-1]) if len(y_arr) > 0 else 0.0
        s = self.seasonal_period

        if len(y_arr) >= 2 * s:
            candidate_seasonal = [
                ((1, 1, 1), (1, 1, 0, s)),
                ((0, 1, 1), (0, 1, 1, s)),
                ((1, 0, 1), (1, 0, 0, s)),
                ((1, 1, 0), (0, 1, 1, s)),
            ]
        else:
            candidate_seasonal = [
                ((1, 1, 1), (0, 0, 0, 0)),
                ((0, 1, 1), (0, 0, 0, 0)),
            ]

        best_aic = float("inf")
        best_fit = None
        best_cfg = ((1, 1, 1), (0, 0, 0, 0))

        for ord_t, s_ord_t in candidate_seasonal:
            try:
                fit_c = ARIMA(y_arr, order=ord_t, seasonal_order=s_ord_t).fit()
                if fit_c.aic < best_aic:
                    best_aic = fit_c.aic
                    best_fit = fit_c
                    best_cfg = (ord_t, s_ord_t)
            except Exception:
                continue

        if best_fit is not None:
            self._fitted_sarima = best_fit
            self.fitted_values = np.asarray(best_fit.fittedvalues)
            self.residuals = y - self.fitted_values
            self.residual_std = float(np.std(self.residuals)) or 1.0
            self.name = f"SARIMA{best_cfg[0]}x{best_cfg[1]}"
            self.params = {
                "order": best_cfg[0],
                "seasonal_order": best_cfg[1],
                "aic": round(float(best_fit.aic), 2),
                "bic": round(float(best_fit.bic), 2),
            }
        else:
            # Fallback
            self.fitted_values = np.roll(y, 1)
            self.fitted_values[0] = y[0]
            self.residuals = y - self.fitted_values
            self.residual_std = float(np.std(self.residuals)) or 1.0
            self.params = {"fallback": True}

        self.is_fitted = True
        return self

    def predict(
        self,
        horizon: int,
        confidence_level: float = 0.95,
        allow_negative: bool = False,
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        z = self.get_z_score(confidence_level)
        alpha = 1.0 - confidence_level

        if self._fitted_sarima is not None:
            try:
                forecast_res = self._fitted_sarima.get_forecast(steps=horizon)
                point = np.asarray(forecast_res.predicted_mean, dtype=float)
                conf_int = forecast_res.conf_int(alpha=alpha)
                lower = np.asarray(conf_int[:, 0], dtype=float)
                upper = np.asarray(conf_int[:, 1], dtype=float)
            except Exception:
                point = np.full(horizon, self.last_observation, dtype=float)
                margin = z * self.residual_std * np.sqrt(np.arange(1, horizon + 1))
                lower = point - margin
                upper = point + margin
        else:
            point = np.full(horizon, self.last_observation, dtype=float)
            margin = z * self.residual_std * np.sqrt(np.arange(1, horizon + 1))
            lower = point - margin
            upper = point + margin

        if not allow_negative:
            lower = np.maximum(lower, 0.0)
            point = np.maximum(point, 0.0)

        return point, lower, upper
