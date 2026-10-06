"""Hybrid semantic and keyword retrieval engine with metadata isolation and citation ranking."""

import math
import re
from typing import List, Tuple

from app.database.models.knowledge import KnowledgeChunk, KnowledgeDocument, KnowledgeDocumentVersion
from app.knowledge.embedding import EmbeddingProvider
from app.knowledge.schemas import KnowledgeCitation, KnowledgeSearchResultItem


class HybridRetriever:
    """Combines dense vector similarity with sparse keyword matching to rank knowledge chunks."""

    def __init__(self, embedding_provider: EmbeddingProvider) -> None:
        self.embedding_provider = embedding_provider

    @staticmethod
    def _cosine_similarity(vec1: List[float], vec2: List[float]) -> float:
        """Compute cosine similarity between two dense vectors."""
        if not vec1 or not vec2 or len(vec1) != len(vec2):
            return 0.0
        dot = sum(a * b for a, b in zip(vec1, vec2))
        norm1 = math.sqrt(sum(a * a for a in vec1))
        norm2 = math.sqrt(sum(b * b for b in vec2))
        if norm1 <= 1e-9 or norm2 <= 1e-9:
            return 0.0
        return max(0.0, min(1.0, dot / (norm1 * norm2)))

    @staticmethod
    def _keyword_similarity(query_tokens: List[str], chunk_text: str) -> float:
        """BM25-style keyword frequency overlap score with sub-stem matching."""
        if not query_tokens or not chunk_text:
            return 0.0

        chunk_tokens = [c.lower() for c in re.findall(r"\b\w+\b", chunk_text.lower())]
        if not chunk_tokens:
            return 0.0

        chunk_len = len(chunk_tokens)
        score = 0.0

        for q in query_tokens:
            q_lower = q.lower()
            q_stem = q_lower[:4] if len(q_lower) >= 4 else q_lower
            count = sum(
                1 for c in chunk_tokens if q_lower in c or c in q_lower or (len(q_stem) >= 4 and c.startswith(q_stem))
            )
            if count > 0:
                tf = (count * 2.2) / (count + 1.2 * (1.0 - 0.75 + 0.75 * (chunk_len / 100.0)))
                score += tf

        return min(1.0, score / max(1.0, len(query_tokens) * 0.8))

    def retrieve(
        self,
        query: str,
        candidates: List[Tuple[KnowledgeChunk, KnowledgeDocument, KnowledgeDocumentVersion]],
        top_k: int = 5,
        min_similarity: float = 0.25,
    ) -> Tuple[List[KnowledgeSearchResultItem], List[KnowledgeCitation], bool]:
        """Rank candidates using hybrid scoring and construct verifiable citations."""
        if not query or not candidates:
            return [], [], False

        query_embedding = self.embedding_provider.embed_text(query)
        query_tokens = [t for t in re.findall(r"\b\w+\b", query.lower()) if len(t) > 2]

        scored_items: List[Tuple[float, KnowledgeChunk, KnowledgeDocument, KnowledgeDocumentVersion]] = []

        for chunk, doc, ver in candidates:
            chunk_embedding = chunk.embedding_json if isinstance(chunk.embedding_json, list) else None
            vector_score = self._cosine_similarity(query_embedding, chunk_embedding) if chunk_embedding else 0.0
            keyword_score = self._keyword_similarity(query_tokens, chunk.content)

            # Combined Hybrid Score: 60% semantic vector + 40% exact keyword matching
            hybrid_score = (0.60 * vector_score) + (0.40 * keyword_score)

            # Boost exact title or heading match
            if doc.title.lower() in query.lower() or (
                chunk.section_heading and chunk.section_heading.lower() in query.lower()
            ):
                hybrid_score = min(1.0, hybrid_score + 0.15)

            if hybrid_score >= min_similarity:
                scored_items.append((hybrid_score, chunk, doc, ver))

        # Sort descending by hybrid score
        scored_items.sort(key=lambda x: x[0], reverse=True)
        top_results = scored_items[:top_k]

        results: List[KnowledgeSearchResultItem] = []
        citations: List[KnowledgeCitation] = []

        for idx, (score, chunk, doc, ver) in enumerate(top_results, start=1):
            citation_label = (
                f"[{doc.title}, p. {chunk.page_number}]"
                if chunk.page_number
                else f"[{doc.title}, {chunk.section_heading or 'General'}]"
            )

            results.append(
                KnowledgeSearchResultItem(
                    chunk_id=chunk.id,
                    document_id=doc.id,
                    document_title=doc.title,
                    document_version_id=ver.id,
                    version_number=ver.version_number,
                    chunk_index=chunk.chunk_index,
                    content=chunk.content,
                    page_number=chunk.page_number,
                    section_heading=chunk.section_heading,
                    similarity_score=round(score, 4),
                    citation_label=citation_label,
                    metadata=chunk.metadata_json or {},
                )
            )

            citations.append(
                KnowledgeCitation(
                    citation_index=idx,
                    document_id=doc.id,
                    document_title=doc.title,
                    document_version_id=ver.id,
                    version_number=ver.version_number,
                    page_number=chunk.page_number,
                    section_heading=chunk.section_heading,
                    chunk_id=chunk.id,
                    source_snippet=chunk.content[:200] + ("…" if len(chunk.content) > 200 else ""),
                    similarity_score=round(score, 4),
                )
            )

        has_sufficient_evidence = len(results) > 0
        return results, citations, has_sufficient_evidence
