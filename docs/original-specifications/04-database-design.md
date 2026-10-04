# 04 — Database Design

# InsightFlow AI

## Database Design

**Project:** InsightFlow AI

**Subtitle:** AI-Driven Automated Data Analysis & Context-Aware Dashboard Generation

**Document:** Database Design

**Version:** 0.1.0

**Status:** Draft

**Project Phase:** Phase 0 — Documentation

**Previous Document:** 03 — System Architecture

**Next Document:** 05 — AI Architecture

**Primary Database:** PostgreSQL

---

# 1. Database Overview

InsightFlow AI will use **PostgreSQL** as its primary relational database.

The database will store application metadata and structured information required to operate the platform.

The database will **not necessarily store the raw contents of every uploaded dataset directly inside PostgreSQL**.

Instead, the architecture will separate:

```
Application Metadata
        ↓
   PostgreSQL

Large Dataset Files
        ↓
   Object Storage
```

This separation allows the system to manage large files more efficiently while maintaining structured metadata in a relational database.

---

# 2. Database Objectives

The database architecture must provide:

1. Data integrity
2. Referential integrity
3. Secure data isolation
4. Efficient querying
5. Scalability
6. Transactional consistency
7. Auditability
8. Version management
9. Analytical traceability
10. Maintainability
11. Extensibility
12. Appropriate indexing

---

# 3. Database Responsibilities

PostgreSQL will primarily manage:

```
Users
Roles
Permissions
Datasets
Dataset Versions
Dataset Metadata
Analyses
Analysis Results
Conversations
Messages
Tool Calls
Dashboards
Dashboard Versions
Dashboard Widgets
AI Evaluations
Audit Logs
System Configuration
```

The database will provide the persistent state required by the application.

---

# 4. Data Storage Architecture

The complete storage architecture is:

```
                    INSIGHTFLOW AI
                           │
             ┌─────────────┴─────────────┐
             │                           │
             ▼                           ▼
       PostgreSQL                  Object Storage
             │                           │
             │                           │
      Application Data              Dataset Files
             │                           │
             ├── Users                   ├── CSV
             ├── Datasets                ├── XLSX
             ├── Analyses                ├── JSON
             ├── Dashboards              └── Parquet
             ├── Conversations
             └── Metadata
```

PostgreSQL stores references to objects in object storage rather than requiring all large files to be stored inside relational tables.

---

# 5. Database Design Principles

The database will follow these principles.

## 5.1 Data Integrity

Invalid relationships and inconsistent records should be prevented through:

- Primary keys
- Foreign keys
- Unique constraints
- Check constraints
- Not-null constraints

---

## 5.2 Referential Integrity

Relationships between entities must remain valid.

For example:

```
User
 ↓
Dataset
 ↓
Analysis
 ↓
Dashboard
```

An analysis should not reference a dataset that does not exist.

---

## 5.3 Data Isolation

Every user-owned resource must be associated with an owner or workspace.

Access control will be enforced by the backend.

---

## 5.4 Normalization

The database will initially follow a normalized relational design to reduce unnecessary duplication.

Denormalization may be introduced later where performance measurements justify it.

---

## 5.5 Versioning

Important resources such as datasets and dashboards should support versioning.

---

## 5.6 Auditability

Important actions should be traceable through audit records.

---

# 6. Entity Overview

The initial logical data model contains the following entities:

```
User
Role
Permission
UserRole
RolePermission

Dataset
DatasetVersion
DatasetColumn

Analysis
AnalysisResult
ToolCall

Conversation
Message

Dashboard
DashboardVersion
DashboardWidget

Evaluation
EvaluationCase
EvaluationResult

AuditLog
```

---

# 7. Entity Relationship Overview

The high-level relationships are:

```
                         ┌──────────┐
                         │   Role   │
                         └────┬─────┘
                              │
                              │
                         UserRole
                              │
                              ▼
┌──────────┐             ┌──────────┐
│   User   │────────────▶│ Dataset  │
└────┬─────┘             └────┬─────┘
     │                         │
     │                         ▼
     │                  DatasetVersion
     │                         │
     │                         ▼
     │                   DatasetColumn
     │
     ├──────────────────────┐
     │                      │
     ▼                      ▼
Conversation              Analysis
     │                      │
     ▼                      ├──────────────┐
  Message                   │              │
                            ▼              ▼
                        ToolCall     AnalysisResult
                            │
                            │
                            ▼
                       Dashboard
                            │
                            ▼
                    DashboardVersion
                            │
                            ▼
                     DashboardWidget
```

