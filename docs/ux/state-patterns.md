# UI State Patterns

Every major component must define:

| State | Required behavior |
|---|---|
| Empty | Explain what the user can do next |
| Loading | Preserve context and show progress |
| Processing | Show stage; avoid fake percentages |
| Success | Confirm result and next action |
| Partial | Explain what completed and what did not |
| Error | Human-readable cause + recovery |
| Forbidden | Explain permission boundary |
| Offline/degraded | Explain impact and retry behavior |

Never use an infinite spinner with no explanation.
