"""Formal multi-agent communication contracts, evidence models, claims, and validation schemas."""

import enum
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field


class AgentID(str, enum.Enum):
    SUPERVISOR = "supervisor"
    DATA_ANALYST = "data_analyst"
    KNOWLEDGE_AGENT = "knowledge_agent"
    FORECASTING_AGENT = "forecasting_agent"
    ANOMALY_AGENT = "anomaly_agent"
    SCENARIO_AGENT = "scenario_agent"
    VISUALIZATION_AGENT = "visualization_agent"
    REPORTING_AGENT = "reporting_agent"
    CRITIC_AGENT = "critic_agent"


class TaskType(str, enum.Enum):
    PLANNING = "PLANNING"
    DATA_ANALYSIS = "DATA_ANALYSIS"
    KNOWLEDGE_RETRIEVAL = "KNOWLEDGE_RETRIEVAL"
    FORECAST = "FORECAST"
    ANOMALY_DETECTION = "ANOMALY_DETECTION"
    SCENARIO_SIMULATION = "SCENARIO_SIMULATION"
    VISUALIZATION = "VISUALIZATION"
    REPORTING = "REPORTING"
    VALIDATION = "VALIDATION"
    SYNTHESIS = "SYNTHESIS"


class EvidenceType(str, enum.Enum):
    DATA = "DATA"
    KNOWLEDGE = "KNOWLEDGE"
    CALCULATION = "CALCULATION"
    FORECAST = "FORECAST"
    ANOMALY = "ANOMALY"
    SCENARIO = "SCENARIO"
    ASSUMPTION = "ASSUMPTION"
    USER_INPUT = "USER_INPUT"


class ClaimType(str, enum.Enum):
    FACT = "FACT"
    CALCULATION = "CALCULATION"
    INTERPRETATION = "INTERPRETATION"
    FORECAST = "FORECAST"
    ASSUMPTION = "ASSUMPTION"
    RECOMMENDATION = "RECOMMENDATION"


class MessageType(str, enum.Enum):
    TASK_REQUEST = "TASK_REQUEST"
    TASK_RESULT = "TASK_RESULT"
    TASK_FAILURE = "TASK_FAILURE"
    VALIDATION_REQUEST = "VALIDATION_REQUEST"
    VALIDATION_RESULT = "VALIDATION_RESULT"
    CLARIFICATION_REQUEST = "CLARIFICATION_REQUEST"


class ValidationStatus(str, enum.Enum):
    VALID = "VALID"
    WARNING = "WARNING"
    INVALID = "INVALID"
    UNVERIFIED = "UNVERIFIED"


class AgentMessage(BaseModel):
    """Structured message communicated between agents or supervisor."""

    model_config = ConfigDict(extra="ignore")

    sender: AgentID
    receiver: AgentID
    task_id: str
    message_type: MessageType
    payload: Dict[str, Any] = Field(default_factory=dict)
    evidence: List["EvidenceItem"] = Field(default_factory=list)
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class EvidenceItem(BaseModel):
    """Unified evidence piece with source attribution and exact values."""

    model_config = ConfigDict(extra="ignore")

    id: str
    evidence_type: EvidenceType
    source: str
    dataset_version_id: Optional[str] = None
    document_version_id: Optional[str] = None
    operation: str
    raw_value: Any
    confidence: float = 1.0
    provenance: Dict[str, Any] = Field(default_factory=dict)
    created_at: str = Field(default_factory=lambda: datetime.utcnow().isoformat())


class ClaimItem(BaseModel):
    """Categorized factual or analytical claim linked to evidence items."""

    model_config = ConfigDict(extra="ignore")

    claim_id: str
    statement: str
    claim_type: ClaimType
    evidence_ids: List[str] = Field(default_factory=list)
    confidence: float = 1.0
    citation_label: Optional[str] = None


class ValidationFinding(BaseModel):
    """Specific finding from the Critic/Validation agent."""

    model_config = ConfigDict(extra="ignore")

    check_name: str
    status: ValidationStatus
    description: str
    affected_claims: List[str] = Field(default_factory=list)
    suggested_correction: Optional[str] = None


class ValidationReport(BaseModel):
    """Comprehensive critic evaluation of agent outputs."""

    model_config = ConfigDict(extra="ignore")

    overall_status: ValidationStatus = ValidationStatus.VALID
    findings: List[ValidationFinding] = Field(default_factory=list)
    numerical_consistency: bool = True
    citation_grounding: bool = True
    contradiction_detected: bool = False
    validation_score: float = 1.0
    summary_notes: Optional[str] = None


class ExecutionBudget(BaseModel):
    """Resource constraints to prevent runaway loops and excessive costs."""

    model_config = ConfigDict(extra="ignore")

    max_agents: int = 5
    max_tasks: int = 10
    max_recursion_depth: int = 4
    max_tool_calls_per_agent: int = 3
    timeout_seconds: float = 30.0
    token_budget: int = 12000
    max_parallel_tasks: int = 3


class AgentRequest(BaseModel):
    """Standardized input payload provided to an individual agent."""

    model_config = ConfigDict(extra="ignore")

    task_id: str
    conversation_id: str
    user_id: str
    workspace_id: Optional[str] = None
    dataset_id: str
    dataset_version_id: str
    query: str
    objective: str
    context: Dict[str, Any] = Field(default_factory=dict)
    prior_evidence: List[EvidenceItem] = Field(default_factory=list)
    allowed_tools: List[str] = Field(default_factory=list)
    budget: ExecutionBudget = Field(default_factory=ExecutionBudget)


class AgentResponse(BaseModel):
    """Standardized output produced by an individual agent."""

    model_config = ConfigDict(extra="ignore")

    task_id: str
    agent_id: AgentID
    status: str = "COMPLETED"  # COMPLETED, FAILED, SKIPPED, CLARIFICATION
    summary: str
    data_payload: Dict[str, Any] = Field(default_factory=dict)
    evidence: List[EvidenceItem] = Field(default_factory=list)
    claims: List[ClaimItem] = Field(default_factory=list)
    citations: List[Dict[str, Any]] = Field(default_factory=list)
    tool_calls_executed: List[Dict[str, Any]] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    error_message: Optional[str] = None
    execution_time_ms: float = 0.0


class TaskPlanStep(BaseModel):
    """A single node step in the multi-agent task plan."""

    model_config = ConfigDict(extra="ignore")

    task_id: str
    agent_id: AgentID
    task_type: TaskType
    objective: str
    dependencies: List[str] = Field(default_factory=list)
    input_parameters: Dict[str, Any] = Field(default_factory=dict)
    priority: int = 1


class MultiAgentPlan(BaseModel):
    """Structured task decomposition produced by the Supervisor."""

    model_config = ConfigDict(extra="ignore")

    intent_category: str
    explanation: str
    steps: List[TaskPlanStep] = Field(default_factory=list)
    requires_validation: bool = True
    estimated_tokens: int = 0
