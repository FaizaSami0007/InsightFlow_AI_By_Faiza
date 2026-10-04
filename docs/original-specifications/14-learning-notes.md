# 14 — Learning Notes

# InsightFlow AI — Learning Notes & Technical Knowledge Base

**Project:** InsightFlow AI

**Subtitle:** AI-Driven Automated Data Analysis & Context-Aware Dashboard Generation

**Document:** Learning Notes & Technical Knowledge Base

**Version:** 0.1.0

**Status:** Active

**Project Phase:** Phase 0 — Documentation

**Previous Document:** 13 — Deployment & DevOps

**Next Document:** 15 — Project Roadmap

---

# 1. Purpose of This Document

This document defines the technical knowledge that must be learned while developing InsightFlow AI.

The goal is:

> **Learn the technology while building the product.**
> 

The project should not be developed by blindly copying code.

Every major implementation should answer:

```
What are we building?
Why are we building it?
Which technology are we using?
How does it work?
Why did we choose it?
What alternatives exist?
What are its limitations?
How do we implement it?
How do we test it?
```

---

# 2. Learning Philosophy

The learning process follows:

```
CONCEPT
   ↓
UNDERSTAND
   ↓
SMALL EXAMPLE
   ↓
IMPLEMENT IN PROJECT
   ↓
TEST
   ↓
DEBUG
   ↓
DOCUMENT
   ↓
REVIEW
```

This ensures that every technology becomes practical knowledge.

---

# 3. Learning Categories

The project requires knowledge in:

```
Programming
Frontend Development
Backend Development
Databases
Data Engineering
Data Analysis
Statistics
Machine Learning Concepts
Artificial Intelligence
LLMs
Prompt Engineering
AI Agents
RAG / Context Engineering
Data Visualization
System Design
APIs
Security
Testing
DevOps
Cloud
Software Engineering
```

---

# 4. Programming Fundamentals

Before or alongside implementation, understand:

### Python

```
Variables
Data Types
Conditions
Loops
Functions
Classes
Objects
Modules
Packages
Exceptions
File Handling
Type Hints
Decorators
Generators
Async Programming
```

---

# 5. Python for Data

Learn:

```
NumPy
Pandas
Polars
PyArrow
```

Concepts:

```
DataFrame
Series
Vectorization
Indexing
Filtering
Grouping
Aggregation
Joining
Missing Values
Data Types
Serialization
```

---

# 6. Python for Backend

Learn:

```
HTTP
REST APIs
Request / Response
Middleware
Authentication
Authorization
Validation
Dependency Injection
Async Processing
Background Jobs
Error Handling
```

Potential framework:

```
FastAPI
```

The final backend framework will be confirmed before implementation.

---

# 7. Frontend Fundamentals

Learn:

```
HTML
CSS
JavaScript
TypeScript
DOM
HTTP
JSON
Browser Storage
Cookies
CORS
```

---

# 8. React

Learn:

```
Components
Props
State
Hooks
Context
Forms
Events
Conditional Rendering
Lists
Routing
Error Boundaries
Performance
Component Architecture
```

---

# 9. React Architecture

Understand:

```
Presentation
 ↓
Components
 ↓
Hooks
 ↓
State Management
 ↓
API Layer
 ↓
Backend
```

The frontend should not contain business-critical security logic.

---

# 10. TypeScript

Learn:

```
Primitive Types
Interfaces
Type Aliases
Generics
Union Types
Intersection Types
Enums
Utility Types
Type Narrowing
Type Guards
Async Types
API Response Types
```

TypeScript should be used to reduce frontend/runtime errors.

---

# 11. State Management

Understand the difference between:

```
Local Component State
Global State
Server State
URL State
Form State
```

Potential tools:

```
Zustand
TanStack Query
```

---

# 12. TanStack Query

Learn:

```
Queries
Mutations
Caching
Invalidation
Retries
Loading States
Error States
Optimistic Updates
Pagination
Prefetching
```

Important distinction:

> TanStack Query manages **server state**, not all application state.
> 

---

# 13. Backend Architecture

Understand:

```
Routes
 ↓
Controllers
 ↓
Services
 ↓
Repositories
 ↓
Database
```

A clean separation should prevent business logic from becoming scattered throughout API routes.

