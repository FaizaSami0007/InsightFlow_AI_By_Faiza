"""Unit tests for AI Provider abstraction, MockLLMProvider, and GeminiProvider serialization."""

import pytest

from app.ai.providers.base import (
    LLMMessage,
    LLMResponse,
    LLMUsage,
    ToolCallSpec,
    ToolDefinition,
    ToolResultSpec,
)
from app.ai.providers.factory import get_llm_provider
from app.ai.providers.gemini_provider import GeminiProvider
from app.ai.providers.mock_provider import MockLLMProvider
from app.core.config import Settings


@pytest.mark.asyncio
async def test_mock_provider_scripted_response():
    provider = MockLLMProvider()
    queued = LLMResponse(
        message="Predetermined grounded response",
        tool_calls=[ToolCallSpec(name="group_by", arguments={"dimension": "region"})],
        finish_reason="tool_calls",
        usage=LLMUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30),
    )
    provider.queue_response(queued)

    resp = await provider.generate(messages=[LLMMessage(role="user", content="Hello")])
    assert resp.message == "Predetermined grounded response"
    assert len(resp.tool_calls) == 1
    assert resp.tool_calls[0].name == "group_by"
    assert resp.usage.total_tokens == 30

    # Next call falls back to heuristic
    resp2 = await provider.generate(
        messages=[LLMMessage(role="user", content="What is the highest revenue by region?")]
    )
    assert len(resp2.tool_calls) == 1
    assert resp2.tool_calls[0].name == "group_by"


@pytest.mark.asyncio
async def test_mock_provider_heuristics_and_grounding():
    provider = MockLLMProvider()

    # Turn 1: User asks for correlation
    resp1 = await provider.generate(messages=[LLMMessage(role="user", content="Calculate correlation for sales")])
    assert len(resp1.tool_calls) == 1
    assert resp1.tool_calls[0].name == "correlation"

    # Turn 2: Provide tool result
    tool_res = ToolResultSpec(
        call_id="call_corr_1",
        name="correlation",
        result={"rows": [{"dimension": "North", "revenue": 1820000.0}], "row_count": 1},
    )
    messages = [
        LLMMessage(role="user", content="Calculate correlation for sales"),
        LLMMessage(role="assistant", content="Running tool", tool_calls=resp1.tool_calls),
        LLMMessage(role="tool", tool_results=[tool_res]),
    ]
    resp2 = await provider.generate(messages=messages)
    assert resp2.finish_reason == "stop"
    assert "North" in resp2.message
    assert "1,820,000.00" in resp2.message


def test_gemini_provider_serialization():
    provider = GeminiProvider(api_key="fake-test-key", model="gemini-1.5-pro")

    tools = [
        ToolDefinition(
            name="group_by",
            description="Group by dimension",
            parameters={
                "type": "object",
                "properties": {"dimension": {"type": "string"}},
                "required": ["dimension"],
            },
        )
    ]
    converted_tools = provider._convert_tools(tools)
    assert len(converted_tools) == 1
    assert "functionDeclarations" in converted_tools[0]
    assert converted_tools[0]["functionDeclarations"][0]["name"] == "group_by"

    messages = [
        LLMMessage(role="user", content="Show revenue by region"),
        LLMMessage(
            role="assistant",
            content="Calling tool",
            tool_calls=[ToolCallSpec(name="group_by", arguments={"dimension": "region"})],
        ),
        LLMMessage(
            role="tool",
            tool_results=[
                ToolResultSpec(
                    call_id="call_1",
                    name="group_by",
                    result={"rows": [{"region": "East", "revenue": 50000}]},
                )
            ],
        ),
    ]
    converted_msgs = provider._convert_messages(messages)
    assert len(converted_msgs) == 3
    assert converted_msgs[0]["role"] == "user"
    assert converted_msgs[1]["role"] == "model"
    assert "functionCall" in converted_msgs[1]["parts"][1]
    assert converted_msgs[2]["role"] == "user"
    assert "functionResponse" in converted_msgs[2]["parts"][0]