---

# 8. User Entity

The `users` table represents application users.

## Purpose

Stores identity and account information.

## Proposed Fields

| Field | Type | Constraints | Description |
| --- | --- | --- | --- |
| id | UUID | PK | Unique user identifier |
| email | VARCHAR | UNIQUE, NOT NULL | User email |
| password_hash | VARCHAR | NULL | Secure password hash |
| full_name | VARCHAR | NOT NULL | User name |
| is_active | BOOLEAN | NOT NULL | Account status |
| created_at | TIMESTAMP | NOT NULL | Creation timestamp |
| updated_at | TIMESTAMP | NOT NULL | Last update |

Additional authentication fields may be added later.

---

# 9. Role Entity

The `roles` table defines application roles.

Example roles:

```
ADMIN
ANALYST
BUSINESS_USER
RESEARCHER
VIEWER
```

## Proposed Fields

| Field | Type | Constraints |
| --- | --- | --- |
| id | UUID | PK |
| name | VARCHAR | UNIQUE |
| description | TEXT | NULL |
| created_at | TIMESTAMP | NOT NULL |

---

# 10. Permission Entity

Permissions define individual actions.

Examples:

```
dataset:create
dataset:read
dataset:update
dataset:delete

analysis:create
analysis:read

dashboard:create
dashboard:read
dashboard:update
dashboard:delete

user:manage
system:manage
```

## Proposed Fields

| Field | Type | Constraints |
| --- | --- | --- |
| id | UUID | PK |
| name | VARCHAR | UNIQUE |
| description | TEXT | NULL |
| created_at | TIMESTAMP | NOT NULL |

---

# 11. UserRole Entity

A user may have one or more roles.

This creates a many-to-many relationship:

```
User
  ↕
UserRole
  ↕
Role
```

## Proposed Fields

| Field | Type | Constraints |
| --- | --- | --- |
| user_id | UUID | FK |
| role_id | UUID | FK |

Composite primary key:

```
(user_id, role_id)
```

---

# 12. RolePermission Entity

Roles may contain multiple permissions.

Relationship:

```
Role
  ↕
RolePermission
  ↕
Permission
```

## Proposed Fields

| Field | Type | Constraints |
| --- | --- | --- |
| role_id | UUID | FK |
| permission_id | UUID | FK |

Composite primary key:

```
(role_id, permission_id)
```

---

# 13. Dataset Entity

The `datasets` table represents a logical dataset owned or managed by a user.

A dataset is different from the physical uploaded file.

For example:

```
Dataset:
Sales Data

Version 1:
sales_january.csv

Version 2:
sales_february.csv
```

The dataset represents the logical resource while versions represent individual states.

## Proposed Fields

| Field | Type | Constraints | Description |
| --- | --- | --- | --- |
| id | UUID | PK | Dataset ID |
| owner_id | UUID | FK | Dataset owner |
| name | VARCHAR | NOT NULL | Dataset name |
| description | TEXT | NULL | Description |
| status | VARCHAR | NOT NULL | Processing status |
| current_version_id | UUID | NULL | Current dataset version |
| created_at | TIMESTAMP | NOT NULL | Creation time |
| updated_at | TIMESTAMP | NOT NULL | Last update |

---

# 14. Dataset Status

Possible states:

```
UPLOADING
VALIDATING
PROCESSING
READY
FAILED
ARCHIVED
DELETED
```

The application should control valid state transitions.

---

# 15. DatasetVersion Entity

Each uploaded or processed version of a dataset will have its own record.

## Proposed Fields

| Field | Type | Constraints |
| --- | --- | --- |
| id | UUID | PK |
| dataset_id | UUID | FK |
| version_number | INTEGER | NOT NULL |
| object_storage_key | VARCHAR | NOT NULL |
| file_name | VARCHAR | NOT NULL |
| file_type | VARCHAR | NOT NULL |
| file_size_bytes | BIGINT | NOT NULL |
| row_count | BIGINT | NULL |
| column_count | INTEGER | NULL |
| checksum | VARCHAR | NULL |
| processing_status | VARCHAR | NOT NULL |
| created_at | TIMESTAMP | NOT NULL |

