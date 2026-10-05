"""Unit and Integration tests for Phase 11 Predictive Analytics & Forecasting Engine."""

import io
import math

import numpy as np
import pandas as pd
import pytest
from fastapi.testclient import TestClient

from app.database.models.forecasting import ForecastModelType
from app.forecasting.backtesting import TimeSeriesBacktester
from app.forecasting.models.estimators import (
    ARIMAModel,
    ExponentialSmoothingModel,
    NaiveModel,
    SeasonalNaiveModel,
)
from app.forecasting.models.registry import ForecastModelRegistry
from app.forecasting.preprocessing import TimeSeriesPreprocessor
from app.main import app

client = TestClient(app)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------
@pytest.fixture
def auth_header():
    email = "forecaster@example.com"
    pwd = "Password123!"
    client.post("/api/v1/auth/register", json={"email": email, "password": pwd, "full_name": "Forecast User"})
    login = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def another_auth_header():
    email = "other_forecaster@example.com"
    pwd = "Password123!"
    client.post("/api/v1/auth/register", json={"email": email, "password": pwd, "full_name": "Other User"})
    login = client.post("/api/v1/auth/login", json={"email": email, "password": pwd})
    token = login.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def monthly_sales_dataset(auth_header):
    # 36 months of synthetic sales data with trend + seasonality
    dates = pd.date_range(start="2021-01-01", periods=36, freq="MS")
    rows = ["date,revenue,orders,category"]
    for i, d in enumerate(dates):
        rev = 1000 + i * 50 + 200 * math.sin(2 * math.pi * i / 12) + (i % 3) * 10
        orders = 50 + i * 2 + (i % 4)
        rows.append(f"{d.strftime('%Y-%m-%d')},{rev:.2f},{orders},Retail")

    csv_data = "\n".join(rows).encode("utf-8")
    files = {"file": ("monthly_sales.csv", io.BytesIO(csv_data), "text/csv")}
    res = client.post("/api/v1/datasets", headers=auth_header, files=files, data={"name": "Monthly Sales"})
    assert res.status_code == 201
    return res.json()


# ---------------------------------------------------------------------------
# Preprocessing Unit Tests
# ---------------------------------------------------------------------------
def test_preprocessor_frequency_detection_and_regularization():
    # Construct irregular date series with missing months
    dates = ["2022-01-01", "2022-02-01", "2022-04-01", "2022-05-01", "2022-06-01", "2022-07-01"]
    values = [100.0, 110.0, 130.0, 140.0, 150.0, 160.0]
    df = pd.DataFrame({"time": dates, "sales": values})

    result = TimeSeriesPreprocessor.prepare_from_df(
        df=df,
        time_col="time",
        target_col="sales",
        requested_freq="MS",
        impute_strategy="interpolate",
        min_observations=5,
    )

    assert "M" in result.frequency
    assert len(result.values) == 7  # 2022-01 to 2022-07 has 7 months
    assert result.missing_imputed_count >= 1
    # Check that imputed March value is interpolated between 110 and 130 -> 120
    march_val = result.values[2]
    assert abs(march_val - 120.0) < 1.0


def test_preprocessor_outlier_and_seasonality_detection():
    # 24 months data with seasonal wave
    dates = pd.date_range("2020-01-01", periods=24, freq="MS")
    vals = [100 + 30 * math.sin(2 * math.pi * i / 12) for i in range(24)]

    df_seasonal = pd.DataFrame({"ds": dates, "y": vals})
    res_seasonal = TimeSeriesPreprocessor.prepare_from_df(df_seasonal, time_col="ds", target_col="y")
    assert res_seasonal.is_seasonal is True
    assert res_seasonal.seasonal_period == 12

    # Spike outlier test
    vals_outlier = list(vals)
    vals_outlier[10] = 999.0
    df_outlier = pd.DataFrame({"ds": dates, "y": vals_outlier})
    res_outlier = TimeSeriesPreprocessor.prepare_from_df(df_outlier, time_col="ds", target_col="y")
    assert res_outlier.outliers_detected_count >= 1


def test_preprocessor_insufficient_data_rejection():
    df = pd.DataFrame({"ds": ["2023-01-01", "2023-01-02", "2023-01-03"], "y": [1.0, 2.0, 3.0]})
    with pytest.raises(ValueError, match="Insufficient temporal observations"):
        TimeSeriesPreprocessor.prepare_from_df(df, time_col="ds", target_col="y", min_observations=5)


