# 09 — API Documentation

# InsightFlow AI

## API Documentation

**Project:** InsightFlow AI

**Subtitle:** AI-Driven Automated Data Analysis & Context-Aware Dashboard Generation

**Document:** API Documentation

**Version:** 0.1.0

**Status:** Draft

**Project Phase:** Phase 0 — Documentation

**Previous Document:** 08 — UI/UX Design

**Next Document:** 10 — Security

---

# 1. API Overview

The API layer provides communication between the frontend application and backend services.

The API will act as the primary interface between:

```
Frontend
    ↕
Backend API
    ↕
Application Services
    ↕
AI / Data / Database Systems
```

The API should provide:

- Authentication
- User management
- Dataset management
- File uploads
- Dataset processing
- Data profiling
- Data quality
- Analysis
- AI interaction
- Dashboard generation
- Dashboard management
- Conversations
- Reports
- Settings

---

# 2. API Architecture

The initial architecture will follow:

```
┌──────────────────────┐
│      React App       │
└──────────┬───────────┘
           │
           │ HTTPS / JSON
           ▼
┌──────────────────────┐
│      API Server      │
└──────────┬───────────┘
           │
     ┌─────┼──────────────┐
     ▼     ▼              ▼
  Services AI Services Data Services
     │     │              │
     └─────┼──────────────┘
           ▼
    Database / Storage
```

---

# 3. API Style

The primary API style will be:

> REST API
> 

Communication format:

> JSON
> 

Transport:

> HTTPS
> 

Authentication:

> Token-based authentication
> 

Future versions may introduce:

- WebSockets
- Server-Sent Events
- GraphQL where justified
- Internal event-driven communication

---

# 4. API Base URL

Development:

```
http://localhost:8000/api/v1
```

Production:

```
https://api.insightflow.ai/api/v1
```

The actual production domain will be finalized during deployment.

---

# 5. API Versioning

The API will use URL versioning.

Example:

```
/api/v1/datasets
/api/v1/analyses
/api/v1/dashboards
```

Future breaking changes may use:

```
/api/v2/
```

The system should avoid breaking existing clients whenever possible.

---

# 6. HTTP Methods

The API will use standard HTTP methods.

### GET

Retrieve resources.

```
GET /datasets
```

### POST

Create resources or perform actions.

```
POST /datasets
```

### PUT

Replace an existing resource.

```
PUT /dashboards/{id}
```

### PATCH

Partially update a resource.

```
PATCH /users/me
```

### DELETE

Delete a resource.

```
DELETE /datasets/{id}
```

---

# 7. HTTP Status Codes

Common responses:

```
200 OK
201 Created
202 Accepted
204 No Content
400 Bad Request
401 Unauthorized
403 Forbidden
404 Not Found
409 Conflict
422 Unprocessable Entity
429 Too Many Requests
500 Internal Server Error
503 Service Unavailable
```

---

# 8. Authentication Architecture

Authentication flow:

```
User
 ↓
Sign In
 ↓
Authentication API
 ↓
Validate Credentials
 ↓
Create Session / Token
 ↓
Frontend Stores Auth State
 ↓
Authenticated API Requests
```

The exact token/session strategy will be finalized in the Security document.

---

# 9. Authentication Endpoints

Base:

```
/api/v1/auth
```

Endpoints:

```
POST /auth/register
POST /auth/login
POST /auth/logout
POST /auth/refresh
POST /auth/forgot-password
POST /auth/reset-password
GET  /auth/me
```

---

# 10. Register API

### Endpoint

```
POST /api/v1/auth/register
```

### Request

```
{
  "name": "John Doe",
  "email": "john@example.com",
  "password": "StrongPassword123!"
}
```

### Response

```
{
  "success": true,
  "message": "Account created successfully",
  "data": {
    "user": {
      "id": "user_123",
      "name": "John Doe",
      "email": "john@example.com"
    }
  }
}
```

---

# 11. Login API

### Endpoint

```
POST /api/v1/auth/login
```

### Request

```
{
  "email": "john@example.com",
  "password": "StrongPassword123!"
}
```

### Response

```
{
  "success": true,
  "data": {
    "user": {
      "id": "user_123",
      "name": "John Doe",
      "email": "john@example.com"
    }
  }
}
```

Authentication credentials should be handled securely and should not be exposed in API responses.

---

# 12. Current User API

