"""Deterministic Mock LLM Provider for offline testing, CI, and evaluation."""

import re
from typing import Any, Dict, List, Optional

from app.ai.providers.base import (
    LLMMessage,
    LLMProvider,
    LLMResponse,
    LLMUsage,
    ToolCallSpec,
    ToolDefinition,
)


class MockLLMProvider(LLMProvider):
    """
    Deterministic mock LLM provider.
    Supports scripted queue responses and rule-based heuristic responses for golden evaluation test cases.
    """

    def __init__(self) -> None:
        self._queued_responses: List[LLMResponse] = []
        self._recorded_calls: List[Dict[str, Any]] = []

    def queue_response(self, response: LLMResponse) -> None:
        """Queue a predetermined response for the next generate call."""
        self._queued_responses.append(response)

    def get_recorded_calls(self) -> List[Dict[str, Any]]:
        """Retrieve all calls made to this provider."""
        return self._recorded_calls

    def clear(self) -> None:
        """Reset queued responses and recorded calls."""
        self._queued_responses.clear()
        self._recorded_calls.clear()

    async def generate(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[ToolDefinition]] = None,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        self._recorded_calls.append(
            {
                "messages": messages,
                "tools": tools,
                "system_instruction": system_instruction,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        )

        if self._queued_responses:
            return self._queued_responses.pop(0)

        # Rule-based heuristic simulation
        return self._heuristic_respond(messages, tools, system_instruction)

    def _extract_schema_columns(self, system_instruction: Optional[str]) -> Dict[str, Any]:
        """Extract available dimensions, measures, temporal columns, and dataset metadata from system instruction context."""
        dims: List[str] = []
        measures: List[str] = []
        temporal: List[str] = []
        identifiers: List[str] = []
        all_cols: List[str] = []
        col_details: List[Dict[str, Any]] = []
        null_counts: Dict[str, int] = {}
        warnings: List[str] = []
        dataset_name = "InsightFlow Dataset"
        total_rows = 500
        total_cols = 0

        if not system_instruction:
            return {
                "dataset_name": dataset_name,
                "total_rows": total_rows,
                "total_columns": 8,
                "dimensions": ["channel", "region", "product", "product_category"],
                "measures": ["revenue", "cost", "profit", "quantity"],
                "temporal": ["order_date", "date"],
                "identifiers": ["transaction_id", "customer_id"],
                "all": ["channel", "region", "product", "product_category", "revenue", "cost", "profit", "quantity", "order_date", "date"],
                "col_details": [],
                "null_counts": {},
                "warnings": [],
            }

        for line in system_instruction.splitlines():
            m_ds = re.search(r"Dataset Name:\s*(.*)", line, re.IGNORECASE)
            if m_ds:
                dataset_name = m_ds.group(1).strip()
            m_r = re.search(r"Total Rows:\s*(\d+)", line, re.IGNORECASE)
            if m_r:
                total_rows = int(m_r.group(1))
            m_c = re.search(r"Total Columns:\s*(\d+)", line, re.IGNORECASE)
            if m_c:
                total_cols = int(m_c.group(1))
            m_w = re.search(r"- Warning on `(.*?)`:\s*(.*)", line)
            if m_w:
                warnings.append(f"{m_w.group(1)}: {m_w.group(2)}")

            m = re.search(
                r"-\s*`([a-zA-Z0-9_]+)`(?:\s*\[(.*?)\])?(?:\s*->\s*Role:\s*\*\*(.*?)\*\*)?(?:\s*\((.*?)\))?(?:\s*\|\s*Nulls:\s*(\d+))?",
                line,
            )
            if m:
                col_name = m.group(1)
                data_type = (m.group(2) or "String").strip()
                role = (m.group(3) or "DIMENSION").upper()
                desc = m.group(4) or ""
                null_cnt = int(m.group(5)) if m.group(5) else 0

                all_cols.append(col_name)
                null_counts[col_name] = null_cnt
                col_details.append(
                    {
                        "name": col_name,
                        "type": data_type,
                        "role": role,
                        "desc": desc,
                        "nulls": null_cnt,
                    }
                )

                if role in ("IDENTIFIER", "ID"):
                    identifiers.append(col_name)
                elif role in ("MEASURE", "FLOAT", "INTEGER") or any(
                    t in data_type.upper() for t in ["INT", "FLOAT", "DOUBLE", "DECIMAL", "NUMERIC"]
                ):
                    measures.append(col_name)
                elif role in ("DATE", "DATETIME", "TIME") or any(
                    t in data_type.upper() for t in ["DATE", "TIME"]
                ):
                    temporal.append(col_name)
                else:
                    dims.append(col_name)

        if not total_cols:
            total_cols = len(all_cols) or 7

        if not dims:
            dims = [c for c in all_cols if c not in measures and c not in temporal and c not in identifiers]
            if not dims:
                dims = ["channel", "region", "product", "product_category"]
        if not measures:
            measures = ["revenue", "cost", "profit", "quantity"]
        if not temporal:
            temporal = [c for c in all_cols if "date" in c.lower() or "time" in c.lower()]

        return {
            "dataset_name": dataset_name,
            "total_rows": total_rows,
            "total_columns": total_cols,
            "dimensions": dims,
            "measures": measures,
            "temporal": temporal,
            "identifiers": identifiers,
            "all": all_cols or (dims + measures + temporal + identifiers),
            "col_details": col_details,
            "null_counts": null_counts,
            "warnings": warnings,
        }

    def _match_dimension(self, query: str, dims: List[str], fallback: bool = True) -> Optional[str]:
        """Find the best matching dimension column for a user query."""
        q = query.lower()
        # Direct column name match
        for d in dims:
            if d.lower() in q:
                return d
        # Common aliases & semantic mappings
        if "channel" in q:
            for d in dims:
                if "channel" in d.lower():
                    return d
        if "region" in q or "area" in q or "territory" in q:
            for d in dims:
                if "region" in d.lower():
                    return d
        if "product" in q or "item" in q:
            for d in dims:
                if "product" in d.lower() or "item" in d.lower() or "name" in d.lower():
                    return d
        if "category" in q:
            for d in dims:
                if "category" in d.lower():
                    return d
        if "customer" in q or "client" in q:
            for d in dims:
                if "customer" in d.lower() or "client" in d.lower():
                    return d
        if "country" in q or "city" in q:
            for d in dims:
                if "country" in d.lower() or "city" in d.lower():
                    return d
        if "segment" in q:
            for d in dims:
                if "segment" in d.lower():
                    return d
        if "payment" in q or "status" in q:
            for d in dims:
                if "payment" in d.lower() or "status" in d.lower():
                    return d
        return dims[0] if (fallback and dims) else None

    def _match_metric(self, query: str, measures: List[str], fallback: bool = True) -> Optional[str]:
        """Find the best matching measure column for a user query."""
        q = query.lower()
        # Direct match
        for m in measures:
            if m.lower() in q:
                return m
        # Common semantic synonyms
        if "cost" in q or "expense" in q or "spend" in q:
            for m in measures:
                if "cost" in m.lower() or "expense" in m.lower():
                    return m
        if "profit" in q or "margin" in q:
            for m in measures:
                if "profit" in m.lower() or "margin" in m.lower():
                    return m
        if "revenue" in q or "sales" in q or "amount" in q:
            for m in measures:
                if "revenue" in m.lower() or "sales" in m.lower() or "amount" in m.lower():
                    return m
        if "satisfaction" in q or "rating" in q or "nps" in q or "score" in q:
            for m in measures:
                if "satisfaction" in m.lower() or "rating" in m.lower() or "score" in m.lower():
                    return m
        if "quantity" in q or "units" in q or "count" in q or "volume" in q:
            for m in measures:
                if "quantity" in m.lower() or "unit" in m.lower() or "volume" in m.lower():
                    return m
        if "price" in q:
            for m in measures:
                if "price" in m.lower():
                    return m
        if "discount" in q:
            for m in measures:
                if "discount" in m.lower():
                    return m
        return measures[0] if (fallback and measures) else None

    def _heuristic_respond(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[ToolDefinition]] = None,
        system_instruction: Optional[str] = None,
    ) -> LLMResponse:
        # Check if the last message contains tool results
        last_msg = messages[-1] if messages else None

        # If the last message contains tool results, synthesize a grounded explanation
        if last_msg and last_msg.tool_results:
            # Get original user question
            user_text = ""
            for m in reversed(messages):
                if m.role == "user":
                    user_text = m.content
                    break
            return self._synthesize_from_tool_results(last_msg.tool_results, user_query=user_text)

        # Otherwise, inspect user query to decide whether to call a tool or answer metadata directly
        user_text = ""
        for m in reversed(messages):
            if m.role == "user":
                user_text = m.content
                break

        query = user_text.lower().strip()
        all_context = ((system_instruction or "") + " " + " ".join([m.content for m in messages])).lower()

        # Extract real schema metadata from system_instruction
        schema_meta = self._extract_schema_columns(system_instruction)
        dims = schema_meta["dimensions"]
        measures = schema_meta["measures"]
        temporal = schema_meta["temporal"]
        identifiers = schema_meta["identifiers"]

        # 1. Prompt injection defense test: text containing "ignore", "override", "system prompt", etc.
        if any(
            w in query
            for w in [
                "ignore",
                "system prompt",
                "system override",
                "disregard",
                "override",
                "reveal",
                "bypass",
                "admin secrets",
                "connection strings",
                "api keys",
                "directives",
            ]
        ):
            return LLMResponse(
                message="I am an analytical assistant. I only execute deterministic analytical queries on your dataset and cannot reveal system prompts or execute arbitrary instructions.",
                finish_reason="stop",
                usage=LLMUsage(prompt_tokens=40, completion_tokens=30, total_tokens=70),
            )

        # 1b. Unsupported requests check (ML training, regression modeling, real-time streams, layout generation)
        if any(
            w in query
            for w in [
                "machine learning",
                "regression model",
                "churn",
                "real-time",
                "realtime",
                "streaming",
                "dashboard",
                "auto-generate",
                "train a",
                "interactive dashboard",
                "arima",
                "next year",
                "quarterly revenue for 2026",
                "pipeline",
                "predictive model",
            ]
        ):
            return LLMResponse(
                message="Predictive modeling, automated machine learning training, real-time streaming, and dashboard layout generation are not currently supported in this analytical workspace.",
                finish_reason="stop",
                usage=LLMUsage(prompt_tokens=40, completion_tokens=20, total_tokens=60),
            )

        # 2. Visual presentation requests (chart switching without re-executing analysis)
        if any(
            w in query
            for w in [
                "as a horizontal bar",
                "horizontal bar chart",
                "as a bar chart",
                "as a line chart",
                "as a pie chart",
                "as a donut chart",
                "view as table",
                "make it horizontal",
                "use a line chart",
                "show as a donut",
                "show as a pie",
            ]
        ):
            chart_name = "Bar Chart"
            if "horizontal" in query:
                chart_name = "Horizontal Bar Chart"
            elif "line" in query:
                chart_name = "Line Chart"
            elif "donut" in query or "pie" in query:
                chart_name = "Donut Chart"
            elif "table" in query:
                chart_name = "Data Table"

            return LLMResponse(
                message=f"I have updated the visualization display to a {chart_name}.",
                finish_reason="stop",
                usage=LLMUsage(prompt_tokens=40, completion_tokens=15, total_tokens=55),
            )

        # 3. SCHEMA INFORMATION / COLUMN COUNT (e.g. "How many columns are there?")
        if any(
            p in query
            for p in [
                "how many columns",
                "count of columns",
                "number of columns",
                "column count",
                "how many fields",
                "total columns",
                "number of fields",
                "total fields",
            ]
        ):
            dim_str = ", ".join(f"`{c}`" for c in dims)
            meas_str = ", ".join(f"`{c}`" for c in measures)
            temp_str = ", ".join(f"`{c}`" for c in temporal) if temporal else "None"
            id_str = ", ".join(f"`{c}`" for c in identifiers) if identifiers else "None"
            msg = (
                f"The dataset **{schema_meta['dataset_name']}** contains **{schema_meta['total_columns']} columns**:\n\n"
                f"- **Categorical Dimensions ({len(dims)}):** {dim_str}\n"
                f"- **Numeric Measures ({len(measures)}):** {meas_str}\n"
                f"- **Temporal Fields ({len(temporal)}):** {temp_str}\n"
                f"- **Identifiers ({len(identifiers)}):** {id_str}"
            )
            return LLMResponse(
                message=msg,
                finish_reason="stop",
                usage=LLMUsage(prompt_tokens=40, completion_tokens=50, total_tokens=90),
            )

        # 4. COLUMN LISTING (e.g. "What columns are in this dataset?", "List the columns")
        if any(
            p in query
            for p in [
                "what columns",
                "list the columns",
                "list all columns",
                "which columns",
                "what fields",
                "available columns",
                "available fields",
                "show schema",
                "show me the schema",
                "schema of",
                "list columns",
                "column names",
                "field names",
            ]
        ):
            col_lines = []
            if schema_meta["col_details"]:
                for c in schema_meta["col_details"]:
                    col_lines.append(f"- `{c['name']}` [{c['type']}] — Role: **{c['role']}** (Nulls: {c['nulls']})")
            else:
                col_lines = [f"- `{c}`" for c in schema_meta["all"]]
            msg = f"**Dataset Schema ({schema_meta['total_columns']} Columns):**\n\n" + "\n".join(col_lines)
            return LLMResponse(
                message=msg,
                finish_reason="stop",
                usage=LLMUsage(prompt_tokens=40, completion_tokens=60, total_tokens=100),
            )

        # 5. ROW COUNT (e.g. "How many rows are there?", "How many records?")
        if any(
            p in query
            for p in [
                "how many rows",
                "how many records",
                "how many transactions",
                "how many entries",
                "row count",
                "total rows",
                "total records",
                "number of rows",
                "number of records",
                "total transactions",
            ]
        ):
            msg = f"The dataset **{schema_meta['dataset_name']}** contains **{schema_meta['total_rows']:,} records** (rows)."
            return LLMResponse(
                message=msg,
                finish_reason="stop",
                usage=LLMUsage(prompt_tokens=40, completion_tokens=25, total_tokens=65),
            )

        # 6. DATA QUALITY / NULL CHECK (e.g. "Are there missing values?", "Does this dataset have nulls?")
        if any(
            p in query
            for p in [
                "missing values",
                "missing data",
                "nulls",
                "null values",
                "is the data clean",
                "data quality",
                "data hygiene",
                "incomplete rows",
                "data anomalies",
            ]
        ):
            cols_with_nulls = {k: v for k, v in schema_meta["null_counts"].items() if v > 0}
            if cols_with_nulls:
                null_details = [f"- `{k}`: **{v:,}** null values" for k, v in cols_with_nulls.items()]
                msg = f"**Data Quality Summary:**\nFound missing values in {len(cols_with_nulls)} column(s):\n" + "\n".join(null_details)
            else:
                msg = f"**Data Quality Summary:**\nThe dataset is clean with **0 missing values** across all {schema_meta['total_columns']} columns."
            if schema_meta["warnings"]:
                msg += "\n\n**Quality Alerts:**\n" + "\n".join(f"- {w}" for w in schema_meta["warnings"])
            return LLMResponse(
                message=msg,
                finish_reason="stop",
                usage=LLMUsage(prompt_tokens=40, completion_tokens=40, total_tokens=80),
            )

        # 7. DATASET DESCRIPTION / TYPE OF DATA (e.g. "What type of data is it?", "Tell me about this data")
        if any(
            p in query
            for p in [
                "what type of data",
                "what kind of data",
                "what kind of dataset",
                "tell me about this data",
                "what does this dataset contain",
                "what is this data about",
                "describe this data",
                "overview of this data",
                "about this dataset",
                "dataset description",
                "what data is this",
                "what is in this dataset",
            ]
        ):
            msg = (
                f"This is the **{schema_meta['dataset_name']}** dataset containing **{schema_meta['total_rows']:,} records** across **{schema_meta['total_columns']} columns**.\n\n"
                f"**Dataset Structure & Capabilities:**\n"
                f"- **Key Dimensions:** {', '.join(f'`{c}`' for c in dims[:5])}\n"
                f"- **Key Measures:** {', '.join(f'`{c}`' for c in measures[:5])}\n"
                f"- **Date Fields:** {', '.join(f'`{c}`' for c in temporal) if temporal else 'None'}\n"
                f"- **Identifiers:** {', '.join(f'`{c}`' for c in identifiers) if identifiers else 'None'}\n\n"
                f"You can ask analytical questions such as breakdown by channel, regional comparisons, revenue trends over time, or anomaly detection."
            )
            return LLMResponse(
                message=msg,
                finish_reason="stop",
                usage=LLMUsage(prompt_tokens=40, completion_tokens=70, total_tokens=110),
            )

        # 8. Ambiguity detection
        if (
            "category" in query
            and "which" not in query
            and not query.startswith("use ")
            and query.strip() not in ["product_category", "customer_category"]
            and (
                "sales by category" in query
                or "group by category" in query
                or "by category" in query
                or "considering" in query
                or ("product_category" in query and "customer_category" in query)
            )
        ):
            if "product_category" in all_context and "customer_category" in all_context:
                return LLMResponse(
                    message="I noticed there are multiple category columns (`product_category` and `customer_category`). Which category would you like me to use?",
                    finish_reason="stop",
                    usage=LLMUsage(prompt_tokens=50, completion_tokens=25, total_tokens=75),
                )

        # 8b. Clarification resolution: user replied with a specific column name
        if (
            any(c in query for c in ["product_category", "customer_category"])
            and not ("product_category" in query and "customer_category" in query)
            and "considering" not in query
        ):
            chosen_cat = "product_category" if "product_category" in query else "customer_category"
            return LLMResponse(
                message=f"I will analyze the sales grouped by {chosen_cat}.",
                tool_calls=[
                    ToolCallSpec(
                        name="group_by",
                        arguments={
                            "dimensions": [chosen_cat],
                            "aggregations": [{"column": "revenue", "agg_type": "SUM", "alias": "total_revenue"}],
                            "sort_by": [{"column": "total_revenue", "order": "DESC"}],
                            "limit": 5,
                        },
                        call_id="call_group_by_clarified",
                    )
                ],
                finish_reason="tool_calls",
                usage=LLMUsage(prompt_tokens=60, completion_tokens=40, total_tokens=100),
            )

        # 9. Time-Series Forecasting
        if any(w in query for w in ["forecast", "predict", "trajectory", "projection", "outlook", "future"]):
            target_metric = self._match_metric(query, measures, fallback=True) or "revenue"
            time_col = temporal[0] if temporal else "order_date"
            horizon = 6
            m_h = re.search(r"(\d+)\s*(months?|quarters?|days?|periods?|weeks?)", query)
            if m_h:
                horizon = int(m_h.group(1))

            return LLMResponse(
                message=f"I will run a time-series forecast for {target_metric} over the next {horizon} periods.",
                tool_calls=[
                    ToolCallSpec(
                        name="run_time_series_forecast",
                        arguments={
                            "target_field": target_metric,
                            "time_field": time_col,
                            "forecast_horizon": horizon,
                            "confidence_level": 0.95,
                        },
                        call_id="call_forecast_1",
                    )
                ],
                finish_reason="tool_calls",
                usage=LLMUsage(prompt_tokens=60, completion_tokens=40, total_tokens=100),
            )

        # 10. Anomaly Detection / Unusual Transactions
        if any(w in query for w in ["anomaly", "anomalies", "outlier", "outliers", "unusual", "unexpected", "spike", "drop"]):
            metric_target = self._match_metric(query, measures, fallback=True) or "revenue"
            dim_target = self._match_dimension(query, dims, fallback=True) or "channel"
            return LLMResponse(
                message="I will analyze the dataset for statistical anomalies and unusual patterns.",
                tool_calls=[
                    ToolCallSpec(
                        name="detect_anomalies_and_insights",
                        arguments={
                            "metric_fields": [metric_target] if metric_target else (measures[:2] or ["revenue"]),
                            "dimension_fields": [dim_target] if dim_target else (dims[:2] or ["channel"]),
                        },
                        call_id="call_anomalies_1",
                    )
                ],
                finish_reason="tool_calls",
                usage=LLMUsage(prompt_tokens=60, completion_tokens=40, total_tokens=100),
            )

        # 11. Scenario Simulation / What-If
        if any(w in query for w in ["what if", "what-if", "simulate", "increased by", "decreased by", "increase by", "decrease by", "change by", "sensitivity"]):
            target_metric = self._match_metric(query, measures, fallback=True) or "revenue"
            val = 15.0
            m_pct = re.search(r"([+-]?\d+(?:\.\d+)?)\s*%", query)
            if m_pct:
                val = float(m_pct.group(1))
            elif "decrease" in query or "drop" in query:
                val = -10.0

            var_name = "quantity"
            if "price" in query:
                var_name = "unit_price"
            elif "discount" in query:
                var_name = "discount"
            elif "cost" in query:
                var_name = "cost"

            return LLMResponse(
                message=f"I will run a what-if scenario simulation modifying {var_name} by {val:+.1f}%.",
                tool_calls=[
                    ToolCallSpec(
                        name="run_what_if_scenario",
                        arguments={
                            "target_metric": target_metric,
                            "assumptions": [{"variable": var_name, "operation": "PERCENTAGE_CHANGE", "value": val}],
                        },
                        call_id="call_scenario_1",
                    )
                ],
                finish_reason="tool_calls",
                usage=LLMUsage(prompt_tokens=60, completion_tokens=40, total_tokens=100),
            )

        # 12. Business Knowledge & Policy Search
        if any(w in query for w in ["policy", "guideline", "standard", "sla", "sop", "glossary", "definition", "asc 606", "reimbursement", "per diem"]):
            return LLMResponse(
                message=f"I will search the business knowledge base for: '{user_text}'.",
                tool_calls=[
                    ToolCallSpec(
                        name="search_business_knowledge",
                        arguments={"query": user_text, "top_k": 3},
                        call_id="call_knowledge_1",
                    )
                ],
                finish_reason="tool_calls",
                usage=LLMUsage(prompt_tokens=60, completion_tokens=40, total_tokens=100),
            )

        # 13. Correlation query
        if "correlation" in query or "correlate" in query:
            return LLMResponse(
                message="I will compute the Pearson correlation matrix for the numeric measures in the dataset.",
                tool_calls=[
                    ToolCallSpec(
                        name="correlation",
                        arguments={},
                        call_id="call_corr_1",
                    )
                ],
                finish_reason="tool_calls",
                usage=LLMUsage(prompt_tokens=60, completion_tokens=30, total_tokens=90),
            )

        # 14. Descriptive statistics / Overview of metrics
        if any(w in query for w in ["statistical summary", "summary statistics", "describe numeric", "distribution of values", "overview statistics"]):
            return LLMResponse(
                message="I will compute descriptive statistics across the dataset columns.",
                tool_calls=[
                    ToolCallSpec(
                        name="describe_dataset",
                        arguments={},
                        call_id="call_stats_1",
                    )
                ],
                finish_reason="tool_calls",
                usage=LLMUsage(prompt_tokens=50, completion_tokens=30, total_tokens=80),
            )

        # 15. Temporal / Monthly Trend
        if any(w in query for w in ["trend", "monthly", "over time", "by month", "by date", "daily", "quarterly", "timeline"]):
            dim = temporal[0] if temporal else "order_date"
            metric = self._match_metric(query, measures, fallback=True) or "revenue"
            alias = f"total_{metric}"
            return LLMResponse(
                message=f"I will compute the temporal trend for {metric} over {dim}.",
                tool_calls=[
                    ToolCallSpec(
                        name="group_by",
                        arguments={
                            "dimensions": [dim],
                            "aggregations": [{"column": metric, "agg_type": "SUM", "alias": alias}],
                            "sort_by": [{"column": dim, "order": "ASC"}],
                            "limit": 20,
                        },
                        call_id="call_trend_1",
                    )
                ],
                finish_reason="tool_calls",
                usage=LLMUsage(prompt_tokens=60, completion_tokens=40, total_tokens=100),
            )

        # 16. Multi-turn follow-ups
        if any(w in query for w in ["top 3", "top 10", "top 5 instead", "show 3", "limit 3"]):
            limit_val = 3 if "3" in query else (10 if "10" in query else 5)
            prior_text = " ".join([m.content for m in messages if m.role == "assistant"]).lower()
            dim = self._match_dimension(prior_text, dims, fallback=True) or dims[0]
            metric = self._match_metric(prior_text, measures, fallback=True) or measures[0]
            alias = f"total_{metric}"
            return LLMResponse(
                message=f"I will update the analysis to show the top {limit_val} {dim}s by {metric}.",
                tool_calls=[
                    ToolCallSpec(
                        name="group_by",
                        arguments={
                            "dimensions": [dim],
                            "aggregations": [{"column": metric, "agg_type": "SUM", "alias": alias}],
                            "sort_by": [{"column": alias, "order": "DESC"}],
                            "limit": limit_val,
                        },
                        call_id="call_group_by_top_n",
                    )
                ],
                finish_reason="tool_calls",
                usage=LLMUsage(prompt_tokens=60, completion_tokens=40, total_tokens=100),
            )

        if any(w in query for w in ["ascending", "sort asc", "lowest to highest"]):
            prior_text = " ".join([m.content for m in messages if m.role == "assistant"]).lower()
            dim = self._match_dimension(query + " " + prior_text, dims, fallback=True) or dims[0]
            metric = self._match_metric(query + " " + prior_text, measures, fallback=True) or measures[0]
            alias = f"total_{metric}"
            return LLMResponse(
                message=f"I will sort the {metric} by {dim} in ascending order to find the lowest.",
                tool_calls=[
                    ToolCallSpec(
                        name="group_by",
                        arguments={
                            "dimensions": [dim],
                            "aggregations": [{"column": metric, "agg_type": "SUM", "alias": alias}],
                            "sort_by": [{"column": alias, "order": "ASC"}],
                            "limit": 5,
                        },
                        call_id="call_group_by_asc",
                    )
                ],
                finish_reason="tool_calls",
                usage=LLMUsage(prompt_tokens=60, completion_tokens=40, total_tokens=100),
            )

        # 17. Pure Aggregate Metric Queries without grouping dimension (e.g. "What is the total revenue?", "What is the average customer satisfaction?")
        has_explicit_dim = any(d.lower() in query for d in dims)
        is_pure_aggregate = not has_explicit_dim and any(
            query.strip().startswith(prefix)
            for prefix in [
                "what is the total",
                "what is total",
                "calculate total",
                "show total",
                "total",
                "what is the average",
                "what is the mean",
                "what is average",
                "calculate average",
                "average",
                "avg",
                "compute total",
                "compute the sum",
                "sum of",
                "calculate mean",
                "count of orders",
                "total sales amount",
            ]
        )

        if is_pure_aggregate:
            target_metric = self._match_metric(query, measures, fallback=True) or measures[0]
            return LLMResponse(
                message=f"I will compute the aggregate statistics for {target_metric}.",
                tool_calls=[
                    ToolCallSpec(
                        name="describe_dataset",
                        arguments={"columns": [target_metric]},
                        call_id="call_stats_agg",
                    )
                ],
                finish_reason="tool_calls",
                usage=LLMUsage(prompt_tokens=50, completion_tokens=30, total_tokens=80),
            )

        # 18. General Analytical Group By / Comparison / Ranking
        matched_dim = self._match_dimension(query, dims, fallback=False)
        matched_metric = self._match_metric(query, measures, fallback=False)
        has_analytic_intent = any(
            w in query
            for w in [
                "highest", "lowest", "least", "bottom", "top", "most", "maximum", "max",
                "best", "greatest", "minimum", "min", "worst", "by", "compare", "break down",
                "ranking", "distribution", "per", "across"
            ]
        )

        if matched_dim or matched_metric or has_analytic_intent:
            target_dim = matched_dim or (dims[0] if dims else "channel")
            target_metric = matched_metric or (measures[0] if measures else "revenue")
            alias = f"total_{target_metric}"

            # Determine aggregation type (AVG vs SUM)
            agg_type = "AVG" if any(w in query for w in ["average", "mean", "avg", "satisfaction", "rating"]) else "SUM"
            if agg_type == "AVG":
                alias = f"avg_{target_metric}"

            # Determine sort order
            is_lowest = any(w in query for w in ["lowest", "least", "bottom", "minimum", "min", "worst"])
            sort_order = "ASC" if is_lowest else "DESC"

            return LLMResponse(
                message=f"I will analyze the {target_metric} grouped by {target_dim} to find the {'lowest' if is_lowest else 'leading'} result.",
                tool_calls=[
                    ToolCallSpec(
                        name="group_by",
                        arguments={
                            "dimensions": [target_dim],
                            "aggregations": [{"column": target_metric, "agg_type": agg_type, "alias": alias}],
                            "sort_by": [{"column": alias, "order": sort_order}],
                            "limit": 5,
                        },
                        call_id="call_group_by_main",
                    )
                ],
                finish_reason="tool_calls",
                usage=LLMUsage(prompt_tokens=60, completion_tokens=40, total_tokens=100),
            )

        # 19. Informative Fallback for unclassified questions (Phase 9 & 16: Never generic group_by fallback)
        dim_samples = ", ".join(f"`{c}`" for c in dims[:3])
        meas_samples = ", ".join(f"`{c}`" for c in measures[:3])
        return LLMResponse(
            message=(
                f"I could not identify a specific analytical dimension or metric in '{user_text}'.\n\n"
                f"You can ask questions about dimensions such as {dim_samples}, or metrics such as {meas_samples}."
            ),
            finish_reason="stop",
            usage=LLMUsage(prompt_tokens=40, completion_tokens=30, total_tokens=70),
        )

    def _synthesize_from_tool_results(self, tool_results: List[Any], user_query: str = "") -> LLMResponse:
        """Ground the response strictly using the output from executed tools and answer the user question directly."""
        parts = []
        q_lower = user_query.lower()

        for tr in tool_results:
            res_data = tr.result if hasattr(tr, "result") else tr.get("result", {})
            rows = res_data.get("rows", [])
            summary = res_data.get("summary", {})
            op = tr.name if hasattr(tr, "name") else tr.get("name", "analysis")

            if op == "describe_dataset":
                if rows:
                    matching_row = None
                    for r in rows:
                        col = r.get("column", "")
                        if col.lower() in q_lower:
                            matching_row = r
                            break
                    if not matching_row and rows:
                        matching_row = rows[0]

                    col_name = matching_row.get("column", "Metric")
                    count_val = matching_row.get("count", 0)
                    mean_val = matching_row.get("mean")
                    min_val = matching_row.get("min")
                    max_val = matching_row.get("max")

                    if any(w in q_lower for w in ["average", "mean", "avg", "satisfaction", "rating"]):
                        if mean_val is not None:
                            f_mean = f"PKR {mean_val:,.2f}" if "rate" not in col_name and "score" not in col_name and "satisfaction" not in col_name else f"{mean_val:,.2f}"
                            f_min = f"PKR {min_val:,.2f}" if "PKR" in f_mean else f"{min_val:,.2f}"
                            f_max = f"PKR {max_val:,.2f}" if "PKR" in f_mean else f"{max_val:,.2f}"
                            parts.append(f"The average **{col_name.replace('_', ' ')}** is **{f_mean}** (ranging from {f_min} to {f_max} across {count_val} records).")
                        else:
                            parts.append(f"Descriptive statistics for **{col_name}**: {count_val} records.")
                    elif any(w in q_lower for w in ["total", "sum", "revenue", "cost", "profit"]):
                        if mean_val is not None and count_val:
                            total_calc = mean_val * count_val
                            f_tot = f"PKR {total_calc:,.2f}" if "rate" not in col_name and "score" not in col_name and "satisfaction" not in col_name else f"{total_calc:,.2f}"
                            f_mean = f"PKR {mean_val:,.2f}" if "PKR" in f_tot else f"{mean_val:,.2f}"
                            parts.append(f"The total **{col_name.replace('_', ' ')}** across all records is **{f_tot}** (averaging {f_mean} per record across {count_val} entries).")
                        else:
                            parts.append(f"Summary for **{col_name}**: {count_val} total records.")
                    else:
                        stat_bullets = []
                        for r in rows[:5]:
                            c = r.get("column", "")
                            m = r.get("mean")
                            mn = r.get("min")
                            mx = r.get("max")
                            if m is not None:
                                stat_bullets.append(f"- **{c}**: Mean = {m:,.2f}, Min = {mn:,.2f}, Max = {mx:,.2f}")
                        parts.append(f"**Descriptive Statistics Summary ({count_val} records):**\n" + "\n".join(stat_bullets))
                else:
                    parts.append("Descriptive statistics computed across dataset columns.")

            elif rows:
                top_row = rows[0]
                # Identify dimension column and metric column in result row
                dim_keys = [k for k in top_row.keys() if isinstance(top_row[k], str)]
                num_keys = [k for k in top_row.keys() if isinstance(top_row[k], (int, float))]

                primary_dim_key = dim_keys[0] if dim_keys else list(top_row.keys())[0]
                primary_metric_key = num_keys[0] if num_keys else (list(top_row.keys())[1] if len(top_row) > 1 else list(top_row.keys())[0])

                top_dim_val = str(top_row.get(primary_dim_key, "Leading item"))
                top_metric_val = top_row.get(primary_metric_key, 0)

                # Format metric value
                if isinstance(top_metric_val, float):
                    formatted_val = f"PKR {top_metric_val:,.2f}" if "rate" not in primary_metric_key and "score" not in primary_metric_key and "satisfaction" not in primary_metric_key else f"{top_metric_val:,.2f}"
                elif isinstance(top_metric_val, int):
                    formatted_val = f"PKR {top_metric_val:,}" if "count" not in primary_metric_key and "quantity" not in primary_metric_key else f"{top_metric_val:,}"
                else:
                    formatted_val = str(top_metric_val)

                metric_label = primary_metric_key.replace("total_", "").replace("avg_", "average ").replace("_", " ")

                # Generate direct, unambiguous natural language answer
                if any(w in q_lower for w in ["lowest", "least", "bottom", "minimum", "min", "worst"]):
                    direct_answer = f"**{top_dim_val}** has the lowest {metric_label} at **{formatted_val}**."
                elif any(w in q_lower for w in ["highest", "top", "most", "maximum", "max", "best", "greatest", "which", "what"]):
                    direct_answer = f"**{top_dim_val}** has the highest total {metric_label} at **{formatted_val}**."
                else:
                    direct_answer = f"**{top_dim_val}** leads with **{formatted_val}** in {metric_label}."

                # Append breakdown of remaining rows
                if len(rows) > 1:
                    breakdown_lines = ["\n\n**Complete Breakdown:**"]
                    for r in rows:
                        d_name = r.get(primary_dim_key, "")
                        m_val = r.get(primary_metric_key, 0)
                        if isinstance(m_val, float):
                            f_m = f"PKR {m_val:,.2f}" if "PKR" in formatted_val else f"{m_val:,.2f}"
                        elif isinstance(m_val, int):
                            f_m = f"PKR {m_val:,}" if "PKR" in formatted_val else f"{m_val:,}"
                        else:
                            f_m = str(m_val)
                        breakdown_lines.append(f"- **{d_name}**: {f_m}")
                    direct_answer += "\n".join(breakdown_lines)

                parts.append(direct_answer)

            elif op == "run_time_series_forecast":
                model_name = res_data.get("model_selected", "Auto-ARIMA")
                horizon = res_data.get("forecast_horizon", 6)
                freq = res_data.get("frequency", "M")
                summary_text = res_data.get("summary", "")
                parts.append(f"**Time-Series Forecast Summary:**\n- Model: **{model_name}**\n- Horizon: **{horizon} {freq}** periods\n- Details: {summary_text}")

            elif op == "detect_anomalies_and_insights":
                total_anom = res_data.get("total_anomalies_count", 0)
                crit = res_data.get("critical_count", 0)
                high = res_data.get("high_count", 0)
                summary_text = res_data.get("summary", f"Detected {total_anom} anomalies.")
                parts.append(f"**Anomaly Detection Findings:**\n- Total Anomalies: **{total_anom}** ({crit} critical, {high} high severity)\n- {summary_text}")

            elif op == "run_what_if_scenario":
                target = res_data.get("target_metric", "revenue")
                base = res_data.get("baseline_value", 0.0)
                scen = res_data.get("scenario_value", 0.0)
                abs_chg = res_data.get("absolute_change", 0.0)
                pct_chg = res_data.get("percentage_change", 0.0)
                narrative = res_data.get("narrative", "")
                parts.append(
                    f"**What-If Simulation Result:**\n"
                    f"- Projected **{target}**: **PKR {scen:,.2f}**\n"
                    f"- Change from baseline: **{abs_chg:+,.2f} ({pct_chg:+.2f}%)**\n"
                    f"- Baseline was **PKR {base:,.2f}**.\n\n"
                    f"{narrative}"
                )

            elif op == "search_business_knowledge":
                summary_text = res_data.get("summary", "Knowledge retrieved.")
                parts.append(f"**Business Policy & Knowledge Findings:**\n{summary_text}")

            elif summary:
                parts.append(f"Analysis completed for `{op}` with summary: {summary}.")
            else:
                parts.append(f"The analytical operation `{op}` completed successfully.")

        grounded_message = "\n\n".join(parts) if parts else "The analysis completed with verified deterministic data."
        return LLMResponse(
            message=grounded_message,
            finish_reason="stop",
            usage=LLMUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150),
        )