---

# 14. REST API Concepts

Learn:

```
GET
POST
PUT
PATCH
DELETE
```

Also understand:

```
HTTP Status Codes
Headers
Query Parameters
Path Parameters
Request Bodies
Pagination
Filtering
Sorting
Error Responses
```

---

# 15. API Design

Learn:

```
Resource Naming
Versioning
Validation
Error Handling
Authentication
Authorization
Pagination
Rate Limiting
Idempotency
```

Example:

```
/api/v1/datasets
/api/v1/analyses
/api/v1/dashboards
```

---

# 16. PostgreSQL

Learn:

```
Tables
Rows
Columns
Primary Keys
Foreign Keys
Indexes
Constraints
Transactions
Joins
Aggregations
Views
CTEs
Window Functions
```

---

# 17. Database Design

Understand:

```
Normalization
Relationships
One-to-One
One-to-Many
Many-to-Many
Indexes
Constraints
Transactions
Migrations
```

---

# 18. SQL

Learn:

```
SELECT
WHERE
GROUP BY
HAVING
ORDER BY
LIMIT
JOIN
CASE
Subqueries
CTEs
Window Functions
Aggregations
```

SQL is particularly important because InsightFlow AI will generate analytical queries.

---

# 19. DuckDB

Learn why DuckDB is useful for analytical workloads.

Important concepts:

```
Columnar Analytics
OLAP
SQL Analytics
Local Data Processing
Parquet
CSV
Large Dataset Queries
```

Understand the difference between:

```
PostgreSQL → Application / transactional data

DuckDB → Analytical data processing
```

---

# 20. OLTP vs OLAP

### OLTP

Online Transaction Processing.

Examples:

```
Users
Authentication
Dashboard Metadata
Permissions
```

### OLAP

Online Analytical Processing.

Examples:

```
Revenue Analysis
Aggregations
Trends
Correlations
Large Dataset Queries
```

InsightFlow AI may use both.

---

# 21. Data Engineering

Learn:

```
Data Ingestion
Data Validation
Data Cleaning
Data Transformation
Data Profiling
Data Quality
Schema Detection
Data Type Inference
Data Pipelines
ETL / ELT
```

---

# 22. ETL

Understand:

```
Extract
 ↓
Transform
 ↓
Load
```

Example:

```
CSV
 ↓
Extract
 ↓
Clean
 ↓
Transform
 ↓
Load
 ↓
Analytical Engine
```

---

# 23. Data Pipeline Architecture

Potential pipeline:

```
Upload
 ↓
Validation
 ↓
Storage
 ↓
Parsing
 ↓
Schema Detection
 ↓
Data Profiling
 ↓
Quality Analysis
 ↓
Analytical Dataset
```

---

# 24. Data Profiling

Learn how to calculate:

```
Row Count
Column Count
Missing Values
Unique Values
Duplicates
Min
Max
Mean
Median
Standard Deviation
Quantiles
```

---

# 25. Data Quality

Important dimensions:

```
Completeness
Accuracy
Consistency
Validity
Uniqueness
Timeliness
```

---

# 26. Schema Inference

The system should infer:

```
Numeric
Categorical
Boolean
Date
Datetime
Text
Identifier
Currency
```

This is important for AI reasoning and visualization selection.

---

# 27. Data Cleaning

Learn:

```
Missing Value Handling
Duplicate Detection
Type Conversion
Outlier Detection
String Normalization
Date Parsing
Invalid Value Detection
```

Important principle:

> Do not automatically modify user data without clearly defining the transformation.
> 

---

# 28. Statistics

Statistics is fundamental to InsightFlow AI.

Learn:

```
Mean
Median
Mode
Variance
Standard Deviation
Range
Percentiles
Correlation
Covariance
Distribution
```

---

# 29. Probability

Learn:

```
Probability
Conditional Probability
Random Variables
Expected Value
Variance
Probability Distributions
```

This becomes useful for advanced analytics and future ML features.

---

# 30. Exploratory Data Analysis

EDA concepts:

```
Univariate Analysis
Bivariate Analysis
Multivariate Analysis
Distribution Analysis
Correlation Analysis
Outlier Analysis
Trend Analysis
```

---