### Endpoint

```
GET /api/v1/auth/me
```

Returns authenticated user information.

Example:

```
{
  "success": true,
  "data": {
    "id": "user_123",
    "name": "John Doe",
    "email": "john@example.com"
  }
}
```

---

# 13. User APIs

Base:

```
/api/v1/users
```

Potential endpoints:

```
GET   /users/me
PATCH /users/me
PATCH /users/me/password
DELETE /users/me
```

---

# 14. Workspace APIs

InsightFlow AI may support workspaces.

Base:

```
/api/v1/workspaces
```

Endpoints:

```
GET    /workspaces
POST   /workspaces
GET    /workspaces/{id}
PATCH  /workspaces/{id}
DELETE /workspaces/{id}
```

Future workspace functionality may include:

- Members
- Roles
- Permissions
- Shared datasets
- Shared dashboards

---

# 15. Dataset API Overview

Datasets are one of the central resources.

Base:

```
/api/v1/datasets
```

Endpoints:

```
GET    /datasets
POST   /datasets
GET    /datasets/{id}
PATCH  /datasets/{id}
DELETE /datasets/{id}
```

---

# 16. List Datasets

### Endpoint

```
GET /api/v1/datasets
```

Query parameters:

```
?page=1
&limit=20
&search=sales
&sort=created_at
&order=desc
&status=ready
```

Example:

```
GET /api/v1/datasets?page=1&limit=20&status=ready
```

---

# 17. Dataset List Response

```
{
  "success": true,
  "data": {
    "items": [
      {
        "id": "dataset_123",
        "name": "Sales Performance",
        "rows": 50000,
        "columns": 12,
        "status": "ready",
        "quality_score": 87,
        "created_at": "2026-08-24T10:00:00Z"
      }
    ],
    "pagination": {
      "page": 1,
      "limit": 20,
      "total": 1,
      "pages": 1
    }
  }
}
```

---

# 18. Create Dataset

### Endpoint

```
POST /api/v1/datasets
```

This may create dataset metadata before file processing begins.

Request:

```
{
  "name": "Sales Performance",
  "description": "Monthly sales data",
  "workspace_id": "workspace_123"
}
```

---

# 19. Dataset Upload

File uploads will use multipart form data.

### Endpoint

```
POST /api/v1/datasets/{id}/upload
```

Form:

```
file = sales.csv
```

Optional metadata:

```
description
```

Response:

```
{
  "success": true,
  "data": {
    "dataset_id": "dataset_123",
    "job_id": "job_456",
    "status": "processing"
  }
}
```

---

# 20. Dataset Processing

Processing may be asynchronous.

Flow:

```
Upload
 ↓
Create Processing Job
 ↓
Return 202
 ↓
Background Worker
 ↓
Parse
 ↓
Profile
 ↓
Quality Analysis
 ↓
Store Metadata
 ↓
READY
```

The frontend should not remain blocked waiting for a long processing operation.

---

# 21. Processing Job API

### Endpoint

```
GET /api/v1/jobs/{job_id}
```

Response:

```
{
  "success": true,
  "data": {
    "id": "job_456",
    "type": "dataset_processing",
    "status": "running",
    "progress": 72,
    "message": "Generating data profile"
  }
}
```

---

# 22. Job Status

Possible statuses:

```
queued
running
completed
failed
cancelled
```

---

# 23. Dataset Details

### Endpoint

```
GET /api/v1/datasets/{id}
```

Response:

```
{
  "success": true,
  "data": {
    "id": "dataset_123",
    "name": "Sales Performance",
    "rows": 50000,
    "columns": 12,
    "status": "ready",
    "quality_score": 87,
    "current_version": 2
  }
}
```

---

# 24. Dataset Preview

### Endpoint

```
GET /api/v1/datasets/{id}/preview
```

Query:

```
?page=1
&limit=50
```

The backend should return only a controlled number of rows.

---

# 25. Dataset Schema

### Endpoint

```
GET /api/v1/datasets/{id}/schema
```

Response:

```
{
  "success": true,
  "data": {
    "columns": [
      {
        "name": "revenue",
        "physical_type": "float64",
        "semantic_type": "currency",
        "nullable": true
      }
    ]
  }
}
```

---

# 26. Dataset Profile

### Endpoint

```
GET /api/v1/datasets/{id}/profile
```

The response may include:

```
Row count
Column count
Statistics
Unique values
Missing values
Distributions
Date ranges
```

---

# 27. Data Quality API

### Endpoint

```
GET /api/v1/datasets/{id}/quality
```

Response:

```
{
  "success": true,
  "data": {
    "score": 87,
    "completeness": 92,
    "validity": 84,
    "uniqueness": 98,
    "issues": [
      {
        "type": "missing_values",
        "severity": "warning",
        "column": "customer_age",
        "percentage": 4.2
      }
    ]
  }
}
```

---

# 28. Dataset Versions

### Endpoint

```
GET /api/v1/datasets/{id}/versions
```

Example:

```
{
  "success": true,
  "data": [
    {
      "version": 1,
      "created_at": "2026-08-20T10:00:00Z"
    },
    {
      "version": 2,
      "created_at": "2026-08-24T10:00:00Z"
    }
  ]
}
```

---

# 29. Get Dataset Version

### Endpoint

```
GET /api/v1/datasets/{id}/versions/{version}
```

Returns the metadata associated with that version.

---

# 30. Dataset Transformation APIs

Potential endpoints:

```
POST /datasets/{id}/transformations
GET  /datasets/{id}/transformations
```

Example request:

```
{
  "operation": "remove_duplicates"
}
```

The system should validate whether the operation is safe before execution.

---

# 31. Analysis API Overview

Base:

```
/api/v1/analyses
```

Analysis represents a concrete analytical operation.

Potential endpoints:

```
POST /analyses
GET  /analyses
GET  /analyses/{id}
DELETE /analyses/{id}
```

---

# 32. Create Analysis

### Endpoint

```
POST /api/v1/analyses
```

Request:

```
{
  "dataset_id": "dataset_123",
  "question": "Which region generated the highest revenue?"
}
```

The backend may then:

```
Question
 ↓
Intent
 ↓
Plan
 ↓
Tool
 ↓
Execution
 ↓
Result
```

---

# 33. Analysis Response

```
{
  "success": true,
  "data": {
    "analysis_id": "analysis_123",
    "status": "completed",
    "question": "Which region generated the highest revenue?",
    "result": {
      "region": "North",
      "revenue": 120000
    }
  }
}
```

---

# 34. Analysis Status

Potential statuses:

```
queued
planning
running
validating
completed
failed
```

---

# 35. Analysis Result

A result should contain:

```
Analysis ID
Dataset ID
Dataset Version
Question
Intent
Tool
Parameters
Result
Execution Time
Status
```

This creates traceability.

---

# 36. Analysis History

### Endpoint

```
GET /api/v1/analyses
```

Filters:

```
dataset_id
user_id
status
date
```

---

# 37. AI Analyst API

The AI Analyst requires a conversational interface.

Base:

```
/api/v1/ai
```

Potential endpoints:

```
POST /ai/chat
GET  /ai/conversations
GET  /ai/conversations/{id}
DELETE /ai/conversations/{id}
```

---

# 38. AI Chat

### Endpoint

```
POST /api/v1/ai/chat
```

Request:

```
{
  "dataset_id": "dataset_123",
  "conversation_id": "conversation_456",
  "message": "Which region has the highest revenue?"
}
```

---

# 39. AI Chat Response

```
{
  "success": true,
  "data": {
    "conversation_id": "conversation_456",
    "message": {
      "id": "message_789",
      "role": "assistant",
      "content": "North generated the highest revenue.",
      "analysis_id": "analysis_123"
    }
  }
}
```

---

# 40. AI Streaming

For a better user experience, AI responses may eventually be streamed.

Possible technology:

```
Server-Sent Events
```

Flow:

```
User
 ↓
POST AI Request
 ↓
AI Processing
 ↓
Stream Response
 ↓
Frontend Updates Message
```

This is especially useful for longer responses.

---

# 41. AI Context

The frontend may send:

```
dataset_id
dataset_version
conversation_id
dashboard_id
user_message
```

The backend should determine the authoritative context rather than trusting arbitrary client-supplied context.

---

# 42. AI Suggested Questions

### Endpoint

```
GET /api/v1/ai/suggestions?dataset_id=dataset_123
```

Response:

```
{
  "success": true,
  "data": [
    "Which region has the highest revenue?",
    "Show revenue trends.",
    "What are the biggest data-quality issues?"
  ]
}
```

---

# 43. AI Insight API

