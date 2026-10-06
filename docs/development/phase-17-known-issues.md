# Phase 17 — Known Operational Boundaries & Constraints

## 1. Network Timeouts
- Ad-hoc connection tests and previews enforce a default 10-second socket timeout to prevent hung worker threads.
- Large database extractions are streamed with batch chunking to avoid memory spikes.

## 2. API Rate Limits
- REST API connectors observe upstream HTTP `429 Too Many Requests` status codes and exponential backoff retry headers where provided.

## 3. Spreadsheet Range Limits
- Google Sheets extraction limits single worksheet ingestion to 500,000 cells per sync run to preserve responsiveness.