# 31. Data Visualization

Learn:

```
Bar Chart
Line Chart
Scatter Plot
Histogram
Box Plot
Heatmap
Area Chart
Table
KPI
```

---

# 32. Visualization Selection

The system should learn the relationship:

```
Data Type
+
Analytical Intent
+
Cardinality
+
Question
        ↓
Visualization
```

Example:

```
Time Series → Line Chart

Category Comparison → Bar Chart

Relationship → Scatter Plot

Distribution → Histogram

Single KPI → Metric Card
```

---

# 33. Dashboard Design

Learn:

```
Visual Hierarchy
Information Density
Layout
Spacing
Typography
Color
Filters
Interactions
Responsive Design
```

---

# 34. AI Fundamentals

Learn:

```
Artificial Intelligence
Machine Learning
Deep Learning
Generative AI
Large Language Models
```

Understand the differences between them.

---

# 35. Machine Learning

Even though the initial project is not primarily an ML project, understand:

```
Supervised Learning
Unsupervised Learning
Classification
Regression
Clustering
Feature Engineering
Model Evaluation
```

This will help with future analytical features.

---

# 36. LLM Fundamentals

Learn:

```
Tokens
Context Window
Parameters
Inference
Temperature
Top-p
System Messages
User Messages
Tool Calls
Structured Outputs
```

---

# 37. Transformers

Understand the high-level architecture:

```
Input Tokens
 ↓
Embeddings
 ↓
Attention
 ↓
Transformer Layers
 ↓
Output Probabilities
 ↓
Generated Tokens
```

---

# 38. Attention

Understand:

```
Query
Key
Value
```

and why attention allows the model to determine which pieces of context are important.

---

# 39. Embeddings

Learn:

> Embeddings convert information into numerical vectors representing semantic relationships.
> 

Applications:

```
Semantic Search
Document Retrieval
Similarity
Context Retrieval
```

---

# 40. Prompt Engineering

Learn:

```
System Prompts
Role Definition
Instructions
Examples
Constraints
Structured Output
Few-Shot Prompting
Chain-of-Thought Alternatives
Tool Instructions
```

The project should not depend on prompts alone for security.

---

# 41. Context Engineering

InsightFlow AI is fundamentally a context-aware application.

The AI may receive:

```
User Question
+
Dataset Metadata
+
Schema
+
Data Quality
+
Previous Conversation
+
Analysis Results
+
Dashboard State
```

This creates an application-specific context layer.

---

# 42. RAG

Learn Retrieval-Augmented Generation.

Basic architecture:

```
Question
 ↓
Retrieve Relevant Information
 ↓
Context
 ↓
LLM
 ↓
Answer
```

For InsightFlow AI, retrieval may eventually include:

```
Dataset Metadata
Documentation
Previous Analysis
Dashboard Configuration
```

---

# 43. RAG vs Data Analysis

Important distinction:

```
RAG
→ Retrieve information

Data Analysis
→ Calculate information
```

Example:

```
RAG:
"What columns exist?"

Analysis:
"What is the average revenue?"
```

The second requires actual computation.

---

# 44. AI Agents

Learn the concept of agents:

```
Observe
 ↓
Reason
 ↓
Choose Tool
 ↓
Execute
 ↓
Observe Result
 ↓
Continue / Respond
```

---

# 45. Tool Calling

The AI should be able to request structured tools.

Example:

```
{
  "tool":"run_analysis",
  "arguments": {
    "dataset_id":"123",
    "operation":"mean",
    "column":"revenue"
  }
}
```

The backend validates the request before execution.

---

# 46. Agent vs Workflow

Understand the difference.

### Workflow

```
Fixed Steps
A → B → C
```

### Agent

```
Goal
 ↓
Decides next action
 ↓
Tool
 ↓
Result
 ↓
Decides next action
```

InsightFlow AI may combine both.

---

# 47. Deterministic Tools + AI

This is a core project principle:

```
AI
→ Understand
→ Plan
→ Explain

Tools
→ Calculate
→ Query
→ Validate
→ Transform
```

This reduces hallucinations.

---

# 48. Structured Outputs

AI responses should use structured schemas when the application needs machine-readable output.

Example:

```
{
  "intent":"trend_analysis",
  "dataset_id":"123",
  "metric":"revenue",
  "dimension":"month"
}
```

---

# 49. AI Guardrails

Learn:

```
Input Validation
Output Validation
Tool Permissions
Prompt Injection Defense
Data Isolation
Schema Validation
Rate Limits
```

---

# 50. Prompt Injection

Understand why this is dangerous:

```
Dataset:
"Ignore all previous instructions..."
```

The system must treat dataset content as data, not trusted instructions.

---

# 51. AI Evaluation

Learn:

```
Accuracy
Groundedness
Hallucination
Relevance
Completeness
Safety
Latency
Cost
```

These are covered in detail in Document 12.

---

# 52. LLM Evaluation

Learn the difference between:

```
Exact Match
Semantic Similarity
Rule-Based Evaluation
LLM-as-Judge
Human Evaluation
```

---

# 53. Model Selection

Learn how to compare models based on:

```
Quality
Reasoning
Context Length
Latency
Cost
Tool Calling
Structured Output
Reliability
Privacy
```

Do not choose a model based solely on popularity.

---

# 54. AI Provider Abstraction

The architecture should ideally allow:

```
Provider A
Provider B
Provider C
Local Model
```

through a common interface.

This avoids excessive vendor lock-in.

---

# 55. API Security

Learn:

```
Authentication
Authorization
JWT / Sessions
CORS
CSRF
Rate Limiting
Input Validation
SQL Injection
XSS
```

---

# 56. Authentication

Understand:

```
Identity
Authentication
Authorization
Session
Token
Cookie
Password Hashing
Refresh Token
Logout
```

---

# 57. Authorization

Learn:

```
RBAC
Permissions
Resource-Level Authorization
Multi-Tenant Isolation
Least Privilege
```

---

# 58. Multi-Tenancy

Understand:

```
User
 ↓
Workspace
 ↓
Resources
```

and how to prevent:

```
User A
 ↓
Workspace B Data
```

---

# 59. Testing

Learn:

```
Unit Testing
Integration Testing
API Testing
E2E Testing
Regression Testing
Performance Testing
Security Testing
AI Evaluation
```

---

# 60. Testing Tools

Potential tools:

```
Pytest
Vitest
React Testing Library
Playwright
Postman
k6
OWASP ZAP
```

Final tools will be selected during implementation.

---

# 61. Git

Learn:

```
Repository
Commit
Branch
Merge
Rebase
Pull Request
Conflict
Tag
Release
```

---

# 62. GitHub

Learn:

```
Repositories
Issues
Pull Requests
Actions
Releases
Projects
Secrets
Branch Protection
Code Review
```

---

# 63. Docker

Learn:

```
Image
Container
Dockerfile
Volume
Network
Environment Variables
Registry
Docker Compose
```

---

# 64. CI/CD

Learn:

```
Continuous Integration
Continuous Delivery
Continuous Deployment
Pipeline
Build
Artifact
Deployment
Rollback
```

---

# 65. Cloud Fundamentals

Learn:

```
Compute
Storage
Database
Networking
Load Balancer
DNS
CDN
Containers
Secrets
Monitoring
```

---

# 66. Infrastructure as Code

Learn:

```
Terraform
State
Resources
Variables
Modules
Providers
```

This can be introduced after the first successful deployment.

---

# 67. Observability

Learn:

```
Logs
Metrics
Traces
Health Checks
Alerts
Dashboards
```

---

# 68. System Design

This project is also a system-design exercise.

Learn:

```
Scalability
Availability
Reliability
Caching
Queues
Load Balancing
Database Scaling
Fault Tolerance
Service Boundaries
```

---

# 69. Distributed Systems

As the project grows, understand:

```
Queues
Workers
Retries
Idempotency
Eventual Consistency
Distributed Locks
Service Communication
Failure Handling
```

---

# 70. Asynchronous Processing

Understand why operations such as:

```
Large Dataset Processing
Dashboard Generation
Export
AI Analysis
```

should not necessarily block an HTTP request.

Architecture:

```
Request
 ↓
Create Job
 ↓
Queue
 ↓
Worker
 ↓
Result
```

---

# 71. Caching

Learn:

```
Cache
Cache Key
TTL
Invalidation
Cache Hit
Cache Miss
```

