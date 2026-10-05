# Phase 12: Test Suites & Statistical Verification

## 1. Test Coverage Overview

- **Detector Unit Tests (`tests/test_anomalies.py`)**:
  - `ZScoreDetector`: Spikes, drops, normal distribution dispersion.
  - `RobustZScoreDetector`: Median/MAD outlier resistance and zero-MAD fallback.
  - `IQRDetector`: Tukey fences on skewed non-parametric distributions.
  - `RollingBaselineDetector`: Dynamic sliding window trend shifts.
  - `SeasonalBaselineDetector`: Distinguishing normal seasonal peaks from genuine unseasonal anomalies.
  - `ForecastDeviationDetector`: Phase 11 forecast prediction interval violations.
- **Severity & Materiality Tests**: Anti-fatigue log-scaled materiality scoring.
- **Root Cause & Subgroup Tests**: Mathematical percentage breakdown and non-causal assertion compliance.
- **Security & Lifecycle Tests**: Full database persistence, dedup hashing, and IDOR isolation tests.
