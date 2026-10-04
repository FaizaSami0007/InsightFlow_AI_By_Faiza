# Phase 5: AI Provider Abstraction

## 1. Provider Interface

The AI subsystem communicates with Large Language Models via the abstract base class `LLMProvider` located in `app.ai.providers.base`.

```python
class LLMProvider(ABC):
    @abstractmethod
    async def generate(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[ToolDefinition]] = None,
        system_instruction: Optional[str] = None,
        temperature: float = 0.0,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        pass
```

### Key Data Structures

- **`LLMMessage`**: Standardized conversation message supporting `role` (`system`, `user`, `assistant`, `tool`), `content`, `tool_calls`, and `tool_results`.
- **`ToolDefinition`**: Provider-agnostic declaration of callable analytical functions with JSON Schema parameters.
- **`ToolCallSpec`**: Structured function call requested by the model (`call_id`, `name`, `arguments`).
- **`ToolResultSpec`**: Result of a tool execution fed back to the model (`tool_call_id`, `name`, `result`, `error`).
- **`LLMResponse`**: Standardized response containing `message`, `tool_calls`, `finish_reason`, and `usage` token counts.

---

## 2. Concrete Adapters

### Google Gemini Provider (`GeminiProvider`)
- Implements direct asynchronous REST communication with Google Gemini `v1beta` models (`gemini-1.5-pro`, `gemini-1.5-flash`, etc.).
- Converts `ToolDefinition` schemas into Gemini `functionDeclarations`.
- Parses Gemini response candidates into `ToolCallSpec` and `LLMResponse`.
- Configurable timeout and automatic error classification (`AIProviderTimeoutError`, `AIProviderRateLimitError`, `AIProviderAuthError`).

### Deterministic Mock Provider (`MockLLMProvider`)
- Provides deterministic, offline execution for CI/CD pipelines without API keys.
- Supports queued scripted responses (`queue_response`) or rule-based heuristics to simulate tool calling (`group_by`, `correlation`, `descriptive_stats`) and grounded synthesis.

---

## 3. Factory & Configuration

The provider instance is created dynamically via `get_llm_provider(settings)`:
- `LLM_PROVIDER`: `"gemini" | "mock"` (defaults to `mock` when `LLM_API_KEY` is absent).
- `LLM_MODEL`: e.g. `"gemini-1.5-flash"`
- `LLM_API_KEY`: Secure API key (never committed, never logged).
- `LLM_TIMEOUT`: Request timeout in seconds (default: 30.0s).
- `LLM_MAX_TOKENS`: Max generation tokens.
