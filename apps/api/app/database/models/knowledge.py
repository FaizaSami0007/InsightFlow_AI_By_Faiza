"""SQLAlchemy models for Phase 14 Knowledge Intelligence, RAG & Business Knowledge."""

import enum

from sqlalchemy import Boolean, Column, Enum, Float, ForeignKey, Integer, String, Text
from sqlalchemy.dialects.sqlite import JSON as SQLITE_JSON
from sqlalchemy.orm import relationship
from sqlalchemy.types import JSON

from app.database.base import Base, TimestampMixin, UUIDPrimaryKeyMixin


class DocumentProcessingStatus(str, enum.Enum):
    """Lifecycle status of an ingested knowledge document."""

    UPLOADED = "UPLOADED"
    EXTRACTING = "EXTRACTING"
    CHUNKED = "CHUNKED"
    EMBEDDED = "EMBEDDED"
    INDEXED = "INDEXED"
    READY = "READY"
    FAILED = "FAILED"
    STALE = "STALE"


class DocumentType(str, enum.Enum):
    """Supported file/document types."""

    PDF = "PDF"
    DOCX = "DOCX"
    TXT = "TXT"
    MARKDOWN = "MARKDOWN"
    CSV_REFERENCE = "CSV_REFERENCE"
    OTHER = "OTHER"


class KnowledgeType(str, enum.Enum):
    """Categorical semantic purpose of knowledge item."""

    GENERAL_POLICY = "GENERAL_POLICY"
    KPI_DEFINITION = "KPI_DEFINITION"
    METRIC_FORMULA = "METRIC_FORMULA"
    BUSINESS_RULE = "BUSINESS_RULE"
    SOP = "SOP"
    GLOSSARY = "GLOSSARY"
    DOMAIN_GUIDE = "DOMAIN_GUIDE"


class KnowledgeCollection(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Organizes knowledge documents into domain groups (e.g. Sales Policies, HR, Financial SOPs)."""

    __tablename__ = "knowledge_collections"

    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    is_system = Column(Boolean, default=False, nullable=False)
    metadata_json = Column(JSON().with_variant(SQLITE_JSON, "sqlite"), default=dict, nullable=False)

    documents = relationship("KnowledgeDocument", back_populates="collection", cascade="all, delete-orphan")


class KnowledgeDocument(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """A business or domain document ingested for contextual reasoning and citation."""

    __tablename__ = "knowledge_documents"

    collection_id = Column(
        String(36), ForeignKey("knowledge_collections.id", ondelete="SET NULL"), nullable=True, index=True
    )
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(255), nullable=False, index=True)
    filename = Column(String(255), nullable=False)
    file_type = Column(Enum(DocumentType), default=DocumentType.TXT, nullable=False)
    file_size_bytes = Column(Integer, default=0, nullable=False)
    storage_reference = Column(String(512), nullable=False)
    checksum = Column(String(64), nullable=False, index=True)
    knowledge_type = Column(Enum(KnowledgeType), default=KnowledgeType.GENERAL_POLICY, nullable=False)
    status = Column(
        Enum(DocumentProcessingStatus), default=DocumentProcessingStatus.UPLOADED, nullable=False, index=True
    )
    current_version_num = Column(Integer, default=1, nullable=False)
    error_message = Column(Text, nullable=True)
    metadata_json = Column(JSON().with_variant(SQLITE_JSON, "sqlite"), default=dict, nullable=False)

    collection = relationship("KnowledgeCollection", back_populates="documents")
    versions = relationship("KnowledgeDocumentVersion", back_populates="document", cascade="all, delete-orphan")
    chunks = relationship("KnowledgeChunk", back_populates="document", cascade="all, delete-orphan")


class KnowledgeDocumentVersion(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Immutable version snapshot of a knowledge document to preserve historical citations."""

    __tablename__ = "knowledge_document_versions"

    document_id = Column(
        String(36), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    version_number = Column(Integer, nullable=False)
    storage_reference = Column(String(512), nullable=False)
    checksum = Column(String(64), nullable=False)
    extracted_text_length = Column(Integer, default=0, nullable=False)
    chunk_count = Column(Integer, default=0, nullable=False)
    is_ocr = Column(Boolean, default=False, nullable=False)
    ocr_confidence = Column(Float, nullable=True)
    status = Column(Enum(DocumentProcessingStatus), default=DocumentProcessingStatus.READY, nullable=False)

    document = relationship("KnowledgeDocument", back_populates="versions")
    chunks = relationship("KnowledgeChunk", back_populates="document_version", cascade="all, delete-orphan")


class KnowledgeChunk(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Semantic segment of a document equipped with structural metadata and vector embeddings."""

    __tablename__ = "knowledge_chunks"

    document_id = Column(
        String(36), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=False, index=True
    )
    document_version_id = Column(
        String(36), ForeignKey("knowledge_document_versions.id", ondelete="CASCADE"), nullable=False, index=True
    )
    chunk_index = Column(Integer, nullable=False)
    content = Column(Text, nullable=False)
    token_count = Column(Integer, default=0, nullable=False)
    page_number = Column(Integer, nullable=True)
    section_heading = Column(String(255), nullable=True)
    embedding_json = Column(JSON().with_variant(SQLITE_JSON, "sqlite"), nullable=True)
    metadata_json = Column(JSON().with_variant(SQLITE_JSON, "sqlite"), default=dict, nullable=False)

    document = relationship("KnowledgeDocument", back_populates="chunks")
    document_version = relationship("KnowledgeDocumentVersion", back_populates="chunks")


class DatasetKnowledgeLink(Base, UUIDPrimaryKeyMixin, TimestampMixin):
    """Direct contextual association between structured datasets and domain knowledge."""

    __tablename__ = "dataset_knowledge_links"

    dataset_id = Column(String(36), ForeignKey("datasets.id", ondelete="CASCADE"), nullable=False, index=True)
    dataset_version_id = Column(String(36), nullable=True)
    document_id = Column(
        String(36), ForeignKey("knowledge_documents.id", ondelete="CASCADE"), nullable=True, index=True
    )
    collection_id = Column(
        String(36), ForeignKey("knowledge_collections.id", ondelete="CASCADE"), nullable=True, index=True
    )
    user_id = Column(String(36), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    relationship_nature = Column(
        String(64), default="governed_by", nullable=False
    )  # e.g. defined_by, governed_by, contextual_reference
    metadata_json = Column(JSON().with_variant(SQLITE_JSON, "sqlite"), default=dict, nullable=False)
