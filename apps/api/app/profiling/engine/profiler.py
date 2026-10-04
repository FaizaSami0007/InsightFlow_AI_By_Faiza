import re
import time
from typing import Any, Dict, List, Optional, Tuple

import numpy as np
import polars as pl

from app.database.models.profiling import ConceptualType


def normalize_column_name(name: str) -> str:
    """Deterministically normalize column names to snake_case without losing characters."""
    clean = re.sub(r"[^\w\s]", "", name).strip()
    clean = re.sub(r"[\s\-]+", "_", clean)
    normalized = clean.lower()
    return normalized if normalized else "col"


def map_polars_type_to_conceptual(dtype: pl.DataType) -> ConceptualType:
    """Map native Polars data types to standardized conceptual data types."""
    if dtype in (
        pl.Int8,
        pl.Int16,
        pl.Int32,
        pl.Int64,
        pl.UInt8,
        pl.UInt16,
        pl.UInt32,
        pl.UInt64,
    ):
        return ConceptualType.INTEGER
    if dtype in (pl.Float32, pl.Float64, pl.Decimal):
        return ConceptualType.FLOAT
    if dtype == pl.Boolean:
        return ConceptualType.BOOLEAN
    if dtype == pl.Date:
        return ConceptualType.DATE
    if dtype in (pl.Datetime, pl.Duration):
        return ConceptualType.DATETIME
    if dtype == pl.Time:
        return ConceptualType.TIME
    if dtype in (pl.String, pl.Categorical, pl.Enum):
        return ConceptualType.STRING
    return ConceptualType.UNKNOWN