Unique constraint:

```
(dataset_id, version_number)
```

---

# 16. Why Dataset Versioning?

Versioning allows the system to distinguish:

```
Dataset
│
├── Version 1
│
├── Version 2
│
└── Version 3
```

This becomes important when:

- A dataset changes
- A user uploads a corrected file
- An analysis needs to be reproduced
- A dashboard was generated from an older dataset

It also improves analytical reproducibility.

---

# 17. DatasetColumn Entity

The `dataset_columns` table stores schema information for a dataset version.

## Proposed Fields

| Field | Type | Constraints |
| --- | --- | --- |
| id | UUID | PK |
| dataset_version_id | UUID | FK |
| column_name | VARCHAR | NOT NULL |
| data_type | VARCHAR | NOT NULL |
| ordinal_position | INTEGER | NOT NULL |
| nullable | BOOLEAN | NOT NULL |
| unique_count | BIGINT | NULL |
| missing_count | BIGINT | NULL |
| missing_percentage | DECIMAL | NULL |
| metadata | JSONB | NULL |

Potential metadata:

```
{
  "semantic_type": "currency",
  "is_identifier": false,
  "is_sensitive": false
}
```

---

# 18. Analysis Entity

The `analyses` table represents an analytical operation initiated by a user or system.

Examples:

```
"Find top products by revenue"

"Calculate monthly sales growth"

"Detect anomalies in transaction amount"
```

## Proposed Fields

| Field | Type | Constraints |
| --- | --- | --- |
| id | UUID | PK |
| dataset_id | UUID | FK |
| dataset_version_id | UUID | FK |
| user_id | UUID | FK |
| analysis_type | VARCHAR | NOT NULL |
| question | TEXT | NULL |
| status | VARCHAR | NOT NULL |
| created_at | TIMESTAMP | NOT NULL |
| completed_at | TIMESTAMP | NULL |
| execution_time_ms | INTEGER | NULL |

---

# 19. Analysis Status

Possible states:

```
PENDING
PLANNING
RUNNING
COMPLETED
FAILED
CANCELLED
```

---

# 20. AnalysisResult Entity

The `analysis_results` table stores the result of an analytical operation.

## Proposed Fields

| Field | Type | Constraints |
| --- | --- | --- |
| id | UUID | PK |
| analysis_id | UUID | FK |
| result_type | VARCHAR | NOT NULL |
| result_data | JSONB | NOT NULL |
| summary | TEXT | NULL |
| created_at | TIMESTAMP | NOT NULL |

The result may contain structured data such as:

```
{
  "columns": ["region", "revenue"],
  "rows": [
    ["North", 120000],
    ["South", 98000]
  ]
}
```

---

# 21. ToolCall Entity

The `tool_calls` table records analytical tools invoked by the AI.

This is important for traceability.

## Proposed Fields

| Field | Type | Constraints |
| --- | --- | --- |
| id | UUID | PK |
| analysis_id | UUID | FK |
| tool_name | VARCHAR | NOT NULL |
| input_data | JSONB | NOT NULL |
| output_data | JSONB | NULL |
| status | VARCHAR | NOT NULL |
| execution_time_ms | INTEGER | NULL |
| error_message | TEXT | NULL |
| created_at | TIMESTAMP | NOT NULL |

---

# 22. Why Store Tool Calls?

Suppose the user asks:

> "Which region has the highest revenue?"
> 

We want to know:

```
Question
   ↓
AI Plan
   ↓
Tool:
run_sql
   ↓
SQL
   ↓
Result
   ↓
Final Answer
```

Storing tool calls allows us to:

- Debug AI behavior
- Audit analytical operations
- Evaluate tool selection
- Reproduce analyses
- Investigate failures
- Measure latency
- Improve the AI system

---

# 23. Conversation Entity

The `conversations` table represents an analytics conversation.

## Proposed Fields

| Field | Type | Constraints |
| --- | --- | --- |
| id | UUID | PK |
| user_id | UUID | FK |
| dataset_id | UUID | FK, NULL |
| title | VARCHAR | NULL |
| status | VARCHAR | NOT NULL |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

A conversation may optionally be associated with a dataset.

---

# 24. Message Entity

The `messages` table stores conversation messages.

## Proposed Fields

