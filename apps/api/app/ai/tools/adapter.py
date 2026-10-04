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

        return tool_defs

    @classmethod
    def validate_tool_call(cls, tool_call: ToolCallSpec) -> None:
        """Ensure tool exists in allowlist and arguments are well-formed."""
        tool = analysis_registry.get(tool_call.name)
        if not tool:
            allowed = [m.name for m in analysis_registry.list_tools()]
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
        Execute tool call deterministically via AnalyticsService.
        Returns execution result dict including analysis_id, columns, rows, summary, and provenance.
        """
        cls.validate_tool_call(tool_call)

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
