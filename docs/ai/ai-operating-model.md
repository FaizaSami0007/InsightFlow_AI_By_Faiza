# AI Operating Model

## Principle

**Reasoning is probabilistic; computation is deterministic.**

## Single-orchestrator baseline

```text
Question
 ↓
Context builder
 ↓
Intent
 ↓
Structured plan
 ↓
Schema validation
 ↓
Authorization + tool policy
 ↓
Tool execution
 ↓
Result validation
 ↓
Grounded response
```

## Tool classes

### Read-only analytical tools

- profile_dataset
- get_column_statistics
- filter_data
- aggregate_data
- group_data
- correlation_analysis
- distribution_analysis
- execute_safe_sql

### Presentation tools

- recommend_chart
- build_dashboard
- modify_dashboard

## Tool budget

Each AI request has:
- maximum tool calls
- maximum execution time
- maximum output rows
- maximum query complexity
- maximum model tokens

If the budget is exceeded, the system asks for clarification or returns a bounded failure instead of continuing indefinitely.

## Clarification policy

Ask a clarification question when:
- multiple columns plausibly match the request
- metric definition is ambiguous
- time range is missing and materially affects the answer
- the requested operation is unsupported

Do not ask unnecessary questions when a reasonable interpretation is strongly supported by dataset metadata.

## Hallucination controls

The response generator may only state numerical claims supported by the validated result object. If no result exists, it must not invent one.
