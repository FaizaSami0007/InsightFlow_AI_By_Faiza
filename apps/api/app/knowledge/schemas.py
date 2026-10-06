"""Pydantic schemas for Phase 14 Knowledge Intelligence, RAG & Business Knowledge."""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, ConfigDict, Field

from app.database.models.knowledge import (
    DocumentProcessingStatus,
    DocumentType,
    KnowledgeType,
)


class KnowledgeCollectionCreateRequest(BaseModel):
    """Payload to create a new domain knowledge collection."""

    name: str = Field(..., min_length=1, max_length=255, description="Collection name e.g. 'Sales Policies'")
    description: Optional[str] = Field(None, description="Optional description of knowledge domain")
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict, description="Custom collection metadata")


class KnowledgeCollectionResponse(BaseModel):
    """Knowledge collection response entity."""

    id: str
    user_id: str
    name: str
    description: Optional[str] = None
    is_system: bool = False
    document_count: int = 0
    metadata_json: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KnowledgeChunkResponse(BaseModel):
    """Single semantic chunk with structural lineage and vector indicators."""

    id: str
    document_id: str
    document_version_id: str
    chunk_index: int
    content: str
    token_count: int
    page_number: Optional[int] = None
    section_heading: Optional[str] = None
    has_embedding: bool = False
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KnowledgeDocumentVersionResponse(BaseModel):
    """Immutable version snapshot representation of a document."""

    id: str
    document_id: str
    version_number: int
    storage_reference: str
    checksum: str
    extracted_text_length: int
    chunk_count: int
    is_ocr: bool
    ocr_confidence: Optional[float] = None
    status: DocumentProcessingStatus
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KnowledgeDocumentResponse(BaseModel):
    """Detailed metadata and processing status of an ingested knowledge document."""

    id: str
    collection_id: Optional[str] = None
    collection_name: Optional[str] = None
    user_id: str
    title: str
    filename: str
    file_type: DocumentType
    file_size_bytes: int
    checksum: str
    knowledge_type: KnowledgeType
    status: DocumentProcessingStatus
    current_version_num: int
    chunk_count: int = 0
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = Field(default_factory=dict)
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class KnowledgeDocumentListResponse(BaseModel):
    """List of documents response with total count."""

    items: List[KnowledgeDocumentResponse]
    total: int


class KnowledgeSearchRequest(BaseModel):
    """Payload to perform hybrid semantic and keyword search across authorized documents."""

    query: str = Field(..., min_length=1, description="Natural language search query or concept")
    collection_id: Optional[str] = Field(None, description="Optional filter by collection")
    document_ids: Optional[List[str]] = Field(None, description="Optional restrict to specific documents")
    dataset_id: Optional[str] = Field(None, description="Optional filter by associated dataset")
    knowledge_types: Optional[List[KnowledgeType]] = Field(None, description="Filter by knowledge category")
    top_k: int = Field(default=5, ge=1, le=20, description="Max number of relevant chunks to retrieve")
    min_similarity: float = Field(default=0.3, ge=0.0, le=1.0, description="Minimum similarity score threshold")
    include_full_chunks: bool = Field(default=True, description="Whether to include full chunk text in results")


class KnowledgeCitation(BaseModel):
    """Formal citation mapping an extracted claim to its immutable source document and page."""

    citation_index: int = Field(..., description="1-indexed marker [1], [2] in generated narrative")
    document_id: str
    document_title: str
    document_version_id: str
    version_number: int
    page_number: Optional[int] = None
    section_heading: Optional[str] = None
    chunk_id: str
    source_snippet: str
    similarity_score: float


class KnowledgeSearchResultItem(BaseModel):
    """Single retrieved candidate chunk with relevance score and citation metadata."""

    chunk_id: str
    document_id: str
    document_title: str
    document_version_id: str
    version_number: int
    chunk_index: int
    content: str
    page_number: Optional[int] = None
    section_heading: Optional[str] = None
    similarity_score: float
    citation_label: str
    metadata: Dict[str, Any] = Field(default_factory=dict)


class KnowledgeSearchResponse(BaseModel):
    """Complete hybrid search response with ranked candidates and citations."""

    query: str
    results_count: int
    execution_time_ms: float = 0.0
    results: List[KnowledgeSearchResultItem]
    citations: List[KnowledgeCitation]
    has_sufficient_evidence: bool = True
    notice: Optional[str] = None


class DatasetKnowledgeLinkRequest(BaseModel):
    """Request to link a dataset with a knowledge document or collection."""

    dataset_id: str = Field(..., description="Target dataset ID")
    dataset_version_id: Optional[str] = Field(None, description="Optional specific dataset version")
    document_id: Optional[str] = Field(None, description="Knowledge document ID to associate")
    collection_id: Optional[str] = Field(None, description="Knowledge collection ID to associate")
    relationship_nature: str = Field(default="governed_by", description="Semantic relationship e.g. defined_by, governed_by")


class DatasetKnowledgeLinkResponse(BaseModel):
    """Confirmed dataset knowledge association."""

    id: str
    dataset_id: str
    dataset_version_id: Optional[str] = None
    document_id: Optional[str] = None
    document_title: Optional[str] = None
    collection_id: Optional[str] = None
    collection_name: Optional[str] = None
    relationship_nature: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
