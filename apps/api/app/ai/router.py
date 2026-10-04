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