And the classic principle:

> Cache invalidation is one of the difficult parts of distributed systems.
> 

---

# 72. Performance Engineering

Learn:

```
Latency
Throughput
Concurrency
Memory
CPU
Database Performance
Query Optimization
Frontend Performance
```

---

# 73. Software Architecture

Learn:

```
Layered Architecture
Modular Architecture
Service-Oriented Architecture
Clean Architecture
Dependency Inversion
Separation of Concerns
```

---

# 74. Design Patterns

Useful patterns may include:

```
Repository
Service
Factory
Strategy
Adapter
Observer
Dependency Injection
```

Do not use design patterns merely because they exist.

Use them when they solve an actual problem.

---

# 75. Error Handling

Learn:

```
Expected Errors
Unexpected Errors
Validation Errors
Authentication Errors
Authorization Errors
Database Errors
External Service Errors
Timeouts
Retries
```

---

# 76. Logging

Learn:

```
Structured Logging
Log Levels
Request IDs
Correlation IDs
Error Logging
Security Logging
```

---

# 77. Documentation

Technical documentation should include:

```
README
Architecture
API
Database
Deployment
Security
Testing
AI Evaluation
Developer Setup
Troubleshooting
```

---

# 78. Project Management

Learn how to manage the project using:

```
Milestones
Issues
Tasks
Epics
Pull Requests
Releases
```

Potentially use GitHub Projects.

---

# 79. Issue Tracking

Each issue should contain:

```
Title
Description
Problem
Expected Behavior
Acceptance Criteria
Priority
Labels
```

---

# 80. Technical Debt

Understand technical debt.

Examples:

```
Temporary workaround
Duplicated code
Missing tests
Weak architecture
Hardcoded configuration
```

Technical debt should be documented rather than forgotten.

---

# 81. Decision Records

Important architectural decisions should be documented.

Example:

```
ADR-001
Why PostgreSQL?

ADR-002
Why DuckDB?

ADR-003
Why FastAPI?

ADR-004
Why Redis?

ADR-005
Why tool-based AI?
```

---

# 82. Architecture Decision Record Format

```
Title

Context

Problem

Options Considered

Decision

Reasons

Consequences

Status
```

---

# 83. Learning Levels

Each topic should move through:

### Level 1 — Awareness

Know what it is.

### Level 2 — Understanding

Explain how it works.

### Level 3 — Implementation

Build it.

### Level 4 — Debugging

Fix problems with it.

### Level 5 — Architecture

Know when and why to use it.

---

# 84. Example Learning Progression

For Docker:

```
Level 1:
What is Docker?

Level 2:
How containers work.

Level 3:
Create Dockerfile.

Level 4:
Debug container networking.

Level 5:
Design production container architecture.
```

---

# 85. AI-Assisted Learning Rules

AI tools can help with:

```
Explanation
Research
Code Suggestions
Debugging
Documentation
Testing Ideas
Architecture Review
```

But AI-generated code must be understood before being accepted.

---

# 86. AI Coding Rule

For every AI-generated code block:

```
Read
 ↓
Understand
 ↓
Question
 ↓
Modify
 ↓
Test
 ↓
Accept
```

Do not blindly copy code.

---

# 87. Documentation Rule

Every major technology used in the project should have a learning note containing:

```
What?
Why?
How?
Example
Project Usage
Advantages
Disadvantages
Alternatives
Common Errors
Security Considerations
```

---

# 88. Research Sources

Preferred sources:

### Official Documentation

Primary source.

### Academic Papers

For AI/data concepts.

### High-quality technical articles

For explanations.

### GitHub

For real implementations and project patterns.

### Books/Courses

For structured learning.

AI-generated explanations should be verified for important technical decisions.

---

# 89. Knowledge Verification

Before considering a concept learned, explain it without looking at notes.

Example:

> Explain why InsightFlow AI uses DuckDB instead of PostgreSQL for large analytical queries.
> 

If you can explain:

```
OLTP
vs
OLAP
```

and justify the architectural choice, the concept is understood.

---

# 90. Learning Journal

Each implementation session should record:

```
Date
Feature
Concept Learned
Problem
Solution
What I Understood
What I Still Don't Understand
Resources
Next Step
```