class ProfilingEngine:
    """Deterministic Polars-powered dataset profiler calculating exact statistical summaries."""

    def __init__(self, max_top_values: int = 10, near_constant_threshold: float = 0.99):
        self.max_top_values = max_top_values
        self.near_constant_threshold = near_constant_threshold

    def profile_dataframe(self, df: pl.DataFrame) -> Dict[str, Any]:
        """Profile an in-memory Polars DataFrame and return structured metadata."""
        start_time = time.perf_counter()
        row_count = df.height
        column_count = df.width
        memory_size_bytes = df.estimated_size()

        # Duplicates analysis
        if row_count > 0:
            duplicate_rows = row_count - df.n_unique()
            duplicate_percentage = round((duplicate_rows / row_count) * 100.0, 2)
        else:
            duplicate_rows = 0
            duplicate_percentage = 0.0

        columns_profile: List[Dict[str, Any]] = []

        for idx, col_name in enumerate(df.columns):
            series = df[col_name]
            col_profile = self._profile_column(series, idx, row_count)
            columns_profile.append(col_profile)

        duration_ms = round((time.perf_counter() - start_time) * 1000.0, 2)

        return {
            "row_count": row_count,
            "column_count": column_count,
            "memory_size_bytes": memory_size_bytes,
            "duplicate_rows": duplicate_rows,
            "duplicate_percentage": duplicate_percentage,
            "duration_ms": duration_ms,
            "columns": columns_profile,
        }

    def _profile_column(self, series: pl.Series, ordinal_position: int, total_rows: int) -> Dict[str, Any]:
        col_name = series.name
        norm_name = normalize_column_name(col_name)
        dtype = series.dtype
        conceptual_type = map_polars_type_to_conceptual(dtype)

        null_count = series.null_count()
        null_percentage = round((null_count / total_rows * 100.0), 2) if total_rows > 0 else 0.0

        non_null_series = series.drop_nulls()
        non_null_count = len(non_null_series)
        unique_count = non_null_series.n_unique() if non_null_count > 0 else 0
        unique_percentage = round((unique_count / total_rows * 100.0), 2) if total_rows > 0 else 0.0

        is_constant = unique_count <= 1
        is_near_constant = False

        numeric_stats: Optional[Dict[str, Any]] = None
        categorical_stats: Optional[Dict[str, Any]] = None
        temporal_stats: Optional[Dict[str, Any]] = None
        boolean_stats: Optional[Dict[str, Any]] = None
        outlier_count = 0
        outlier_percentage = 0.0

        # Dominant value / near-constant check
        if non_null_count > 0:
            top_vc = non_null_series.value_counts(sort=True)
            if top_vc.height > 0:
                top_freq = top_vc[top_vc.columns[1]][0]
                if (top_freq / non_null_count) >= self.near_constant_threshold:
                    is_near_constant = True

        # Numeric Profiling
        if conceptual_type in (ConceptualType.INTEGER, ConceptualType.FLOAT) and non_null_count > 0:
            numeric_stats, outlier_count, outlier_percentage = self._profile_numeric(non_null_series, total_rows)

        # Categorical / String Profiling
        elif conceptual_type == ConceptualType.STRING and non_null_count > 0:
            categorical_stats = self._profile_categorical(non_null_series, non_null_count)

        # Temporal Profiling
        elif conceptual_type in (ConceptualType.DATE, ConceptualType.DATETIME) and non_null_count > 0:
            temporal_stats = self._profile_temporal(non_null_series)

        # Boolean Profiling
        elif conceptual_type == ConceptualType.BOOLEAN:
            boolean_stats = self._profile_boolean(series, total_rows)

        return {
            "column_name": col_name,
            "normalized_name": norm_name,
            "ordinal_position": ordinal_position,
            "data_type": str(dtype),
            "conceptual_type": conceptual_type.value,
            "null_count": null_count,
            "null_percentage": null_percentage,
            "unique_count": unique_count,
            "unique_percentage": unique_percentage,
            "is_constant": is_constant,
            "is_near_constant": is_near_constant,
            "numeric_stats": numeric_stats,
            "categorical_stats": categorical_stats,
            "temporal_stats": temporal_stats,
            "boolean_stats": boolean_stats,
            "outlier_count": outlier_count,
            "outlier_percentage": outlier_percentage,
        }

    def _profile_numeric(self, series: pl.Series, total_rows: int) -> Tuple[Dict[str, Any], int, float]:
        """Compute exact numeric statistics and Tukey IQR outliers."""
        values = series.to_numpy()
        min_val = float(np.min(values))
        max_val = float(np.max(values))
        mean_val = float(np.mean(values))
        median_val = float(np.median(values))
        std_val = float(np.std(values, ddof=1)) if len(values) > 1 else 0.0
        var_val = float(np.var(values, ddof=1)) if len(values) > 1 else 0.0

        # Quantiles & Percentiles
        q1 = float(np.percentile(values, 25))
        q2 = median_val
        q3 = float(np.percentile(values, 75))
        iqr = float(q3 - q1)

        p01 = float(np.percentile(values, 1))
        p05 = float(np.percentile(values, 5))
        p10 = float(np.percentile(values, 10))
        p25 = q1
        p50 = median_val
        p75 = q3
        p90 = float(np.percentile(values, 90))
        p95 = float(np.percentile(values, 95))
        p99 = float(np.percentile(values, 99))

        # Outlier calculation via IQR
        lower_bound = q1 - (1.5 * iqr)
        upper_bound = q3 + (1.5 * iqr)
        outliers = values[(values < lower_bound) | (values > upper_bound)]
        outlier_count = int(len(outliers))
        outlier_percentage = round((outlier_count / total_rows * 100.0), 2) if total_rows > 0 else 0.0

        stats = {
            "count": int(len(values)),
            "min": min_val,
            "max": max_val,
            "mean": round(mean_val, 4),
            "median": round(median_val, 4),
            "std_dev": round(std_val, 4),
            "variance": round(var_val, 4),
            "q1": round(q1, 4),
            "q2": round(q2, 4),
            "q3": round(q3, 4),
            "iqr": round(iqr, 4),
            "lower_bound": round(lower_bound, 4),
            "upper_bound": round(upper_bound, 4),
            "percentiles": {
                "p01": round(p01, 4),
                "p05": round(p05, 4),
                "p10": round(p10, 4),
                "p25": round(p25, 4),
                "p50": round(p50, 4),
                "p75": round(p75, 4),
                "p90": round(p90, 4),
                "p95": round(p95, 4),
                "p99": round(p99, 4),
            },
        }
        return stats, outlier_count, outlier_percentage

    def _profile_categorical(self, series: pl.Series, non_null_count: int) -> Dict[str, Any]:
        """Compute cardinality ratio and top frequent values."""
        vc = series.value_counts(sort=True).head(self.max_top_values)
        val_col = vc.columns[0]
        cnt_col = vc.columns[1]

        top_values = []
        for row in vc.iter_rows(named=True):
            v = str(row[val_col]) if row[val_col] is not None else "null"
            c = int(row[cnt_col])
            pct = round((c / non_null_count) * 100.0, 2)
            top_values.append({"value": v, "count": c, "percentage": pct})

        unique_count = series.n_unique()
        cardinality_ratio = round((unique_count / non_null_count), 4) if non_null_count > 0 else 0.0

        return {
            "top_values": top_values,
            "cardinality_ratio": cardinality_ratio,
        }

    def _profile_temporal(self, series: pl.Series) -> Dict[str, Any]:
        """Compute min and max timestamp boundaries."""
        min_dt = series.min()
        max_dt = series.max()
        return {
            "min_date": str(min_dt) if min_dt is not None else None,
            "max_date": str(max_dt) if max_dt is not None else None,
        }

    def _profile_boolean(self, series: pl.Series, total_rows: int) -> Dict[str, Any]:
        """Compute true/false/null distribution."""
        true_count = int((series == True).sum() or 0)  # noqa: E712
        false_count = int((series == False).sum() or 0)  # noqa: E712
        null_count = series.null_count()

        return {
            "true_count": true_count,
            "false_count": false_count,
            "null_count": null_count,
            "true_percentage": round((true_count / total_rows) * 100.0, 2) if total_rows > 0 else 0.0,
            "false_percentage": round((false_count / total_rows) * 100.0, 2) if total_rows > 0 else 0.0,
        }
