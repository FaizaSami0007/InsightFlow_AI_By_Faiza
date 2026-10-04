"""Unit tests for ContextBuilder, token budgeting, and message bounding."""

from app.ai.context.builder import ContextBuilder
from app.database.models.ai import AIMessage, MessageRole


def test_compress_tool_result():
    # Small result (under limit)
    small_data = {
        "columns": ["region", "revenue"],
        "rows": [{"region": "North", "revenue": 100}, {"region": "South", "revenue": 200}],
        "row_count": 2,
    }
    comp_small = ContextBuilder.compress_tool_result(small_data, max_rows=5)
    assert len(comp_small["rows"]) == 2
    assert "is_truncated" not in comp_small

    # Large result (over limit)
    large_rows = [{"id": i, "val": i * 10} for i in range(50)]
    large_data = {
        "columns": ["id", "val"],
        "rows": large_rows,
        "row_count": 50,
    }
    comp_large = ContextBuilder.compress_tool_result(large_data, max_rows=10)
    assert len(comp_large["rows"]) == 10
    assert comp_large["is_truncated"] is True
    assert comp_large["total_row_count"] == 50
    assert "Showing top 10 of 50 rows" in comp_large["truncation_note"]


def test_build_bounded_messages():
    messages = [
        AIMessage(
            id=f"msg_{i}",
            conversation_id="c1",
            role=MessageRole.USER.value if i % 2 == 0 else MessageRole.ASSISTANT.value,
            content=f"Message {i}",
        )
        for i in range(10)
    ]
    bounded = ContextBuilder.build_bounded_messages(messages, max_turns=4)
    assert len(bounded) == 4
    assert bounded[0].content == "Message 6"
    assert bounded[-1].content == "Message 9"
