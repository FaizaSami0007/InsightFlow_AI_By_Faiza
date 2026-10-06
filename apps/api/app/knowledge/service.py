"""Service layer managing business knowledge document ingestion, indexing, and hybrid retrieval."""

import hashlib
import time
from typing import List, Optional, Tuple

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.database.models.dataset import Dataset
from app.database.models.knowledge import (
    DatasetKnowledgeLink,
    DocumentProcessingStatus,
    DocumentType,
    KnowledgeChunk,
    KnowledgeCollection,
    KnowledgeDocument,
    KnowledgeDocumentVersion,
    KnowledgeType,
)
from app.datasets.storage import get_storage_provider
from app.knowledge.chunker import DocumentChunker
from app.knowledge.embedding import get_embedding_provider
from app.knowledge.extractor import DocumentExtractor
from app.knowledge.retriever import HybridRetriever
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


class KnowledgeServiceError(Exception):
    """Domain exception raised during knowledge service operations."""

    pass


class KnowledgeService:
    """Orchestrates end-to-end knowledge lifecycle: ingestion, chunking, embedding, search, and provenance."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.storage = get_storage_provider()
        self.chunker = DocumentChunker()
        self.embedding_provider = get_embedding_provider()
        self.retriever = HybridRetriever(self.embedding_provider)

    # ==========================================
    # 1. COLLECTIONS MANAGEMENT
    # ==========================================

    async def create_collection(
        self, user_id: str, request: KnowledgeCollectionCreateRequest
    ) -> KnowledgeCollectionResponse:
        """Create a new domain knowledge collection for the authorized user."""
        collection = KnowledgeCollection(
            user_id=user_id,
            name=request.name.strip(),
            description=request.description.strip() if request.description else None,
            metadata_json=request.metadata or {},
        )
        self.db.add(collection)
        await self.db.commit()
        await self.db.refresh(collection)

        return KnowledgeCollectionResponse(
            id=collection.id,
            user_id=collection.user_id,
            name=collection.name,
            description=collection.description,
            is_system=collection.is_system,
            document_count=0,
            metadata_json=collection.metadata_json or {},
            created_at=collection.created_at,
            updated_at=collection.updated_at,
        )

    async def list_collections(self, user_id: str) -> List[KnowledgeCollectionResponse]:
        """List all collections belonging to the current user with document counts."""
        stmt = (
            select(KnowledgeCollection)
            .where(KnowledgeCollection.user_id == user_id)
            .options(selectinload(KnowledgeCollection.documents))
            .order_by(KnowledgeCollection.created_at.desc())
        )
        res = await self.db.execute(stmt)
        collections = res.scalars().all()

        return [
            KnowledgeCollectionResponse(
                id=c.id,
                user_id=c.user_id,
                name=c.name,
                description=c.description,
                is_system=c.is_system,
                document_count=len(c.documents),
                metadata_json=c.metadata_json or {},
                created_at=c.created_at,
                updated_at=c.updated_at,
            )
            for c in collections
        ]

    async def delete_collection(self, user_id: str, collection_id: str) -> bool:
        """Delete a collection belonging to the user."""
        stmt = select(KnowledgeCollection).where(
            KnowledgeCollection.id == collection_id, KnowledgeCollection.user_id == user_id
        )
        res = await self.db.execute(stmt)
        col = res.scalar_one_or_none()
        if not col:
            raise KnowledgeServiceError(f"Collection {collection_id} not found or access denied.")

        await self.db.delete(col)
        await self.db.commit()
        return True

    # ==========================================
    # 2. DOCUMENT INGESTION & PIPELINE
    # ==========================================

    async def ingest_document(
        self,
        user_id: str,
        filename: str,
        file_bytes: bytes,
        title: Optional[str] = None,
        collection_id: Optional[str] = None,
        knowledge_type: KnowledgeType = KnowledgeType.GENERAL_POLICY,
    ) -> KnowledgeDocumentResponse:
        """Ingests, extracts, chunks, and embeds a knowledge document."""
        if not file_bytes:
            raise KnowledgeServiceError("Cannot ingest an empty document.")

        checksum = hashlib.sha256(file_bytes).hexdigest()
        clean_filename = filename.strip()
        doc_title = (title or clean_filename).strip()

        # Validate collection if specified
        if collection_id:
            c_stmt = select(KnowledgeCollection).where(
                KnowledgeCollection.id == collection_id, KnowledgeCollection.user_id == user_id
            )
            c_res = await self.db.execute(c_stmt)
            if not c_res.scalar_one_or_none():
                raise KnowledgeServiceError(f"Collection {collection_id} not found or access denied.")

        # Determine file type
        ext = clean_filename.split(".")[-1].upper() if "." in clean_filename else "TXT"
        if "PDF" in ext:
            file_type = DocumentType.PDF
        elif "DOC" in ext:
            file_type = DocumentType.DOCX
        elif "MD" in ext or "MARKDOWN" in ext:
            file_type = DocumentType.MARKDOWN
        elif "CSV" in ext:
            file_type = DocumentType.CSV_REFERENCE
        else:
            file_type = DocumentType.TXT

        # 1. Save file to storage
        storage_ref = self.storage.save_file(file_bytes, clean_filename)

        # 2. Check for existing document with same filename / title under user
        existing_stmt = select(KnowledgeDocument).where(
            KnowledgeDocument.user_id == user_id,
            KnowledgeDocument.filename == clean_filename,
        )
        existing_res = await self.db.execute(existing_stmt)
        existing_doc = existing_res.scalar_one_or_none()

        if existing_doc:
            doc = existing_doc
            doc.current_version_num += 1
            doc.storage_reference = storage_ref
            doc.checksum = checksum
            doc.status = DocumentProcessingStatus.EXTRACTING
            if collection_id:
                doc.collection_id = collection_id
        else:
            doc = KnowledgeDocument(
                user_id=user_id,
                collection_id=collection_id,
                title=doc_title,
                filename=clean_filename,
                file_type=file_type,
                file_size_bytes=len(file_bytes),
                storage_reference=storage_ref,
                checksum=checksum,
                knowledge_type=knowledge_type,
                status=DocumentProcessingStatus.EXTRACTING,
                current_version_num=1,
            )
            self.db.add(doc)

        await self.db.commit()
        await self.db.refresh(doc)

        # 3. Extraction
        try:
            extraction = DocumentExtractor.extract(file_bytes, clean_filename, file_type)
        except Exception as exc:
            doc.status = DocumentProcessingStatus.FAILED
            doc.error_message = f"Extraction failed: {exc}"
            await self.db.commit()
            raise KnowledgeServiceError(f"Document extraction error: {exc}")

        # 4. Chunking
        doc.status = DocumentProcessingStatus.CHUNKED
        chunks = self.chunker.chunk_sections(extraction.sections)

        # 5. Create Version Record
        doc_version = KnowledgeDocumentVersion(
            document_id=doc.id,
            version_number=doc.current_version_num,
            storage_reference=storage_ref,
            checksum=checksum,
            extracted_text_length=extraction.total_characters,
            chunk_count=len(chunks),
            is_ocr=extraction.is_ocr,
            ocr_confidence=extraction.ocr_confidence,
            status=DocumentProcessingStatus.EMBEDDED,
        )
        self.db.add(doc_version)
        await self.db.commit()
        await self.db.refresh(doc_version)

        # 6. Embedding & Indexing
        for c in chunks:
            embedding_vec = self.embedding_provider.embed_text(c.content)
            chunk_record = KnowledgeChunk(
                document_id=doc.id,
                document_version_id=doc_version.id,
                chunk_index=c.chunk_index,
                content=c.content,
                token_count=c.token_count,
                page_number=c.page_number,
                section_heading=c.section_heading,
                embedding_json=embedding_vec,
                metadata_json=c.metadata,
            )
            self.db.add(chunk_record)

        doc.status = DocumentProcessingStatus.READY
        doc_version.status = DocumentProcessingStatus.READY
        await self.db.commit()
        await self.db.refresh(doc)

        return KnowledgeDocumentResponse(
            id=doc.id,
            collection_id=doc.collection_id,
            user_id=doc.user_id,
            title=doc.title,
            filename=doc.filename,
            file_type=doc.file_type,
            file_size_bytes=doc.file_size_bytes,
            checksum=doc.checksum,
            knowledge_type=doc.knowledge_type,
            status=doc.status,
            current_version_num=doc.current_version_num,
            chunk_count=len(chunks),
            metadata=doc.metadata_json or {},
            created_at=doc.created_at,
            updated_at=doc.updated_at,
        )

    async def list_documents(
        self,
        user_id: str,
        collection_id: Optional[str] = None,
        knowledge_type: Optional[KnowledgeType] = None,
    ) -> KnowledgeDocumentListResponse:
        """List documents owned by the user with optional collection filtering."""
        stmt = (
            select(KnowledgeDocument)
            .where(KnowledgeDocument.user_id == user_id)
            .options(selectinload(KnowledgeDocument.collection), selectinload(KnowledgeDocument.chunks))
            .order_by(KnowledgeDocument.created_at.desc())
        )
        if collection_id:
            stmt = stmt.where(KnowledgeDocument.collection_id == collection_id)
        if knowledge_type:
            stmt = stmt.where(KnowledgeDocument.knowledge_type == knowledge_type)

        res = await self.db.execute(stmt)
        docs = res.scalars().all()

        items = [
            KnowledgeDocumentResponse(
                id=d.id,
                collection_id=d.collection_id,
                collection_name=d.collection.name if d.collection else None,
                user_id=d.user_id,
                title=d.title,
                filename=d.filename,
                file_type=d.file_type,
                file_size_bytes=d.file_size_bytes,
                checksum=d.checksum,
                knowledge_type=d.knowledge_type,
                status=d.status,
                current_version_num=d.current_version_num,
                chunk_count=len(d.chunks),
                error_message=d.error_message,
                metadata=d.metadata_json or {},
                created_at=d.created_at,
                updated_at=d.updated_at,
            )
            for d in docs
        ]

        return KnowledgeDocumentListResponse(items=items, total=len(items))

    async def get_document(self, user_id: str, document_id: str) -> KnowledgeDocumentResponse:
        """Retrieve a single knowledge document with authorization verification."""
        stmt = (
            select(KnowledgeDocument)
            .where(KnowledgeDocument.id == document_id, KnowledgeDocument.user_id == user_id)
            .options(selectinload(KnowledgeDocument.collection), selectinload(KnowledgeDocument.chunks))
        )
        res = await self.db.execute(stmt)
        d = res.scalar_one_or_none()
        if not d:
            raise KnowledgeServiceError(f"Document {document_id} not found or unauthorized.")

        return KnowledgeDocumentResponse(
            id=d.id,
            collection_id=d.collection_id,
            collection_name=d.collection.name if d.collection else None,
            user_id=d.user_id,
            title=d.title,
            filename=d.filename,
            file_type=d.file_type,
            file_size_bytes=d.file_size_bytes,
            checksum=d.checksum,
            knowledge_type=d.knowledge_type,
            status=d.status,
            current_version_num=d.current_version_num,
            chunk_count=len(d.chunks),
            error_message=d.error_message,
            metadata=d.metadata_json or {},
            created_at=d.created_at,
            updated_at=d.updated_at,
        )

    async def get_document_chunks(self, user_id: str, document_id: str) -> List[KnowledgeChunkResponse]:
        """Retrieve indexed chunks for a given document."""
        # Verify document ownership
        await self.get_document(user_id, document_id)

        stmt = (
            select(KnowledgeChunk)
            .where(KnowledgeChunk.document_id == document_id)
            .order_by(KnowledgeChunk.chunk_index.asc())
        )
        res = await self.db.execute(stmt)
        chunks = res.scalars().all()

        return [
            KnowledgeChunkResponse(
                id=c.id,
                document_id=c.document_id,
                document_version_id=c.document_version_id,
                chunk_index=c.chunk_index,
                content=c.content,
                token_count=c.token_count,
                page_number=c.page_number,
                section_heading=c.section_heading,
                has_embedding=bool(c.embedding_json),
                metadata=c.metadata_json or {},
                created_at=c.created_at,
            )
            for c in chunks
        ]

    async def get_document_versions(self, user_id: str, document_id: str) -> List[KnowledgeDocumentVersionResponse]:
        """Retrieve version history for a given document."""
        await self.get_document(user_id, document_id)

        stmt = (
            select(KnowledgeDocumentVersion)
            .where(KnowledgeDocumentVersion.document_id == document_id)
            .order_by(KnowledgeDocumentVersion.version_number.desc())
        )
        res = await self.db.execute(stmt)
        versions = res.scalars().all()

        return [
            KnowledgeDocumentVersionResponse(
                id=v.id,
                document_id=v.document_id,
                version_number=v.version_number,
                storage_reference=v.storage_reference,
                checksum=v.checksum,
                extracted_text_length=v.extracted_text_length,
                chunk_count=v.chunk_count,
                is_ocr=v.is_ocr,
                ocr_confidence=v.ocr_confidence,
                status=v.status,
                created_at=v.created_at,
            )
            for v in versions
        ]

    async def delete_document(self, user_id: str, document_id: str) -> bool:
        """Delete document, version history, and indexed chunks."""
        stmt = select(KnowledgeDocument).where(
            KnowledgeDocument.id == document_id, KnowledgeDocument.user_id == user_id
        )
        res = await self.db.execute(stmt)
        doc = res.scalar_one_or_none()
        if not doc:
            raise KnowledgeServiceError(f"Document {document_id} not found or unauthorized.")

        await self.db.delete(doc)
        await self.db.commit()
        return True

    # ==========================================
    # 3. DATASET LINKING
    # ==========================================

    async def link_dataset(self, user_id: str, request: DatasetKnowledgeLinkRequest) -> DatasetKnowledgeLinkResponse:
        """Associate a dataset with a knowledge document or collection."""
        # Verify dataset ownership
        d_stmt = select(Dataset).where(Dataset.id == request.dataset_id, Dataset.owner_id == user_id)
        d_res = await self.db.execute(d_stmt)
        if not d_res.scalar_one_or_none():
            raise KnowledgeServiceError(f"Dataset {request.dataset_id} not found or unauthorized.")

        link = DatasetKnowledgeLink(
            dataset_id=request.dataset_id,
            dataset_version_id=request.dataset_version_id,
            document_id=request.document_id,
            collection_id=request.collection_id,
            user_id=user_id,
            relationship_nature=request.relationship_nature,
        )
        self.db.add(link)
        await self.db.commit()
        await self.db.refresh(link)

        doc_title = None
        if link.document_id:
            doc_stmt = select(KnowledgeDocument.title).where(KnowledgeDocument.id == link.document_id)
            doc_res = await self.db.execute(doc_stmt)
            doc_title = doc_res.scalar_one_or_none()

        col_name = None
        if link.collection_id:
            col_stmt = select(KnowledgeCollection.name).where(KnowledgeCollection.id == link.collection_id)
            col_res = await self.db.execute(col_stmt)
            col_name = col_res.scalar_one_or_none()

        return DatasetKnowledgeLinkResponse(
            id=link.id,
            dataset_id=link.dataset_id,
            dataset_version_id=link.dataset_version_id,
            document_id=link.document_id,
            document_title=doc_title,
            collection_id=link.collection_id,
            collection_name=col_name,
            relationship_nature=link.relationship_nature,
            created_at=link.created_at,
        )

    # ==========================================
    # 4. HYBRID SEARCH & CITATIONS
    # ==========================================

    async def search(self, user_id: str, request: KnowledgeSearchRequest) -> KnowledgeSearchResponse:
        """Perform hybrid search over user's authorized knowledge documents."""
        t_start = time.perf_counter()

        # Build candidate query
        stmt = (
            select(KnowledgeChunk, KnowledgeDocument, KnowledgeDocumentVersion)
            .join(KnowledgeDocument, KnowledgeChunk.document_id == KnowledgeDocument.id)
            .join(KnowledgeDocumentVersion, KnowledgeChunk.document_version_id == KnowledgeDocumentVersion.id)
            .where(KnowledgeDocument.user_id == user_id, KnowledgeDocument.status == DocumentProcessingStatus.READY)
        )

        if request.collection_id:
            stmt = stmt.where(KnowledgeDocument.collection_id == request.collection_id)
        if request.document_ids:
            stmt = stmt.where(KnowledgeDocument.id.in_(request.document_ids))
        if request.knowledge_types:
            stmt = stmt.where(KnowledgeDocument.knowledge_type.in_(request.knowledge_types))

        # Filter by dataset links if dataset_id provided
        if request.dataset_id:
            link_stmt = select(DatasetKnowledgeLink).where(
                DatasetKnowledgeLink.dataset_id == request.dataset_id, DatasetKnowledgeLink.user_id == user_id
            )
            link_res = await self.db.execute(link_stmt)
            links = link_res.scalars().all()
            linked_doc_ids = [link_item.document_id for link_item in links if link_item.document_id]
            linked_col_ids = [link_item.collection_id for link_item in links if link_item.collection_id]

            if linked_doc_ids or linked_col_ids:
                stmt = stmt.where(
                    (KnowledgeDocument.id.in_(linked_doc_ids))
                    | (KnowledgeDocument.collection_id.in_(linked_col_ids))
                )

        res = await self.db.execute(stmt)
        candidates: List[Tuple[KnowledgeChunk, KnowledgeDocument, KnowledgeDocumentVersion]] = res.all()  # type: ignore[assignment]

        results, citations, has_sufficient = self.retriever.retrieve(
            query=request.query,
            candidates=candidates,
            top_k=request.top_k,
            min_similarity=request.min_similarity,
        )

        t_elapsed_ms = round((time.perf_counter() - t_start) * 1000, 2)

        notice = None
        if not has_sufficient:
            notice = "The available business knowledge base does not contain sufficient grounded evidence for this query."

        return KnowledgeSearchResponse(
            query=request.query,
            results_count=len(results),
            execution_time_ms=t_elapsed_ms,
            results=results,
            citations=citations,
            has_sufficient_evidence=has_sufficient,
            notice=notice,
        )
