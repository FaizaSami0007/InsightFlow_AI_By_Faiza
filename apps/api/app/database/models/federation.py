"""SQLAlchemy ORM models for Phase 10 Multi-Dataset Federation and Relationships."""

import enum
from typing import Any, Dict, List, Optional

from sqlalchemy import JSON, Float, ForeignKey, String, Text
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class RelationshipType(str, enum.Enum):
    ONE_TO_ONE = "ONE_TO_ONE"
    ONE_TO_MANY = "ONE_TO_MANY"
    MANY_TO_ONE = "MANY_TO_ONE"


class RelationshipStatus(str, enum.Enum):
    PROPOSED = "PROPOSED"
    VALIDATED = "VALIDATED"
    REJECTED = "REJECTED"
    DISABLED = "DISABLED"


class DatasetCollection(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Logical grouping / workspace of related datasets for federated intelligence."""

    __tablename__ = "dataset_collections"

    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    user_id: Mapped[str] = mapped_column(String(36), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    metadata_json: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    items: Mapped[List["DatasetCollectionItem"]] = relationship(
        "DatasetCollectionItem",
        back_populates="collection",
        cascade="all, delete-orphan",
        lazy="selectin",
    )
    relationships: Mapped[List["DatasetRelationship"]] = relationship(
        "DatasetRelationship",
        back_populates="collection",
        cascade="all, delete-orphan",
        lazy="selectin",
    )


class DatasetCollectionItem(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Membership of a dataset within a DatasetCollection."""

    __tablename__ = "dataset_collection_items"

    collection_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("dataset_collections.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    dataset_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    dataset_version_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("dataset_versions.id", ondelete="SET NULL"),
        nullable=True,
    )

    # Relationships
    collection: Mapped["DatasetCollection"] = relationship("DatasetCollection", back_populates="items")


class DatasetRelationship(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Controlled, version-aware join relationship between two dataset fields."""

    __tablename__ = "dataset_relationships"

    collection_id: Mapped[Optional[str]] = mapped_column(
        String(36),
        ForeignKey("dataset_collections.id", ondelete="CASCADE"),
        index=True,
        nullable=True,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Source dataset & field
    source_dataset_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    source_version_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("dataset_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    source_field: Mapped[str] = mapped_column(String(255), nullable=False)

    # Target dataset & field
    target_dataset_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("datasets.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    target_version_id: Mapped[str] = mapped_column(
        String(36),
        ForeignKey("dataset_versions.id", ondelete="CASCADE"),
        nullable=False,
    )
    target_field: Mapped[str] = mapped_column(String(255), nullable=False)

    # Cardinality & validation status
    relationship_type: Mapped[RelationshipType] = mapped_column(
        SQLEnum(RelationshipType, native_enum=False),
        default=RelationshipType.MANY_TO_ONE,
        nullable=False,
    )
    status: Mapped[RelationshipStatus] = mapped_column(
        SQLEnum(RelationshipStatus, native_enum=False),
        default=RelationshipStatus.PROPOSED,
        index=True,
        nullable=False,
    )

    # Deterministic metrics & evidence
    coverage_ratio: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    source_unique_ratio: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    target_unique_ratio: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    null_rate: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    quality_score: Mapped[float] = mapped_column(Float, default=0.0, nullable=False)
    evidence: Mapped[Dict[str, Any]] = mapped_column(JSON, default=dict, nullable=False)

    # Relationships
    collection: Mapped[Optional["DatasetCollection"]] = relationship(
        "DatasetCollection", back_populates="relationships"
    )
