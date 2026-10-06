"""API endpoints for AI Analyst conversations and orchestration."""

import logging
from typing import List, Optional

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.orchestrator.orchestrator import AIOrchestrator
from app.ai.schemas import (
    ChatRequest,
    ChatResponse,
    ConversationCreate,
    ConversationListItem,
    ConversationResponse,
    MessageItem,
)
from app.core.exceptions import NotFoundError
from app.database.models.ai import AIConversation, AIMessage
from app.database.models.dataset import Dataset, DatasetVersion
from app.database.models.user import User
from app.database.session import get_db
from app.users.dependencies import get_current_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/ai", tags=["AI Analyst"])


@router.post("/conversations", response_model=ConversationResponse, status_code=status.HTTP_201_CREATED)
async def create_conversation(
    payload: ConversationCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationResponse:
    """Create a new AI conversation session for a specific dataset version."""
    # Verify dataset ownership
    stmt_dataset = select(Dataset).where(Dataset.id == payload.dataset_id, Dataset.owner_id == current_user.id)
    res_dataset = await db.execute(stmt_dataset)
    dataset = res_dataset.scalar_one_or_none()
    if not dataset:
        raise NotFoundError("Dataset not found or access unauthorized.")

    stmt_ver = select(DatasetVersion).where(
        DatasetVersion.id == payload.dataset_version_id,
        DatasetVersion.dataset_id == dataset.id,
    )
    res_ver = await db.execute(stmt_ver)
    version = res_ver.scalar_one_or_none()
    if not version:
        raise NotFoundError("Dataset version not found.")

    conversation = AIConversation(
        user_id=current_user.id,
        dataset_id=dataset.id,
        dataset_version_id=version.id,
        title=payload.title or f"Analysis for {dataset.name} v{version.version_number}",
    )
    db.add(conversation)
    await db.commit()
    await db.refresh(conversation)

    return ConversationResponse(
        id=conversation.id,
        dataset_id=conversation.dataset_id,
        dataset_version_id=conversation.dataset_version_id,
        title=conversation.title,
        created_at=conversation.created_at,
        updated_at=conversation.updated_at,
        messages=[],
    )


@router.get("/conversations", response_model=List[ConversationListItem])
async def list_conversations(
    dataset_id: Optional[str] = Query(None, description="Filter by dataset ID"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[ConversationListItem]:
    """List all AI conversations for the current user."""
    query = (
        select(
            AIConversation,
            func.count(AIMessage.id).label("message_count"),
        )
        .outerjoin(AIMessage, AIMessage.conversation_id == AIConversation.id)
        .where(AIConversation.user_id == current_user.id)
        .group_by(AIConversation.id)
        .order_by(AIConversation.updated_at.desc())
    )

    if dataset_id:
        query = query.where(AIConversation.dataset_id == dataset_id)

    res = await db.execute(query)
    results = res.all()

    items = []
    for conv, count in results:
        items.append(
            ConversationListItem(
                id=conv.id,
                dataset_id=conv.dataset_id,
                dataset_version_id=conv.dataset_version_id,
                title=conv.title,
                created_at=conv.created_at,
                updated_at=conv.updated_at,
                message_count=count,
            )
        )
    return items


@router.get("/conversations/{conversation_id}", response_model=ConversationResponse)
async def get_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ConversationResponse:
    """Retrieve an AI conversation and its message history."""
    stmt = (
        select(AIConversation)
        .options(selectinload(AIConversation.messages))
        .where(AIConversation.id == conversation_id, AIConversation.user_id == current_user.id)
    )
    res = await db.execute(stmt)
    conv = res.scalar_one_or_none()
    if not conv:
        raise NotFoundError("Conversation not found or access unauthorized.")

    messages = [
        MessageItem(
            id=m.id,
            role=m.role,
            content=m.content,
            tool_calls=m.tool_calls_json,
            tool_results=m.tool_results_json,
            analysis_ids=m.analysis_ids,
            visualization=m.visualization_json,
            created_at=m.created_at,
        )
        for m in conv.messages
    ]

    return ConversationResponse(
        id=conv.id,
        dataset_id=conv.dataset_id,
        dataset_version_id=conv.dataset_version_id,
        title=conv.title,
        created_at=conv.created_at,
        updated_at=conv.updated_at,
        messages=messages,
    )


@router.delete("/conversations/{conversation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_conversation(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """Delete an AI conversation."""
    stmt = select(AIConversation).where(AIConversation.id == conversation_id, AIConversation.user_id == current_user.id)
    res = await db.execute(stmt)
    conv = res.scalar_one_or_none()
    if not conv:
        raise NotFoundError("Conversation not found.")

    await db.delete(conv)
    await db.commit()


@router.get("/datasets/{dataset_id}/versions/{version_id}/starters", response_model=List[str])
async def get_starter_questions(
    dataset_id: str,
    version_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[str]:
    """Retrieve dynamic, schema-verified starter questions for the specified dataset version."""
    from app.ai.context.builder import ContextBuilder

    stmt = select(Dataset).where(Dataset.id == dataset_id, Dataset.owner_id == current_user.id)
    res = await db.execute(stmt)
    dataset = res.scalar_one_or_none()
    if not dataset:
        raise NotFoundError("Dataset not found.")

    return await ContextBuilder.generate_starter_questions(db, version_id)


@router.post("/chat", response_model=ChatResponse)
async def chat(
    payload: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ChatResponse:
    """
    Send an analytical inquiry to the AI Orchestrator.
    The orchestrator plans, executes deterministic analytical tools safely,
    and returns a grounded response with analytical provenance.
    """
    orchestrator = AIOrchestrator()
    return await orchestrator.chat(
        request=payload,
        user=current_user,
        db=db,
    )


@router.get("/agents")
async def list_registered_agents(
    current_user: User = Depends(get_current_user),
) -> List[dict]:
    """List all registered specialized agents, descriptions, capabilities, and tool allowlists."""
    from app.ai.agents.registry import agent_registry

    return [agent.model_dump() for agent in agent_registry.list_agents()]


@router.get("/conversations/{conversation_id}/tasks")
async def get_conversation_tasks(
    conversation_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> List[dict]:
    """Retrieve multi-agent task execution records and dependency graph nodes for a conversation."""
    from app.database.models.ai import AITask

    stmt = select(AITask).where(
        AITask.conversation_id == conversation_id,
        AITask.user_id == current_user.id,
    ).order_by(AITask.created_at.asc())
    res = await db.execute(stmt)
    tasks = res.scalars().all()

    return [
        {
            "id": t.id,
            "conversation_id": t.conversation_id,
            "parent_task_id": t.parent_task_id,
            "agent_id": t.agent_id,
            "task_type": t.task_type,
            "status": t.status,
            "priority": t.priority,
            "dependencies": t.dependencies_json,
            "input": t.input_json,
            "output": t.output_json,
            "evidence": t.evidence_json,
            "error_message": t.error_message,
            "execution_time_ms": t.execution_time_ms,
            "created_at": t.created_at.isoformat() if t.created_at else None,
            "completed_at": t.completed_at.isoformat() if t.completed_at else None,
        }
        for t in tasks
    ]

