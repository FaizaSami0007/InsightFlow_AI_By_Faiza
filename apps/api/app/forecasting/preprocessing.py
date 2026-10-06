"""Time-series preprocessing, frequency normalization, imputation, and diagnostic checks."""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import pandas as pd
from statsmodels.tsa.stattools import adfuller

from app.analytics.duckdb.manager import DuckDBManager


class PreprocessingError(Exception):
    """Raised when time series fails validation or has insufficient data."""

    pass


@dataclass
class PreprocessedSeries:
    """Cleaned, regularized, and diagnosed time series ready for model training."""

    dates: List[pd.Timestamp]
    values: np.ndarray  # 1D float array
    frequency: str  # D, W, M, Q, Y
    seasonal_period: Optional[int]
    is_seasonal: bool
    is_stationary: bool
    missing_imputed_count: int
    outliers_detected_count: int
    raw_observations_count: int
    transformations: List[str]


class TimeSeriesPreprocessor:
    """Extracts raw temporal observations from DuckDB, regularizes index, and computes diagnostics."""

    MIN_OBSERVATIONS = 6

    @classmethod
    def prepare_from_df(
        cls,
        df: pd.DataFrame,
        time_col: str,
        target_col: str,
        requested_freq: Optional[str] = None,
        impute_strategy: str = "interpolate",
        min_observations: Optional[int] = None,
    ) -> PreprocessedSeries:
        """Clean, regularize, and compute diagnostics directly from a pandas DataFrame."""
        min_obs = min_observations or cls.MIN_OBSERVATIONS
        if df.empty or len(df) < min_obs:
            raise ValueError(f"Insufficient temporal observations ({len(df)} found). Minimum required is {min_obs}.")

        df_clean = df[[time_col, target_col]].dropna().copy()
        df_clean[time_col] = pd.to_datetime(df_clean[time_col])
        df_clean = df_clean.sort_values(time_col)
        df_dedup = df_clean.groupby(time_col, as_index=False)[target_col].sum()
        df_dedup.rename(columns={time_col: "ts", target_col: "val"}, inplace=True)

        freq = requested_freq or cls._detect_frequency(df_dedup["ts"])
        df_resampled, imputed_count = cls._regularize_timeline(df_dedup, freq)

        if len(df_resampled) < min_obs:
            raise ValueError(
                f"Insufficient temporal observations ({len(df_resampled)} found). Minimum required is {min_obs}."
            )

        values = df_resampled["val"].to_numpy(dtype=float)
        outliers_count = cls._count_outliers(values)
        is_seasonal, seasonal_period = cls._detect_seasonality(values, freq)
        is_stationary = cls._test_stationarity(values)

        transformations = [f"Frequency aggregation to '{freq}'"]
        if imputed_count > 0:
            transformations.append(f"Linear interpolation of {imputed_count} missing period(s)")

        return PreprocessedSeries(
            dates=df_resampled["ts"].tolist(),
            values=values,
            frequency=freq,
            seasonal_period=seasonal_period,
            is_seasonal=is_seasonal,
            is_stationary=is_stationary,
            missing_imputed_count=imputed_count,
            outliers_detected_count=outliers_count,
            raw_observations_count=len(df),
            transformations=transformations,
        )

    @classmethod
    def load_and_preprocess(
        cls,
        duckdb_manager: DuckDBManager,
        dataset_version_id: str,
        target_field: str,
        time_field: str,
        requested_frequency: Optional[str] = None,
        filters: Optional[List[Dict[str, Any]]] = None,
    ) -> PreprocessedSeries:
        """Query DuckDB for target and time columns, clean, regularize, and compute diagnostics."""
        table_name = duckdb_manager.get_table_name(dataset_version_id)
        if not table_name:
            raise PreprocessingError(f"Dataset version {dataset_version_id} is not registered in analytical engine.")

        # Sanitize column names
        t_col = f'"{target_field.replace('"', '""')}"'
        time_col = f'"{time_field.replace('"', '""')}"'

        where_clauses = [f"{time_col} IS NOT NULL", f"{t_col} IS NOT NULL"]
        if filters:
            for f in filters:
                f_field = f.get("field")
                f_op = f.get("operator", "=")
                f_val = f.get("value")
                if f_field and f_val is not None:
                    clean_f = f'"{f_field.replace('"', '""')}"'
                    if isinstance(f_val, (int, float)):
                        where_clauses.append(f"{clean_f} {f_op} {f_val}")
                    else:
                        where_clauses.append(f"{clean_f} {f_op} '{str(f_val).replace("'", "''")}'")

        sql = f"""
        SELECT
            TRY_CAST({time_col} AS TIMESTAMP) AS ts,
            TRY_CAST({t_col} AS DOUBLE) AS val
        FROM {table_name}
        WHERE {" AND ".join(where_clauses)}
        ORDER BY ts ASC
        """

        res = duckdb_manager.execute_federated_query(sql, max_rows=50000)
        rows = res.get("rows", [])
        if not rows or len(rows) < cls.MIN_OBSERVATIONS:
            raise PreprocessingError(
                f"Insufficient historical observations ({len(rows)} found). Minimum required is {cls.MIN_OBSERVATIONS}."
            )

        # Build raw pandas DataFrame
        df_raw = pd.DataFrame(rows, columns=["ts", "val"]).dropna()
        if len(df_raw) < cls.MIN_OBSERVATIONS:
            raise PreprocessingError("Dataset contains insufficient valid non-null datetime and numeric target values.")

        df_raw["ts"] = pd.to_datetime(df_raw["ts"])
        df_raw = df_raw.sort_values("ts")

        # Deduplicate same timestamps by taking sum
        df_dedup = df_raw.groupby("ts", as_index=False)["val"].sum()

        # 1. Detect Frequency
        freq = requested_frequency or cls._detect_frequency(df_dedup["ts"])

        # 2. Resample and Regularize Timeline
        df_resampled, imputed_count = cls._regularize_timeline(df_dedup, freq)

        if len(df_resampled) < cls.MIN_OBSERVATIONS:
            raise PreprocessingError(
                f"Resampled series has only {len(df_resampled)} regular periods ({freq}). Minimum required is {cls.MIN_OBSERVATIONS}."
            )

        # 3. Detect Outliers
        values = df_resampled["val"].to_numpy(dtype=float)
        outliers_count = cls._count_outliers(values)

        # 4. Seasonality Diagnostics
        is_seasonal, seasonal_period = cls._detect_seasonality(values, freq)

        # 5. Stationarity Diagnostics
        is_stationary = cls._test_stationarity(values)

        transformations: List[str] = []
        if imputed_count > 0:
            transformations.append(f"Linear interpolation of {imputed_count} missing period(s)")
        transformations.append(f"Frequency aggregation to '{freq}'")

        return PreprocessedSeries(
            dates=df_resampled["ts"].tolist(),
            values=values,
            frequency=freq,
            seasonal_period=seasonal_period,
            is_seasonal=is_seasonal,
            is_stationary=is_stationary,
            missing_imputed_count=imputed_count,
            outliers_detected_count=outliers_count,
            raw_observations_count=len(df_raw),
            transformations=transformations,
        )

    @staticmethod
    def _detect_frequency(timestamps: pd.Series) -> str:
        """Infer time-series frequency based on median time delta between steps."""
        if len(timestamps) < 2:
            return "M"

        deltas = timestamps.diff().dropna()
        median_seconds = deltas.dt.total_seconds().median()

        if median_seconds <= 1.5 * 86400:  # <= ~1.5 days
            return "D"
        elif median_seconds <= 10 * 86400:  # <= ~10 days
            return "W"
        elif median_seconds <= 45 * 86400:  # <= ~45 days
            return "M"
        elif median_seconds <= 120 * 86400:  # <= ~120 days
            return "Q"
        else:
            return "Y"

    @classmethod
    def _regularize_timeline(cls, df: pd.DataFrame, freq: str) -> Tuple[pd.DataFrame, int]:
        """Resample to regular frequency grid and interpolate missing intermediate values."""
        df_indexed = df.set_index("ts")

        # Pandas offset alias mapping
        alias_map = {
            "D": "D",
            "W": "W-MON",
            "M": "MS",
            "MS": "MS",
            "Q": "QS",
            "QS": "QS",
            "Y": "YS",
            "YS": "YS",
        }
        pandas_freq = alias_map.get(freq, freq)

        try:
            resampled = df_indexed.resample(pandas_freq).sum(min_count=1)
        except Exception:
            resampled = df_indexed.resample("MS").sum(min_count=1)

        missing_before = int(resampled["val"].isna().sum())
        # Impute missing values via linear interpolation and forward/backward fill boundaries
        resampled["val"] = resampled["val"].interpolate(method="linear").bfill().ffill().fillna(0.0)

        resampled_df = resampled.reset_index()
        return resampled_df, missing_before

    @staticmethod
    def _count_outliers(values: np.ndarray) -> int:
        """Count values outside 1.5 * IQR bounds."""
        if len(values) < 4:
            return 0
        q25, q75 = np.percentile(values, [25, 75])
        iqr = q75 - q25
        if iqr == 0:
            return 0
        lower = q25 - 1.5 * iqr
        upper = q75 + 1.5 * iqr
        return int(np.sum((values < lower) | (values > upper)))

    @staticmethod
    def _detect_seasonality(values: np.ndarray, freq: str) -> Tuple[bool, Optional[int]]:
        """Determine if significant autocorrelation exists at expected seasonal periodicity."""
        n = len(values)
        norm_freq = freq.replace("S", "").replace("-MON", "")
        candidate_lags: Dict[str, List[int]] = {
            "D": [7, 14, 30],
            "W": [52, 26, 13],
            "M": [12, 6, 4, 3],
            "Q": [4, 2],
            "Y": [2],
        }
        lags = candidate_lags.get(norm_freq, [12, 6, 4])

        if n < 6:
            return False, None

        # Calculate sample autocorrelation
        demeaned = values - np.mean(values)
        var = np.sum(demeaned**2)
        if var == 0:
            return False, None

        for lag in lags:
            if n >= 2 * lag and lag < n:
                autocorr = float(np.sum(demeaned[:-lag] * demeaned[lag:]) / var)
                # Significant autocorrelation threshold
                if autocorr > 0.25:
                    return True, lag

        return False, None

    @staticmethod
    def _test_stationarity(values: np.ndarray) -> bool:
        """Perform Augmented Dickey-Fuller test with p-value < 0.05 indicating stationarity."""
        if len(values) < 10:
            # Fallback simple variance ratio test for small series
            half = len(values) // 2
            mean1, mean2 = np.mean(values[:half]), np.mean(values[half:])
            std = np.std(values) or 1.0
            return abs(mean1 - mean2) / std < 1.0

        try:
            result = adfuller(values, autolag="AIC")
            p_value = result[1]
            return bool(p_value < 0.05)
        except Exception:
            return True
