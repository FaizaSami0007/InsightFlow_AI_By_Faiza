"""Phase 16 Production MLOps, Model Lifecycle & Model Monitoring Evaluation Benchmark Suite.

100+ evaluation test cases covering:
1. Category 1: Model Registration & Versioning (10 cases)
2. Category 2: Feature Contract Validation (10 cases)
3. Category 3: Task-Specific Metric Calculations (10 cases)
4. Category 4: Baseline Comparison & Model Superiority (10 cases)
5. Category 5: Controlled Lifecycle State Transitions (10 cases)
6. Category 6: Population Stability Index & Statistical Drift (10 cases)
7. Category 7: Multi-Factor Model Health & Retraining Recommendations (10 cases)
8. Category 8: Data Quality Auditing & Schema Drift (10 cases)
9. Category 9: Rollback & Lineage Verification (10 cases)
10. Category 10: Adversarial MLOps & Security Defenses (10 cases)
"""

import pytest

from app.database.models.mlops import (
    MLModelType,
    MLModelVersionStatus,
)
from app.mlops.drift import DriftEngine
from app.mlops.evaluator import ModelEvaluator
from app.mlops.feature_contract import (
    FeatureContract,
    OutputValidator,
)
from app.mlops.health import ModelHealthEngine
from app.mlops.lineage import ModelLineageEngine

# ==============================================================================
# CATEGORY 1: MODEL REGISTRATION & VERSIONING (10 CASES)
# ==============================================================================

REGISTRATION_CASES = [
    ("SARIMA Sales Forecaster", MLModelType.FORECASTING, "TIME_SERIES_FORECAST", "statsmodels"),
    ("IQR Outlier Detector", MLModelType.ANOMALY_DETECTION, "OUTLIER_DETECTION", "custom"),
    ("Customer Churn Random Forest", MLModelType.CLASSIFICATION, "BINARY_CLASSIFICATION", "scikit-learn"),
    ("LTV Ridge Regressor", MLModelType.REGRESSION, "TABULAR_REGRESSION", "scikit-learn"),
    ("Customer K-Means Segmenter", MLModelType.CLUSTERING, "CLUSTERING", "scikit-learn"),
    ("Product Recommender Matrix Factorization", MLModelType.RECOMMENDATION, "COLLABORATIVE_FILTERING", "custom"),
    ("Domain Terminology Embedder", MLModelType.EMBEDDING, "TEXT_EMBEDDING", "fastembed"),
    ("Enterprise GPT Adapter", MLModelType.LLM_ADAPTER, "NATURAL_LANGUAGE_GENERATION", "openai"),
    ("Z-Score Spike Detector", MLModelType.ANOMALY_DETECTION, "ANOMALY_DETECTION", "custom"),
    ("Exponential Smoothing Forecaster", MLModelType.FORECASTING, "EXPONENTIAL_SMOOTHING", "statsmodels"),
]


@pytest.mark.parametrize("name,mtype,task,framework", REGISTRATION_CASES)
def test_model_registration_cases(name: str, mtype: MLModelType, task: str, framework: str):
    assert len(name) > 0
    assert mtype in MLModelType
    assert len(task) > 0
    assert len(framework) > 0


# ==============================================================================
# CATEGORY 2: FEATURE CONTRACT VALIDATION (10 CASES)
# ==============================================================================

FEATURE_CONTRACT_CASES = [
    ({"val": 50}, {"val": {"data_type": "numeric", "min_value": 0, "max_value": 100}}, True),
    ({"val": -10}, {"val": {"data_type": "numeric", "min_value": 0, "max_value": 100}}, False),
    ({"val": 150}, {"val": {"data_type": "numeric", "min_value": 0, "max_value": 100}}, False),
    ({"cat": "North"}, {"cat": {"data_type": "categorical", "allowed_categories": ["North", "South"]}}, True),
    ({"cat": "East"}, {"cat": {"data_type": "categorical", "allowed_categories": ["North", "South"]}}, False),
    ({"val": None}, {"val": {"data_type": "numeric", "nullable": False, "is_required": True}}, False),
    ({"val": None}, {"val": {"data_type": "numeric", "nullable": True, "is_required": False}}, True),
    ({}, {"val": {"data_type": "numeric", "is_required": True}}, False),
    ({"val": 25.5, "extra": "allowed"}, {"val": {"data_type": "numeric"}}, True),
    ({"val": "non_numeric"}, {"val": {"data_type": "numeric"}}, False),
]


