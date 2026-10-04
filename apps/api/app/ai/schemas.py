"""Pydantic schemas for AI Analyst conversations, messages, and orchestration responses."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class ToolCallItem(BaseModel):
    name: str
    arguments: Dict[str, Any]
    call_id: Optional[str] = None


class ToolResultItem(BaseModel):
    name: str
    analysis_id: Optional[str] = None
    row_count: int = 0
    columns: List[str] = Field(default_factory=list)
    summary: Optional[Dict[str, Any]] = None
    execution_time_ms: float = 0.0


class MessageItem(BaseModel):
    id: str
    role: str
    content: str
    tool_calls: Optional[List[Dict[str, Any]]] = None
    tool_results: Optional[List[Dict[str, Any]]] = None
    analysis_ids: Optional[List[str]] = None
    created_at: datetime


class ConversationCreate(BaseModel):
    dataset_id: str
    dataset_version_id: str
    title: Optional[str] = "New Analysis Session"


class ConversationResponse(BaseModel):
    id: str
    dataset_id: str
    dataset_version_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    messages: List[MessageItem] = Field(default_factory=list)


class ConversationListItem(BaseModel):
    id: str
    dataset_id: str
    dataset_version_id: str
    title: str
    created_at: datetime
    updated_at: datetime
    message_count: int = 0


class ChatRequest(BaseModel):
    dataset_id: str
    dataset_version_id: str
    message: str = Field(..., min_length=1, max_length=2000)
    conversation_id: Optional[str] = None


class ChatResponse(BaseModel):
    conversation_id: str
    message_id: str
    message: str
    tool_calls: List[Dict[str, Any]] = Field(default_factory=list)
    tool_results: List[Dict[str, Any]] = Field(default_factory=list)
    analysis_ids: List[str] = Field(default_factory=list)
    provenance: List[Dict[str, Any]] = Field(default_factory=list)
    needs_clarification: bool = False
    execution_time_ms: float = 0.0
    tokens_used: int = 0
    created_at: datetime
