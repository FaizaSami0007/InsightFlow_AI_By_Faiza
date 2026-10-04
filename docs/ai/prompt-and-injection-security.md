# Prompt Registry & Injection Security

## Prompt registry

Prompts are versioned artifacts, not strings scattered through code.

Each prompt records:
- prompt_id
- version
- purpose
- expected output schema
- allowed model families
- safety notes
- evaluation cases

## Trust boundaries

```text
System policy      = trusted
Tool definitions   = trusted
User instruction   = untrusted
Dataset contents   = untrusted data
Retrieved context  = untrusted unless explicitly trusted
Model output       = untrusted
```

## Dataset prompt injection

A cell containing text such as "ignore previous instructions" must remain data. It must never override system instructions or tool policy.

## Defenses

- Structured tool schemas
- No arbitrary Python execution
- SQL parser + allowlist
- Read-only analytics credentials
- Output schema validation
- Context size limits
- Prompt injection test suite
- Sensitive field redaction
- Tool authorization independent of model output