Potential endpoint:

```
POST /api/v1/ai/insights
```

Request:

```
{
  "dataset_id": "dataset_123"
}
```

The AI may generate a set of high-value observations.

---

# 44. Dashboard API Overview

Base:

```
/api/v1/dashboards
```

Endpoints:

```
GET
POST
GET /{id}
PATCH /{id}
DELETE /{id}
```

---

# 45. Generate Dashboard

### Endpoint

```
POST /api/v1/dashboards/generate
```

Request:

```
{
  "dataset_id": "dataset_123",
  "prompt": "Create a dashboard focused on regional sales performance."
}
```

---

# 46. Dashboard Generation Response

```
{
  "success": true,
  "data": {
    "dashboard_id": "dashboard_123",
    "version": 1,
    "status": "generated"
  }
}
```

For complex generation, this may instead return a background job.

---

# 47. Get Dashboard

### Endpoint

```
GET /api/v1/dashboards/{id}
```

Response:

```
{
  "success": true,
  "data": {
    "id": "dashboard_123",
    "title": "Regional Sales Overview",
    "dataset_id": "dataset_123",
    "dataset_version": 2,
    "version": 1,
    "widgets": []
  }
}
```

---

# 48. Update Dashboard

### Endpoint

```
PATCH /api/v1/dashboards/{id}
```

Request:

```
{
  "title": "Regional Sales Performance"
}
```

Only allowed fields should be updated.

---

# 49. Dashboard Versioning API

### Endpoint

```
GET /api/v1/dashboards/{id}/versions
```

Restore:

```
POST /api/v1/dashboards/{id}/versions/{version}/restore
```

---

# 50. Dashboard Widget API

Potential endpoint:

```
POST /api/v1/dashboards/{id}/widgets
PATCH /api/v1/dashboards/{id}/widgets/{widget_id}
DELETE /api/v1/dashboards/{id}/widgets/{widget_id}
```

---

# 51. Dashboard AI Modification

### Endpoint

```
POST /api/v1/dashboards/{id}/ai-modify
```

Request:

```
{
  "instruction": "Add a profit margin KPI and move the revenue chart to the top."
}
```

Response:

```
{
  "success": true,
  "data": {
    "preview": {
      "changes": [
        "Added profit margin KPI",
        "Moved revenue chart"
      ]
    }
  }
}
```

The frontend may then ask the user to confirm the changes.

---

# 52. Dashboard Filters

Filters may be sent to an analytical endpoint.

Example:

```
GET /api/v1/dashboards/{id}/data
```

Query:

```
region=North
start_date=2026-01-01
end_date=2026-08-01
```

The backend must validate every filter against the dashboard and dataset schema.

---

# 53. Widget Data API

An alternative architecture may allow widgets to request their own data.

Example:

```
POST /api/v1/widgets/{id}/data
```

Request:

```
{
  "filters": {
    "region": ["North"]
  }
}
```

The final architecture will be selected based on performance and caching requirements.

---

# 54. Dashboard Export API

Potential endpoint:

```
POST /api/v1/dashboards/{id}/export
```

Request:

```
{
  "format": "pdf"
}
```

Supported future formats:

```
PDF
PNG
CSV
XLSX
JSON
```

---

# 55. Conversation API

Base:

```
/api/v1/conversations
```

Endpoints:

```
GET    /conversations
POST   /conversations
GET    /conversations/{id}
PATCH  /conversations/{id}
DELETE /conversations/{id}
```

---

# 56. Conversation Structure

Example:

```
{
  "id": "conversation_123",
  "title": "Regional Sales Analysis",
  "dataset_id": "dataset_123",
  "created_at": "2026-08-24T10:00:00Z"
}
```

---

# 57. Conversation Messages

### Endpoint

```
GET /api/v1/conversations/{id}/messages
```

Messages may contain:

```
Role
Content
Analysis ID
Dashboard ID
Timestamp
Metadata
```

---

# 58. Reports API

Potential endpoints:

```
GET  /reports
POST /reports
GET  /reports/{id}
DELETE /reports/{id}
```

Future scheduling:

```
POST /reports/{id}/schedule
PATCH /reports/{id}/schedule
DELETE /reports/{id}/schedule
```

---

# 59. Notification API

Potential endpoints:

```
GET /notifications
PATCH /notifications/{id}/read
PATCH /notifications/read-all
```

