"""Result Synthesizer constructing grounded responses with explicit role separation."""

from typing import Any, Dict, List, Optional

from app.ai.agents.contracts import (
    AgentResponse,
    ClaimType,
    ValidationReport,
)


class ResultSynthesizer:
    """Combines multi-agent evidence and claims into a coherent, verifiable answer."""

    @classmethod
    def synthesize(
        cls,
        query: str,
        agent_responses: List[AgentResponse],
        validation_report: Optional[ValidationReport] = None,
    ) -> Dict[str, Any]:
        data_facts: List[str] = []
        knowledge_facts: List[str] = []
        calculations: List[str] = []
        assumptions: List[str] = []
        recommendations: List[str] = []
        citations: List[Dict[str, Any]] = []
        visualization: Optional[Dict[str, Any]] = None
        evidence_summary: List[Dict[str, Any]] = []

        for resp in agent_responses:
            if resp.data_payload.get("visualization"):
                visualization = resp.data_payload["visualization"]

            if resp.citations:
                citations.extend(resp.citations)

            for claim in resp.claims:
                if claim.claim_type == ClaimType.FACT:
                    # check if from knowledge or data
                    if any("know" in ev_id for ev_id in claim.evidence_ids):
                        knowledge_facts.append(f"{claim.statement} {claim.citation_label or ''}".strip())
                    else:
                        data_facts.append(claim.statement)
                elif claim.claim_type == ClaimType.CALCULATION:
                    calculations.append(claim.statement)
                elif claim.claim_type == ClaimType.ASSUMPTION:
                    assumptions.append(claim.statement)
                elif claim.claim_type == ClaimType.RECOMMENDATION:
                    recommendations.append(claim.statement)
                elif claim.claim_type == ClaimType.FORECAST:
                    calculations.append(f"[FORECAST] {claim.statement}")

            for ev in resp.evidence:
                evidence_summary.append({
                    "id": ev.id,
                    "type": ev.evidence_type.value,
                    "source": ev.source,
                    "operation": ev.operation,
                    "provenance": ev.provenance,
                })

        # Build clean narrative sections
        narrative_parts: List[str] = []

        if data_facts or calculations:
            narrative_parts.append("### Analytical Findings")
            for item in data_facts + calculations:
                narrative_parts.append(f"- {item}")

        if knowledge_facts:
            narrative_parts.append("\n### Domain & Policy Context")
            for item in knowledge_facts:
                narrative_parts.append(f"- {item}")

        if assumptions:
            narrative_parts.append("\n### Simulated Assumptions")
            for item in assumptions:
                narrative_parts.append(f"- {item}")

        if recommendations:
            narrative_parts.append("\n### Recommendations & Next Steps")
            for item in recommendations:
                narrative_parts.append(f"- {item}")

        if not narrative_parts:
            primary_text = "InsightFlow AI analyzed your request across specialized agents."
        else:
            primary_text = "\n".join(narrative_parts)

        return {
            "content": primary_text,
            "citations": citations,
            "visualization": visualization,
            "evidence": evidence_summary,
            "validation_report": validation_report.model_dump() if validation_report else None,
            "agent_count": len(agent_responses),
        }
