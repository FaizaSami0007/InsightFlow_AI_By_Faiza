import enum
import uuid
from datetime import datetime
from typing import Any, List, Optional

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class MessageRole(str, enum.Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"
    TOOL = "tool"


class AIConversation(Base):
    """
    Persisted chat session between a user and the AI analyst for a specific dataset version.
    """

    __tablename__ = "ai_conversations"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    dataset_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("datasets.id", ondelete="CASCADE"), index=True, nullable=False
    )
    dataset_version_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("dataset_versions.id", ondelete="CASCADE"), index=True, nullable=False
    )

    title: Mapped[str] = mapped_column(String(255), default="New Analysis Session", nullable=False)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )

    # Relationships
    user = relationship("User", backref="ai_conversations")
    dataset = relationship("Dataset", backref="ai_conversations")
    dataset_version = relationship("DatasetVersion", backref="ai_conversations")
    messages = relationship(
        "AIMessage",
        back_populates="conversation",
        cascade="all, delete-orphan",
        order_by="AIMessage.created_at",
        lazy="selectin",
    )


class AIMessage(Base):
    """
    Individual message turn in an AI conversation, supporting user prompts, assistant answers,
    tool call specifications, and tool results.
    """

    __tablename__ = "ai_messages"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    conversation_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("ai_conversations.id", ondelete="CASCADE"), index=True, nullable=False
    )

    role: Mapped[str] = mapped_column(String(20), nullable=False)  # user, assistant, tool, system
    content: Mapped[str] = mapped_column(Text, nullable=False)

    tool_calls_json: Mapped[Optional[List[dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    tool_results_json: Mapped[Optional[List[dict[str, Any]]]] = mapped_column(JSON, nullable=True)
    analysis_ids: Mapped[Optional[List[str]]] = mapped_column(JSON, nullable=True)
    visualization_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)

    # Relationships
    conversation = relationship("AIConversation", back_populates="messages")


class AIRequestLog(Base):
    """
    Observability and audit log for AI requests, token usage, latency, and status.
    Contains zero secrets or credentials.
    """

    __tablename__ = "ai_request_logs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(
        String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False
    )
    conversation_id: Mapped[Optional[str]] = mapped_column(String(36), nullable=True, index=True)

    provider: Mapped[str] = mapped_column(String(64), nullable=False)
    model: Mapped[str] = mapped_column(String(64), nullable=False)

    latency_ms: Mapped[float] = mapped_column(Float, nullable=False)
    prompt_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    completion_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_tokens: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    tool_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    status: Mapped[str] = mapped_column(String(32), default="SUCCESS", nullable=False)  # SUCCESS, FAILED, CLARIFICATION
    error_message: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