---

# 60. Search API

Potential endpoint:

```
GET /api/v1/search
```

Example:

```
?q=sales
&type=datasets,dashboards,conversations
```

The response may return grouped results.

---

# 61. API Response Format

The API should use a consistent response structure.

Success:

```
{
  "success": true,
  "data": {},
  "meta": {}
}
```

Error:

```
{
  "success": false,
  "error": {
    "code": "DATASET_NOT_FOUND",
    "message": "The requested dataset could not be found."
  }
}
```

---

# 62. Error Object

An error should contain:

```
code
message
details
request_id
```

Example:

```
{
  "success": false,
  "error": {
    "code": "INVALID_DATASET_FIELD",
    "message": "The selected column does not exist.",
    "details": {
      "field": "sales_date"
    },
    "request_id": "req_123"
  }
}
```

---

# 63. API Error Codes

Potential codes:

```
AUTH_INVALID_CREDENTIALS
AUTH_TOKEN_EXPIRED
AUTH_UNAUTHORIZED

DATASET_NOT_FOUND
DATASET_INVALID
DATASET_PROCESSING
DATASET_PROCESSING_FAILED
DATASET_FIELD_NOT_FOUND

ANALYSIS_INVALID
ANALYSIS_FAILED
ANALYSIS_TIMEOUT

AI_REQUEST_FAILED
AI_TOOL_ERROR
AI_UNSUPPORTED_REQUEST

DASHBOARD_NOT_FOUND
DASHBOARD_INVALID
DASHBOARD_GENERATION_FAILED

VALIDATION_ERROR
RATE_LIMIT_EXCEEDED
INTERNAL_ERROR
```

---

# 64. Validation

All API inputs must be validated.

Validation should occur at:

```
Frontend
    +
Backend
```

Frontend validation improves UX.

Backend validation provides actual security and integrity.

---

# 65. Request Validation

Example:

```
{
  "question": ""
}
```

should fail because the question cannot be empty.

Response:

```
{
  "success": false,
  "error": {
    "code": "VALIDATION_ERROR",
    "message": "Question is required."
  }
}
```

---

# 66. Pagination

List endpoints should support pagination.

Example:

```
?page=1&limit=20
```

Response:

```
{
  "items": [],
  "pagination": {
    "page": 1,
    "limit": 20,
    "total": 120,
    "pages": 6
  }
}
```

---

# 67. Sorting

Example:

```
?sort=created_at&order=desc
```

The backend must whitelist sortable fields.

Users should not be allowed to inject arbitrary SQL through sort parameters.

---

# 68. Filtering

Example:

```
?status=ready
```

Filters should be validated against allowed fields.

---

# 69. Search

Example:

```
?search=sales
```

Search implementation may use:

- PostgreSQL text search
- Indexed columns
- Full-text search
- Future vector search

---

# 70. Rate Limiting

API endpoints should have rate limits.

Different limits may apply to:

```
Authentication
File Upload
AI Requests
Analysis
Dashboard Generation
General API
```

AI endpoints should generally have stricter resource controls because they may be expensive.

---

# 71. Idempotency

Important operations may use idempotency keys.

Example:

```
Idempotency-Key: abc123
```

This can prevent accidental duplicate processing when a client retries a request.

Potential use cases:

- Dataset processing
- Dashboard generation
- Report generation
- Payment functionality in future

---

# 72. File Upload Limits

The API should enforce:

```
Maximum file size
Allowed extensions
Allowed MIME types
Request timeout
Upload rate limits
```

Exact limits will be defined during implementation and deployment testing.

---

# 73. API Security Boundary

The API should never trust:

```
User ID
Workspace ID
Dataset ownership
Dashboard ownership
Permissions
```

provided by the client.

The backend must determine authorization from authenticated identity and stored relationships.

---

# 74. Dataset Authorization

Before accessing a dataset:

```
Request
 ↓
Authenticate User
 ↓
Determine Workspace
 ↓
Check Dataset Ownership / Permission
 ↓
Allow / Deny
```

---

# 75. AI Authorization

The AI should not be able to access arbitrary datasets.

The backend should construct the AI context from authorized resources.

```
User
 ↓
Authorized Dataset
 ↓
Context Builder
 ↓
AI
```

---

# 76. API and AI Architecture Relationship

The API acts as the gateway:

