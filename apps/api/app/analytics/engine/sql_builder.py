import re
from typing import Any, List, Optional, Tuple, Union

from app.analytics.engine.contracts import (
    AggregationSpec,
    AggregationType,
    FilterCondition,
    FilterGroup,
    FilterOperator,
    SortOrder,
    SortSpecification,
)


class SafeSQLBuilder:
    """
    Constructs parameterized, read-only SQL queries deterministically.
    Validates identifiers strictly against the dataset schema and prevents SQL injection.
    """

    SAFE_IDENTIFIER_REGEX = re.compile(r"^[a-zA-Z0-9_\s\$\(\)\%\-\.\:\/]+$")

    @classmethod
    def quote_identifier(cls, identifier: str) -> str:
        """Escape double quotes and wrap in double quotes."""
        if not identifier:
            raise ValueError("Identifier cannot be empty")
        escaped = identifier.replace('"', '""')
        return f'"{escaped}"'

    @classmethod
    def validate_identifier(cls, identifier: str, valid_columns: Optional[List[str]] = None) -> str:
        """Validate column name against known dataset columns or pattern."""
        if not cls.SAFE_IDENTIFIER_REGEX.match(identifier):
            raise ValueError(f"Invalid characters in identifier: '{identifier}'")
        if valid_columns is not None and identifier not in valid_columns:
            raise ValueError(f"Column '{identifier}' does not exist in dataset schema: {valid_columns}")
        return identifier

    @classmethod
    def build_filter_clause(
        cls,
        filter_obj: Union[FilterGroup, FilterCondition, dict[str, Any], None],
        valid_columns: Optional[List[str]] = None,
    ) -> Tuple[str, List[Any]]:
        """
        Builds SQL WHERE predicate and returns (sql_string, params_list).
        """
        if filter_obj is None:
            return "", []

        # Convert dict to FilterGroup / FilterCondition if needed
        if isinstance(filter_obj, dict):
            if "conditions" in filter_obj or "groups" in filter_obj:
                filter_obj = FilterGroup(**filter_obj)
            elif "column" in filter_obj:
                filter_obj = FilterCondition(**filter_obj)
            else:
                return "", []

        if isinstance(filter_obj, FilterCondition):
            return cls._build_single_condition(filter_obj, valid_columns)
        elif isinstance(filter_obj, FilterGroup):
            return cls._build_group(filter_obj, valid_columns)

        return "", []

    @classmethod
    def _build_single_condition(
        cls,
        cond: FilterCondition,
        valid_columns: Optional[List[str]] = None,
    ) -> Tuple[str, List[Any]]:
        col_name = cls.validate_identifier(cond.column, valid_columns)
        col_quoted = cls.quote_identifier(col_name)
        op = cond.operator

        if op == FilterOperator.IS_NULL:
            return f"{col_quoted} IS NULL", []
        if op == FilterOperator.IS_NOT_NULL:
            return f"{col_quoted} IS NOT NULL", []

        if op == FilterOperator.BETWEEN:
            if cond.value is None or cond.value_to is None:
                raise ValueError("BETWEEN operator requires both value and value_to")
            return f"{col_quoted} BETWEEN ? AND ?", [cond.value, cond.value_to]

        if op in (FilterOperator.IN, FilterOperator.NOT_IN):
            vals = (
                cond.values
                if cond.values is not None
                else (cond.value if isinstance(cond.value, list) else [cond.value])
            )
            if not vals:
                return "1=0" if op == FilterOperator.IN else "1=1", []
            placeholders = ", ".join(["?"] * len(vals))
            op_sql = "IN" if op == FilterOperator.IN else "NOT IN"
            return f"{col_quoted} {op_sql} ({placeholders})", list(vals)

        if op in (
            FilterOperator.EQ,
            FilterOperator.NEQ,
            FilterOperator.GT,
            FilterOperator.GTE,
            FilterOperator.LT,
            FilterOperator.LTE,
            FilterOperator.LIKE,
            FilterOperator.ILIKE,
        ):
            if cond.value is None:
                if op == FilterOperator.EQ:
                    return f"{col_quoted} IS NULL", []
                if op == FilterOperator.NEQ:
                    return f"{col_quoted} IS NOT NULL", []
            return f"{col_quoted} {op.value} ?", [cond.value]

        raise ValueError(f"Unsupported filter operator: {op}")

    @classmethod
    def _build_group(
        cls,
        group: FilterGroup,
        valid_columns: Optional[List[str]] = None,
    ) -> Tuple[str, List[Any]]:
        parts = []
        all_params = []

        for cond in group.conditions:
            sql, params = cls._build_single_condition(cond, valid_columns)
            if sql:
                parts.append(sql)
                all_params.extend(params)

        for sub_group in group.groups:
            sql, params = cls._build_group(sub_group, valid_columns)
            if sql:
                parts.append(f"({sql})")
                all_params.extend(params)

        if not parts:
            return "", []

        logical_op = group.logical_op.value
        if logical_op == "NOT":
            joined = " AND ".join(parts)
            return f"NOT ({joined})", all_params

        joined = f" {logical_op} ".join(parts)
        return joined, all_params

    @classmethod
    def build_aggregation_expression(
        cls,
        spec: AggregationSpec,
        valid_columns: Optional[List[str]] = None,
    ) -> str:
        """
        Builds SQL aggregation expression like `SUM("revenue") AS "revenue_sum"`.
        """
        col_name = spec.column
        if col_name != "*":
            col_name = cls.validate_identifier(col_name, valid_columns)
            col_quoted = cls.quote_identifier(col_name)
        else:
            col_quoted = "*"

        agg_type = spec.agg_type
        alias = spec.alias or f"{col_name}_{agg_type.value.lower().replace(' ', '_')}"
        alias_quoted = cls.quote_identifier(alias)

        if agg_type == AggregationType.COUNT:
            expr = f"COUNT({col_quoted})"
        elif agg_type == AggregationType.COUNT_DISTINCT:
            if col_quoted == "*":
                raise ValueError("COUNT DISTINCT cannot be applied to *")
            expr = f"COUNT(DISTINCT {col_quoted})"
        elif agg_type == AggregationType.SUM:
            expr = f"SUM({col_quoted})"
        elif agg_type == AggregationType.AVG:
            expr = f"AVG({col_quoted})"
        elif agg_type == AggregationType.MIN:
            expr = f"MIN({col_quoted})"
        elif agg_type == AggregationType.MAX:
            expr = f"MAX({col_quoted})"
        elif agg_type == AggregationType.MEDIAN:
            expr = f"MEDIAN({col_quoted})"
        elif agg_type == AggregationType.STDDEV:
            expr = f"STDDEV({col_quoted})"
        elif agg_type == AggregationType.VARIANCE:
            expr = f"VARIANCE({col_quoted})"
        else:
            raise ValueError(f"Unsupported aggregation type: {agg_type}")

        return f"{expr} AS {alias_quoted}"

    @classmethod
    def build_order_by(
        cls,
        sort_specs: Optional[List[SortSpecification]],
        valid_columns: Optional[List[str]] = None,
    ) -> str:
        """Builds ORDER BY clause from sort specifications."""
        if not sort_specs:
            return ""
        sort_parts = []
        for s in sort_specs:
            col = cls.validate_identifier(s.column, valid_columns)
            direction = "DESC" if s.order == SortOrder.DESC else "ASC"
            sort_parts.append(f"{cls.quote_identifier(col)} {direction}")
        return "ORDER BY " + ", ".join(sort_parts)