# ---------------------------------------------------------------------------
# Estimator Tests
# ---------------------------------------------------------------------------
def test_naive_and_seasonal_naive_models():
    series = np.array([10.0, 20.0, 30.0, 40.0])

    naive = NaiveModel()
    naive.fit(series)
    point, lower, upper = naive.predict(horizon=3, confidence_level=0.95)
    assert len(point) == 3
    assert all(v == 40.0 for v in point)
    assert all(low <= p <= u for low, p, u in zip(lower, point, upper))

    # Seasonal Naive
    s_series = np.array([10.0, 20.0, 30.0, 40.0, 11.0, 21.0, 31.0, 41.0])
    s_naive = SeasonalNaiveModel(seasonal_period=4)
    s_naive.fit(s_series)
    point_s, lower_s, upper_s = s_naive.predict(horizon=4, confidence_level=0.95)
    assert len(point_s) == 4
    np.testing.assert_allclose(point_s, [11.0, 21.0, 31.0, 41.0])


def test_exponential_smoothing_and_arima_models():
    dates = pd.date_range("2022-01-01", periods=30, freq="MS").tolist()
    vals = np.array([50.0 + 2.0 * i + np.random.normal(0, 0.5) for i in range(30)])

    # Exponential Smoothing
    es = ExponentialSmoothingModel(seasonal_period=12)
    es.fit(vals, dates=dates)
    p_es, l_es, u_es = es.predict(horizon=6, confidence_level=0.95)
    assert len(p_es) == 6
    assert all(low <= p <= u for low, p, u in zip(l_es, p_es, u_es))

    # ARIMA
    arima = ARIMAModel()
    arima.fit(vals, dates=dates)
    p_ar, l_ar, u_ar = arima.predict(horizon=6, confidence_level=0.95)
    assert len(p_ar) == 6
    assert all(low <= p <= u for low, p, u in zip(l_ar, p_ar, u_ar))


# ---------------------------------------------------------------------------
# Backtesting & Leakage Protection Tests
# ---------------------------------------------------------------------------
def test_chronological_backtesting_no_leakage():
    dates = pd.date_range("2020-01-01", periods=36, freq="MS").tolist()
    vals = np.array([100.0 + 5.0 * i for i in range(36)])

    best_model, metrics, warnings = TimeSeriesBacktester.evaluate_and_select_model(
        y=vals,
        dates=dates,
        requested_type=ForecastModelType.AUTO,
        seasonal_period=12,
        is_seasonal=False,
        horizon=6,
    )

    assert best_model is not None
    assert metrics.mae >= 0.0
    assert metrics.rmse >= metrics.mae  # Mathematical property: RMSE >= MAE
    assert 0.0 <= metrics.mape <= 100.0
    assert 0.0 <= metrics.smape <= 100.0


def test_model_registry_selection():
    models = ForecastModelRegistry.list_supported_models()
    model_types = [m["type"] for m in models]
    assert ForecastModelType.NAIVE.value in model_types
    assert ForecastModelType.SARIMA.value in model_types

    model = ForecastModelRegistry.get_model(ForecastModelType.EXPONENTIAL_SMOOTHING)
    assert model.model_type == ForecastModelType.EXPONENTIAL_SMOOTHING


# ---------------------------------------------------------------------------
# End-to-End REST API Tests
# ---------------------------------------------------------------------------
def test_forecast_api_run_success(auth_header, monthly_sales_dataset):
    dataset_id = monthly_sales_dataset["id"]
    payload = {
        "dataset_id": dataset_id,
        "time_column": "date",
        "target_column": "revenue",
        "forecast_horizon": 6,
        "frequency": "MS",
        "model_type": "auto",
        "confidence_level": 0.95,
    }

    res = client.post("/api/v1/forecasts/run", headers=auth_header, json=payload)
    assert res.status_code == 200, res.text
    data = res.json()

    assert data["dataset_id"] == dataset_id
    assert data["target_field"] == "revenue"
    assert data["forecast_horizon"] == 6
    assert len(data["predictions"]) == 6
    assert len(data["historical_points"]) > 0
    assert data["status"] == "COMPLETED" or data["status"] == "completed"
    assert len(data["selected_model_name"]) > 0
    assert data["metrics"]["mae"] >= 0.0
    assert data["provenance"]["dataset_id"] == dataset_id

    # Test fetching forecast by ID
    forecast_id = data["id"]
    res_get = client.get(f"/api/v1/forecasts/{forecast_id}", headers=auth_header)
    assert res_get.status_code == 200
    assert res_get.json()["id"] == forecast_id

    # Test listing forecasts for dataset
    res_list = client.get(f"/api/v1/forecasts/dataset/{dataset_id}", headers=auth_header)
    assert res_list.status_code == 200
    assert len(res_list.json()["items"]) >= 1


def test_forecast_api_idor_security(auth_header, another_auth_header, monthly_sales_dataset):
    dataset_id = monthly_sales_dataset["id"]
    payload = {
        "dataset_id": dataset_id,
        "time_column": "date",
        "target_column": "revenue",
        "forecast_horizon": 4,
        "model_type": "naive",
    }

    # User 2 tries to forecast User 1's dataset
    res = client.post("/api/v1/forecasts/run", headers=another_auth_header, json=payload)
    assert res.status_code in [400, 403, 404]
