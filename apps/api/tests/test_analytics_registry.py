from app.analytics.engine.contracts import AnalysisToolMetadata
from app.analytics.engine.registry import analysis_registry


def test_registry_tool_discovery():
    tools = analysis_registry.list_tools()
    assert len(tools) >= 10
    names = [t.name for t in tools]
    assert "describe_dataset" in names
    assert "filter_data" in names
    assert "sort_data" in names
    assert "group_by" in names
    assert "compare_groups" in names
    assert "frequency" in names
    assert "correlation" in names
    assert "distribution" in names
    assert "time_series_summary" in names
    assert "percent_change" in names
    assert "outlier_analysis" in names


def test_registry_tool_metadata_contract():
    group_tool = analysis_registry.get("group_by")
    assert group_tool is not None
    meta = group_tool.metadata
    assert isinstance(meta, AnalysisToolMetadata)
    assert meta.name == "group_by"
    assert "dimensions" in meta.required_params
    assert "aggregations" in meta.required_params
    assert meta.category == "aggregation"


def test_unknown_tool_rejection():
    tool = analysis_registry.get("non_existent_tool_xyz")
    assert tool is None
