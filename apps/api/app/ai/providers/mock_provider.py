"""Deterministic Mock LLM Provider for offline testing, CI, and evaluation."""

from typing import Any, Dict, List, Optional

from app.ai.providers.base import (
    LLMMessage,
    LLMProvider,
    LLMResponse,
    LLMUsage,
    ToolCallSpec,
    ToolDefinition,
)


class MockLLMProvider(LLMProvider):
    """
    Deterministic mock LLM provider.
    Supports scripted queue responses and rule-based heuristic responses for golden evaluation test cases.
    """

    def __init__(self) -> None:
        self._queued_responses: List[LLMResponse] = []
        self._recorded_calls: List[Dict[str, Any]] = []

    def queue_response(self, response: LLMResponse) -> None:
        """Queue a predetermined response for the next generate call."""
        self._queued_responses.append(response)

    def get_recorded_calls(self) -> List[Dict[str, Any]]:
        """Retrieve all calls made to this provider."""
        return self._recorded_calls

    def clear(self) -> None:
        """Reset queued responses and recorded calls."""
        self._queued_responses.clear()
        self._recorded_calls.clear()

    async def generate(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[ToolDefinition]] = None,
        system_instruction: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> LLMResponse:
        self._recorded_calls.append(
            {
                "messages": messages,
                "tools": tools,
                "system_instruction": system_instruction,
                "temperature": temperature,
                "max_tokens": max_tokens,
            }
        )

        if self._queued_responses:
            return self._queued_responses.pop(0)

        # Rule-based heuristic simulation
        return self._heuristic_respond(messages, tools, system_instruction)

    def _heuristic_respond(
        self,
        messages: List[LLMMessage],
        tools: Optional[List[ToolDefinition]] = None,
        system_instruction: Optional[str] = None,
    ) -> LLMResponse:
        # Check if the last message contains tool results
        last_msg = messages[-1] if messages else None

        # If the last message contains tool results, synthesize a grounded explanation
        if last_msg and last_msg.tool_results:
            return self._synthesize_from_tool_results(last_msg.tool_results)

        # Otherwise, inspect user query to decide whether to call a tool or ask clarification
        user_text = ""
        for m in reversed(messages):
            if m.role == "user":
                user_text = m.content
                break

        query = user_text.lower()
        all_context = ((system_instruction or "") + " " + " ".join([m.content for m in messages])).lower()

        # 0. Unsupported requests check (ML, forecasting, real-time streams, layout generation, etc.)
        if any(
            w in query
            for w in [
                "predict",
                "forecast",
                "machine learning",
                "regression",
                "dashboard",
                "layout",
                "arima",
                "churn",
                "real-time",
                "realtime",
                "streaming",
                "stream",
            ]
        ):
            return LLMResponse(
                message="Forecasting, predictive modeling, real-time streaming, and automated dashboard generation are not currently supported in this analytical workspace.",
                finish_reason="stop",
                usage=LLMUsage(prompt_tokens=40, completion_tokens=20, total_tokens=60),
            )

        # 0b. Visual presentation requests (chart switching without re-executing analysis)
        if any(
            w in query
            for w in [
                "horizontal",
                "as a bar chart",
                "as a line chart",
                "as a pie chart",
                "as a donut chart",
                "as a table",
                "view as table",
                "make it horizontal",
                "use a line chart",
                "show as a donut",
                "show as a pie",
            ]
        ):
            chart_name = "Bar Chart"
            if "horizontal" in query:
                chart_name = "Horizontal Bar Chart"
            elif "line" in query:
                chart_name = "Line Chart"
            elif "donut" in query or "pie" in query:
                chart_name = "Donut Chart"
            elif "table" in query:
                chart_name = "Data Table"

            return LLMResponse(
                message=f"I have updated the visualization display to a {chart_name}.",
                finish_reason="stop",
                usage=LLMUsage(prompt_tokens=40, completion_tokens=15, total_tokens=55),
            )

        # 1. Ambiguity detection
        if (
            "category" in query
            and "which" not in query
            and not query.startswith("use ")
            and query.strip() not in ["product_category", "customer_category"]
            and (
                "sales by category" in query
                or "group by category" in query
                or "by category" in query
                or "considering" in query
                or ("product_category" in query and "customer_category" in query)
            )
        ):
            # If context mentions product_category and customer_category
            if "product_category" in all_context or "customer_category" in all_context:
                return LLMResponse(
                    message="I noticed there are multiple category columns (`product_category` and `customer_category`). Which category would you like me to use?",
                    finish_reason="stop",
                    usage=LLMUsage(prompt_tokens=50, completion_tokens=25, total_tokens=75),
                )

        # 1b. Clarification resolution: user replied with a specific column name
        if (
            any(c in query for c in ["product_category", "customer_category"])
            and not ("product_category" in query and "customer_category" in query)
            and "considering" not in query
        ):
            chosen_cat = "product_category" if "product_category" in query else "customer_category"
            return LLMResponse(
                message=f"I will analyze the sales grouped by {chosen_cat}.",
                tool_calls=[
                    ToolCallSpec(
                        name="group_by",
                        arguments={
                            "dimensions": [chosen_cat],
                            "aggregations": [{"column": "revenue", "agg_type": "SUM", "alias": "total_revenue"}],
                            "sort_by": [{"column": "total_revenue", "order": "DESC"}],
                            "limit": 5,
                        },
                        call_id="call_group_by_clarified",
                    )
                ],
                finish_reason="tool_calls",
                usage=LLMUsage(prompt_tokens=60, completion_tokens=40, total_tokens=100),
            )

        # 2. Prompt injection defense test: text containing "ignore", "override", "system prompt", etc.
        if any(
            w in query
            for w in [
                "ignore",
                "system prompt",
                "system override",
                "disregard",
                "override",
                "reveal",
                "bypass",
                "admin secrets",
                "connection strings",
                "api keys",
                "directives",
            ]
        ):
            return LLMResponse(
                message="I am an analytical assistant. I only execute deterministic analytical queries on your dataset and cannot reveal system prompts or execute arbitrary instructions.",
                finish_reason="stop",
                usage=LLMUsage(prompt_tokens=40, completion_tokens=30, total_tokens=70),
            )

        # 2b. Multi-turn follow-up: "What about profit?" or "Show profit"
        if "profit" in query and any(w in query for w in ["what about", "how much", "show", "compare"]):
            # Check if prior history had region or another dimension
            prior_text = " ".join([m.content for m in messages if m.role == "assistant"]).lower()
            dim = "region" if "region" in prior_text else "category"
            alias = "total_profit"
            return LLMResponse(
                message=f"I will analyze the profit grouped by {dim}.",
                tool_calls=[
                    ToolCallSpec(
                        name="group_by",
                        arguments={
                            "dimensions": [dim],
                            "aggregations": [{"column": "profit", "agg_type": "SUM", "alias": alias}],
                            "sort_by": [{"column": alias, "order": "DESC"}],
                            "limit": 5,
                        },
                        call_id="call_group_by_profit",
                    )
                ],
                finish_reason="tool_calls",
                usage=LLMUsage(prompt_tokens=60, completion_tokens=40, total_tokens=100),
            )

        # 2c. Multi-turn follow-up: "Show the top 3" / "limit 3"
        if any(w in query for w in ["top 3", "top 10", "top 5 instead", "show 3"]):
            limit_val = 3 if "3" in query else (10 if "10" in query else 5)
            prior_text = " ".join([m.content for m in messages if m.role == "assistant"]).lower()
            dim = "region" if "region" in prior_text else "category"
            metric = "revenue" if "revenue" in prior_text else "profit"
            alias = f"total_{metric}"
            return LLMResponse(
                message=f"I will update the analysis to show the top {limit_val} {dim}s by {metric}.",
                tool_calls=[
                    ToolCallSpec(
                        name="group_by",
                        arguments={
                            "dimensions": [dim],
                            "aggregations": [{"column": metric, "agg_type": "SUM", "alias": alias}],
                            "sort_by": [{"column": alias, "order": "DESC"}],
                            "limit": limit_val,
                        },
                        call_id="call_group_by_top_n",
                    )
                ],
                finish_reason="tool_calls",
                usage=LLMUsage(prompt_tokens=60, completion_tokens=40, total_tokens=100),
            )

        # 2d. Multi-turn follow-up: "Sort ascending"
        if any(w in query for w in ["ascending", "sort asc", "lowest to highest"]):
            prior_text = " ".join([m.content for m in messages if m.role == "assistant"]).lower()
            dim = "region" if "region" in prior_text else "category"
            metric = "revenue" if "revenue" in prior_text else "profit"
            alias = f"total_{metric}"
            return LLMResponse(
                message=f"I will re-sort the {metric} by {dim} in ascending order.",
                tool_calls=[
                    ToolCallSpec(
                        name="group_by",
                        arguments={
                            "dimensions": [dim],
                            "aggregations": [{"column": metric, "agg_type": "SUM", "alias": alias}],
                            "sort_by": [{"column": alias, "order": "ASC"}],
                            "limit": 5,
                        },
                        call_id="call_group_by_asc",
                    )
                ],
                finish_reason="tool_calls",
                usage=LLMUsage(prompt_tokens=60, completion_tokens=40, total_tokens=100),
            )

        # 3. Highest / Top / Group by query
        if any(w in query for w in ["highest", "top", "most", "maximum", "revenue by region", "sales by region"]):
            # Target dimension: region (or first detected dimension), metric: revenue
            dim = "region" if "region" in query else ("category" if "category" in query else "dimension")
            metric = "revenue" if "revenue" in query else ("sales" if "sales" in query else "metric")
            alias = f"total_{metric}"
            return LLMResponse(
                message=f"I will analyze the {metric} grouped by {dim} to find the top result.",
                tool_calls=[
                    ToolCallSpec(
                        name="group_by",
                        arguments={
                            "dimensions": [dim],
                            "aggregations": [{"column": metric, "agg_type": "SUM", "alias": alias}],
                            "sort_by": [{"column": alias, "order": "DESC"}],
                            "limit": 5,
                        },
                        call_id="call_group_by_1",
                    )
                ],
                finish_reason="tool_calls",
                usage=LLMUsage(prompt_tokens=60, completion_tokens=40, total_tokens=100),
            )

        # 4. Correlation query
        if "correlation" in query or "correlate" in query:
            return LLMResponse(
                message="I will compute the Pearson correlation matrix for the numeric measures in the dataset.",
                tool_calls=[
                    ToolCallSpec(
                        name="correlation",
                        arguments={},
                        call_id="call_corr_1",
                    )
                ],
                finish_reason="tool_calls",
                usage=LLMUsage(prompt_tokens=60, completion_tokens=30, total_tokens=90),
            )

        # 5. Descriptive statistics query
        if any(w in query for w in ["summary", "distribution", "statistics", "describe"]):
            return LLMResponse(
                message="I will compute descriptive statistics across the dataset columns.",
                tool_calls=[
                    ToolCallSpec(
                        name="descriptive_stats",
                        arguments={},
                        call_id="call_stats_1",
                    )
                ],
                finish_reason="tool_calls",
                usage=LLMUsage(prompt_tokens=50, completion_tokens=30, total_tokens=80),
            )

        # 6. Aggregate metrics query (count, sum, avg)
        if any(w in query for w in ["total", "count", "average", "mean", "sum"]):
            metric = "revenue" if "revenue" in query else ("amount" if "amount" in query else "price")
            agg = "avg" if ("average" in query or "mean" in query) else "sum"
            return LLMResponse(
                message=f"I will calculate the {agg} for {metric}.",
                tool_calls=[
                    ToolCallSpec(
                        name="aggregate_metrics",
                        arguments={
                            "metric": metric,
                            "aggregation": agg,
                        },
                        call_id="call_agg_1",
                    )
                ],
                finish_reason="tool_calls",
                usage=LLMUsage(prompt_tokens=50, completion_tokens=30, total_tokens=80),
            )

        # Default conversational response
        return LLMResponse(
            message="I am ready to analyze your dataset. You can ask for revenue by region, top categories, statistical summaries, or correlations.",
            finish_reason="stop",
            usage=LLMUsage(prompt_tokens=40, completion_tokens=25, total_tokens=65),
        )

    def _synthesize_from_tool_results(self, tool_results: List[Any]) -> LLMResponse:
        """Ground the response strictly using the output from executed tools."""
        parts = []
        for tr in tool_results:
            res_data = tr.result if hasattr(tr, "result") else tr.get("result", {})
            rows = res_data.get("rows", [])
            summary = res_data.get("summary", {})
            op = tr.name if hasattr(tr, "name") else tr.get("name", "analysis")

            if rows:
                top_row = rows[0]
                # Format numerical values safely
                formatted_items = []
                for k, v in top_row.items():
                    if isinstance(v, (int, float)):
                        formatted_items.append(f"**{k}**: {v:,.2f}" if isinstance(v, float) else f"**{k}**: {v:,}")
                    else:
                        formatted_items.append(f"**{k}**: {v}")

                parts.append(
                    f"Based on the `{op}` tool execution:\n- The leading result is " + ", ".join(formatted_items) + "."
                )
            elif summary:
                parts.append(f"Analysis completed for `{op}` with summary: {summary}.")
            else:
                parts.append(f"The analytical tool `{op}` executed successfully.")

        grounded_message = "\n\n".join(parts)
        return LLMResponse(
            message=grounded_message,
            finish_reason="stop",
            usage=LLMUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150),
        )
