"""Deterministic analytics contracts. LLM output must map into these structures."""

from typing import Any, Dict, List, Literal

from pydantic import BaseModel, Field


class AnalysisPlan(BaseModel):
    operation: Literal["profile", "filter", "aggregate", "group_by", "correlation", "distribution", "sql"]
    dataset_version_id: str
    dimensions: List[str] = Field(default_factory=list)
    measures: List[str] = Field(default_factory=list)
    filters: List[Dict[str, Any]] = Field(default_factory=list)
    limit: int = Field(default=100, ge=1, le=10000)
    rationale: str = ""
