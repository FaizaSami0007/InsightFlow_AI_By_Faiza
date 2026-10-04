import enum
from typing import TYPE_CHECKING, List, Optional

from sqlalchemy import Enum as SQLEnum
from sqlalchemy import ForeignKey, Index, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin

if TYPE_CHECKING:
    from app.database.models.user import User


class DatasetStatus(str, enum.Enum):
    UPLOADING = "UPLOADING"
    VALIDATING = "VALIDATING"
    READY = "READY"
    FAILED = "FAILED"
    ARCHIVED = "ARCHIVED"


class FileFormat(str, enum.Enum):
    CSV = "CSV"
    PARQUET = "PARQUET"


class Dataset(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Logical dataset container owning versioned uploads."""

    __tablename__ = "datasets"

    owner_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    status: Mapped[DatasetStatus] = mapped_column(
        SQLEnum(DatasetStatus, name="dataset_status_enum", native_enum=False),
        default=DatasetStatus.READY,
        nullable=False,
    )

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="datasets")
    versions: Mapped[List["DatasetVersion"]] = relationship(
        "DatasetVersion",
        back_populates="dataset",
        cascade="all, delete-orphan",
        order_by="DatasetVersion.version_number.desc()",
        lazy="selectin",
    )


class DatasetVersion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Immutable physical dataset version representing an uploaded CSV or Parquet file."""

    __tablename__ = "dataset_versions"

    dataset_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_format: Mapped[FileFormat] = mapped_column(
        SQLEnum(FileFormat, name="file_format_enum", native_enum=False),
        nullable=False,
    )
    file_size: Mapped[int] = mapped_column(Integer, nullable=False)
    storage_reference: Mapped[str] = mapped_column(String(512), nullable=False)
    checksum: Mapped[str] = mapped_column(String(64), nullable=False)  # SHA-256
    status: Mapped[DatasetStatus] = mapped_column(
        SQLEnum(DatasetStatus, name="dataset_version_status_enum", native_enum=False),
        default=DatasetStatus.READY,
        nullable=False,
    )
    row_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    column_count: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)

    # Relationships
    dataset: Mapped["Dataset"] = relationship("Dataset", back_populates="versions")

    __table_args__ = (
        UniqueConstraint("dataset_id", "version_number", name="uq_dataset_version"),
        Index("ix_dataset_version_lookup", "dataset_id", "version_number"),
    )
