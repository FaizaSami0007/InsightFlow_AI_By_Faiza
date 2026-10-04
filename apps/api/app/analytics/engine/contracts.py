import enum
from datetime import datetime
from typing import Any, List, Optional, Union

from pydantic import BaseModel, Field


class FilterOperator(str, enum.Enum):
    EQ = "="
    NEQ = "!="
    GT = ">"
    GTE = ">="
    LT = "<"
    LTE = "<="
    IN = "IN"
    NOT_IN = "NOT IN"
    BETWEEN = "BETWEEN"
    IS_NULL = "IS NULL"
    IS_NOT_NULL = "IS NOT NULL"
    LIKE = "LIKE"
    ILIKE = "ILIKE"


class LogicalOperator(str, enum.Enum):
    AND = "AND"
    OR = "OR"
    NOT = "NOT"


class FilterCondition(BaseModel):
    column: str
    operator: FilterOperator
    value: Optional[Any] = None
    value_to: Optional[Any] = None  # for BETWEEN
    values: Optional[List[Any]] = None  # for IN, NOT IN


class FilterGroup(BaseModel):
    logical_op: LogicalOperator = LogicalOperator.AND
    conditions: List[FilterCondition] = Field(default_factory=list)
    groups: List["FilterGroup"] = Field(default_factory=list)


class SortOrder(str, enum.Enum):
    ASC = "ASC"
    DESC = "DESC"


class SortSpecification(BaseModel):
    column: str
    order: SortOrder = SortOrder.ASC


class AggregationType(str, enum.Enum):
    COUNT = "COUNT"
    COUNT_DISTINCT = "COUNT DISTINCT"
    SUM = "SUM"
    AVG = "AVG"
    MIN = "MIN"
    MAX = "MAX"
    MEDIAN = "MEDIAN"
    STDDEV = "STDDEV"
    VARIANCE = "VARIANCE"


class AggregationSpec(BaseModel):
    column: str
    agg_type: AggregationType
    alias: Optional[str] = None


class AnalysisProvenance(BaseModel):
    dataset_id: str
    dataset_version_id: str
    operation: str
    parameters: dict[str, Any]
    filters: Optional[dict[str, Any]] = None
    execution_time_ms: float
    tool_version: str = "1.0.0"
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class AnalysisRequest(BaseModel):
    dataset_id: str
    dataset_version_id: str
    operation: str
    parameters: dict[str, Any] = Field(default_factory=dict)
    filters: Optional[Union[FilterGroup, FilterCondition, dict[str, Any]]] = None
    sort_by: Optional[List[SortSpecification]] = None
    limit: Optional[int] = Field(default=1000, ge=1, le=10000)
    offset: Optional[int] = Field(default=0, ge=0)


class AnalysisResult(BaseModel):
    analysis_id: str
    dataset_id: str
    dataset_version_id: str
    operation: str
    status: str  # PENDING, RUNNING, COMPLETED, FAILED
    columns: List[str] = Field(default_factory=list)
    rows: List[dict[str, Any]] = Field(default_factory=list)
    summary: Optional[dict[str, Any]] = None
    execution_time_ms: float = 0.0
    row_count: int = 0
    provenance: Optional[AnalysisProvenance] = None
    error_message: Optional[str] = None


class AnalysisToolMetadata(BaseModel):
    name: str
    display_name: str
    description: str
    category: str  # "descriptive", "aggregation", "statistical", "temporal", "filtering"
    required_params: List[str] = Field(default_factory=list)
    optional_params: List[str] = Field(default_factory=list)
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    semantic_prerequisites: dict[str, Any] = Field(default_factory=dict)
