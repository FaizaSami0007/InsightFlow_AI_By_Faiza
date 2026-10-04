# Product Specification

## Product promise

InsightFlow AI lets a user move from a raw structured dataset to trustworthy analysis and an interactive dashboard without requiring them to write SQL or manually build every chart.

## Primary persona

### The analyst / student / business operator

Needs to:
- understand an unfamiliar dataset quickly
- answer business questions
- verify numerical evidence
- create presentable dashboards
- iterate without rebuilding charts manually

## Jobs to be done

1. "Tell me what is inside this dataset."
2. "Tell me whether the data is reliable enough to analyze."
3. "Answer this business question using the data."
4. "Show me the evidence."
5. "Turn the important findings into a dashboard."
6. "Change the dashboard without manually editing every widget."

## Non-goals

- Replace a full enterprise data warehouse
- Autonomous financial/medical/legal decision-making
- Unrestricted code execution
- Fabricate missing data
- Hide uncertainty

## Trust principles

Every numerical answer should expose, directly or through an evidence affordance:
- dataset version
- relevant columns
- operation
- filters
- result timestamp
- confidence/limitations when applicable

## Product states

Every major workflow defines:
- empty
- loading
- processing
- success
- partial success
- error
- permission denied
- unavailable/degraded

## Feature gating

Use feature flags for experimental AI and dashboard capabilities. Never silently enable high-risk experimental behavior for all users.
