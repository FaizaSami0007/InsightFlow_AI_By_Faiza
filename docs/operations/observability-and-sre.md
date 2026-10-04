# Observability & SRE

## Three pillars

### Logs
Structured JSON logs with:
- request_id
- user_id hash / safe identifier
- dataset_id
- analysis_id
- tool_call_id
- latency
- outcome

Never log secrets or raw sensitive dataset contents.

### Metrics
Track:
- request latency
- error rate
- upload failures
- profiling duration
- analytical query duration
- AI latency
- AI token/cost estimate
- tool calls per request
- validation failures
- dashboard render errors

### Traces
Trace:

```text
HTTP request
 → AI orchestration
 → tool selection
 → analytical execution
 → result validation
 → response generation
```

## SLO starting point

For MVP, define targets rather than pretending they are already achieved:

- API availability target: 99.5%
- simple API p95: < 500ms
- simple analytics p95: < 3s
- AI response p95: < 15s

Measure before tightening targets.

## Alerts

Alert on sustained:
- elevated 5xx
- database connectivity failures
- queue backlog
- abnormal AI cost
- repeated tool validation failures
- unusual authorization failures