| Field | Type | Constraints |
| --- | --- | --- |
| id | UUID | PK |
| conversation_id | UUID | FK |
| role | VARCHAR | NOT NULL |
| content | TEXT | NOT NULL |
| metadata | JSONB | NULL |
| created_at | TIMESTAMP | NOT NULL |

Possible roles:

```
USER
ASSISTANT
SYSTEM
TOOL
```

---

# 25. Message Metadata

Metadata may contain information such as:

```
{
  "analysis_id": "uuid",
  "tool_call_ids": ["uuid"],
  "dataset_version_id": "uuid"
}
```

This allows conversational messages to be connected to actual analytical operations.

---

# 26. Dashboard Entity

The `dashboards` table represents a logical dashboard.

## Proposed Fields

| Field | Type | Constraints |
| --- | --- | --- |
| id | UUID | PK |
| owner_id | UUID | FK |
| dataset_id | UUID | FK |
| name | VARCHAR | NOT NULL |
| description | TEXT | NULL |
| status | VARCHAR | NOT NULL |
| current_version_id | UUID | NULL |
| created_at | TIMESTAMP | NOT NULL |
| updated_at | TIMESTAMP | NOT NULL |

---

# 27. DashboardVersion Entity

Dashboards may have multiple versions.

## Proposed Fields

| Field | Type | Constraints |
| --- | --- | --- |
| id | UUID | PK |
| dashboard_id | UUID | FK |
| version_number | INTEGER | NOT NULL |
| layout_config | JSONB | NOT NULL |
| created_by | UUID | FK |
| created_at | TIMESTAMP | NOT NULL |

Unique constraint:

```
(dashboard_id, version_number)
```

---

# 28. DashboardWidget Entity

A dashboard consists of multiple widgets.

## Proposed Fields

| Field | Type | Constraints |
| --- | --- | --- |
| id | UUID | PK |
| dashboard_version_id | UUID | FK |
| widget_type | VARCHAR | NOT NULL |
| title | VARCHAR | NULL |
| configuration | JSONB | NOT NULL |
| position_x | INTEGER | NOT NULL |
| position_y | INTEGER | NOT NULL |
| width | INTEGER | NOT NULL |
| height | INTEGER | NOT NULL |
| created_at | TIMESTAMP | NOT NULL |

---

# 29. Widget Configuration

A widget may contain structured configuration.

Example:

```
{
  "type": "line_chart",
  "xField": "month",
  "yField": "revenue",
  "aggregation": "sum"
}
```

Another example:

```
{
  "type": "kpi",
  "metric": "total_revenue",
  "aggregation": "sum",
  "format": "currency"
}
```

JSONB provides flexibility while the application-level schema ensures validation.

---

# 30. Evaluation Entity

The `evaluations` table represents an AI evaluation run.

## Proposed Fields

| Field | Type | Constraints |
| --- | --- | --- |
| id | UUID | PK |
| name | VARCHAR | NOT NULL |
| model_name | VARCHAR | NULL |
| evaluation_type | VARCHAR | NOT NULL |
| status | VARCHAR | NOT NULL |
| started_at | TIMESTAMP | NULL |
| completed_at | TIMESTAMP | NULL |
| created_at | TIMESTAMP | NOT NULL |

---

# 31. EvaluationCase Entity

An evaluation case represents an individual benchmark question.

Example:

```
Question:
Which region has the highest revenue?

Expected:
North

Expected Tool:
run_sql
```

## Proposed Fields

| Field | Type | Constraints |
| --- | --- | --- |
| id | UUID | PK |
| evaluation_id | UUID | FK |
| question | TEXT | NOT NULL |
| expected_result | JSONB | NOT NULL |
| expected_tool | VARCHAR | NULL |
| created_at | TIMESTAMP | NOT NULL |

---

# 32. EvaluationResult Entity

Stores the actual evaluation result.

## Proposed Fields

| Field | Type | Constraints |
| --- | --- | --- |
| id | UUID | PK |
| evaluation_case_id | UUID | FK |
| actual_result | JSONB | NULL |
| score | DECIMAL | NULL |
| passed | BOOLEAN | NOT NULL |
| latency_ms | INTEGER | NULL |
| explanation | TEXT | NULL |
| created_at | TIMESTAMP | NOT NULL |

---

# 33. AuditLog Entity

The audit log records important system actions.

