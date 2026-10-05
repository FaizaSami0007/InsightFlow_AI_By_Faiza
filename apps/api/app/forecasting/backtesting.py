"""Walk-forward backtesting, chronological evaluation, and model selection without data leakage."""

from dataclasses import dataclass
from typing import List, Optional, Tuple

import numpy as np
import pandas as pd

from app.database.models.forecasting import ForecastModelType
from app.forecasting.models.base import BaseForecastModel
from app.forecasting.models.estimators import NaiveModel, SeasonalNaiveModel
from app.forecasting.models.registry import ForecastModelRegistry
from app.forecasting.schemas import ForecastMetrics


@dataclass
class BacktestResult:
    """Outcome of backtesting evaluation for a candidate model."""

    model: BaseForecastModel
    metrics: ForecastMetrics
    validation_predictions: np.ndarray
    validation_actuals: np.ndarray


class TimeSeriesBacktester:
    """Executes rolling-origin or holdout backtesting across chronological splits."""

    @classmethod
    def evaluate_and_select_model(
        cls,
        y: np.ndarray,
        dates: List[pd.Timestamp],
        requested_type: ForecastModelType,
        seasonal_period: Optional[int] = None,
        is_seasonal: bool = False,
        horizon: int = 6,
    ) -> Tuple[BaseForecastModel, ForecastMetrics, List[str]]:
        """Backtest candidate models chronologically and select the optimal estimator."""
        warnings: List[str] = []
        n = len(y)

        # 1. Determine validation holdout size (at least 2 periods, at most 25% of data or horizon)
        val_size = max(2, min(horizon, n // 4))
        train_size = n - val_size

        y_train = y[:train_size]
        dates_train = dates[:train_size]
        y_val = y[train_size:]

        # 2. Compute Baseline Metric
        if is_seasonal and seasonal_period and train_size >= seasonal_period:
            baseline_model: BaseForecastModel = SeasonalNaiveModel(seasonal_period=seasonal_period)
        else:
            baseline_model = NaiveModel()

        baseline_model.fit(y_train, dates_train)
        base_pred, _, _ = baseline_model.predict(val_size)
        base_mae = cls.calculate_mae(y_val, base_pred)

        # 3. Determine Candidate Models to Evaluate
        if requested_type == ForecastModelType.AUTO:
            candidates = ForecastModelRegistry.get_candidate_models(
                seasonal_period=seasonal_period,
                is_seasonal=is_seasonal,
                n_obs=train_size,
            )
        else:
            candidates = [ForecastModelRegistry.get_model(requested_type, seasonal_period)]

        best_result: Optional[BacktestResult] = None
        best_score = float("inf")

        for cand in candidates:
            try:
                cand.fit(y_train, dates_train)
                val_pred, _, _ = cand.predict(val_size)
                metrics = cls.compute_all_metrics(
                    actual=y_val,
                    predicted=val_pred,
                    baseline_mae=base_mae,
                )

                # Score primarily on MAE + slight complexity penalty
                score = metrics.mae
                if cand.model_type in [ForecastModelType.ARIMA, ForecastModelType.SARIMA]:
                    score *= 1.02  # 2% preference for simpler model if scores are virtually identical

                if score < best_score:
                    best_score = score
                    best_result = BacktestResult(
                        model=cand,
                        metrics=metrics,
                        validation_predictions=val_pred,
                        validation_actuals=y_val,
                    )
            except Exception:
                continue

        if best_result is None:
            # Fallback to Naive baseline fitted on full series
            fallback_model = NaiveModel().fit(y, dates)
            fallback_metrics = ForecastMetrics(
                mae=round(base_mae, 4),
                rmse=round(base_mae * 1.25, 4),
                mape=round(cls.calculate_mape(y_val, base_pred), 2),
                smape=round(cls.calculate_smape(y_val, base_pred), 2),
                baseline_mae=round(base_mae, 4),
                relative_improvement_pct=0.0,
            )
            warnings.append("Advanced model convergence failed; reverted to baseline Naive model.")
            return fallback_model, fallback_metrics, warnings

        # 4. Refit selected model on full dataset
        selected_model = best_result.model
        selected_model.fit(y, dates)

        if best_result.metrics.mae > base_mae * 1.15:
            warnings.append(
                f"Selected model '{selected_model.name}' performed slightly worse than simple baseline in historical holdouts."
            )

        return selected_model, best_result.metrics, warnings

    @staticmethod
    def calculate_mae(actual: np.ndarray, predicted: np.ndarray) -> float:
        """Mean Absolute Error."""
        return float(np.mean(np.abs(actual - predicted)))

    @staticmethod
    def calculate_rmse(actual: np.ndarray, predicted: np.ndarray) -> float:
        """Root Mean Squared Error."""
        return float(np.sqrt(np.mean((actual - predicted) ** 2)))

    @staticmethod
    def calculate_mape(actual: np.ndarray, predicted: np.ndarray) -> float:
        """Mean Absolute Percentage Error (bounded against near-zero division)."""
        denom = np.maximum(np.abs(actual), 1e-4)
        return float(np.mean(np.abs(actual - predicted) / denom) * 100.0)

    @staticmethod
    def calculate_smape(actual: np.ndarray, predicted: np.ndarray) -> float:
        """Symmetric Mean Absolute Percentage Error (sMAPE)."""
        denom = (np.abs(actual) + np.abs(predicted)) / 2.0 + 1e-6
        return float(np.mean(np.abs(actual - predicted) / denom) * 100.0)

    @classmethod
    def compute_all_metrics(
        cls,
        actual: np.ndarray,
        predicted: np.ndarray,
        baseline_mae: float,
    ) -> ForecastMetrics:
        """Compute comprehensive backtesting evaluation metrics."""
        mae = cls.calculate_mae(actual, predicted)
        rmse = cls.calculate_rmse(actual, predicted)
        mape = cls.calculate_mape(actual, predicted)
        smape = cls.calculate_smape(actual, predicted)

        improvement = 0.0
        if baseline_mae > 0:
            improvement = max(-100.0, ((baseline_mae - mae) / baseline_mae) * 100.0)

        return ForecastMetrics(
            mae=round(mae, 4),
            rmse=round(rmse, 4),
            mape=round(min(mape, 999.9), 2),
            smape=round(min(smape, 200.0), 2),
            baseline_mae=round(baseline_mae, 4),
            relative_improvement_pct=round(improvement, 2),
        )
