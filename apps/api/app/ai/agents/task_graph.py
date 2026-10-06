"""Directed Acyclic Graph (DAG) Task Execution Engine for Multi-Agent Planning."""

import asyncio
import logging
import time
from typing import Any, Callable, Coroutine, Dict, List, Optional, Set

from app.ai.agents.contracts import (
    AgentID,
    AgentRequest,
    AgentResponse,
    EvidenceItem,
    ExecutionBudget,
    TaskPlanStep,
    TaskType,
)
from app.core.exceptions import AppError

logger = logging.getLogger(__name__)


class TaskGraphCycleError(AppError):
    """Raised when a cyclical dependency is detected in the agent task graph."""

    pass


class TaskNode:
    """Individual node in the task dependency DAG."""

    def __init__(self, step: TaskPlanStep) -> None:
        self.task_id: str = step.task_id
        self.agent_id: AgentID = step.agent_id
        self.task_type: TaskType = step.task_type
        self.objective: str = step.objective
        self.dependencies: Set[str] = set(step.dependencies)
        self.input_parameters: Dict[str, Any] = step.input_parameters
        self.priority: int = step.priority

        self.status: str = "PENDING"
        self.response: Optional[AgentResponse] = None
        self.error: Optional[str] = None
        self.execution_time_ms: float = 0.0


class TaskGraph:
    """DAG Task Graph executor with cycle detection and parallel batching."""

    def __init__(self, budget: Optional[ExecutionBudget] = None) -> None:
        self.nodes: Dict[str, TaskNode] = {}
        self.budget: ExecutionBudget = budget or ExecutionBudget()
        self.accumulated_evidence: List[EvidenceItem] = []

    def add_step(self, step: TaskPlanStep) -> None:
        if len(self.nodes) >= self.budget.max_tasks:
            raise AppError(f"Task graph exceeded maximum task count of {self.budget.max_tasks}")
        self.nodes[step.task_id] = TaskNode(step)

    def validate_and_get_batches(self) -> List[List[TaskNode]]:
        """
        Validates graph for missing dependencies and cycles using Kahn's algorithm.
        Returns ordered batches where tasks in each batch can execute concurrently.
        """
        in_degree: Dict[str, int] = {}
        dependents: Dict[str, List[str]] = {t_id: [] for t_id in self.nodes}

        for t_id, node in self.nodes.items():
            in_degree[t_id] = 0
            for dep_id in node.dependencies:
                if dep_id not in self.nodes:
                    raise AppError(f"Task '{t_id}' depends on non-existent task '{dep_id}'")
                dependents[dep_id].append(t_id)

        for t_id, node in self.nodes.items():
            in_degree[t_id] = len(node.dependencies)

        # Kahn's algorithm for batching
        ready_queue = [t_id for t_id, deg in in_degree.items() if deg == 0]
        batches: List[List[TaskNode]] = []
        visited_count = 0

        while ready_queue:
            batch_nodes = [self.nodes[t_id] for t_id in ready_queue]
            batches.append(batch_nodes)
            visited_count += len(ready_queue)

            next_queue = []
            for t_id in ready_queue:
                for dep_t_id in dependents[t_id]:
                    in_degree[dep_t_id] -= 1
                    if in_degree[dep_t_id] == 0:
                        next_queue.append(dep_t_id)
            ready_queue = next_queue

        if visited_count < len(self.nodes):
            raise TaskGraphCycleError("Cyclical dependency detected in multi-agent task plan.")

        if len(batches) > self.budget.max_recursion_depth:
            raise AppError(f"Task graph depth {len(batches)} exceeds max depth {self.budget.max_recursion_depth}")

        return batches

    async def execute(
        self,
        base_request: AgentRequest,
        agent_dispatcher: Callable[[AgentID, AgentRequest], Coroutine[Any, Any, AgentResponse]],
    ) -> List[AgentResponse]:
        """
        Executes task graph batch by batch.
        Concurrent tasks in the same batch execute via asyncio.gather.
        """
        batches = self.validate_and_get_batches()
        all_responses: List[AgentResponse] = []

        for batch_idx, batch in enumerate(batches):
            logger.info(f"Executing task batch {batch_idx + 1}/{len(batches)} with {len(batch)} tasks.")

            # Limit concurrency to budget
            semaphore = asyncio.Semaphore(self.budget.max_parallel_tasks)

            async def run_single_node(node: TaskNode) -> AgentResponse:
                async with semaphore:
                    node_start = time.perf_counter()
                    node.status = "RUNNING"
                    req = AgentRequest(
                        task_id=node.task_id,
                        conversation_id=base_request.conversation_id,
                        user_id=base_request.user_id,
                        workspace_id=base_request.workspace_id,
                        dataset_id=base_request.dataset_id,
                        dataset_version_id=base_request.dataset_version_id,
                        query=base_request.query,
                        objective=node.objective,
                        context=node.input_parameters,
                        prior_evidence=list(self.accumulated_evidence),
                        allowed_tools=base_request.allowed_tools,
                        budget=self.budget,
                    )
                    try:
                        resp = await asyncio.wait_for(
                            agent_dispatcher(node.agent_id, req),
                            timeout=self.budget.timeout_seconds,
                        )
                        node.status = resp.status
                        node.response = resp
                        node.execution_time_ms = (time.perf_counter() - node_start) * 1000.0
                        return resp
                    except asyncio.TimeoutError:
                        logger.error(f"Task '{node.task_id}' timed out after {self.budget.timeout_seconds}s")
                        node.status = "FAILED"
                        node.error = f"Agent {node.agent_id.value} timed out"
                        return AgentResponse(
                            task_id=node.task_id,
                            agent_id=node.agent_id,
                            status="FAILED",
                            summary="Task timed out",
                            error_message=node.error,
                            execution_time_ms=(time.perf_counter() - node_start) * 1000.0,
                        )
                    except Exception as ex:
                        logger.exception(f"Task '{node.task_id}' failed: {ex}")
                        node.status = "FAILED"
                        node.error = str(ex)
                        return AgentResponse(
                            task_id=node.task_id,
                            agent_id=node.agent_id,
                            status="FAILED",
                            summary="Task execution error",
                            error_message=str(ex),
                            execution_time_ms=(time.perf_counter() - node_start) * 1000.0,
                        )

            # Execute all nodes in the current batch in parallel
            batch_results = await asyncio.gather(*(run_single_node(node) for node in batch))

            for resp in batch_results:
                all_responses.append(resp)
                if resp.evidence:
                    self.accumulated_evidence.extend(resp.evidence)

        return all_responses
