import os
import tempfile

import polars as pl

from app.database.models.profiling import ConceptualType
from app.profiling.engine.profiler import (
    ProfilingEngine,
    map_polars_type_to_conceptual,
    normalize_column_name,
)
from app.profiling.readers.csv_reader import CSVDataReader
from app.profiling.readers.factory import get_data_reader
from app.profiling.readers.parquet_reader import ParquetDataReader


def test_column_name_normalization():
    assert normalize_column_name("Customer Revenue ($)") == "customer_revenue"
    assert normalize_column_name("Total_Amount") == "total_amount"
    assert normalize_column_name("User-ID #1") == "userid_1"
    assert normalize_column_name("   Spaces   Around   ") == "spaces_around"


def test_polars_type_mapping():
    assert map_polars_type_to_conceptual(pl.Int64) == ConceptualType.INTEGER
    assert map_polars_type_to_conceptual(pl.Float64) == ConceptualType.FLOAT
    assert map_polars_type_to_conceptual(pl.String) == ConceptualType.STRING
    assert map_polars_type_to_conceptual(pl.Boolean) == ConceptualType.BOOLEAN
    assert map_polars_type_to_conceptual(pl.Date) == ConceptualType.DATE
    assert map_polars_type_to_conceptual(pl.Datetime) == ConceptualType.DATETIME


def test_numerical_exact_correctness():
    """Verify numerical correctness against known analytical arrays."""
    # Array: [1, 2, 3, 4, 5]
    df = pl.DataFrame({"numbers": [1, 2, 3, 4, 5]})
    engine = ProfilingEngine()
    profile = engine.profile_dataframe(df)

    assert profile["row_count"] == 5
    assert profile["column_count"] == 1
    assert profile["duplicate_rows"] == 0

    col = profile["columns"][0]
    assert col["column_name"] == "numbers"
    assert col["conceptual_type"] == ConceptualType.INTEGER.value
    assert col["null_count"] == 0
    assert col["unique_count"] == 5

    num = col["numeric_stats"]
    assert num is not None
    assert num["count"] == 5
    assert num["min"] == 1.0
    assert num["max"] == 5.0
    assert num["mean"] == 3.0
    assert num["median"] == 3.0
    assert num["q1"] == 2.0
    assert num["q3"] == 4.0
    assert num["iqr"] == 2.0
    assert num["lower_bound"] == -1.0  # 2 - 1.5*2
    assert num["upper_bound"] == 7.0  # 4 + 1.5*2
    assert col["outlier_count"] == 0


def test_outlier_detection_iqr():
    """Verify Tukey IQR outlier detection on array with an extreme point."""
    # Array: [10, 12, 11, 13, 12, 11, 10, 100] -> 100 is an outlier
    df = pl.DataFrame({"values": [10.0, 12.0, 11.0, 13.0, 12.0, 11.0, 10.0, 100.0]})
    engine = ProfilingEngine()
    profile = engine.profile_dataframe(df)

    col = profile["columns"][0]
    assert col["outlier_count"] == 1
    assert col["outlier_percentage"] == 12.5


def test_categorical_and_boolean_profiling():
    df = pl.DataFrame({
        "category": ["A", "B", "A", "C", "A", None],
        "is_active": [True, False, True, True, False, True],
    })
    engine = ProfilingEngine()
    profile = engine.profile_dataframe(df)

    cat_col = profile["columns"][0]
    assert cat_col["null_count"] == 1
    assert cat_col["unique_count"] == 3
    assert cat_col["categorical_stats"] is not None
    top_vals = cat_col["categorical_stats"]["top_values"]
    assert top_vals[0]["value"] == "A"
    assert top_vals[0]["count"] == 3

    bool_col = profile["columns"][1]
    assert bool_col["boolean_stats"] is not None
    assert bool_col["boolean_stats"]["true_count"] == 4
    assert bool_col["boolean_stats"]["false_count"] == 2


def test_csv_reader_with_delimiters():
    with tempfile.NamedTemporaryFile(mode="w+", suffix=".csv", delete=False) as f:
        f.write("id;name;revenue\n1;Alpha;150.5\n2;Beta;200.0\n")
        f.flush()
        file_path = f.name

    try:
        reader = CSVDataReader()
        df = reader.read_dataframe(file_path)
        assert df.shape == (2, 3)
        assert df.columns == ["id", "name", "revenue"]
        assert reader.get_row_count(file_path) == 2
    finally:
        os.remove(file_path)


def test_parquet_reader_and_factory():
    with tempfile.NamedTemporaryFile(mode="wb+", suffix=".parquet", delete=False) as f:
        file_path = f.name

    try:
        df_orig = pl.DataFrame({"x": [1, 2, 3], "y": ["a", "b", "c"]})
        df_orig.write_parquet(file_path)

        reader = get_data_reader("PARQUET")
        assert isinstance(reader, ParquetDataReader)
        df_read = reader.read_dataframe(file_path)
        assert df_read.shape == (3, 2)
        assert reader.get_row_count(file_path) == 3
    finally:
        os.remove(file_path)
