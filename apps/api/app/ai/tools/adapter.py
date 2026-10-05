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

        return tool_defs

    @classmethod
    def validate_tool_call(cls, tool_call: ToolCallSpec) -> None:
        """Ensure tool exists in allowlist and arguments are well-formed."""
        if tool_call.name in ["execute_federated_query", "run_time_series_forecast"]:
            return
        tool = analysis_registry.get(tool_call.name)
        if not tool:
            allowed = [m.name for m in analysis_registry.list_tools()] + ["execute_federated_query", "run_time_series_forecast"]
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