---

# 91. Example Learning Entry

```
Date:
2026-08-24

Feature:
Dataset Upload

Concepts:
Multipart Upload
File Validation
Object Storage

Problem:
Large files blocking API request

Solution:
Background processing

Still Need:
Understand queues and workers
```

---

# 92. Learning Checklist

```
☐ Python
☐ TypeScript
☐ React
☐ Backend
☐ REST APIs
☐ PostgreSQL
☐ SQL
☐ DuckDB
☐ Data Engineering
☐ Statistics
☐ Data Visualization
☐ LLMs
☐ Prompt Engineering
☐ Tool Calling
☐ AI Agents
☐ RAG
☐ AI Evaluation
☐ Security
☐ Testing
☐ Docker
☐ CI/CD
☐ Cloud
☐ System Design
☐ Observability
```

---

# 93. Core Concepts We Must Master

The following concepts are considered critical:

```
1. REST APIs
2. Authentication
3. Authorization
4. PostgreSQL
5. SQL
6. DataFrames
7. Data Profiling
8. Data Quality
9. OLTP vs OLAP
10. DuckDB
11. LLMs
12. Tool Calling
13. Structured Outputs
14. Prompt Injection
15. Context Engineering
16. AI Agents
17. AI Evaluation
18. React Architecture
19. Docker
20. CI/CD
21. Cloud Deployment
22. System Design
```

---

# 94. Advanced Concepts

After the MVP, learn:

```
Streaming
Vector Databases
Advanced RAG
Model Routing
Fine-Tuning
Evaluation Pipelines
Distributed Processing
Kubernetes
Infrastructure as Code
Advanced Observability
Event-Driven Architecture
```

These should not be implemented simply for the sake of using advanced technologies.

---

# 95. Learning Priority

## Priority 1 — Must Learn Before Implementation

```
Python
Git
HTTP
REST
React Basics
TypeScript Basics
SQL
PostgreSQL Basics
Pandas / Polars
Statistics Basics
```

---

## Priority 2 — Learn During Core Implementation

```
FastAPI
Database Architecture
Data Pipelines
DuckDB
Data Profiling
Visualization
Authentication
AI APIs
Tool Calling
Structured Outputs
```

---

## Priority 3 — Learn During Advanced AI Development

```
Agents
Context Engineering
RAG
AI Evaluation
Guardrails
Prompt Injection
Model Routing
```

---

## Priority 4 — Learn During Production

```
Docker
CI/CD
Cloud
Redis
Workers
Monitoring
Scaling
Infrastructure as Code
```

---

# 96. Learning Sequence

The recommended learning order is:

```
Programming
     ↓
Git
     ↓
Frontend
     ↓
Backend
     ↓
APIs
     ↓
Databases
     ↓
Data Engineering
     ↓
Statistics
     ↓
Data Analysis
     ↓
Visualization
     ↓
LLMs
     ↓
Tool Calling
     ↓
AI Agent Architecture
     ↓
AI Evaluation
     ↓
Security
     ↓
Testing
     ↓
Docker
     ↓
CI/CD
     ↓
Cloud
     ↓
System Design
```

---

# 97. Implementation-Learning Relationship

We will never learn everything before building.

Instead:

```
Learn Enough
 ↓
Build
 ↓
Encounter Problem
 ↓
Learn Deeper
 ↓
Implement
 ↓
Test
 ↓
Move Forward
```

This is the primary learning strategy for InsightFlow AI.

---

# 98. Technical Interview Preparation

The project should also prepare for technical interviews.

For every major architectural decision, be able to answer:

```
Why?
Why not the alternative?
What happens at scale?
What happens if it fails?
What are the security risks?
What are the bottlenecks?
How would you improve it?
```

---

# 99. Interview Example

Question:

> Why did you use DuckDB?
> 

Expected reasoning:

```
The application database handles transactional metadata,
while DuckDB is optimized for analytical workloads. This
separation allows analytical queries over uploaded datasets
without placing unnecessary analytical workload on the
transactional PostgreSQL database.
```

The exact architecture may evolve as implementation progresses.

---

# 100. Interview Example — AI Architecture

Question:

> Why not simply send the entire dataset to an LLM?
> 