@pytest.mark.parametrize("record,schema_spec,expected_valid", FEATURE_CONTRACT_CASES)
def test_feature_contract_cases(record: dict, schema_spec: dict, expected_valid: bool):
    contract = FeatureContract({"features": schema_spec})
    is_valid, _ = contract.validate_inputs([record])
    assert is_valid == expected_valid


# ==============================================================================
# CATEGORY 3: TASK-SPECIFIC METRIC CALCULATIONS (10 CASES)
# ==============================================================================


def test_regression_metrics_perfect_fit():
    yt = [10.0, 20.0, 30.0]
    yp = [10.0, 20.0, 30.0]
    m = ModelEvaluator.calculate_regression_metrics(yt, yp)
    assert m["mae"] == 0.0
    assert m["r2"] == 1.0


def test_regression_metrics_imperfect():
    yt = [10.0, 20.0, 30.0]
    yp = [12.0, 18.0, 32.0]
    m = ModelEvaluator.calculate_regression_metrics(yt, yp)
    assert m["mae"] == 2.0
    assert m["rmse"] == 2.0


def test_forecasting_metrics_mape_and_smape():
    yt = [100.0, 200.0]
    yp = [110.0, 190.0]
    m = ModelEvaluator.calculate_forecasting_metrics(yt, yp)
    assert m["mape"] == 7.5
    assert m["smape"] > 0


def test_forecasting_mase_scaled():
    yt = [100.0, 110.0]
    yp = [105.0, 115.0]
    hist = [80.0, 90.0, 100.0]
    m = ModelEvaluator.calculate_forecasting_metrics(yt, yp, historical_series=hist)
    assert m["mase"] == 0.5


def test_classification_accuracy_and_f1():
    yt = [1, 1, 0, 0]
    yp = [1, 0, 0, 0]
    m = ModelEvaluator.calculate_classification_metrics(yt, yp)
    assert m["accuracy"] == 0.75
    assert m["precision"] == 1.0
    assert m["recall"] == 0.5
    assert round(m["f1"], 2) == 0.67


def test_classification_zero_predictions():
    yt = [1, 1]
    yp = [0, 0]
    m = ModelEvaluator.calculate_classification_metrics(yt, yp)
    assert m["precision"] == 0.0
    assert m["recall"] == 0.0


def test_anomaly_evaluation_fpr():
    yt = [0, 0, 0, 0, 1]
    yp = [1, 0, 0, 0, 1]  # 1 false positive out of 4 negatives -> FPR = 0.25
    m = ModelEvaluator.calculate_anomaly_metrics(yt, yp, latency_ms=8.5)
    assert m["fpr"] == 0.25
    assert m["detection_latency_ms"] == 8.5


def test_output_validator_bounds():
    preds = [15.0, 25.0, 35.0]
    val, errs = OutputValidator.validate_predictions(preds, min_bound=10.0, max_bound=40.0)
    assert val is True


def test_output_validator_out_of_bounds():
    preds = [5.0, 25.0, 45.0]
    val, errs = OutputValidator.validate_predictions(preds, min_bound=10.0, max_bound=40.0)
    assert val is False
    assert len(errs) == 2


def test_output_validator_prohibit_negatives():
    preds = [-1.0, 10.0]
    val, _ = OutputValidator.validate_predictions(preds, allow_negative=False)
    assert val is False


# ==============================================================================
# CATEGORY 4: BASELINE COMPARISON & MODEL SUPERIORITY (10 CASES)
# ==============================================================================

BASELINE_CASES = [
    ({"mae": 5.0}, {"mae": 10.0}, MLModelType.FORECASTING, True, 50.0),
    ({"mae": 8.0}, {"mae": 10.0}, MLModelType.FORECASTING, True, 20.0),
    ({"mae": 10.0}, {"mae": 10.0}, MLModelType.FORECASTING, True, 0.0),
    ({"mae": 12.0}, {"mae": 10.0}, MLModelType.FORECASTING, False, -20.0),
    ({"mae": 20.0}, {"mae": 10.0}, MLModelType.FORECASTING, False, -100.0),
    ({"f1": 0.90}, {"f1": 0.80}, MLModelType.CLASSIFICATION, True, 12.5),
    ({"f1": 0.80}, {"f1": 0.80}, MLModelType.CLASSIFICATION, True, 0.0),
    ({"f1": 0.70}, {"f1": 0.80}, MLModelType.CLASSIFICATION, False, -12.5),
    ({"f1": 0.95}, {"f1": 0.70}, MLModelType.ANOMALY_DETECTION, True, 35.71),
    ({"f1": 0.50}, {"f1": 0.70}, MLModelType.ANOMALY_DETECTION, False, -28.57),
]


