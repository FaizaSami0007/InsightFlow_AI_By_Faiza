import os
import tempfile

import polars as pl
import pytest

from app.analytics.duckdb.dataset import AnalyticalDataset
from app.analytics.duckdb.manager import duckdb_manager
from app.analytics.engine.contracts import (
    FilterCondition,
    FilterOperator,
)
from app.analytics.tools import (
    CorrelationTool,
    DescribeDatasetTool,
    DistributionTool,
    FilterDataTool,
    FrequencyTool,
    GroupByTool,
    OutlierAnalysisTool,
    PercentChangeTool,
    SortDataTool,
    TimeSeriesSummaryTool,
)


@pytest.fixture
def test_dataset():
    # Synthetic dataset with exact known values
    data = {
        "region": ["North", "North", "South", "South", "East"],
        "product": ["Widget", "Gadget", "Widget", "Gadget", "Widget"],
        "sales": [100.0, 200.0, 300.0, 400.0, 500.0],
        "units": [1, 2, 3, 4, 5],
        "order_date": ["2026-01-15", "2026-01-20", "2026-02-10", "2026-02-15", "2026-03-01"],
    }
    df = pl.DataFrame(data)

    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as f:
        temp_path = f.name

    df.write_csv(temp_path)
    version_id = "test_ver_analytics_1"
    view_name = duckdb_manager.register_dataset(version_id, temp_path, "csv")
    schema_dict = duckdb_manager.get_schema(version_id)

    dataset = AnalyticalDataset(
        dataset_id="test_ds_1",
        version_id=version_id,
        view_name=view_name,
        file_path=temp_path,
        file_format="csv",
        schema=schema_dict,
        columns=list(schema_dict.keys()),
    )

    yield dataset

    if os.path.exists(temp_path):
        os.remove(temp_path)


def test_describe_dataset_mathematical_exactness(test_dataset):
    tool = DescribeDatasetTool()
    tool.validate(test_dataset, {"columns": ["units", "sales"]})
    cols, rows, summary = tool.execute(test_dataset, {"columns": ["units"]})

    assert "column" in cols
    units_row = next(r for r in rows if r["column"] == "units")
    # For units: [1, 2, 3, 4, 5] -> mean: 3.0, median: 3.0, min: 1.0, max: 5.0, q1: 2.0, q3: 4.0, iqr: 2.0
    assert units_row["count"] == 5
    assert units_row["mean"] == 3.0
    assert units_row["median"] == 3.0
    assert units_row["min"] == 1.0
    assert units_row["max"] == 5.0
    assert units_row["q1"] == 2.0
    assert units_row["q3"] == 4.0
    assert units_row["iqr"] == 2.0


def test_group_by_tool(test_dataset):
    tool = GroupByTool()
    params = {
        "dimensions": ["region"],
        "aggregations": [
            {"column": "sales", "agg_type": "SUM", "alias": "total_sales"},
            {"column": "sales", "agg_type": "AVG", "alias": "avg_sales"},
            {"column": "*", "agg_type": "COUNT", "alias": "record_count"},
        ],
    }
    tool.validate(test_dataset, params)
    cols, rows, summary = tool.execute(test_dataset, params)

    assert cols == ["region", "total_sales", "avg_sales", "record_count"]
    assert len(rows) == 3

    north_row = next(r for r in rows if r["region"] == "North")
    assert north_row["total_sales"] == 300.0
    assert north_row["avg_sales"] == 150.0
    assert north_row["record_count"] == 2

    south_row = next(r for r in rows if r["region"] == "South")
    assert south_row["total_sales"] == 700.0
    assert south_row["avg_sales"] == 350.0


def test_filter_and_sort_data_tools(test_dataset):
    filter_tool = FilterDataTool()
    cond = FilterCondition(column="sales", operator=FilterOperator.GTE, value=300.0)
    cols, rows, summary = filter_tool.execute(test_dataset, {}, filters=cond)

    assert summary["total_matched_rows"] == 3
    assert len(rows) == 3

    sort_tool = SortDataTool()
    sort_params = {"sort_by": [{"column": "sales", "order": "DESC"}]}
    cols, rows, summary = sort_tool.execute(test_dataset, sort_params)
    assert rows[0]["sales"] == 500.0
    assert rows[-1]["sales"] == 100.0


def test_frequency_tool(test_dataset):
    tool = FrequencyTool()
    cols, rows, summary = tool.execute(test_dataset, {"column": "region"})

    assert summary["total_records"] == 5
    north = next(r for r in rows if r["value"] == "North")
    assert north["count"] == 2
    assert north["percentage"] == 40.0


def test_correlation_tool(test_dataset):
    tool = CorrelationTool()
    params = {"columns": ["sales", "units"], "method": "pearson"}
    tool.validate(test_dataset, params)
    cols, rows, summary = tool.execute(test_dataset, params)

    # Sales [100, 200, 300, 400, 500] and Units [1, 2, 3, 4, 5] have perfect positive correlation r = 1.0
    sales_row = next(r for r in rows if r["column"] == "sales")
    assert sales_row["units"] == 1.0


def test_distribution_tool(test_dataset):
    tool = DistributionTool()
    cols, rows, summary = tool.execute(test_dataset, {"column": "sales", "bins": 5})

    assert summary["min"] == 100.0
    assert summary["max"] == 500.0
    assert summary["mean"] == 300.0
    assert len(rows) == 5


def test_time_series_summary_tool(test_dataset):
    tool = TimeSeriesSummaryTool()
    params = {
        "date_column": "order_date",
        "metric_column": "sales",
        "period": "month",
        "aggregation": "SUM",
    }
    tool.validate(test_dataset, params)
    cols, rows, summary = tool.execute(test_dataset, params)

    assert len(rows) == 3  # Jan, Feb, Mar
    assert summary["total_buckets"] == 3


def test_percent_change_tool(test_dataset):
    tool = PercentChangeTool()
    params = {
        "metric_column": "sales",
        "order_by_column": "order_date",
    }
    tool.validate(test_dataset, params)
    cols, rows, summary = tool.execute(test_dataset, params)

    assert len(rows) == 5
    # First row has no previous value
    assert rows[0]["previous_value"] is None
    assert rows[0]["percent_change"] is None
    # Second row: 200 vs 100 -> +100%
    assert rows[1]["percent_change"] == 100.0
    assert rows[1]["delta"] == 100.0


def test_outlier_analysis_tool(test_dataset):
    tool = OutlierAnalysisTool()
    cols, rows, summary = tool.execute(test_dataset, {"column": "sales", "multiplier": 1.5})
    assert summary["q1"] == 200.0
    assert summary["q3"] == 400.0
    assert summary["iqr"] == 200.0
    assert summary["lower_bound"] == -100.0
    assert summary["upper_bound"] == 700.0
    # No values outside [-100, 700] in our test dataset
    assert summary["outlier_count"] == 0