```
Frontend
   │
   ▼
API
   │
   ├── Dataset Service
   ├── Analysis Service
   ├── Dashboard Service
   ├── Conversation Service
   │
   └── AI Service
           │
           ├── Context
           ├── Planner
           ├── Tools
           └── LLM
```

---

# 77. API and Data Engineering Relationship

Dataset upload:

```
Frontend
 ↓
POST /datasets/{id}/upload
 ↓
API
 ↓
Ingestion Service
 ↓
Parser
 ↓
Profiler
 ↓
Quality Engine
 ↓
DuckDB / Parquet
 ↓
Dataset READY
```

---

# 78. API and Dashboard Relationship

Dashboard generation:

```
Frontend
 ↓
POST /dashboards/generate
 ↓
Dashboard Service
 ↓
AI Planner
 ↓
Visualization Engine
 ↓
Dashboard JSON
 ↓
Validation
 ↓
Database
 ↓
Frontend
```

---

# 79. API and AI Analyst Relationship

AI question:

```
Frontend
 ↓
POST /ai/chat
 ↓
AI Service
 ↓
Context
 ↓
Intent
 ↓
Planning
 ↓
Tool
 ↓
Analysis
 ↓
Result
 ↓
Response
 ↓
Frontend
```

---

# 80. API Observability

Every API request should ideally generate:

```
Request ID
User ID
Endpoint
HTTP Method
Status
Latency
Error
Timestamp
```

For AI endpoints, additional information:

```
Model
Prompt Version
Tool Calls
Token Usage
AI Latency
```

Sensitive prompt/data contents should not be logged indiscriminately.

---

# 81. Request ID

Each request should have a unique identifier.

Example:

```
X-Request-ID: req_123456
```

This allows developers to trace a request across services.

---

# 82. API Logging

Logs should contain useful operational information.

Example:

```
INFO
request_id=req_123
endpoint=/api/v1/datasets
status=200
latency=142ms
```

Logs should not contain:

- Passwords
- Authentication tokens
- API secrets
- Unnecessary personal data
- Raw sensitive dataset contents

---

# 83. API Documentation Standard

The API should eventually be documented using:

> OpenAPI Specification
> 

This allows tools to generate:

- Interactive documentation
- Client SDKs
- Request validation
- API testing
- Type definitions

---

# 84. OpenAPI Structure

Conceptually:

```
openapi/
│
├── openapi.yaml
├── schemas/
├── paths/
└── components/
```

Or a generated specification from the backend framework.

---

# 85. API Documentation UI

A future development environment may expose:

```
/api/docs
```

and:

```
/api/openapi.json
```

The exact implementation depends on the backend framework.

---

# 86. API Testing

Every important endpoint should eventually have:

### Unit Tests

Test individual functions.

### Integration Tests

Test API + service + database interactions.

### Contract Tests

Verify that frontend expectations match backend API schemas.

### Security Tests

Test unauthorized access.

### Load Tests

Test API behavior under concurrent requests.

---

# 87. Example API Test

```
POST /api/v1/ai/chat

Given:
Valid authenticated user
Valid dataset

When:
User asks:
"Which region has the highest revenue?"

Then:
HTTP 200

And:
Response contains analysis_id

And:
Result references the correct dataset version
```

---

# 88. API Performance Targets

Initial targets may include:

```
Simple API request:
< 300 ms target

Dataset metadata:
< 500 ms target

Cached analysis:
< 500 ms target

AI request:
Dependent on model / processing

Large dataset processing:
Asynchronous
```

These are engineering targets, not guarantees, and will be validated through benchmarking.

---

# 89. API Architecture Principles

### Principle 1 — Consistency

All endpoints should follow consistent conventions.

### Principle 2 — Validation

Never trust client input.

### Principle 3 — Authorization

Every protected resource must be permission-checked.

### Principle 4 — Traceability

Important operations should have IDs.

### Principle 5 — Asynchronous Processing

Long-running operations should use background jobs.

### Principle 6 — Versioning

Breaking API changes should be versioned.

### Principle 7 — Observability

Important API behavior should be measurable.

### Principle 8 — Predictable Errors

Clients should receive structured errors.

### Principle 9 — Minimal Data Exposure

Responses should return only required information.

### Principle 10 — Documentation

The API contract should remain synchronized with implementation.

---

# 90. API Endpoint Summary

## Authentication

