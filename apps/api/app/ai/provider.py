from typing import Any, Dict, Protocol


class LLMProvider(Protocol):
    async def structured_generate(self, *, system: str, user: str, schema: Dict[str, Any]) -> Dict[str, Any]: ...


class ProviderNotConfigured(RuntimeError):
    pass
