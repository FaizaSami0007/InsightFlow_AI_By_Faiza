import logging
from typing import Any, Dict, List, Optional, Tuple

from app.analytics.duckdb.dataset import AnalyticalDataset
from app.analytics.engine.contracts import (
    AnalysisToolMetadata,
    SortSpecification,
)
from app.analytics.tools import (
    AnalysisTool,
    CompareGroupsTool,
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

logger = logging.getLogger(__name__)


class AnalysisRegistry:
    """
    Centralized discovery and execution registry for deterministic analysis tools.
    Provides metadata catalogs for future AI tool-calling and web UI consumption.
    """

    def __init__(self) -> None:
        self._tools: Dict[str, AnalysisTool] = {}
        self._register_default_tools()

    def _register_default_tools(self) -> None:
        tools: List[AnalysisTool] = [
            DescribeDatasetTool(),
            FilterDataTool(),
            SortDataTool(),
            GroupByTool(),
            CompareGroupsTool(),
            FrequencyTool(),
            CorrelationTool(),
            DistributionTool(),
            TimeSeriesSummaryTool(),
            PercentChangeTool(),
            OutlierAnalysisTool(),
        ]
        for t in tools:
            self.register(t)

    def register(self, tool: AnalysisTool) -> None:
        name = tool.metadata.name
        self._tools[name] = tool
        logger.debug("Registered analysis tool: %s", name)

    def get(self, tool_name: str) -> Optional[AnalysisTool]:
        return self._tools.get(tool_name)

    def list_tools(self) -> List[AnalysisToolMetadata]:
        return [t.metadata for t in self._tools.values()]

    def validate(
        self,
        tool_name: str,
        dataset: AnalyticalDataset,
        parameters: dict[str, Any],
        filters: Optional[Any] = None,
    ) -> None:
        tool = self.get(tool_name)
        if not tool:
            raise ValueError(f"Unknown analysis tool '{tool_name}'. Available: {list(self._tools.keys())}")
        tool.validate(dataset, parameters, filters)

    def execute(
        self,
        tool_name: str,
        dataset: AnalyticalDataset,
        parameters: dict[str, Any],
        filters: Optional[Any] = None,
        sort_by: Optional[List[SortSpecification]] = None,
        limit: int = 1000,
        offset: int = 0,
    ) -> Tuple[List[str], List[dict[str, Any]], Optional[dict[str, Any]]]:
        tool = self.get(tool_name)
        if not tool:
            raise ValueError(f"Unknown analysis tool '{tool_name}'")
        return tool.execute(
            dataset=dataset,
            parameters=parameters,
            filters=filters,
            sort_by=sort_by,
            limit=limit,
            offset=offset,
        )


# Global Singleton Registry
analysis_registry = AnalysisRegistry()
