# Threat Model

## Assets

- user identity
- uploaded datasets
- dataset-derived analytical results
- AI credentials
- dashboard definitions
- audit logs

## Threats

### Prompt injection
Dataset/user text attempts to override AI policy.

### Broken authorization
User accesses another user's dataset.

### SQL injection / unsafe SQL
Model produces destructive or expensive queries.

### File attack
Malformed or malicious upload abuses parser/resource limits.

### Data exfiltration
AI response reveals hidden columns or sensitive data.

### Denial of service
Huge file, expensive query, tool loop, or repeated AI calls consume resources.

### Supply chain
Compromised dependency or container image.

## Controls

- server-side authorization
- read-only analytical boundary
- query parser/allowlist
- resource limits
- upload validation
- PII masking
- rate limits
- dependency scanning
- secret management
- structured audit logs
- security regression tests
