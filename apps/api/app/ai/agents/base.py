"""Base class for all specialized multi-agent implementations."""

import abc

from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.agents.contracts import (
    AgentID,
    AgentRequest,
    AgentResponse,
)
from app.ai.agents.registry import agent_registry
from app.core.exceptions import AppError


class BaseAgent(abc.ABC):
    """Abstract base class for all specialized domain agents."""

    def __init__(self, agent_id: AgentID, db: AsyncSession) -> None:
        self.agent_id: AgentID = agent_id
        self.db: AsyncSession = db
        self.definition = agent_registry.get_agent(agent_id)
        if not self.definition:
            raise AppError(f"Agent '{agent_id.value}' is not registered in AgentRegistry.")

    def is_tool_allowed(self, tool_name: str) -> bool:
        """Verifies if tool is permitted under this agent's allowlist."""
        return agent_registry.is_tool_allowed(self.agent_id, tool_name)

    @abc.abstractmethod
    async def execute(self, request: AgentRequest) -> AgentResponse:
        """Executes the agent's assigned task and returns structured findings."""
        pass
