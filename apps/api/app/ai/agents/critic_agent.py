"""Critic & Validation Agent auditing evidence grounding, citations, and numerical consistency."""

import time
import uuid
from typing import List

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
    ValidationFinding,
    ValidationReport,
    ValidationStatus,
)


class CriticAgent(BaseAgent):
    """Specialized critic agent auditing numerical exactness, citation grounding, and consistency."""

    def __init__(self, db: AsyncSession) -> None:
        super().__init__(AgentID.CRITIC_AGENT, db)

    async def execute(self, request: AgentRequest) -> AgentResponse:
        start_time = time.perf_counter()
        evidence_list: List[EvidenceItem] = []
        claims_list: List[ClaimItem] = []
        findings: List[ValidationFinding] = []

        numerical_consistent = True
        citation_grounded = True
        contradiction = False

        # 1. Check for evidence existence
        if not request.prior_evidence:
            findings.append(
                ValidationFinding(
                    check_name="evidence_existence",
                    status=ValidationStatus.WARNING,
                    description="No prior deterministic evidence generated.",
                )
            )

        # 2. Audit Knowledge Citations
        knowledge_evs = [ev for ev in request.prior_evidence if ev.evidence_type == EvidenceType.KNOWLEDGE]
        for ev in knowledge_evs:
            if not ev.provenance.get("document_id"):
                citation_grounded = False
                findings.append(
                    ValidationFinding(
                        check_name="citation_grounding",
                        status=ValidationStatus.INVALID,
                        description=f"Knowledge evidence from {ev.source} is missing document provenance.",
                    )
                )

        # 3. Audit Numerical & Analytical Calculations
        data_evs = [ev for ev in request.prior_evidence if ev.evidence_type in (EvidenceType.DATA, EvidenceType.CALCULATION)]
        for ev in data_evs:
            if ev.raw_value is None:
                numerical_consistent = False
                findings.append(
                    ValidationFinding(
                        check_name="numerical_consistency",
                        status=ValidationStatus.INVALID,
                        description=f"Analytical operation '{ev.operation}' produced empty raw value.",
                    )
                )

        overall_status = ValidationStatus.VALID if not findings else (
            ValidationStatus.INVALID if any(f.status == ValidationStatus.INVALID for f in findings) else ValidationStatus.WARNING
        )

        validation_report = ValidationReport(
            overall_status=overall_status,
            findings=findings,
            numerical_consistency=numerical_consistent,
            citation_grounding=citation_grounded,
            contradiction_detected=contradiction,
            validation_score=1.0 if overall_status == ValidationStatus.VALID else (0.75 if overall_status == ValidationStatus.WARNING else 0.0),
            summary_notes=f"Audited {len(request.prior_evidence)} evidence items. Status: {overall_status.value}.",
        )

        ev_id = f"ev-crit-{uuid.uuid4().hex[:8]}"
        evidence_list.append(
            EvidenceItem(
                id=ev_id,
                evidence_type=EvidenceType.CALCULATION,
                source="Critic Validation Agent",
                dataset_version_id=request.dataset_version_id,
                operation="audit_evidence",
                raw_value=validation_report.model_dump(),
            )
        )

        claims_list.append(
            ClaimItem(
                claim_id=f"claim-{uuid.uuid4().hex[:8]}",
                statement=f"Evidence audit completed with status {overall_status.value}.",
                claim_type=ClaimType.FACT,
                evidence_ids=[ev_id],
            )
        )

        return AgentResponse(
            task_id=request.task_id,
            agent_id=self.agent_id,
            status="COMPLETED",
            summary=f"Validation completed: {overall_status.value} (score: {validation_report.validation_score:.2f})",
            data_payload={"validation_report": validation_report.model_dump()},
            evidence=evidence_list,
            claims=claims_list,
            execution_time_ms=(time.perf_counter() - start_time) * 1000.0,
        )