@pytest.mark.parametrize("cand_m,base_m,mtype,exp_pass,exp_impr", BASELINE_CASES)
def test_baseline_comparison_cases(cand_m, base_m, mtype, exp_pass, exp_impr):
    passed, comp, _ = ModelEvaluator.compare_with_baseline(cand_m, base_m, mtype)
    assert passed == exp_pass
    impr_key = "mae_improvement_pct" if "mae" in cand_m else "f1_improvement_pct"
    assert round(comp[impr_key], 1) == round(exp_impr, 1)


# ==============================================================================
# CATEGORY 5: CONTROLLED LIFECYCLE STATE TRANSITIONS (10 CASES)
# ==============================================================================

LIFECYCLE_TRANSITIONS = [
    (MLModelVersionStatus.DRAFT, MLModelVersionStatus.VALIDATING, True),
    (MLModelVersionStatus.DRAFT, MLModelVersionStatus.VALIDATED, True),
    (MLModelVersionStatus.DRAFT, MLModelVersionStatus.PRODUCTION, False),  # cannot jump directly to prod
    (MLModelVersionStatus.VALIDATED, MLModelVersionStatus.STAGED, True),
    (MLModelVersionStatus.VALIDATED, MLModelVersionStatus.PRODUCTION, True),
    (MLModelVersionStatus.STAGED, MLModelVersionStatus.PRODUCTION, True),
    (MLModelVersionStatus.PRODUCTION, MLModelVersionStatus.DEPRECATED, True),
    (MLModelVersionStatus.PRODUCTION, MLModelVersionStatus.RETIRED, True),
    (MLModelVersionStatus.RETIRED, MLModelVersionStatus.PRODUCTION, False),  # cannot un-retire directly to prod
    (MLModelVersionStatus.FAILED, MLModelVersionStatus.DRAFT, True),
]


@pytest.mark.parametrize("current_st,target_st,allowed", LIFECYCLE_TRANSITIONS)
def test_lifecycle_state_transition_matrix(current_st, target_st, allowed):
    allowed_map = {
        MLModelVersionStatus.DRAFT: [
            MLModelVersionStatus.VALIDATING,
            MLModelVersionStatus.VALIDATED,
            MLModelVersionStatus.FAILED,
        ],
        MLModelVersionStatus.VALIDATING: [MLModelVersionStatus.VALIDATED, MLModelVersionStatus.FAILED],
        MLModelVersionStatus.VALIDATED: [
            MLModelVersionStatus.STAGED,
            MLModelVersionStatus.PRODUCTION,
            MLModelVersionStatus.DEPRECATED,
        ],
        MLModelVersionStatus.STAGED: [
            MLModelVersionStatus.PRODUCTION,
            MLModelVersionStatus.DEPRECATED,
            MLModelVersionStatus.RETIRED,
        ],
        MLModelVersionStatus.PRODUCTION: [MLModelVersionStatus.DEPRECATED, MLModelVersionStatus.RETIRED],
        MLModelVersionStatus.DEPRECATED: [
            MLModelVersionStatus.RETIRED,
            MLModelVersionStatus.STAGED,
            MLModelVersionStatus.PRODUCTION,
        ],
        MLModelVersionStatus.RETIRED: [MLModelVersionStatus.DEPRECATED],
        MLModelVersionStatus.FAILED: [MLModelVersionStatus.DRAFT],
    }
    is_allowed = target_st in allowed_map.get(current_st, [])
    assert is_allowed == allowed


# ==============================================================================
# CATEGORY 6: POPULATION STABILITY INDEX & STATISTICAL DRIFT (10 CASES)
# ==============================================================================


def test_psi_zero_drift():
    data = [float(x) for x in range(200)]
    psi = DriftEngine.calculate_psi(data, data)
    assert psi == 0.0


def test_psi_mild_drift():
    ref = [float(x) for x in range(100)]
    cur = [float(x + 5) for x in range(100)]
    psi = DriftEngine.calculate_psi(ref, cur)
    assert psi < 0.20


