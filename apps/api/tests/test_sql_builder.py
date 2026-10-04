import pytest

from app.analytics.engine.contracts import (
    AggregationSpec,
    AggregationType,
    FilterCondition,
    FilterGroup,
    FilterOperator,
    LogicalOperator,
    SortOrder,
    SortSpecification,
)
from app.analytics.engine.sql_builder import SafeSQLBuilder


def test_quote_and_validate_identifier():
    valid_cols = ["region", "revenue", "order_date", "customer_id"]
    assert SafeSQLBuilder.quote_identifier("region") == '"region"'
    assert SafeSQLBuilder.quote_identifier('col"with"quotes') == '"col""with""quotes"'

    assert SafeSQLBuilder.validate_identifier("region", valid_cols) == "region"

    with pytest.raises(ValueError, match="does not exist in dataset schema"):
        SafeSQLBuilder.validate_identifier("malicious_col", valid_cols)

    with pytest.raises(ValueError, match="Invalid characters in identifier"):
        SafeSQLBuilder.validate_identifier("col; DROP TABLE users;--", valid_cols)


def test_build_filter_conditions():
    valid_cols = ["age", "status", "salary"]

    # EQ
    cond = FilterCondition(column="status", operator=FilterOperator.EQ, value="Active")
    sql, params = SafeSQLBuilder.build_filter_clause(cond, valid_cols)
    assert sql == '"status" = ?'
    assert params == ["Active"]

    # BETWEEN
    cond = FilterCondition(column="age", operator=FilterOperator.BETWEEN, value=18, value_to=65)
    sql, params = SafeSQLBuilder.build_filter_clause(cond, valid_cols)
    assert sql == '"age" BETWEEN ? AND ?'
    assert params == [18, 65]

    # IN
    cond = FilterCondition(column="status", operator=FilterOperator.IN, values=["A", "B", "C"])
    sql, params = SafeSQLBuilder.build_filter_clause(cond, valid_cols)
    assert sql == '"status" IN (?, ?, ?)'
    assert params == ["A", "B", "C"]

    # IS NULL
    cond = FilterCondition(column="salary", operator=FilterOperator.IS_NULL)
    sql, params = SafeSQLBuilder.build_filter_clause(cond, valid_cols)
    assert sql == '"salary" IS NULL'
    assert params == []


def test_build_logical_filter_groups():
    valid_cols = ["region", "revenue", "active"]

    group = FilterGroup(
        logical_op=LogicalOperator.OR,
        conditions=[
            FilterCondition(column="region", operator=FilterOperator.EQ, value="North"),
            FilterCondition(column="revenue", operator=FilterOperator.GT, value=1000),
        ],
    )
    sql, params = SafeSQLBuilder.build_filter_clause(group, valid_cols)
    assert sql == '"region" = ? OR "revenue" > ?'
    assert params == ["North", 1000]


def test_build_aggregations_and_sorting():
    valid_cols = ["revenue", "region"]

    # SUM
    agg = AggregationSpec(column="revenue", agg_type=AggregationType.SUM, alias="total_rev")
    sql = SafeSQLBuilder.build_aggregation_expression(agg, valid_cols)
    assert sql == 'SUM("revenue") AS "total_rev"'

    # COUNT DISTINCT
    agg_dist = AggregationSpec(column="region", agg_type=AggregationType.COUNT_DISTINCT)
    sql_dist = SafeSQLBuilder.build_aggregation_expression(agg_dist, valid_cols)
    assert sql_dist == 'COUNT(DISTINCT "region") AS "region_count_distinct"'

    # ORDER BY
    sort_specs = [
        SortSpecification(column="region", order=SortOrder.ASC),
        SortSpecification(column="revenue", order=SortOrder.DESC),
    ]
    order_sql = SafeSQLBuilder.build_order_by(sort_specs, valid_cols)
    assert order_sql == 'ORDER BY "region" ASC, "revenue" DESC'
