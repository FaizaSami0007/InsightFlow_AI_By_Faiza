import enum
import uuid
from datetime import datetime
from typing import Any, Optional

from sqlalchemy import JSON, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base


class AnalysisJobStatus(str, enum.Enum):
    PENDING = "PENDING"
    RUNNING = "RUNNING"
    COMPLETED = "COMPLETED"
    FAILED = "FAILED"


class AnalysisJob(Base):
    """
    Persisted metadata and execution record for deterministic analysis operations.
    Maintains full provenance tracing back to exact dataset version and parameters.
    """
    __tablename__ = "analysis_jobs"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    dataset_id: Mapped[str] = mapped_column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), index=True, nullable=False)
    dataset_version_id: Mapped[str] = mapped_column(String(36), ForeignKey("dataset_versions.id", ondelete="CASCADE"), index=True, nullable=False)

    operation: Mapped[str] = mapped_column(String(64), index=True, nullable=False)
    parameters_json: Mapped[dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)
    filters_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    status: Mapped[AnalysisJobStatus] = mapped_column(
        String(20),
        default=AnalysisJobStatus.PENDING,
        index=True,
        nullable=False,
    )
    error_message: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)

    execution_time_ms: Mapped[Optional[float]] = mapped_column(Float, nullable=True)
    row_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    summary_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)
    result_json: Mapped[Optional[dict[str, Any]]] = mapped_column(JSON, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow, nullable=False)
    completed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    # Relationships
    user = relationship("User", backref="analyses")
    dataset = relationship("Dataset", backref="analyses")
    dataset_version = relationship("DatasetVersion", backref="analyses")
