# Phase 12: Anomaly Detection & Proactive Insight Intelligence Architecture

## 1. Architectural Overview

InsightFlow AI Phase 12 establishes a zero-hallucination, deterministic anomaly detection and proactive analytical insight engine. It ensures the AI never fabricates anomalies, severity levels, or causal claims.

```
DATASET / DUCKDB
   ↓
SEMANTIC LAYER (Measures & Dimensions)
   ↓
ANALYTICAL TIME SERIES / GROUP AGGREGATION
   ↓
EXPECTED STATISTICAL BASELINE (Rolling / Median / MAD / Cycle / Forecast)
   ↓
ANOMALY DETECTOR REGISTRY
   ↓
STATISTICAL VALIDATION & ANOMALY SCORE
   ↓
MATERIALITY & SEVERITY EVALUATOR (Anti-Fatigue Weighting)
   ↓
DIMENSIONAL ROOT-CAUSE CONTRIBUTION ANALYSIS
   ↓
PROACTIVE INSIGHT MODEL & FEED (Deduplication & Lifecycle)
   ↓
AI EXPLANATION / CHAT / DASHBOARDS / EXPORT
   ↓
USER ACTION
```

## 2. Core Tenets

1. **Zero Hallucination Guarantee**: The LLM cannot invent anomaly points, alter statistical scores, or fabricate baseline expectations.
2. **Deterministic Baseline Selection**: Baselines are established strictly using mathematical estimators (Rolling Median, MAD, Seasonal Cycles, and Phase 11 Prediction Intervals).
3. **Materiality & Anti-Fatigue**: Severity is weighted by both absolute magnitude and relative deviation to avoid alerting fatigue on micro-quantities (e.g. 500% jump on $2 is not CRITICAL).
4. **Non-Causal Explanation Principle**: Root-cause analysis reports percentage variance contribution ("accounted for X% of variation") without making ungrounded causal claims.
5. **Reproducible Snapshots & Provenance**: Detected anomalies and insights persist with complete provenance linkages.