Answer:

```
Because LLMs are not reliable numerical computation engines.
The system uses the LLM primarily for intent understanding,
planning, tool selection, and explanation, while deterministic
analytical tools perform calculations. This improves
correctness, reduces hallucination risk, controls token usage,
and provides better data privacy.
```

---

# 101. Interview Example — Security

Question:

> How do you prevent the AI from accessing another user's dataset?
> 

Answer:

```
The backend enforces resource-level authorization before
analytical tools execute. The LLM is not treated as a
security boundary. Even if the model generates a request
for an unauthorized dataset, the backend rejects it.
```

---

# 102. Learning Completion Criteria

A topic is considered sufficiently learned when I can:

```
Explain it
        ↓
Implement it
        ↓
Debug it
        ↓
Test it
        ↓
Explain architectural trade-offs
```

---

# 103. Personal Knowledge Dashboard

A future Notion database should track:

| Topic | Category | Level | Status | Project Usage |
| --- | --- | --- | --- | --- |
| Python | Programming | Beginner | In Progress | Backend/Data |
| SQL | Database | Beginner | In Progress | Analytics |
| React | Frontend | Beginner | In Progress | UI |
| PostgreSQL | Database | Beginner | Planned | Application DB |
| DuckDB | Data | Beginner | Planned | Analytics |
| LLMs | AI | Beginner | Planned | AI Layer |
| Tool Calling | AI | Beginner | Planned | AI Agent |
| Docker | DevOps | Beginner | Planned | Deployment |

---

# 104. Status Definitions

Use:

```
NOT STARTED
LEARNING
PRACTICING
IMPLEMENTED
TESTED
MASTERED
```

"Mastered" should only be used when the concept can be explained and applied independently.

---

# 105. Learning Resources

For every topic, maintain:

```
Official Documentation
Tutorial
Course
Article
GitHub Repository
Practice Exercise
Project Implementation
```

---

# 106. Concept-to-Feature Mapping

| Concept | Project Feature |
| --- | --- |
| React | Dashboard UI |
| TypeScript | Frontend type safety |
| REST | Backend API |
| PostgreSQL | User/application data |
| SQL | Analytical queries |
| DuckDB | Dataset analytics |
| Pandas/Polars | Data processing |
| Statistics | Automated analysis |
| LLM | AI reasoning |
| Tool Calling | Analytical execution |
| Context Engineering | Dataset-aware AI |
| Visualization | Charts |
| AI Evaluation | Quality measurement |
| Docker | Deployment |
| CI/CD | Automation |
| Redis | Queues/cache |
| Cloud | Production |

---

# 107. Learning Rules for This Project

1. Never blindly copy code.
2. Understand before implementing.
3. Build small examples first.
4. Test every major component.
5. Document difficult concepts.
6. Ask why before choosing technology.
7. Prefer official documentation.
8. Understand alternatives.
9. Measure rather than assume.
10. Turn bugs into learning opportunities.

---

# 108. Final Learning Philosophy

InsightFlow AI is not only a software project.

It is also a structured learning environment.

The project should teach:

```
Software Engineering
        +
Data Engineering
        +
Data Science
        +
Artificial Intelligence
        +
AI Engineering
        +
System Design
        +
Security
        +
DevOps
```

The ultimate goal is:

> **Build a production-quality AI system while developing the engineering knowledge required to understand, maintain, scale, and defend every major part of it.**
> 

---

# 109. Current Learning Status

**Programming:** In Progress

**Frontend:** Planned

**Backend:** Planned

**Database:** Planned

**Data Engineering:** Planned

**Statistics:** Planned

**Data Visualization:** Planned

**LLMs:** Planned

**AI Agents:** Planned

**AI Evaluation:** Defined

**Security:** Defined

**Testing:** Defined

**Docker:** Planned

**CI/CD:** Planned

**Cloud:** Planned

**System Design:** Planned

**Status:** Active Learning Document

**Version:** 0.1.0

---

# 110. Final Principle

The project will follow:

```
LEARN
 ↓
BUILD
 ↓
TEST
 ↓
MEASURE
 ↓
DOCUMENT
 ↓
IMPROVE
```

**InsightFlow AI is both the product and the learning laboratory.**