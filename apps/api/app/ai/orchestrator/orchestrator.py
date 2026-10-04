"""AI Orchestrator coordinating context construction, tool validation, execution loop, and grounded synthesis."""

import logging
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.ai.context.builder import ContextBuilder
from app.ai.prompts.analyst_prompt import get_analyst_system_instruction
from app.ai.providers.base import (
    LLMMessage,
    LLMProvider,
    LLMResponse,
    ToolResultSpec,
)
from app.ai.providers.factory import get_llm_provider
from app.ai.schemas import ChatRequest, ChatResponse
from app.ai.tools.adapter import AIToolAdapter
from app.core.config import settings
from app.core.exceptions import AppError, NotFoundError
from app.database.models.ai import AIConversation, AIMessage, AIRequestLog, MessageRole
from app.database.models.dataset import Dataset, DatasetVersion
from app.database.models.user import User

logger = logging.getLogger(__name__)


class AIOrchestrator:
    """
    Safe AI Orchestrator implementing multi-turn reasoning and tool execution loop.
    Enforces strict authorization, schema validation, loop limits, and numerical grounding.
    """

    def __init__(self, provider: Optional[LLMProvider] = None) -> None:
        self.provider = provider or get_llm_provider()

    async def chat(
        self,
        request: ChatRequest,
        user: User,
        db: AsyncSession,
    ) -> ChatResponse:
        start_time = time.perf_counter()
        total_prompt_tokens = 0
        total_completion_tokens = 0

        # Step 1: Authorization & Dataset Resolution
        stmt_dataset = select(Dataset).where(
            Dataset.id == request.dataset_id,
            Dataset.owner_id == user.id,
        )
        res_dataset = await db.execute(stmt_dataset)
        dataset = res_dataset.scalar_one_or_none()
        if not dataset:
            raise NotFoundError("Dataset not found or access unauthorized.")

        stmt_version = select(DatasetVersion).where(
            DatasetVersion.id == request.dataset_version_id,
            DatasetVersion.dataset_id == dataset.id,
        )
        res_version = await db.execute(stmt_version)
        version = res_version.scalar_one_or_none()
        if not version:
            raise NotFoundError("Dataset version not found.")

        raw_history: List[AIMessage] = []
        if request.conversation_id:
            stmt_conv = (
                select(AIConversation)
                .options(selectinload(AIConversation.messages))
                .where(
                    AIConversation.id == request.conversation_id,
                    AIConversation.user_id == user.id,
                )
            )
            res_conv = await db.execute(stmt_conv)
            conversation = res_conv.scalar_one_or_none()
            if not conversation:
                raise NotFoundError("AI Conversation not found.")
            raw_history = list(conversation.messages) if conversation.messages else []
        else:
            # Create new conversation
            conversation = AIConversation(
                user_id=user.id,
                dataset_id=dataset.id,
                dataset_version_id=version.id,
                title=request.message[:40] + ("..." if len(request.message) > 40 else ""),
            )
            db.add(conversation)
            await db.commit()
            await db.refresh(conversation)
            raw_history = []

        # Step 3: Build Safe Context & System Instructions
        dataset_context = await ContextBuilder.build_dataset_context(db, dataset, version)
        system_instruction = get_analyst_system_instruction(dataset_context)

        # Step 4: Build bounded message history
        llm_messages = ContextBuilder.build_bounded_messages(raw_history, max_turns=6)
        llm_messages.append(LLMMessage(role="user", content=request.message))

        # Save user message to DB
        user_db_msg = AIMessage(
            conversation_id=conversation.id,
            role=MessageRole.USER.value,
            content=request.message,
            created_at=datetime.utcnow(),
        )
        db.add(user_db_msg)
        await db.commit()

        # Step 5: Tool Orchestration Loop
        available_tools = AIToolAdapter.get_tool_definitions()
        executed_tool_calls: List[Dict[str, Any]] = []
        executed_tool_results: List[Dict[str, Any]] = []
        executed_analysis_ids: List[str] = []
        provenances: List[Dict[str, Any]] = []

        loop_count = 0
        max_loops = settings.max_tool_calls_per_request
        final_message = ""
        needs_clarification = False

        while loop_count < max_loops:
            loop_count += 1

            try:
                llm_resp: LLMResponse = await self.provider.generate(
                    messages=llm_messages,
                    tools=available_tools,
                    system_instruction=system_instruction,
                    temperature=settings.llm_temperature,
                    max_tokens=settings.llm_max_tokens,
                )
            except Exception as e:
                logger.error("AI Provider error during orchestration: %s", str(e), exc_info=True)
                raise AppError(f"AI Provider error: {str(e)}", status_code=502)

            total_prompt_tokens += llm_resp.usage.prompt_tokens
            total_completion_tokens += llm_resp.usage.completion_tokens

            # If no tool calls, synthesis is complete
            if not llm_resp.tool_calls:
                final_message = llm_resp.message
                if "?" in final_message and any(w in final_message.lower() for w in ["which", "clarify", "specify"]):
                    needs_clarification = True
                break

            # Process tool calls
            current_turn_tool_results: List[ToolResultSpec] = []

            for tc in llm_resp.tool_calls:
                executed_tool_calls.append(
                    {
                        "name": tc.name,
                        "arguments": tc.arguments,
                        "call_id": tc.call_id,
                    }
                )

                try:
                    tool_output = await AIToolAdapter.execute_tool_call(
                        tool_call=tc,
                        user=user,
                        dataset_id=dataset.id,
                        dataset_version_id=version.id,
                        db=db,
                    )

                    analysis_id = tool_output.get("analysis_id")
                    if analysis_id:
                        executed_analysis_ids.append(analysis_id)
                    if tool_output.get("provenance"):
                        provenances.append(tool_output["provenance"])

                    # Compress tool result to adhere to token budget
                    compressed_result = ContextBuilder.compress_tool_result(
                        tool_output,
                        max_rows=settings.max_tool_result_rows,
                    )

                    executed_tool_results.append(
                        {
                            "name": tc.name,
                            "analysis_id": analysis_id,
                            "row_count": tool_output.get("row_count", 0),
                            "columns": tool_output.get("columns", []),
                            "summary": tool_output.get("summary"),
                            "execution_time_ms": tool_output.get("execution_time_ms", 0.0),
                        }
                    )

                    current_turn_tool_results.append(
                        ToolResultSpec(
                            call_id=tc.call_id or tc.name,
                            name=tc.name,
                            result=compressed_result,
                        )
                    )

                except Exception as e:
                    logger.warning("Tool execution error for '%s': %s", tc.name, str(e))
                    current_turn_tool_results.append(
                        ToolResultSpec(
                            call_id=tc.call_id or tc.name,
                            name=tc.name,
                            result={"error": str(e), "status": "FAILED"},
                        )
                    )

            # Append model's tool calls and subsequent tool responses to message chain
            llm_messages.append(
                LLMMessage(
                    role="assistant",
                    content=llm_resp.message or "",
                    tool_calls=llm_resp.tool_calls,
                )
            )
            llm_messages.append(
                LLMMessage(
                    role="tool",
                    tool_results=current_turn_tool_results,
                )
            )

        if not final_message and loop_count >= max_loops:
            final_message = (
                "The analysis completed tool execution steps, but reached the maximum permitted tool call depth limit."
            )

        execution_time_ms = round((time.perf_counter() - start_time) * 1000, 2)
        total_tokens = total_prompt_tokens + total_completion_tokens

        # Step 6: Persist assistant message and AI Request Log
        assistant_db_msg = AIMessage(
            conversation_id=conversation.id,
            role=MessageRole.ASSISTANT.value,
            content=final_message,
            tool_calls_json=executed_tool_calls if executed_tool_calls else None,
            tool_results_json=executed_tool_results if executed_tool_results else None,
            analysis_ids=executed_analysis_ids if executed_analysis_ids else None,
            created_at=datetime.utcnow(),
        )
        db.add(assistant_db_msg)

        log_entry = AIRequestLog(
            user_id=user.id,
            conversation_id=conversation.id,
            provider=settings.llm_provider,
            model=settings.llm_model,
            latency_ms=execution_time_ms,
            prompt_tokens=total_prompt_tokens,
            completion_tokens=total_completion_tokens,
            total_tokens=total_tokens,
            tool_count=len(executed_tool_calls),
            status="CLARIFICATION" if needs_clarification else "SUCCESS",
            created_at=datetime.utcnow(),
        )
        db.add(log_entry)
        await db.commit()
        await db.refresh(assistant_db_msg)

        return ChatResponse(
            conversation_id=conversation.id,
            message_id=assistant_db_msg.id,
            message=final_message,
            tool_calls=executed_tool_calls,
            tool_results=executed_tool_results,
            analysis_ids=executed_analysis_ids,
            provenance=provenances,
            needs_clarification=needs_clarification,
            execution_time_ms=execution_time_ms,
            tokens_used=total_tokens,
            created_at=assistant_db_msg.created_at,
        )
