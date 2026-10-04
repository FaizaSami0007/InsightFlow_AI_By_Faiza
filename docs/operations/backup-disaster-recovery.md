# Backup & Disaster Recovery

## PostgreSQL

- scheduled backups
- point-in-time recovery where infrastructure supports it
- encrypted backup storage
- restore test at least periodically

## Uploaded data

Object storage versioning or backup strategy must match retention requirements.

## Recovery objectives

Set environment-specific:
- RPO — maximum acceptable data loss
- RTO — maximum acceptable recovery time

These values must be tested, not merely documented.
