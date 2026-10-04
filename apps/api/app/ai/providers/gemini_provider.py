"""Google Gemini LLM Provider implementation using async HTTP."""

from typing import Any, Dict, List, Optional

import httpx

from app.ai.providers.base import (
    AIProviderAuthError,
    AIProviderError,
    AIProviderRateLimitError,
    AIProviderTimeoutError,
    LLMMessage,
    LLMProvider,
    LLMResponse,
    LLMUsage,
    ToolCallSpec,
    ToolDefinition,
)


class GeminiProvider(LLMProvider):
    """
    Google Gemini provider implementing structured tool calling and system instructions
    via Google's Gemini REST API.
    """

    def __init__(
        self,
        api_key: str,
        model: str = "gemini-1.5-pro",
        timeout_seconds: int = 45,
    ) -> None:
        self.api_key = api_key
        self.model = model
        self.timeout_seconds = timeout_seconds
        self.base_url = f"https://generativelanguage.googleapis.com/v1beta/models/{self.model}:generateContent"

    def _convert_tools(self, tools: List[ToolDefinition]) -> List[Dict[str, Any]]:
        """Convert ToolDefinition list to Gemini function declarations."""
        declarations = []
        for t in tools:
            declarations.append(
                {
                    "name": t.name,
                    "description": t.description,
                    "parameters": t.parameters,
                }
            )
        return [{"functionDeclarations": declarations}]

    def _convert_messages(self, messages: List[LLMMessage]) -> List[Dict[str, Any]]:
        """Convert LLMMessage objects to Gemini contents format."""
        contents: List[Dict[str, Any]] = []

        for msg in messages:
            if msg.role == "system":
                # System messages are passed separately via systemInstruction in Gemini API
                continue

            parts: List[Dict[str, Any]] = []

            if msg.content:
                parts.append({"text": msg.content})

            if msg.tool_calls:
                for tc in msg.tool_calls:
                    parts.append(
                        {
                            "functionCall": {
                                "name": tc.name,
                                "args": tc.arguments,
                            }
                        }
                    )

            if msg.tool_results:
                for tr in msg.tool_results:
                    parts.append(
                        {
                            "functionResponse": {
                                "name": tr.name,
                                "response": {"output": tr.result},
                            }
                        }
                    )

            role_mapped = "model" if msg.role == "assistant" else ("user" if msg.role in ["user", "tool"] else "user")
            contents.append(
                {
                    "role": role_mapped,
                    "parts": parts,
                }
            )

        return contents

    async def generate(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[ToolDefinition]] = None,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        if not self.api_key:
            raise AIProviderAuthError("Google Gemini API key is missing or not configured.")

        payload: Dict[str, Any] = {
            "contents": self._convert_messages(messages),
        }

        # System instruction
        if system_instruction:
            payload["systemInstruction"] = {"parts": [{"text": system_instruction}]}

        # Tools
        if tools:
            payload["tools"] = self._convert_tools(tools)

        # Generation config
        generation_config: Dict[str, Any] = {}
        if temperature is not None:
            generation_config["temperature"] = temperature
        if max_tokens is not None:
            generation_config["maxOutputTokens"] = max_tokens
        if generation_config:
            payload["generationConfig"] = generation_config

        url = f"{self.base_url}?key={self.api_key}"

        try:
            async with httpx.AsyncClient(timeout=float(self.timeout_seconds)) as client:
                resp = await client.post(
                    url,
                    json=payload,
                    headers={"Content-Type": "application/json"},
                )

            if resp.status_code == 400:
                raise AIProviderError(f"Bad Request to Gemini API: {resp.text}")
            elif resp.status_code in [401, 403]:
                raise AIProviderAuthError("Invalid Gemini API Key or unauthorized access.")
            elif resp.status_code == 429:
                raise AIProviderRateLimitError("Gemini API rate limit exceeded.")
            elif resp.status_code >= 500:
                raise AIProviderError(f"Gemini API Server Error ({resp.status_code}): {resp.text}")
            elif resp.status_code != 200:
                raise AIProviderError(f"Unexpected response from Gemini API ({resp.status_code}): {resp.text}")

            data = resp.json()
            return self._parse_response(data)

        except httpx.TimeoutException as exc:
            raise AIProviderTimeoutError(f"Gemini API request timed out after {self.timeout_seconds}s") from exc
        except (AIProviderError, AIProviderAuthError, AIProviderRateLimitError, AIProviderTimeoutError):
            raise
        except Exception as exc:
            raise AIProviderError(f"Failed to communicate with Gemini API: {str(exc)}") from exc

    def _parse_response(self, data: Dict[str, Any]) -> LLMResponse:
        candidates = data.get("candidates", [])
        if not candidates:
            return LLMResponse(
                message="I was unable to produce an analytical response.",
                finish_reason="stop",
            )

        first_candidate = candidates[0]
        content_obj = first_candidate.get("content", {})
        parts = content_obj.get("parts", [])

        message_texts = []
        tool_calls: List[ToolCallSpec] = []

        for part in parts:
            if "text" in part:
                message_texts.append(part["text"])
            if "functionCall" in part:
                fc = part["functionCall"]
                tool_calls.append(
                    ToolCallSpec(
                        name=fc.get("name", ""),
                        arguments=fc.get("args", {}),
                        call_id=fc.get("name", ""),
                    )
                )

        # Usage metadata
        usage_meta = data.get("usageMetadata", {})
        usage = LLMUsage(
            prompt_tokens=usage_meta.get("promptTokenCount", 0),
            completion_tokens=usage_meta.get("candidatesTokenCount", 0),
            total_tokens=usage_meta.get("totalTokenCount", 0),
        )

        finish_reason = first_candidate.get("finishReason", "STOP").lower()
        if tool_calls:
            finish_reason = "tool_calls"

        return LLMResponse(
            message="\n".join(message_texts).strip(),
            tool_calls=tool_calls,
            finish_reason=finish_reason,
            usage=usage,
            raw_response=data,
        )
