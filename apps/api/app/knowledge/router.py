"""FastAPI endpoints for Phase 14 Knowledge Intelligence, RAG & Business Knowledge."""

from typing import List, Optional

from fastapi import APIRouter, Depends, File, Form, HTTPException, Query, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.knowledge import KnowledgeType
from app.database.models.user import User
from app.database.session import get_db
from app.knowledge.schemas import (
    DatasetKnowledgeLinkRequest,
    DatasetKnowledgeLinkResponse,
    KnowledgeChunkResponse,
    KnowledgeCollectionCreateRequest,
    KnowledgeCollectionResponse,
    KnowledgeDocumentListResponse,
    KnowledgeDocumentResponse,
    KnowledgeDocumentVersionResponse,
    KnowledgeSearchRequest,
    KnowledgeSearchResponse,
)
from app.knowledge.service import KnowledgeService, KnowledgeServiceError
from app.users.dependencies import get_current_user

router = APIRouter(prefix="/knowledge", tags=["Knowledge Intelligence"])


@router.post("/collections", response_model=KnowledgeCollectionResponse, status_code=status.HTTP_201_CREATED)
async def create_collection(
    request: KnowledgeCollectionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeCollectionResponse:
    """Create a new domain knowledge collection."""
    service = KnowledgeService(db)
    try:
        return await service.create_collection(current_user.id, request)
    except KnowledgeServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get("/collections", response_model=List[KnowledgeCollectionResponse])
async def list_collections(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[KnowledgeCollectionResponse]:
    """List all knowledge collections owned by the current user."""
    service = KnowledgeService(db)
    return await service.list_collections(current_user.id)


@router.delete("/collections/{collection_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_collection(
    collection_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a knowledge collection."""
    service = KnowledgeService(db)
    try:
        await service.delete_collection(current_user.id, collection_id)
    except KnowledgeServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/documents/upload", response_model=KnowledgeDocumentResponse, status_code=status.HTTP_201_CREATED)
@router.post("/documents", response_model=KnowledgeDocumentResponse, status_code=status.HTTP_201_CREATED)
async def upload_document(
    file: UploadFile = File(...),
    title: Optional[str] = Form(None),
    collection_id: Optional[str] = Form(None),
    knowledge_type: KnowledgeType = Form(KnowledgeType.GENERAL_POLICY),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeDocumentResponse:
    """Upload, extract, chunk, and index a business knowledge document."""
    service = KnowledgeService(db)
    clean_collection_id = collection_id.strip() if collection_id and collection_id.strip() else None
    clean_title = title.strip() if title and title.strip() else None
    try:
        file_bytes = await file.read()
        return await service.ingest_document(
            user_id=current_user.id,
            filename=file.filename or "uploaded_document.txt",
            file_bytes=file_bytes,
            title=clean_title,
            collection_id=clean_collection_id,
            knowledge_type=knowledge_type,
        )
    except KnowledgeServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail=f"Upload failed: {str(exc)}")


@router.get("/documents", response_model=KnowledgeDocumentListResponse)
async def list_documents(
    collection_id: Optional[str] = Query(None, description="Optional filter by collection"),
    knowledge_type: Optional[KnowledgeType] = Query(None, description="Optional filter by knowledge category"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeDocumentListResponse:
    """List all knowledge documents owned by the current user."""
    service = KnowledgeService(db)
    return await service.list_documents(current_user.id, collection_id=collection_id, knowledge_type=knowledge_type)


@router.get("/documents/{document_id}", response_model=KnowledgeDocumentResponse)
async def get_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeDocumentResponse:
    """Get single document details."""
    service = KnowledgeService(db)
    try:
        return await service.get_document(current_user.id, document_id)
    except KnowledgeServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/documents/{document_id}/chunks", response_model=List[KnowledgeChunkResponse])
async def get_document_chunks(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[KnowledgeChunkResponse]:
    """Inspect indexed semantic chunks of a knowledge document."""
    service = KnowledgeService(db)
    try:
        return await service.get_document_chunks(current_user.id, document_id)
    except KnowledgeServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.get("/documents/{document_id}/versions", response_model=List[KnowledgeDocumentVersionResponse])
async def get_document_versions(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[KnowledgeDocumentVersionResponse]:
    """Inspect version history of a document."""
    service = KnowledgeService(db)
    try:
        return await service.get_document_versions(current_user.id, document_id)
    except KnowledgeServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete("/documents/{document_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_document(
    document_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete a document and all indexed chunks."""
    service = KnowledgeService(db)
    try:
        await service.delete_document(current_user.id, document_id)
    except KnowledgeServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post("/search", response_model=KnowledgeSearchResponse)
async def search_knowledge(
    request: KnowledgeSearchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> KnowledgeSearchResponse:
    """Execute hybrid semantic & keyword retrieval with grounded citations."""
    service = KnowledgeService(db)
    return await service.search(current_user.id, request)


@router.post("/datasets/link", response_model=DatasetKnowledgeLinkResponse, status_code=status.HTTP_201_CREATED)
async def link_dataset(
    request: DatasetKnowledgeLinkRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DatasetKnowledgeLinkResponse:
    """Associate a dataset with a knowledge document or collection."""
    service = KnowledgeService(db)
    try:
        return await service.link_dataset(current_user.id, request)
    except KnowledgeServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