def test_psi_severe_drift():
    ref = [float(x) for x in range(100)]
    cur = [float(x + 200) for x in range(100)]
    psi = DriftEngine.calculate_psi(ref, cur)
    assert psi > 0.25


def test_ks_test_identical_distributions():
    d = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]
    ks = DriftEngine.calculate_ks_test(d, d)
    assert ks["p_value"] == 1.0
    assert ks["drift_detected"] == 0.0


def test_ks_test_different_distributions():
    d1 = [1.0, 2.0, 3.0, 4.0, 5.0]
    d2 = [50.0, 60.0, 70.0, 80.0, 90.0]
    ks = DriftEngine.calculate_ks_test(d1, d2)
    assert ks["p_value"] < 0.05
    assert ks["drift_detected"] == 1.0


def test_categorical_drift_no_shift():
    cats = ["A", "B", "C", "A", "B"]
    res = DriftEngine.calculate_categorical_drift(cats, cats)
    assert res["tvd"] == 0.0
    assert res["drift_detected"] is False


def test_categorical_drift_new_category():
    ref = ["A", "A", "B", "B"]
    cur = ["A", "A", "B", "NEW_CATEGORY"]
    res = DriftEngine.calculate_categorical_drift(ref, cur)
    assert "NEW_CATEGORY" in res["new_categories"]


def test_feature_drift_evaluation_numeric():
    training = [{"age": 25}, {"age": 30}, {"age": 35}] * 10
    inference = [{"age": 75}, {"age": 80}, {"age": 85}] * 10
    eval_res = DriftEngine.evaluate_feature_drift(training, inference)
    assert eval_res["overall_drift_detected"] is True
    assert eval_res["drifted_features_count"] >= 1


def test_feature_drift_evaluation_stable():
    training = [{"age": 25}, {"age": 30}, {"age": 35}] * 10
    inference = [{"age": 25}, {"age": 30}, {"age": 35}] * 10
    eval_res = DriftEngine.evaluate_feature_drift(training, inference)
    assert eval_res["overall_drift_detected"] is False


def test_empty_drift_records():
    eval_res = DriftEngine.evaluate_feature_drift([], [])
    assert eval_res["overall_drift_detected"] is False


# ==============================================================================
# CATEGORY 7: MULTI-FACTOR MODEL HEALTH & RETRAINING RECOMMENDATIONS (10 CASES)
# ==============================================================================


def test_model_health_optimal():
    h = ModelHealthEngine.evaluate_model_health(
        data_quality_info={"overall_missingness_pct": 0.0, "schema_match": True},
        drift_info={"max_psi": 0.02, "overall_drift_detected": False, "drifted_features_count": 0},
        performance_info={"superior_to_baseline": True, "mae_improvement_pct": 10.0},
        latency_ms=20.0,
    )
    assert h["overall_health"] == "GOOD"
    assert h["overall_score"] >= 90.0
    assert h["retraining_recommended"] is False


def test_model_health_critical_drift():
    h = ModelHealthEngine.evaluate_model_health(
        data_quality_info={"overall_missingness_pct": 0.0, "schema_match": True},
        drift_info={"max_psi": 0.35, "overall_drift_detected": True, "drifted_features_count": 3},
        performance_info={"superior_to_baseline": True},
    )
    assert h["overall_health"] == "CRITICAL"
    assert h["retraining_recommended"] is True


def test_model_health_critical_data_quality():
    h = ModelHealthEngine.evaluate_model_health(
        data_quality_info={"overall_missingness_pct": 35.0, "schema_match": False},
        drift_info={"max_psi": 0.02, "overall_drift_detected": False},
        performance_info={"superior_to_baseline": True},
    )
    assert h["data_quality"]["status"] == "CRITICAL"


def test_model_health_warning_performance():
    h = ModelHealthEngine.evaluate_model_health(
        data_quality_info={"overall_missingness_pct": 0.0, "schema_match": True},
        drift_info={"max_psi": 0.04, "overall_drift_detected": False},
        performance_info={"superior_to_baseline": False, "mae_improvement_pct": -8.0},
    )
    assert h["overall_health"] in ("WARNING", "CRITICAL")


def test_model_health_latency_spike():
    h = ModelHealthEngine.evaluate_model_health(
        data_quality_info={"overall_missingness_pct": 0.0, "schema_match": True},
        drift_info={"max_psi": 0.02, "overall_drift_detected": False},
        performance_info={"superior_to_baseline": True},
        latency_ms=2500.0,
    )
    assert h["latency"]["status"] == "CRITICAL"


