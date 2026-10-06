"""Knowledge Agent retrieving business documents and generating grounded citations via hybrid RAG."""

import time
import uuid
from typing import Any, Dict, List

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.agents.base import BaseAgent
from app.ai.agents.contracts import (
    AgentID,
    AgentRequest,
    AgentResponse,
    ClaimItem,
    ClaimType,
    EvidenceItem,
    EvidenceType,
)
from app.knowledge.schemas import KnowledgeSearchRequest
from app.knowledge.service import KnowledgeService


class KnowledgeAgent(BaseAgent):
    """Specialized agent for retrieving domain context, KPI formulas, and business policies."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(AgentID.KNOWLEDGE_AGENT, db)
        self.service = KnowledgeService(db)

    async def execute(self, request: AgentRequest) -> AgentResponse:
        start_time = time.perf_counter()
        evidence_list: List[EvidenceItem] = []
        claims_list: List[ClaimItem] = []
        citations_list: List[Dict[str, Any]] = []

        query = request.context.get("query") or request.query
        top_k = request.context.get("top_k", 3)
        min_similarity = request.context.get("min_similarity", 0.15)

        if not self.is_tool_allowed("search_business_knowledge"):
            return AgentResponse(
                task_id=request.task_id,
                agent_id=self.agent_id,
                status="FAILED",
                summary="Tool 'search_business_knowledge' is not permitted.",
                error_message="Unauthorized tool execution",
                execution_time_ms=(time.perf_counter() - start_time) * 1000.0,
            )

        try:
            search_req = KnowledgeSearchRequest(
                query=query,
                dataset_id=request.dataset_id,
                top_k=top_k,
                min_similarity=min_similarity,
            )
            search_res = await self.service.search_knowledge(search_req, request.user_id)

            if not search_res.has_sufficient_evidence or not search_res.results:
                return AgentResponse(
                    task_id=request.task_id,
                    agent_id=self.agent_id,
                    status="COMPLETED",
                    summary="No sufficiently relevant business knowledge found in knowledge base.",
                    warnings=["Insufficient evidence in domain knowledge base for this query."],
                    data_payload={"has_sufficient_evidence": False, "results": []},
                    execution_time_ms=(time.perf_counter() - start_time) * 1000.0,
                )

            for idx, item in enumerate(search_res.results):
                ev_id = f"ev-know-{uuid.uuid4().hex[:8]}"
                evidence_list.append(
                    EvidenceItem(
                        id=ev_id,
                        evidence_type=EvidenceType.KNOWLEDGE,
                        source=item.document_title,
                        document_version_id=item.document_version_id,
                        operation="search_business_knowledge",
                        raw_value=item.content,
                        confidence=item.similarity_score,
                        provenance={
                            "document_id": item.document_id,
                            "version_number": item.version_number,
                            "page_number": item.page_number,
                            "section_heading": item.section_heading,
                        },
                    )
                )
                citation_label = f"[{item.document_title}, p. {item.page_number or 1}]"
                claims_list.append(
                    ClaimItem(
                        claim_id=f"claim-{uuid.uuid4().hex[:8]}",
                        statement=item.content,
                        claim_type=ClaimType.FACT,
                        evidence_ids=[ev_id],
                        confidence=item.similarity_score,
                        citation_label=citation_label,
                    )
                )
                citations_list.append(
                    {
                        "citation_index": idx + 1,
                        "document_title": item.document_title,
                        "version_number": item.version_number,
                        "page_number": item.page_number,
                        "section_heading": item.section_heading,
                        "snippet": item.content[:180] + "...",
                        "similarity_score": item.similarity_score,
                    }
                )

            summary_text = f"Retrieved {len(search_res.results)} grounded business knowledge excerpts."

            return AgentResponse(
                task_id=request.task_id,
                agent_id=self.agent_id,
                status="COMPLETED",
                summary=summary_text,
                data_payload={
                    "has_sufficient_evidence": True,
                    "results_count": len(search_res.results),
                },
                evidence=evidence_list,
                claims=claims_list,
                citations=citations_list,
                tool_calls_executed=[
                    {"tool": "search_business_knowledge", "query": query, "results_count": len(search_res.results)}
                ],
                execution_time_ms=(time.perf_counter() - start_time) * 1000.0,
            )
        except Exception as ex:
            return AgentResponse(
                task_id=request.task_id,
                agent_id=self.agent_id,
                status="FAILED",
                summary="Knowledge retrieval failed",
                error_message=str(ex),
                execution_time_ms=(time.perf_counter() - start_time) * 1000.0,
            )
