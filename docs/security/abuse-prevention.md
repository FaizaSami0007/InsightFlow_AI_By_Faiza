# Abuse Prevention

Protect the platform from both malicious and accidental resource abuse.

## Controls

- request rate limits
- upload quotas
- dataset size limits
- analytical query timeouts
- AI tool-call budgets
- token/cost budgets
- concurrency limits
- per-user storage quotas
- suspicious authentication monitoring

## AI-specific abuse

Repeatedly asking the model to execute expensive analyses should hit a bounded budget rather than run indefinitely.
