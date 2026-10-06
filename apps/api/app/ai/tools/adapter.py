"""Adapter bridging Phase 4 AnalysisRegistry tools to AI ToolDefinitions."""

from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.providers.base import ToolCallSpec, ToolDefinition
from app.analytics.engine.registry import analysis_registry
from app.analytics.schemas import AnalysisRunRequest
from app.analytics.service import analytics_service
from app.database.models.user import User


class AIToolAdapter:
    """Adapts deterministic Phase 4 analysis tools for LLM tool calling."""

    @classmethod
    def get_tool_definitions(cls) -> List[ToolDefinition]:
        """Convert all registered AnalysisTools into AI ToolDefinitions."""
        tool_defs: List[ToolDefinition] = []
        for meta in analysis_registry.list_tools():
            # Build parameter schema for tool calling
            schema = meta.input_schema or {}
            props = schema.get("properties", {})
            required = schema.get("required", meta.required_params or [])

            param_spec: Dict[str, Any] = {
                "type": "object",
                "properties": props
                if props
                else {
                    param: {"type": "string", "description": f"Parameter {param}"}
                    for param in meta.required_params + meta.optional_params
                },
                "required": required,
            }

            tool_defs.append(
                ToolDefinition(
                    name=meta.name,
                    description=meta.description,
                    parameters=param_spec,
                )
            )

        # Add federated analysis tool definition
        tool_defs.append(
            ToolDefinition(
                name="execute_federated_query",
                description="Executes a multi-dataset federated analytical query across related datasets in a collection using validated join paths.",
                parameters={
                    "type": "object",
                    "properties": {
                        "dataset_version_ids": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of dataset version IDs to join and analyze.",
                        },
                        "dimensions": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "List of qualified dimension columns to group by (e.g. ['Customers.segment']).",
                        },
                        "measures": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "field": {"type": "string", "description": "Column name e.g. 'Orders.revenue'"},
                                    "agg": {"type": "string", "enum": ["SUM", "AVG", "COUNT", "MIN", "MAX", "COUNT_DISTINCT"]},
                                    "alias": {"type": "string", "description": "Optional output column alias"},
                                },
                                "required": ["field", "agg"],
                            },
                            "description": "List of aggregations to compute across joined datasets.",
                        },
                        "limit": {"type": "integer", "description": "Max rows to return (default 100)"},
                        "sort_by": {"type": "string", "description": "Optional column to sort by"},
                    },
                    "required": ["dataset_version_ids", "measures"],
                },
            )
        )

        tool_defs.append(
            ToolDefinition(
                name="run_time_series_forecast",
                description="Performs validated time-series forecasting to predict future values of a numeric target variable over a specified horizon.",
                parameters={
                    "type": "object",
                    "properties": {
                        "target_field": {"type": "string", "description": "Numeric column name to forecast (e.g. 'revenue', 'orders')"},
                        "time_field": {"type": "string", "description": "Date or timestamp column name (e.g. 'order_date')"},
                        "forecast_horizon": {"type": "integer", "description": "Number of future periods to predict (e.g. 6)"},
                        "frequency": {"type": "string", "enum": ["D", "W", "M", "Q", "Y"], "description": "Optional frequency"},
                        "confidence_level": {"type": "number", "description": "Confidence level for prediction interval (default 0.95)"},
                    },
                    "required": ["target_field", "time_field"],
                },
            )
        )

        tool_defs.append(
            ToolDefinition(
                name="detect_anomalies_and_insights",
                description="Performs statistical anomaly detection across numeric metrics and dimensions to identify point anomalies, trends, seasonal outliers, group deviations, and root-cause contributions.",
                parameters={
                    "type": "object",
                    "properties": {
                        "metric_fields": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Numeric column names to analyze for anomalies (e.g. ['revenue', 'orders'])",
                        },
                        "time_field": {"type": "string", "description": "Optional date/timestamp column for temporal series analysis"},
                        "dimension_fields": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": "Optional categorical attributes for group-level and root-cause decomposition (e.g. ['region', 'category'])",
                        },
                        "method": {
                            "type": "string",
                            "enum": ["Z_SCORE", "ROBUST_Z_SCORE", "IQR", "ROLLING_BASELINE", "SEASONAL_BASELINE", "FORECAST_DEVIATION"],
                            "description": "Statistical detection methodology (default: ROBUST_Z_SCORE)",
                        },
                        "sensitivity": {"type": "number", "description": "Threshold multiplier (default: 3.0)"},
                    },
                    "required": ["metric_fields"],
                },
            )
        )

        tool_defs.append(
            ToolDefinition(
                name="run_what_if_scenario",
                description="Simulates a decision intelligence what-if scenario by applying structured assumptions (e.g. price +5%, orders -10%) to analytical baselines without modifying historical data.",
                parameters={
                    "type": "object",
                    "properties": {
                        "target_metric": {"type": "string", "description": "Primary output metric to evaluate (e.g. 'revenue', 'profit')"},
                        "assumptions": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "variable": {"type": "string", "description": "Variable to modify (e.g. 'price', 'quantity')"},
                                    "operation": {
                                        "type": "string",
                                        "enum": ["PERCENTAGE_CHANGE", "ABSOLUTE_CHANGE", "DIRECT_SET", "MULTIPLIER"],
                                        "description": "Operation type (default: PERCENTAGE_CHANGE)",
                                    },
                                    "value": {"type": "number", "description": "Numeric modification value (e.g. 10 for +10%)"},
                                    "unit": {"type": "string", "description": "Unit (e.g. '%', '$')"},
                                },
                                "required": ["variable", "value"],
                            },
                            "description": "List of assumptions applied to baseline drivers",
                        },
                        "name": {"type": "string", "description": "Optional name for scenario run"},
                    },
                    "required": ["target_metric", "assumptions"],
                },
            )
        )

        tool_defs.append(
            ToolDefinition(
                name="search_business_knowledge",
                description="Retrieves grounded business domain knowledge, policy definitions, KPI formulas, and document context with verifiable citations.",
                parameters={
                    "type": "object",
                    "properties": {
                        "query": {"type": "string", "description": "Natural language question or concept to search for in the knowledge base"},
                        "collection_id": {"type": "string", "description": "Optional specific knowledge collection ID"},
                        "top_k": {"type": "integer", "description": "Number of relevant chunks to retrieve (default: 5)"},
                    },
                    "required": ["query"],
                },
            )
        )

        return tool_defs

    @classmethod
    def validate_tool_call(cls, tool_call: ToolCallSpec) -> None:
        """Ensure tool exists in allowlist and arguments are well-formed."""
        allowed_extras = [
            "execute_federated_query",
            "run_time_series_forecast",
            "detect_anomalies_and_insights",
            "run_what_if_scenario",
            "search_business_knowledge",
        ]
        if tool_call.name in allowed_extras:
            return
        tool = analysis_registry.get(tool_call.name)
        if not tool:
            allowed = [m.name for m in analysis_registry.list_tools()] + allowed_extras
            raise ValueError(f"Tool '{tool_call.name}' is not an authorized analytical tool. Allowed: {allowed}")

    @classmethod
    async def execute_tool_call(
        cls,
        tool_call: ToolCallSpec,
        user: User,
        dataset_id: str,
        dataset_version_id: str,
        db: AsyncSession,
    ) -> Dict[str, Any]:
        """
        Execute tool call deterministically via AnalyticsService or FederationService.
        Returns execution result dict including analysis_id, columns, rows, summary, and provenance.
        """
        cls.validate_tool_call(tool_call)

        if tool_call.name == "run_time_series_forecast":
            from app.forecasting.schemas import ForecastRunRequest
            from app.forecasting.service import ForecastService

            args = dict(tool_call.arguments)
            fc_req = ForecastRunRequest(
                dataset_id=dataset_id,
                dataset_version_id=dataset_version_id,
                target_field=args.get("target_field", ""),
                time_field=args.get("time_field", ""),
                frequency=args.get("frequency"),
                forecast_horizon=int(args.get("forecast_horizon", 6)),
                confidence_level=float(args.get("confidence_level", 0.95)),
            )
            fc_service = ForecastService(db)
            fc_res = await fc_service.run_forecast(user.id, fc_req)

            return {
                "forecast_id": fc_res.id,
                "operation": "run_time_series_forecast",
                "status": "COMPLETED",
                "model_selected": fc_res.selected_model_name,
                "frequency": fc_res.frequency,
                "forecast_horizon": fc_res.forecast_horizon,
                "metrics": fc_res.metrics.model_dump(),
                "predictions": [p.model_dump() for p in fc_res.predictions],
                "historical_points_count": len(fc_res.historical_points),
                "summary": f"Fitted {fc_res.selected_model_name} on {len(fc_res.historical_points)} periods with validation MAE of {fc_res.metrics.mae:.2f}. Forecasted next {fc_res.forecast_horizon} periods ({fc_res.frequency}).",
                "provenance": fc_res.provenance,
                "warnings": fc_res.warnings,
            }

        if tool_call.name == "execute_federated_query":
            from app.federation.schemas import FederatedAggregationSpec, FederatedAnalysisRequest
            from app.federation.service import FederationService

            args = dict(tool_call.arguments)
            dv_ids = args.get("dataset_version_ids") or ([dataset_version_id] if dataset_version_id else [])
            dimensions = args.get("dimensions", [])
            raw_measures = args.get("measures", [])
            measures = [
                FederatedAggregationSpec(
                    field=m.get("field", ""),
                    agg=m.get("agg", "SUM"),
                    alias=m.get("alias"),
                )
                for m in raw_measures
            ]
            limit = args.get("limit", 100)
            sort_by = args.get("sort_by")

            fed_req = FederatedAnalysisRequest(
                dataset_version_ids=dv_ids,
                dimensions=dimensions,
                measures=measures,
                limit=limit,
                sort_by=sort_by,
            )

            fed_service = FederationService(db)
            fed_res = await fed_service.execute_federated_analysis(user.id, fed_req)

            return {
                "analysis_id": fed_res.analysis_id,
                "operation": "execute_federated_query",
                "status": "COMPLETED",
                "columns": fed_res.columns,
                "rows": fed_res.rows,
                "row_count": fed_res.row_count,
                "summary": {
                    "join_path": fed_res.join_path_description,
                    "datasets_count": len(fed_res.datasets_involved),
                },
                "execution_time_ms": fed_res.execution_time_ms,
                "provenance": fed_res.provenance,
                "warnings": fed_res.warnings,
            }

        if tool_call.name == "detect_anomalies_and_insights":
            from app.anomalies.schemas import AnomalyDetectionRequest
            from app.anomalies.service import AnomalyService
            from app.database.models.anomalies import DetectionMethod

            args = dict(tool_call.arguments)
            raw_metrics = args.get("metric_fields") or []
            if isinstance(raw_metrics, str):
                raw_metrics = [raw_metrics]
            if not raw_metrics and args.get("metric_field"):
                raw_metrics = [args.get("metric_field")]
            if not raw_metrics and args.get("target_field"):
                raw_metrics = [args.get("target_field")]

            raw_dims = args.get("dimension_fields") or []
            if isinstance(raw_dims, str):
                raw_dims = [raw_dims]
            if not raw_dims and args.get("dimension_field"):
                raw_dims = [args.get("dimension_field")]

            method_str = str(args.get("method") or "ROBUST_Z_SCORE").upper()
            try:
                method_enum = DetectionMethod(method_str)
            except ValueError:
                method_enum = DetectionMethod.ROBUST_Z_SCORE

            anomaly_req = AnomalyDetectionRequest(
                dataset_id=dataset_id,
                dataset_version_id=dataset_version_id,
                metric_fields=raw_metrics,
                time_field=args.get("time_field"),
                dimension_fields=raw_dims,
                method=method_enum,
                sensitivity=float(args.get("sensitivity", 3.0)),
            )
            anomaly_service = AnomalyService(db)
            anom_res = await anomaly_service.detect_anomalies(user.id, anomaly_req)

            return {
                "operation": "detect_anomalies_and_insights",
                "status": "COMPLETED",
                "dataset_id": anom_res.dataset_id,
                "dataset_version_id": anom_res.dataset_version_id,
                "total_anomalies_count": anom_res.total_anomalies_count,
                "critical_count": anom_res.critical_count,
                "high_count": anom_res.high_count,
                "medium_count": anom_res.medium_count,
                "low_count": anom_res.low_count,
                "anomalies": [a.model_dump() for a in anom_res.anomalies],
                "insights": [i.model_dump() for i in anom_res.insights],
                "summary": f"Detected {anom_res.total_anomalies_count} anomalies ({anom_res.critical_count} critical, {anom_res.high_count} high) using {method_enum.value}.",
                "execution_time_ms": anom_res.execution_time_ms,
            }

        if tool_call.name == "run_what_if_scenario":
            from app.scenarios.schemas import AssumptionSpec, WhatIfScenarioRequest
            from app.scenarios.service import ScenarioService

            args = dict(tool_call.arguments)
            raw_target = args.get("target_metric", "revenue")
            raw_assumptions = args.get("assumptions") or []
            parsed_assumptions = [
                AssumptionSpec(**a) if isinstance(a, dict) else AssumptionSpec(variable=str(a), value=10.0)
                for a in raw_assumptions
            ]

            sc_req = WhatIfScenarioRequest(
                dataset_id=dataset_id,
                dataset_version_id=dataset_version_id,
                name=args.get("name"),
                target_metric=raw_target,
                assumptions=parsed_assumptions,
            )

            sc_service = ScenarioService(db)
            sc_res = await sc_service.run_what_if_scenario(user.id, sc_req)

            return {
                "operation": "run_what_if_scenario",
                "status": "COMPLETED",
                "scenario_id": sc_res.id,
                "name": sc_res.name,
                "target_metric": sc_res.target_metric,
                "baseline_value": sc_res.baseline_value,
                "scenario_value": sc_res.scenario_value,
                "absolute_change": sc_res.absolute_change,
                "percentage_change": sc_res.percentage_change,
                "assumptions": [a.model_dump() for a in sc_res.assumptions],
                "narrative": sc_res.narrative,
                "summary": sc_res.narrative,
                "provenance": sc_res.provenance,
            }

        if tool_call.name == "search_business_knowledge":
            from app.knowledge.schemas import KnowledgeSearchRequest
            from app.knowledge.service import KnowledgeService

            k_service = KnowledgeService(db)
            search_req = KnowledgeSearchRequest(
                query=tool_call.arguments.get("query", ""),
                collection_id=tool_call.arguments.get("collection_id"),
                dataset_id=dataset_id,
                top_k=tool_call.arguments.get("top_k", 5),
            )
            k_res = await k_service.search(user.id, search_req)

            citations_text = "\n".join([f"[{c.citation_index}] {c.document_title}: {c.source_snippet}" for c in k_res.citations])
            summary_text = (
                f"Retrieved {len(k_res.results)} grounded knowledge snippets for '{search_req.query}'.\n"
                f"Citations:\n{citations_text}"
                if k_res.has_sufficient_evidence
                else "No sufficiently relevant business knowledge found."
            )

            return {
                "operation": "search_business_knowledge",
                "status": "COMPLETED",
                "query": k_res.query,
                "results_count": k_res.results_count,
                "results": [r.model_dump() for r in k_res.results],
                "citations": [c.model_dump() for c in k_res.citations],
                "has_sufficient_evidence": k_res.has_sufficient_evidence,
                "summary": summary_text,
                "notice": k_res.notice,
            }

        args = dict(tool_call.arguments)
        filters = args.pop("filters", None)
        limit = args.pop("limit", 1000)
        offset = args.pop("offset", 0)
        sort_by = args.pop("sort_by", None)

        run_req = AnalysisRunRequest(
            dataset_id=dataset_id,
            dataset_version_id=dataset_version_id,
            operation=tool_call.name,
            parameters=args,
            filters=filters,
            limit=limit,
            offset=offset,
            sort_by=sort_by,
        )

        response = await analytics_service.run_analysis(
            request=run_req,
            current_user=user,
            db=db,
        )

        return {
            "analysis_id": response.analysis_id,
            "operation": response.operation,
            "status": response.status,
            "columns": response.columns,
            "rows": response.rows,
            "row_count": response.row_count,
            "summary": response.summary,
            "execution_time_ms": response.execution_time_ms,
            "provenance": response.provenance.model_dump() if response.provenance else None,
        }

