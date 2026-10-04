# AI Evaluation Matrix

| Dimension | Measurement |
|---|---|
| Intent | classification accuracy |
| Plan | schema validity + semantic match |
| Tool selection | correct tool rate |
| Tool arguments | argument correctness |
| Numerical result | exact/tolerance match |
| Groundedness | supported claim rate |
| Hallucination | unsupported claim rate |
| Clarification | appropriate clarification rate |
| Efficiency | tool calls/request |
| Latency | p50/p95 |
| Cost | estimated tokens/request |
| Visualization | semantic appropriateness |

## Acceptance principle

Do not optimize only for fluent answers. A shorter correct answer with evidence is better than a persuasive incorrect answer.
