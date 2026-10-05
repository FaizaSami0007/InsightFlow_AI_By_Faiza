"""API Router for Phase 10 Multi-Dataset Collections, Relationships & Federated Intelligence."""

from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.database.models.federation import RelationshipStatus
from app.database.models.user import User
from app.database.session import get_db
from app.federation.planner import FederatedPlannerError
from app.federation.schemas import (
    DatasetCollectionCreateRequest,
    DatasetCollectionListResponse,
    DatasetCollectionResponse,
    DiscoveryResponse,
    FederatedAnalysisRequest,
    FederatedAnalysisResponse,
    RelationshipListResponse,
    RelationshipProposeRequest,
    RelationshipResponse,
    RelationshipStatusUpdateRequest,
)
from app.federation.service import FederationService, FederationServiceError
from app.users.dependencies import get_current_user

router = APIRouter(tags=["Federation"])


# --- Dataset Collections Endpoints ---


@router.post(
    "/collections",
    response_model=DatasetCollectionResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new dataset collection / workspace",
)
async def create_collection(
    request: DatasetCollectionCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DatasetCollectionResponse:
    service = FederationService(db)
    try:
        return await service.create_collection(current_user.id, request)
    except FederationServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get(
    "/collections",
    response_model=DatasetCollectionListResponse,
    summary="List all dataset collections owned by current user",
)
async def list_collections(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DatasetCollectionListResponse:
    service = FederationService(db)
    items = await service.list_collections(current_user.id)
    return DatasetCollectionListResponse(items=items, total=len(items))


@router.get(
    "/collections/{collection_id}",
    response_model=DatasetCollectionResponse,
    summary="Get collection details with items and relationships",
)
async def get_collection(
    collection_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DatasetCollectionResponse:
    service = FederationService(db)
    try:
        return await service.get_collection(current_user.id, collection_id)
    except FederationServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete(
    "/collections/{collection_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a dataset collection",
)
async def delete_collection(
    collection_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = FederationService(db)
    try:
        await service.delete_collection(current_user.id, collection_id)
    except FederationServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/collections/{collection_id}/datasets/{dataset_id}",
    response_model=DatasetCollectionResponse,
    summary="Add a dataset to a collection",
)
async def add_dataset_to_collection(
    collection_id: str,
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DatasetCollectionResponse:
    service = FederationService(db)
    try:
        return await service.add_dataset_to_collection(current_user.id, collection_id, dataset_id)
    except FederationServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.delete(
    "/collections/{collection_id}/datasets/{dataset_id}",
    response_model=DatasetCollectionResponse,
    summary="Remove a dataset from a collection",
)
async def remove_dataset_from_collection(
    collection_id: str,
    dataset_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DatasetCollectionResponse:
    service = FederationService(db)
    try:
        return await service.remove_dataset_from_collection(current_user.id, collection_id, dataset_id)
    except FederationServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.post(
    "/collections/{collection_id}/discover-relationships",
    response_model=DiscoveryResponse,
    summary="Discover candidate relationships among datasets in a collection",
)
async def discover_relationships(
    collection_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> DiscoveryResponse:
    service = FederationService(db)
    try:
        return await service.discover_relationships_in_collection(current_user.id, collection_id)
    except FederationServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


# --- Dataset Relationships Endpoints ---


@router.post(
    "/relationships",
    response_model=RelationshipResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Propose and validate a new dataset relationship",
)
async def propose_relationship(
    request: RelationshipProposeRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RelationshipResponse:
    service = FederationService(db)
    try:
        return await service.propose_relationship(current_user.id, request)
    except FederationServiceError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.get(
    "/relationships",
    response_model=RelationshipListResponse,
    summary="List relationships matching criteria",
)
async def list_relationships(
    collection_id: Optional[str] = Query(default=None),
    status_filter: Optional[RelationshipStatus] = Query(default=None, alias="status"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RelationshipListResponse:
    service = FederationService(db)
    items = await service.list_relationships(current_user.id, collection_id=collection_id, status=status_filter)
    return RelationshipListResponse(items=items, total=len(items))


@router.post(
    "/relationships/{relationship_id}/validate",
    response_model=RelationshipResponse,
    summary="Trigger DuckDB referential validation on a relationship",
)
async def validate_relationship(
    relationship_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RelationshipResponse:
    service = FederationService(db)
    try:
        return await service.validate_relationship(current_user.id, relationship_id)
    except FederationServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.patch(
    "/relationships/{relationship_id}/status",
    response_model=RelationshipResponse,
    summary="Approve, reject, or disable a relationship",
)
async def update_relationship_status(
    relationship_id: str,
    request: RelationshipStatusUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> RelationshipResponse:
    service = FederationService(db)
    try:
        return await service.update_relationship_status(current_user.id, relationship_id, request.status)
    except FederationServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


@router.delete(
    "/relationships/{relationship_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a relationship record",
)
async def delete_relationship(
    relationship_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    service = FederationService(db)
    try:
        await service.delete_relationship(current_user.id, relationship_id)
    except FederationServiceError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))


# --- Federated Analysis Execution ---


@router.post(
    "/federation/analyze",
    response_model=FederatedAnalysisResponse,
    summary="Execute multi-dataset federated analysis with DuckDB",
)
async def execute_federated_analysis(
    request: FederatedAnalysisRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> FederatedAnalysisResponse:
    service = FederationService(db)
    try:
        return await service.execute_federated_analysis(current_user.id, request)
    except (FederationServiceError, FederatedPlannerError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
