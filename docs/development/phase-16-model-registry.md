# Phase 16 — Centralized Model Registry & Versioning

## 1. Registry Architecture
The Model Registry serves as the source of truth for all machine learning and predictive assets in InsightFlow AI.

### Conceptual Hierarchy
- **`MLModel`**: Represents a business model family (e.g. "Q4 Revenue Forecaster", "Customer Churn Predictor").
  - `model_type`: Categorized by `MLModelType` enum.
  - `task_type`: Specific task (`TIME_SERIES_FORECAST`, `BINARY_CLASSIFICATION`, `OUTLIER_DETECTION`, etc.).
  - `framework`: Originating framework (`statsmodels`, `scikit-learn`, `fastembed`, `openai`, `custom`).
  - `provider`: Service provider (`insightflow_native`, `external`).
- **`MLModelVersion`**: Immutable point-in-time version snapshot.
  - `version`: Semantic version string (e.g., `v1.0.0`, `v1.2.0-rc1`).
  - `artifact_location`: Storage URI for model weights/binaries.
  - `checksum`: SHA-256 verification hash.
  - `feature_schema`: Strict JSON schema contract for input features.
  - `metrics`: Standardized evaluation scores (`mae`, `rmse`, `accuracy`, `f1`, etc.).
  - `baseline_metrics`: Metrics achieved by the benchmark naive baseline on identical data.

## 2. Supported Task Metrics
| Task Family | Required Validation Metrics | Baseline Benchmark |
| :--- | :--- | :--- |
| **Forecasting** | `MAE`, `RMSE`, `MAPE`, `sMAPE`, `MASE` | `Seasonal Naive` / `Drift Naive` |
| **Regression** | `MAE`, `RMSE`, `R²` | `Mean Predictor` |
| **Classification** | `Accuracy`, `Precision`, `Recall`, `F1` | `Majority Class Classifier` |
| **Anomaly Detection** | `FPR`, `Precision`, `Recall`, `Latency` | `Empirical Z-score` |

## 3. Database Schema
Defined in `apps/api/app/database/models/mlops.py` with full PostgreSQL UUID primary keys, JSONB support, and cascading integrity constraints.
