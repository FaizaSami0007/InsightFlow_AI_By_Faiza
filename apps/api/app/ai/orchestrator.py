class AIOrchestrator:
    """Single-orchestrator baseline.

    Pipeline: intent -> plan -> validate -> execute -> validate -> explain.
    Multi-agent behavior is intentionally deferred until evaluation proves it is needed.
    """

    async def answer(self, question: str, dataset_context: dict):
        raise NotImplementedError