def test_provider_factory():
    # Mock provider configuration
    settings_mock = Settings(llm_provider="mock")
    prov_mock = get_llm_provider(settings_mock)
    assert isinstance(prov_mock, MockLLMProvider)

    # Gemini without key falls back to mock safely
    settings_gemini_nokey = Settings(llm_provider="gemini", llm_api_key="")
    prov_fallback = get_llm_provider(settings_gemini_nokey)
    assert isinstance(prov_fallback, MockLLMProvider)

    # Gemini with key returns GeminiProvider
    settings_gemini_withkey = Settings(llm_provider="gemini", llm_api_key="test_api_key_123")
    prov_gemini = get_llm_provider(settings_gemini_withkey)
    assert isinstance(prov_gemini, GeminiProvider)


@pytest.mark.asyncio
async def test_intent_routing_metadata_questions_do_not_call_group_by():
    """Verify that schema and dataset metadata queries do not call group_by."""
    provider = MockLLMProvider()
    
    # 1. Dataset description
    resp = await provider.generate(messages=[LLMMessage(role="user", content="What type of data is it?")])
    assert len(resp.tool_calls) == 0
    assert resp.finish_reason == "stop"
    assert "records" in resp.message.lower() or "dataset" in resp.message.lower()

    # 2. Schema column count
    resp = await provider.generate(messages=[LLMMessage(role="user", content="How many columns are there in this data?")])
    assert len(resp.tool_calls) == 0
    assert resp.finish_reason == "stop"
    assert "columns" in resp.message.lower()

    # 3. Column listing
    resp = await provider.generate(messages=[LLMMessage(role="user", content="What columns are in this dataset?")])
    assert len(resp.tool_calls) == 0
    assert resp.finish_reason == "stop"
    assert "schema" in resp.message.lower() or "role" in resp.message.lower()

    # 4. Row count
    resp = await provider.generate(messages=[LLMMessage(role="user", content="How many rows are there?")])
    assert len(resp.tool_calls) == 0
    assert resp.finish_reason == "stop"
    assert "records" in resp.message.lower() or "rows" in resp.message.lower()

    # 5. Data quality / nulls
    resp = await provider.generate(messages=[LLMMessage(role="user", content="Are there missing values?")])
    assert len(resp.tool_calls) == 0
    assert resp.finish_reason == "stop"
    assert "missing" in resp.message.lower() or "quality" in resp.message.lower()


@pytest.mark.asyncio
async def test_intent_routing_analytical_questions_call_proper_tools():
    """Verify analytical queries route to group_by or describe_dataset with matched schema columns."""
    provider = MockLLMProvider()

    # Highest cost by channel
    resp = await provider.generate(messages=[LLMMessage(role="user", content="What channel has the highest cost?")])
    assert len(resp.tool_calls) == 1
    call = resp.tool_calls[0]
    assert call.name == "group_by"
    assert "channel" in call.arguments.get("dimensions", [])
    assert any(agg.get("column") == "cost" for agg in call.arguments.get("aggregations", []))

    # Highest profit by product
    resp = await provider.generate(messages=[LLMMessage(role="user", content="Which product has the highest profit?")])
    assert len(resp.tool_calls) == 1
    call = resp.tool_calls[0]
    assert call.name == "group_by"
    assert "product" in call.arguments.get("dimensions", [])
    assert any(agg.get("column") == "profit" for agg in call.arguments.get("aggregations", []))

    # Total revenue
    resp = await provider.generate(messages=[LLMMessage(role="user", content="What is the total revenue?")])
    assert len(resp.tool_calls) == 1
    call = resp.tool_calls[0]
    assert call.name == "describe_dataset"
    assert call.arguments.get("columns") == ["revenue"]


@pytest.mark.asyncio
async def test_no_generic_group_by_fallback_for_unrelated_queries():
    """Verify that uninterpretable queries do not trigger arbitrary group_by(transaction_id, quantity)."""
    provider = MockLLMProvider()
    resp = await provider.generate(messages=[LLMMessage(role="user", content="Can you bake a chocolate cake?")])
    assert len(resp.tool_calls) == 0
    assert resp.finish_reason == "stop"
    assert "could not identify" in resp.message.lower()

