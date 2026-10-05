"""Service layer orchestrating dataset preprocessing, backtested model fitting, and forecast persistence."""

import uuid
from typing import List, Optional

import pandas as pd
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.analytics.duckdb.manager import DuckDBManager
from app.database.models.dataset import Dataset, DatasetVersion
from app.database.models.forecasting import (
    ForecastExecution,
    ForecastStatus,
)
from app.datasets.storage import get_storage_provider
from app.forecasting.backtesting import TimeSeriesBacktester
from app.forecasting.preprocessing import PreprocessingError, TimeSeriesPreprocessor
from app.forecasting.schemas import (
    ForecastDiagnostics,
    ForecastMetrics,
    ForecastPoint,
    ForecastResponse,
    ForecastRunRequest,
    HistoricalPoint,
)


class ForecastServiceError(Exception):
    """Raised when a forecasting request is unauthorized, invalid, or fails execution."""

    pass


class ForecastService:
    """Core domain service for predictive analytics and forecasting workflows."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.duckdb_mgr = DuckDBManager.get_instance()

    async def run_forecast(self, user_id: str, request: ForecastRunRequest) -> ForecastResponse:
        """Execute end-to-end validated time-series forecast."""
        # 1. Verify Dataset Ownership
        d_stmt = select(Dataset).where(Dataset.id == request.dataset_id, Dataset.owner_id == user_id)
        d_res = await self.db.execute(d_stmt)
        dataset = d_res.scalar_one_or_none()
        if not dataset:
            raise ForecastServiceError(f"Dataset '{request.dataset_id}' not found or unauthorized.")

        # 2. Resolve Dataset Version
        if request.dataset_version_id:
            v_stmt = select(DatasetVersion).where(
                DatasetVersion.id == request.dataset_version_id,
                DatasetVersion.dataset_id == dataset.id,
            )
        else:
            v_stmt = (
                select(DatasetVersion)
                .where(DatasetVersion.dataset_id == dataset.id, DatasetVersion.status == "READY")
                .order_by(DatasetVersion.version_number.desc())
            )
        v_res = await self.db.execute(v_stmt)
        version = v_res.scalar_one_or_none()
        if not version:
            raise ForecastServiceError("No READY dataset version available for forecasting.")

        # 3. Register Dataset in DuckDB
        storage = get_storage_provider()
        file_path = str(getattr(version, "file_path", None) or storage.get_file_path(version.storage_reference))
        self.duckdb_mgr.register_dataset(
            dataset_version_id=version.id,
            file_path=file_path,
            file_format=version.file_format.value if hasattr(version.file_format, "value") else str(version.file_format),
        )

        # 4. Preprocess Time-Series
        try:
            series = TimeSeriesPreprocessor.load_and_preprocess(
                duckdb_manager=self.duckdb_mgr,
                dataset_version_id=version.id,
                target_field=request.target_field,
                time_field=request.time_field,
                requested_frequency=request.frequency,
                filters=request.filters,
            )
        except PreprocessingError as pe:
            raise ForecastServiceError(str(pe))

        # 5. Backtest & Select Model
        model, metrics, warnings = TimeSeriesBacktester.evaluate_and_select_model(
            y=series.values,
            dates=series.dates,
            requested_type=request.model_type,
            seasonal_period=series.seasonal_period,
            is_seasonal=series.is_seasonal,
            horizon=request.forecast_horizon,
        )

        # 6. Generate Future Predictions
        point_preds, lower_preds, upper_preds = model.predict(
            horizon=request.forecast_horizon,
            confidence_level=request.confidence_level,
            allow_negative=request.allow_negative,
        )

        # 7. Construct Future Date Labels
        alias_map = {"D": "D", "W": "W-MON", "M": "MS", "Q": "QS", "Y": "YS"}
        pandas_freq = alias_map.get(series.frequency, "MS")

        last_date = series.dates[-1]
        future_dates = pd.date_range(start=last_date, periods=request.forecast_horizon + 1, freq=pandas_freq)[1:]

        predictions: List[ForecastPoint] = []
        for i in range(request.forecast_horizon):
            dt_str = future_dates[i].strftime("%Y-%m-%d")
            predictions.append(
                ForecastPoint(
                    date=dt_str,
                    forecast=round(float(point_preds[i]), 2),
                    lower=round(float(lower_preds[i]), 2),
                    upper=round(float(upper_preds[i]), 2),
                )
            )

        historical_points = [
            HistoricalPoint(date=d.strftime("%Y-%m-%d"), actual=round(float(v), 2))
            for d, v in zip(series.dates, series.values)
        ]

        diagnostics = ForecastDiagnostics(
            frequency_detected=series.frequency,
            observations_count=len(series.values),
            missing_periods_imputed=series.missing_imputed_count,
            outliers_detected=series.outliers_detected_count,
            seasonality_detected=series.is_seasonal,
            seasonality_period=series.seasonal_period,
            stationarity_is_stationary=series.is_stationary,
            parameters=model.get_parameters(),
            transformations=series.transformations,
        )

        provenance = {
            "dataset_id": dataset.id,
            "dataset_version_id": version.id,
            "version_number": version.version_number,
            "target_field": request.target_field,
            "time_field": request.time_field,
            "frequency": series.frequency,
            "observations": len(series.values),
            "model_selected": model.name,
            "confidence_level": request.confidence_level,
            "baseline_mae": metrics.baseline_mae,
            "validation_mae": metrics.mae,
        }

        # 8. Persist Forecast Record
        forecast_rec = ForecastExecution(
            id=str(uuid.uuid4()),
            user_id=user_id,
            dataset_id=dataset.id,
            dataset_version_id=version.id,
            target_field=request.target_field,
            time_field=request.time_field,
            frequency=series.frequency,
            forecast_horizon=request.forecast_horizon,
            confidence_level=request.confidence_level,
            requested_model_type=request.model_type,
            selected_model_name=model.name,
            status=ForecastStatus.COMPLETED,
            metrics_json=metrics.model_dump(),
            predictions_json=[p.model_dump() for p in predictions],
            historical_points_json=[h.model_dump() for h in historical_points],
            diagnostics_json=diagnostics.model_dump(),
            provenance_json=provenance,
        )
        self.db.add(forecast_rec)
        await self.db.commit()
        await self.db.refresh(forecast_rec)

        return self._to_forecast_response(forecast_rec, warnings)

    async def get_forecast(self, user_id: str, forecast_id: str) -> ForecastResponse:
        """Retrieve stored forecast execution by ID."""
        stmt = select(ForecastExecution).where(
            ForecastExecution.id == forecast_id,
            ForecastExecution.user_id == user_id,
        )
        res = await self.db.execute(stmt)
        rec = res.scalar_one_or_none()
        if not rec:
            raise ForecastServiceError(f"Forecast '{forecast_id}' not found or unauthorized.")
        return self._to_forecast_response(rec)

    async def list_forecasts(
        self,
        user_id: str,
        dataset_id: Optional[str] = None,
    ) -> List[ForecastResponse]:
        """List past forecast executions for user."""
        stmt = select(ForecastExecution).where(ForecastExecution.user_id == user_id)
        if dataset_id:
            stmt = stmt.where(ForecastExecution.dataset_id == dataset_id)
        stmt = stmt.order_by(ForecastExecution.created_at.desc())
        res = await self.db.execute(stmt)
        records = res.scalars().all()
        return [self._to_forecast_response(r) for r in records]

    async def delete_forecast(self, user_id: str, forecast_id: str) -> None:
        """Delete a forecast execution record."""
        stmt = delete(ForecastExecution).where(
            ForecastExecution.id == forecast_id,
            ForecastExecution.user_id == user_id,
        )
        await self.db.execute(stmt)
        await self.db.commit()

    @staticmethod
    def _to_forecast_response(
        rec: ForecastExecution,
        warnings: Optional[List[str]] = None,
    ) -> ForecastResponse:
        """Transform SQLAlchemy model to Pydantic response."""
        return ForecastResponse(
            id=rec.id,
            dataset_id=rec.dataset_id,
            dataset_version_id=rec.dataset_version_id,
            target_field=rec.target_field,
            time_field=rec.time_field,
            frequency=rec.frequency,
            forecast_horizon=rec.forecast_horizon,
            confidence_level=rec.confidence_level,
            requested_model_type=rec.requested_model_type,
            selected_model_name=rec.selected_model_name,
            status=rec.status,
            metrics=ForecastMetrics.model_validate(rec.metrics_json),
            predictions=[ForecastPoint.model_validate(p) for p in rec.predictions_json],
            historical_points=[HistoricalPoint.model_validate(h) for h in rec.historical_points_json],
            diagnostics=ForecastDiagnostics.model_validate(rec.diagnostics_json),
            provenance=rec.provenance_json or {},
            warnings=warnings or [],
            created_at=rec.created_at,
        )