## Proposed Fields

| Field | Type | Constraints |
| --- | --- | --- |
| id | UUID | PK |
| user_id | UUID | FK, NULL |
| action | VARCHAR | NOT NULL |
| resource_type | VARCHAR | NULL |
| resource_id | UUID | NULL |
| metadata | JSONB | NULL |
| ip_address | INET | NULL |
| created_at | TIMESTAMP | NOT NULL |

Examples:

```
USER_LOGIN
DATASET_CREATED
DATASET_DELETED
ANALYSIS_STARTED
DASHBOARD_CREATED
DASHBOARD_UPDATED
ROLE_CHANGED
PERMISSION_DENIED
```

---

# 34. Relationship Summary

## User → Dataset

One user can own many datasets.

```
User 1 ─────── N Dataset
```

---

## Dataset → DatasetVersion

One dataset can have multiple versions.

```
Dataset 1 ─────── N DatasetVersion
```

---

## DatasetVersion → DatasetColumn

One dataset version can contain many columns.

```
DatasetVersion 1 ─────── N DatasetColumn
```

---

## Dataset → Analysis

One dataset can have many analyses.

```
Dataset 1 ─────── N Analysis
```

---

## Analysis → ToolCall

One analysis can invoke multiple tools.

```
Analysis 1 ─────── N ToolCall
```

---

## Analysis → AnalysisResult

An analysis can produce one or more results depending on the operation.

```
Analysis 1 ─────── N AnalysisResult
```

---

## User → Conversation

A user can have multiple conversations.

```
User 1 ─────── N Conversation
```

---

## Conversation → Message

A conversation contains multiple messages.

```
Conversation 1 ─────── N Message
```

---

## User → Dashboard

A user can create multiple dashboards.

```
User 1 ─────── N Dashboard
```

---

## Dashboard → DashboardVersion

A dashboard can have multiple versions.

```
Dashboard 1 ─────── N DashboardVersion
```

---

## DashboardVersion → DashboardWidget

A dashboard version can contain multiple widgets.

```
DashboardVersion 1 ─────── N DashboardWidget
```

---

# 35. Complete Entity Relationship Model

The conceptual ER model is:

```
                                  ┌──────────────┐
                                  │    Role      │
                                  └──────┬───────┘
                                         │
                                    UserRole
                                         │
                                         ▼
┌──────────────┐                  ┌──────────────┐
│    User      │─────────────────▶│   Dataset    │
└──────┬───────┘                  └──────┬───────┘
       │                                 │
       │                                 ▼
       │                         ┌─────────────────┐
       │                         │ DatasetVersion  │
       │                         └────────┬────────┘
       │                                  │
       │                                  ▼
       │                         ┌─────────────────┐
       │                         │ DatasetColumn   │
       │                         └─────────────────┘
       │
       ├──────────────────────┐
       │                      │
       ▼                      ▼
┌──────────────┐       ┌──────────────┐
│ Conversation │       │   Analysis   │
└──────┬───────┘       └──────┬───────┘
       │                      │
       ▼                      ├───────────────┐
┌──────────────┐              │               │
│   Message    │              ▼               ▼
└──────────────┘       ┌──────────────┐ ┌──────────────┐
                       │   ToolCall   │ │AnalysisResult│
                       └──────────────┘ └──────────────┘

       User
        │
        ▼
┌──────────────┐
│  Dashboard   │
└──────┬───────┘
       │
       ▼
┌────────────────────┐
│ DashboardVersion   │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│ DashboardWidget    │
└────────────────────┘

Evaluation
    │
    ├── EvaluationCase
    │       │
    │       └── EvaluationResult
    │
    └── EvaluationRun

User
  │
  └──── AuditLog
```

---

# 36. Primary Keys

The system will primarily use UUIDs as primary keys.

Example:

```
user_id       → UUID
dataset_id    → UUID
analysis_id   → UUID
dashboard_id  → UUID
```

UUIDs provide globally unique identifiers and are suitable for distributed systems.

---

# 37. Foreign Keys

Foreign keys will enforce relationships.

Examples:

```
datasets.owner_id
        ↓
users.id
```

```
analyses.dataset_id
        ↓
datasets.id
```

```
messages.conversation_id
        ↓
conversations.id
```

```
dashboard_widgets.dashboard_version_id
        ↓
dashboard_versions.id
```