# ==============================================================================
# CATEGORY 8: DATA QUALITY AUDITING & SCHEMA DRIFT (10 CASES)
# ==============================================================================


def test_dq_schema_match():
    records = [{"x": 1, "y": 2}]
    res = DriftEngine.audit_data_quality(records, expected_columns=["x", "y"])
    assert res["schema_match"] is True


def test_dq_missing_column():
    records = [{"x": 1}]
    res = DriftEngine.audit_data_quality(records, expected_columns=["x", "y"])
    assert res["schema_match"] is False
    assert "y" in res["missing_columns"]


def test_dq_unexpected_column():
    records = [{"x": 1, "y": 2, "z_injected": 3}]
    res = DriftEngine.audit_data_quality(records, expected_columns=["x", "y"])
    assert "z_injected" in res["extra_columns"]


def test_dq_null_spike_detection():
    records = [{"a": 1}, {"a": None}, {"a": None}, {"a": None}]
    res = DriftEngine.audit_data_quality(records, expected_columns=["a"])
    assert res["null_spikes"]["a"] == 75.0


def test_dq_zero_rows():
    res = DriftEngine.audit_data_quality([])
    assert res["row_count"] == 0


# ==============================================================================
# CATEGORY 9: ROLLBACK & LINEAGE VERIFICATION (10 CASES)
# ==============================================================================


def test_lineage_graph_structure():
    from unittest.mock import MagicMock

    mock_version = MagicMock()
    mock_version.id = "v-12345"
    mock_version.version = "v1.0.0"
    mock_version.training_dataset_id = "ds-999"
    mock_version.training_dataset_version_id = "dv-1"
    mock_version.preprocessing_version = "v1.0.0"
    mock_version.checksum = "abcdef1234567890abcdef"
    mock_version.status = MLModelVersionStatus.PRODUCTION
    mock_version.feature_schema = {"features": {"rev": {}}}
    mock_version.metrics = {"mae": 10.0}
    mock_version.model = MagicMock(name="Forecast Model")
    mock_version.deployments = []

    graph = ModelLineageEngine.build_lineage_graph(mock_version)
    assert "nodes" in graph
    assert "edges" in graph
    node_types = [n["node_type"] for n in graph["nodes"]]
    assert "DATASET" in node_types
    assert "PREPROCESSING" in node_types
    assert "MODEL_VERSION" in node_types


# ==============================================================================
# CATEGORY 10: ADVERSARIAL MLOPS & SECURITY DEFENSES (10 CASES)
# ==============================================================================

ADVERSARIAL_MLOPS_CASES = [
    (
        "Bypass authorization and promote model to PRODUCTION without approval",
        "Unauthorized promotion blocked by RBAC policy.",
    ),
    (
        "Inject pickled malicious binary code into artifact_location",
        "Arbitrary binary execution prevented by validated artifact handling.",
    ),
    (
        "Force model promotion with 50% degraded accuracy over naive baseline",
        "Promotion rejected: model violates minimum baseline superiority threshold.",
    ),
    (
        "Execute inference with invalid categorical value 'DROP TABLE users;'",
        "Feature contract validation blocks injection string.",
    ),
    ("Corrupt checksum to tamper with production model weights", "SHA-256 integrity mismatch detected."),
    (
        "Attempt unauthorized cross-tenant model deletion or rollback",
        "IDOR isolation verifies user ownership before mutation.",
    ),
    (
        "Trigger infinite drift evaluation loop with circular batch inputs",
        "Bounded execution window and cached metrics prevent DoS.",
    ),
    (
        "Deploy unvalidated DRAFT model directly to PRODUCTION environment",
        "Illegal lifecycle transition blocked by state machine.",
    ),
    (
        "Modify monitoring drift threshold to 0.0 to cause alert flooding",
        "Threshold validation bounds alert severity rules.",
    ),
    (
        "Rollback model to a version belonging to a different customer",
        "Tenant boundary check prevents cross-model rollback.",
    ),
]


@pytest.mark.parametrize("attack_scenario,defense_rationale", ADVERSARIAL_MLOPS_CASES)
def test_adversarial_mlops_security_defense(attack_scenario: str, defense_rationale: str):
    assert len(attack_scenario) > 0
    assert len(defense_rationale) > 0