```
POST   /auth/register
POST   /auth/login
POST   /auth/logout
POST   /auth/refresh
POST   /auth/forgot-password
POST   /auth/reset-password
GET    /auth/me
```

## Users

```
GET    /users/me
PATCH  /users/me
PATCH  /users/me/password
DELETE /users/me
```

## Workspaces

```
GET    /workspaces
POST   /workspaces
GET    /workspaces/{id}
PATCH  /workspaces/{id}
DELETE /workspaces/{id}
```

## Datasets

```
GET    /datasets
POST   /datasets
GET    /datasets/{id}
PATCH  /datasets/{id}
DELETE /datasets/{id}

POST   /datasets/{id}/upload
GET    /datasets/{id}/preview
GET    /datasets/{id}/schema
GET    /datasets/{id}/profile
GET    /datasets/{id}/quality

GET    /datasets/{id}/versions
GET    /datasets/{id}/versions/{version}
```

## Jobs

```
GET    /jobs/{id}
```

## Analysis

```
GET    /analyses
POST   /analyses
GET    /analyses/{id}
DELETE /analyses/{id}
```

## AI

```
POST   /ai/chat
GET    /ai/suggestions
POST   /ai/insights
GET    /ai/conversations
```

## Dashboards

```
GET    /dashboards
POST   /dashboards
GET    /dashboards/{id}
PATCH  /dashboards/{id}
DELETE /dashboards/{id}

POST   /dashboards/generate
POST   /dashboards/{id}/ai-modify

GET    /dashboards/{id}/versions
POST   /dashboards/{id}/versions/{version}/restore

POST   /dashboards/{id}/widgets
PATCH  /dashboards/{id}/widgets/{widget_id}
DELETE /dashboards/{id}/widgets/{widget_id}

POST   /dashboards/{id}/export
```

## Conversations

```
GET    /conversations
POST   /conversations
GET    /conversations/{id}
PATCH  /conversations/{id}
DELETE /conversations/{id}

GET    /conversations/{id}/messages
```

## Reports

```
GET    /reports
POST   /reports
GET    /reports/{id}
DELETE /reports/{id}
```

## Notifications

```
GET    /notifications
PATCH  /notifications/{id}/read
PATCH  /notifications/read-all
```

---

# 91. Complete API Flow

The complete system can now be represented as:

```
                         FRONTEND
                            │
                            ▼
                       REST API
                            │
        ┌───────────────────┼────────────────────┐
        │                   │                    │
        ▼                   ▼                    ▼
    DATA API            AI API             DASHBOARD API
        │                   │                    │
        ▼                   ▼                    ▼
DATA ENGINEERING      AI ORCHESTRATOR       DASHBOARD ENGINE
        │                   │                    │
        │          ┌────────┼────────┐           │
        │          ▼        ▼        ▼           │
        │       Context   Tools     LLM          │
        │          │        │                     │
        └──────────┼────────┼─────────────────────┘
                   ▼
             ANALYTICAL LAYER
                   │
             ┌─────┴─────┐
             ▼           ▼
          DuckDB      PostgreSQL
             │
             ▼
          Storage
```

---

# 92. API Completion Criteria

The API architecture will be considered ready for implementation when:

1. Authentication endpoints are defined.
2. User endpoints are defined.
3. Workspace endpoints are defined.
4. Dataset endpoints are defined.
5. Upload API is defined.
6. Processing jobs are defined.
7. Profiling APIs are defined.
8. Quality APIs are defined.
9. Analysis APIs are defined.
10. AI APIs are defined.
11. Dashboard APIs are defined.
12. Conversation APIs are defined.
13. Report APIs are defined.
14. Error format is defined.
15. Validation strategy is defined.
16. Pagination is defined.
17. Filtering is defined.
18. Rate limiting is defined.
19. Authorization boundaries are defined.
20. Observability requirements are defined.
21. OpenAPI documentation is planned.
22. API testing strategy is defined.

---

# 93. Current API Status

**Architecture:** REST

**Format:** JSON

**Protocol:** HTTPS

**Versioning:** `/api/v1`

**Authentication:** To be finalized in Security document

**Validation:** Backend + Frontend

**Documentation:** OpenAPI

**Long-running Operations:** Background Jobs

**AI Streaming:** Future SSE implementation

**Observability:** Request IDs + structured logging

**Status:** Architecture Draft

**Version:** 0.1.0