---

# 38. Indexing Strategy

Indexes will be created for frequently queried fields.

Potential indexes:

```
users.email

datasets.owner_id
datasets.created_at

dataset_versions.dataset_id

analyses.dataset_id
analyses.user_id
analyses.created_at

conversations.user_id

messages.conversation_id
messages.created_at

dashboards.owner_id
dashboards.dataset_id

tool_calls.analysis_id

audit_logs.user_id
audit_logs.created_at
```

Indexes will be added based on actual query patterns and performance measurements.

---

# 39. JSONB Strategy

PostgreSQL JSONB will be used selectively.

Appropriate uses include:

- Dataset metadata
- Tool inputs
- Tool outputs
- Analysis results
- Dashboard configuration
- Widget configuration
- Evaluation results
- Flexible metadata

Structured relational data should remain in normal relational columns when its structure is known and frequently queried.

The principle is:

> **Use relational columns for stable entities and JSONB for flexible or evolving structures.**
> 

---

# 40. Transaction Strategy

Operations requiring multiple related database changes should use database transactions.

Example:

```
Create Dataset
      ↓
Create Dataset Version
      ↓
Create Metadata
      ↓
Create Processing Job
```

If a critical step fails, the transaction should prevent an inconsistent database state where appropriate.

---

# 41. Dataset Deletion Strategy

Dataset deletion must consider related resources.

Potential strategy:

```
Delete Dataset
      ↓
Archive / Delete Dataset Versions
      ↓
Invalidate Analyses
      ↓
Invalidate Dashboards
      ↓
Remove Object Storage
      ↓
Record Audit Event
```

The final retention policy will be defined in the Security and Deployment documentation.

---

# 42. Dashboard Versioning Strategy

Dashboard modifications should not necessarily overwrite historical versions.

Example:

```
Dashboard
│
├── Version 1
│
├── Version 2
│
└── Version 3 ← Current
```

This enables:

- Undo
- Rollback
- Auditing
- Comparison
- Reproducibility

---

# 43. Analytical Reproducibility

An analysis should be traceable to:

```
User
 ↓
Dataset
 ↓
Dataset Version
 ↓
Question
 ↓
Analysis Plan
 ↓
Tool Calls
 ↓
Results
 ↓
AI Explanation
```

This is important because a result may change when the dataset changes.

Therefore, analyses should reference the specific dataset version used.

---

# 44. Data Lifecycle

The general dataset lifecycle is:

```
Upload
  ↓
Validate
  ↓
Store
  ↓
Process
  ↓
Profile
  ↓
Analyze
  ↓
Generate Insights
  ↓
Generate Dashboard
  ↓
Archive
  ↓
Delete
```

Each stage should be represented by appropriate application state.

---

# 45. Security Considerations

The database must protect:

- User identities
- Dataset metadata
- Dataset references
- Analysis history
- Conversations
- AI tool calls
- Dashboard configurations
- Audit logs

Security mechanisms will include:

- Least-privilege database users
- Encrypted connections
- Secure credentials
- Access control
- Parameterized queries
- Backend authorization
- Dataset ownership checks

---

# 46. Multi-Tenant Data Isolation

InsightFlow AI will initially use logical tenant isolation.

Every user-owned resource will be associated with an owner or workspace.

Example:

```
User A
 ├── Dataset A1
 ├── Dataset A2
 └── Dashboard A1

User B
 ├── Dataset B1
 └── Dashboard B1
```

User A must never access User B's resources unless explicit sharing functionality is introduced.

Future versions may use PostgreSQL Row-Level Security where appropriate.

---

# 47. Database Backup Strategy

Production deployment should include:

- Automated backups
- Point-in-time recovery where supported
- Backup encryption
- Backup retention
- Recovery testing

A backup strategy is only considered reliable if restoration is periodically tested.

---

# 48. Database Migration Strategy

Schema changes will be managed through version-controlled migrations.

Potential tooling:

- Alembic
- SQL migration scripts

The migration process will be:

```
Schema Change
      ↓
Migration File
      ↓
Review
      ↓
Testing
      ↓
Staging
      ↓
Production
```

Database schema changes should not be made manually in production.

---

# 49. Database Performance Strategy

Performance will be monitored using:

- Query execution time
- Index usage
- Connection pool usage
- Database CPU
- Database memory
- Slow query logs
- Table size
- Index size

