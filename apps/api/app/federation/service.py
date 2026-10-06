"""Service layer for Phase 10 Multi-Dataset Collections, Relationships & Federated Intelligence."""

import uuid
from typing import Dict, List, Optional, Tuple

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.analytics.duckdb.manager import DuckDBManager
from app.database.models.dataset import Dataset, DatasetVersion
from app.database.models.federation import (
    DatasetCollection,
    DatasetCollectionItem,
    DatasetRelationship,
    RelationshipStatus,
)
from app.database.models.profiling import DatasetProfile
from app.datasets.storage import get_storage_provider
from app.federation.engine import RelationshipEngine
from app.federation.planner import FederatedQueryPlanner
from app.federation.schemas import (
    DatasetCollectionCreateRequest,
    DatasetCollectionItemResponse,
    DatasetCollectionResponse,
    DiscoveredRelationshipCandidate,
    DiscoveryResponse,
    FederatedAnalysisRequest,
    FederatedAnalysisResponse,
    RelationshipProposeRequest,
    RelationshipResponse,
)


class FederationServiceError(Exception):
    """Business logic or authorization error in Federation Service."""

    pass


class FederationService:
    """Central service orchestrating dataset collections, relationship discovery, validation, and federation."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.duckdb_mgr = DuckDBManager.get_instance()

    # --- Collections CRUD ---

    async def create_collection(self, user_id: str, req: DatasetCollectionCreateRequest) -> DatasetCollectionResponse:
        """Create a new dataset collection / workspace."""
        collection = DatasetCollection(
            id=str(uuid.uuid4()),
            name=req.name,
            description=req.description,
            user_id=user_id,
            metadata_json={},
        )
        self.db.add(collection)
        await self.db.flush()

        # Add initial datasets
        if req.dataset_ids:
            for d_id in req.dataset_ids:
                # Verify dataset belongs to user
                d_stmt = select(Dataset).where(Dataset.id == d_id, Dataset.owner_id == user_id)
                d_res = await self.db.execute(d_stmt)
                dataset = d_res.scalar_one_or_none()
                if not dataset:
                    continue

                # Get latest ready version
                v_stmt = (
                    select(DatasetVersion)
                    .where(DatasetVersion.dataset_id == d_id, DatasetVersion.status == "READY")
                    .order_by(DatasetVersion.version_number.desc())
                )
                v_res = await self.db.execute(v_stmt)
                latest_v = v_res.scalar_one_or_none()

                item = DatasetCollectionItem(
                    id=str(uuid.uuid4()),
                    collection_id=collection.id,
                    dataset_id=d_id,
                    dataset_version_id=latest_v.id if latest_v else None,
                )
                self.db.add(item)

        await self.db.commit()
        return await self.get_collection(user_id, collection.id)

    async def list_collections(self, user_id: str) -> List[DatasetCollectionResponse]:
        """List all collections owned by user."""
        stmt = (
            select(DatasetCollection)
            .where(DatasetCollection.user_id == user_id)
            .options(
                selectinload(DatasetCollection.items),
                selectinload(DatasetCollection.relationships),
            )
            .order_by(DatasetCollection.created_at.desc())
        )
        res = await self.db.execute(stmt)
        collections = res.scalars().all()
        return [self._to_collection_response(c) for c in collections]

    async def get_collection(self, user_id: str, collection_id: str) -> DatasetCollectionResponse:
        """Get collection details with items and relationships."""
        stmt = (
            select(DatasetCollection)
            .where(DatasetCollection.id == collection_id, DatasetCollection.user_id == user_id)
            .options(
                selectinload(DatasetCollection.items),
                selectinload(DatasetCollection.relationships),
            )
        )
        res = await self.db.execute(stmt)
        collection = res.scalar_one_or_none()
        if not collection:
            raise FederationServiceError(f"Collection {collection_id} not found or unauthorized.")
        return self._to_collection_response(collection)

    async def delete_collection(self, user_id: str, collection_id: str) -> None:
        """Delete a collection and its associations."""
        stmt = select(DatasetCollection).where(
            DatasetCollection.id == collection_id, DatasetCollection.user_id == user_id
        )
        res = await self.db.execute(stmt)
        collection = res.scalar_one_or_none()
        if not collection:
            raise FederationServiceError(f"Collection {collection_id} not found.")
        await self.db.delete(collection)
        await self.db.commit()

    async def add_dataset_to_collection(
        self, user_id: str, collection_id: str, dataset_id: str
    ) -> DatasetCollectionResponse:
        """Add a dataset to a collection."""
        # 1. Verify collection ownership
        c_stmt = select(DatasetCollection).where(
            DatasetCollection.id == collection_id, DatasetCollection.user_id == user_id
        )
        c_res = await self.db.execute(c_stmt)
        if not c_res.scalar_one_or_none():
            raise FederationServiceError("Collection not found or unauthorized.")

        # 2. Verify dataset ownership
        d_stmt = select(Dataset).where(Dataset.id == dataset_id, Dataset.owner_id == user_id)
        d_res = await self.db.execute(d_stmt)
        if not d_res.scalar_one_or_none():
            raise FederationServiceError("Dataset not found or unauthorized.")

        # 3. Check if already present
        existing_stmt = select(DatasetCollectionItem).where(
            DatasetCollectionItem.collection_id == collection_id,
            DatasetCollectionItem.dataset_id == dataset_id,
        )
        existing_res = await self.db.execute(existing_stmt)
        if existing_res.scalar_one_or_none():
            return await self.get_collection(user_id, collection_id)

        # 4. Get latest version
        v_stmt = (
            select(DatasetVersion)
            .where(DatasetVersion.dataset_id == dataset_id, DatasetVersion.status == "READY")
            .order_by(DatasetVersion.version_number.desc())
        )
        v_res = await self.db.execute(v_stmt)
        latest_v = v_res.scalar_one_or_none()

        item = DatasetCollectionItem(
            id=str(uuid.uuid4()),
            collection_id=collection_id,
            dataset_id=dataset_id,
            dataset_version_id=latest_v.id if latest_v else None,
        )
        self.db.add(item)
        await self.db.commit()
        return await self.get_collection(user_id, collection_id)

    async def remove_dataset_from_collection(
        self, user_id: str, collection_id: str, dataset_id: str
    ) -> DatasetCollectionResponse:
        """Remove a dataset from a collection."""
        stmt = delete(DatasetCollectionItem).where(
            DatasetCollectionItem.collection_id == collection_id,
            DatasetCollectionItem.dataset_id == dataset_id,
        )
        await self.db.execute(stmt)
        await self.db.commit()
        return await self.get_collection(user_id, collection_id)

    # --- Relationships Discovery, Validation & Management ---

    async def discover_relationships_in_collection(self, user_id: str, collection_id: str) -> DiscoveryResponse:
        """Discover candidate relationships among all datasets in a collection."""
        collection = await self.get_collection(user_id, collection_id)
        dataset_ids = [item.dataset_id for item in collection.items]

        if len(dataset_ids) < 2:
            return DiscoveryResponse(candidates=[], total=0)

        # Fetch latest profiles for each dataset
        profiles_map: Dict[str, Tuple[DatasetProfile, str]] = {}
        for d_id in dataset_ids:
            p_stmt = (
                select(DatasetProfile, Dataset.name)
                .join(DatasetVersion, DatasetProfile.dataset_version_id == DatasetVersion.id)
                .join(Dataset, DatasetVersion.dataset_id == Dataset.id)
                .where(Dataset.id == d_id)
                .options(selectinload(DatasetProfile.column_profiles))
                .order_by(DatasetProfile.created_at.desc())
            )
            p_res = await self.db.execute(p_stmt)
            p_row = p_res.first()
            if p_row:
                profiles_map[d_id] = (p_row[0], p_row[1])

        all_candidates: List[DiscoveredRelationshipCandidate] = []
        d_list = list(profiles_map.keys())

        for i in range(len(d_list)):
            for j in range(i + 1, len(d_list)):
                s_id = d_list[i]
                t_id = d_list[j]
                s_prof, s_name = profiles_map[s_id]
                t_prof, t_name = profiles_map[t_id]

                cands = RelationshipEngine.discover_candidate_relationships(
                    source_profile=s_prof,
                    target_profile=t_prof,
                    source_dataset_id=s_id,
                    source_dataset_name=s_name,
                    target_dataset_id=t_id,
                    target_dataset_name=t_name,
                )
                all_candidates.extend(cands)

        return DiscoveryResponse(candidates=all_candidates, total=len(all_candidates))

    async def propose_relationship(self, user_id: str, req: RelationshipProposeRequest) -> RelationshipResponse:
        """Propose or register a new dataset relationship."""
        # 1. Verify ownership of source & target datasets
        s_stmt = select(Dataset).where(Dataset.id == req.source_dataset_id, Dataset.owner_id == user_id)
        t_stmt = select(Dataset).where(Dataset.id == req.target_dataset_id, Dataset.owner_id == user_id)
        s_res = await self.db.execute(s_stmt)
        t_res = await self.db.execute(t_stmt)

        if not s_res.scalar_one_or_none() or not t_res.scalar_one_or_none():
            raise FederationServiceError("Source or target dataset not found or unauthorized.")

        rel = DatasetRelationship(
            id=str(uuid.uuid4()),
            collection_id=req.collection_id,
            user_id=user_id,
            source_dataset_id=req.source_dataset_id,
            source_version_id=req.source_version_id,
            source_field=req.source_field,
            target_dataset_id=req.target_dataset_id,
            target_version_id=req.target_version_id,
            target_field=req.target_field,
            relationship_type=req.relationship_type,
            status=RelationshipStatus.PROPOSED,
            coverage_ratio=0.0,
            quality_score=0.0,
            evidence={},
        )
        self.db.add(rel)
        await self.db.commit()
        await self.db.refresh(rel)

        # Auto-validate immediately
        return await self.validate_relationship(user_id, rel.id)

    async def validate_relationship(self, user_id: str, relationship_id: str) -> RelationshipResponse:
        """Execute DuckDB validation of referential integrity and update metrics."""
        stmt = select(DatasetRelationship).where(
            DatasetRelationship.id == relationship_id, DatasetRelationship.user_id == user_id
        )
        res = await self.db.execute(stmt)
        rel = res.scalar_one_or_none()
        if not rel:
            raise FederationServiceError(f"Relationship {relationship_id} not found.")

        # Fetch file paths of source & target versions
        sv_stmt = select(DatasetVersion).where(DatasetVersion.id == rel.source_version_id)
        tv_stmt = select(DatasetVersion).where(DatasetVersion.id == rel.target_version_id)
        s_v = (await self.db.execute(sv_stmt)).scalar_one_or_none()
        t_v = (await self.db.execute(tv_stmt)).scalar_one_or_none()

        if not s_v or not t_v:
            raise FederationServiceError("Source or target dataset version file not found.")

        # Resolve physical storage paths
        storage = get_storage_provider()
        source_path = str(getattr(s_v, "file_path", None) or storage.get_file_path(s_v.storage_reference))
        target_path = str(getattr(t_v, "file_path", None) or storage.get_file_path(t_v.storage_reference))

        # Execute DuckDB validation
        metrics = RelationshipEngine.validate_relationship_data(
            duckdb_manager=self.duckdb_mgr,
            source_version_id=s_v.id,
            source_file_path=source_path,
            source_format=s_v.file_format.value if hasattr(s_v.file_format, "value") else str(s_v.file_format),
            source_field=rel.source_field,
            target_version_id=t_v.id,
            target_file_path=target_path,
            target_format=t_v.file_format.value if hasattr(t_v.file_format, "value") else str(t_v.file_format),
            target_field=rel.target_field,
        )

        rel.relationship_type = metrics["relationship_type"]
        rel.coverage_ratio = metrics["coverage_ratio"]
        rel.source_unique_ratio = metrics["source_unique_ratio"]
        rel.target_unique_ratio = metrics["target_unique_ratio"]
        rel.null_rate = metrics["null_rate"]
        rel.quality_score = metrics["quality_score"]
        rel.evidence = metrics["evidence"]

        # Automatically mark as VALIDATED if referential coverage > 0.0
        if rel.coverage_ratio > 0.0:
            rel.status = RelationshipStatus.VALIDATED
        else:
            rel.status = RelationshipStatus.PROPOSED

        await self.db.commit()
        await self.db.refresh(rel)
        return RelationshipResponse.model_validate(rel)

    async def update_relationship_status(
        self, user_id: str, relationship_id: str, new_status: RelationshipStatus
    ) -> RelationshipResponse:
        """Manually approve, reject or disable a relationship."""
        stmt = select(DatasetRelationship).where(
            DatasetRelationship.id == relationship_id, DatasetRelationship.user_id == user_id
        )
        res = await self.db.execute(stmt)
        rel = res.scalar_one_or_none()
        if not rel:
            raise FederationServiceError(f"Relationship {relationship_id} not found.")

        rel.status = new_status
        await self.db.commit()
        await self.db.refresh(rel)
        return RelationshipResponse.model_validate(rel)

    async def list_relationships(
        self,
        user_id: str,
        collection_id: Optional[str] = None,
        status: Optional[RelationshipStatus] = None,
    ) -> List[RelationshipResponse]:
        """List relationships matching criteria."""
        stmt = select(DatasetRelationship).where(DatasetRelationship.user_id == user_id)
        if collection_id:
            stmt = stmt.where(DatasetRelationship.collection_id == collection_id)
        if status:
            stmt = stmt.where(DatasetRelationship.status == status)

        stmt = stmt.order_by(DatasetRelationship.created_at.desc())
        res = await self.db.execute(stmt)
        return [RelationshipResponse.model_validate(r) for r in res.scalars().all()]

    async def delete_relationship(self, user_id: str, relationship_id: str) -> None:
        """Delete a relationship record."""
        stmt = delete(DatasetRelationship).where(
            DatasetRelationship.id == relationship_id, DatasetRelationship.user_id == user_id
        )
        await self.db.execute(stmt)
        await self.db.commit()

    # --- Federated Analysis Execution ---

    async def execute_federated_analysis(
        self, user_id: str, request: FederatedAnalysisRequest
    ) -> FederatedAnalysisResponse:
        """Execute safe multi-dataset federated analysis."""
        # 1. Verify and fetch all requested dataset versions
        v_stmt = (
            select(DatasetVersion)
            .join(Dataset, DatasetVersion.dataset_id == Dataset.id)
            .where(
                DatasetVersion.id.in_(request.dataset_version_ids),
                Dataset.owner_id == user_id,
            )
            .options(selectinload(DatasetVersion.dataset))
        )
        v_res = await self.db.execute(v_stmt)
        dataset_versions = v_res.scalars().all()

        if len(dataset_versions) != len(request.dataset_version_ids):
            raise FederationServiceError("One or more dataset versions are invalid or unauthorized.")

        dataset_ids = [dv.dataset_id for dv in dataset_versions]

        # 2. Fetch all validated relationships among these datasets
        rel_stmt = select(DatasetRelationship).where(
            DatasetRelationship.user_id == user_id,
            DatasetRelationship.status == RelationshipStatus.VALIDATED,
            DatasetRelationship.source_dataset_id.in_(dataset_ids),
            DatasetRelationship.target_dataset_id.in_(dataset_ids),
        )
        rel_res = await self.db.execute(rel_stmt)
        validated_relationships = rel_res.scalars().all()

        # 3. Delegate to FederatedQueryPlanner
        return FederatedQueryPlanner.plan_and_execute(
            duckdb_manager=self.duckdb_mgr,
            request=request,
            dataset_versions=dataset_versions,
            validated_relationships=validated_relationships,
        )

    # --- Helpers ---

    def _to_collection_response(self, c: DatasetCollection) -> DatasetCollectionResponse:
        return DatasetCollectionResponse(
            id=c.id,
            name=c.name,
            description=c.description,
            user_id=c.user_id,
            metadata_json=c.metadata_json or {},
            items=[DatasetCollectionItemResponse.model_validate(item) for item in c.items],
            relationships=[RelationshipResponse.model_validate(rel) for rel in c.relationships],
            created_at=c.created_at,
            updated_at=c.updated_at,
        )