Optimization should be based on measurements rather than assumptions.

---

# 50. Database Scalability

Initial scaling strategy:

```
Application
      ↓
Connection Pool
      ↓
PostgreSQL
```

Future scaling options may include:

- Read replicas
- Connection pooling
- Partitioning
- Query optimization
- Caching
- Database scaling
- Separate analytical storage

---

# 51. Why PostgreSQL?

PostgreSQL is proposed because it provides:

- Strong relational integrity
- Transactions
- JSONB
- Indexing
- Mature ecosystem
- Excellent SQL support
- Extensibility
- Good compatibility with Python
- Strong production adoption

It also allows the project to demonstrate professional relational-database skills.

---

# 52. Why Not Store Everything in PostgreSQL?

Large analytical datasets may become inefficient or unnecessarily expensive to store directly as relational application records.

Instead:

```
PostgreSQL
    ↓
Metadata + Application State

Object Storage
    ↓
Large Dataset Files

DuckDB
    ↓
Analytical Query Execution
```

This separation is central to the data architecture.

---

# 53. PostgreSQL vs DuckDB

The two systems have different responsibilities.

### PostgreSQL

Used for:

- Users
- Authentication metadata
- Datasets
- Dashboards
- Conversations
- Analysis metadata
- Application state

### DuckDB

Used for:

- Analytical queries
- Aggregations
- Dataset exploration
- SQL analysis
- Local analytical processing

Conceptually:

```
PostgreSQL = Application Database

DuckDB = Analytical Engine
```

They are complementary rather than competing components in this architecture.

---

# 54. Initial Database Schema Summary

The initial schema will contain approximately:

```
users
roles
permissions
user_roles
role_permissions

datasets
dataset_versions
dataset_columns

analyses
analysis_results
tool_calls

conversations
messages

dashboards
dashboard_versions
dashboard_widgets

evaluations
evaluation_cases
evaluation_results

audit_logs
```

Additional tables may be introduced as implementation requirements become clearer.

---

# 55. Future Database Extensions

Future versions may introduce:

```
workspaces
workspace_members
dataset_shares
dashboard_shares
api_keys
notifications
scheduled_reports
alerts
business_glossary
context_documents
embedding_metadata
model_registry
ai_usage
billing
```

These are not required for the initial MVP.

---

# 56. Database Design Principles Summary

The database architecture follows these principles:

1. PostgreSQL is the primary application database.
2. Large dataset files are stored separately.
3. UUIDs are used as primary identifiers.
4. Foreign keys enforce relationships.
5. Dataset versions provide reproducibility.
6. Dashboard versions provide rollback.
7. JSONB is used for flexible structures.
8. Analytical operations reference dataset versions.
9. Tool calls are stored for AI traceability.
10. Audit logs support security and accountability.
11. Indexes are added based on query patterns.
12. Database migrations are version controlled.
13. User resources are logically isolated.
14. Backups and recovery must be tested.
15. Database optimization should be evidence-driven.

---

# 57. Current Database Status

**Database:** PostgreSQL

**Schema Version:** 0.1.0

**Status:** Draft

**Primary Key Strategy:** UUID

**Application Data:** PostgreSQL

**Large Files:** Object Storage

**Analytical Queries:** DuckDB

**Data Processing:** Polars / Pandas

**Migration Strategy:** Alembic or equivalent

**Isolation Strategy:** Application-level ownership checks initially, with possible PostgreSQL Row-Level Security in future versions.

---

# 58. Next Database Phase

Before implementation, the following artifacts will eventually be created:

1. Entity Relationship Diagram
2. Complete SQL schema
3. Migration scripts
4. Index strategy
5. Constraint strategy
6. Seed data
7. Database testing strategy

These will be created after the architecture and AI requirements are sufficiently stable.

---

# 59. Database Completion Criteria

The database design will be considered ready for implementation when:

1. Core entities are defined.
2. Relationships are defined.
3. Primary keys are defined.
4. Foreign keys are defined.
5. Constraints are defined.
6. Versioning strategy is defined.
7. Data isolation strategy is defined.
8. Indexing strategy is defined.
9. Migration strategy is defined.
10. Backup strategy is defined.
11. Analytical reproducibility is addressed.
12. The ER diagram is finalized.
13. The schema can be mapped to application requirements.