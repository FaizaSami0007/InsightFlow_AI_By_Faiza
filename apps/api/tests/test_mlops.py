"""Unit and integration tests for Phase 16 Production MLOps, Model Lifecycle & Model Monitoring."""

import uuid

import pytest
from fastapi.testclient import TestClient

from app.database.models.mlops import (
    MLDeploymentEnvironment,
    MLModelType,
    MLModelVersionStatus,
)
from app.database.models.user import User
from app.mlops.drift import DriftEngine
from app.mlops.evaluator import ModelEvaluator
from app.mlops.feature_contract import (
    FeatureContract,
    FeatureContractViolationError,
    OutputValidator,
)
from app.mlops.health import ModelHealthEngine
from app.mlops.schemas import (
    MLExperimentCreateRequest,
    MLModelCreateRequest,
    MLModelEvaluationRequest,
    MLModelPromotionRequest,
    MLModelRollbackRequest,
    MLModelVersionCreateRequest,
)
from app.mlops.service import (
    MLOpsService,
)
from tests.conftest import TestingSessionLocal

# ==============================================================================
# 1. UNIT TESTS: FEATURE CONTRACT & VALIDATORS
# ==============================================================================

def test_feature_contract_validation_success():
    schema = {
        "features": {
            "age": {"data_type": "numeric", "is_required": True, "min_value": 18, "max_value": 100},
            "category": {"data_type": "categorical", "is_required": True, "allowed_categories": ["A", "B", "C"]},
            "income": {"data_type": "numeric", "is_required": False, "nullable": True},
        }
    }
    contract = FeatureContract(schema)
    valid_batch = [
        {"age": 25, "category": "A", "income": 50000.0},
        {"age": 60, "category": "B", "income": None},
    ]
    is_valid, violations = contract.validate_inputs(valid_batch)
    assert is_valid is True
    assert len(violations) == 0


def test_feature_contract_validation_violations():
    schema = {
        "features": {
            "age": {"data_type": "numeric", "is_required": True, "min_value": 18, "max_value": 100},
            "category": {"data_type": "categorical", "is_required": True, "allowed_categories": ["A", "B"]},
            "score": {"data_type": "numeric", "is_required": True, "nullable": False},
        }
    }
    contract = FeatureContract(schema)
    invalid_batch = [
        {"age": 15, "category": "C", "score": None},  # age < 18, category not in [A, B], score is null
        {"category": "A", "score": 88.0},  # missing age
    ]
    is_valid, violations = contract.validate_inputs(invalid_batch)
    assert is_valid is False
    assert len(violations) >= 4

    with pytest.raises(FeatureContractViolationError):
        contract.enforce_input_validation(invalid_batch)


def test_output_validator():
    # 1. Normal predictions
    preds = [10.5, 20.2, 35.8]
    valid, errs = OutputValidator.validate_predictions(preds, allow_negative=False, min_bound=0.0)
    assert valid is True
    assert len(errs) == 0

    # 2. Negative prediction violation
    neg_preds = [10.5, -5.2, 35.8]
    valid_neg, errs_neg = OutputValidator.validate_predictions(neg_preds, allow_negative=False)
    assert valid_neg is False
    assert any("negative value" in e for e in errs_neg)

    # 3. NaN / Inf violation
    nan_preds = [10.5, float("nan"), 35.8]
    valid_nan, errs_nan = OutputValidator.validate_predictions(nan_preds)
    assert valid_nan is False
    assert any("non-finite value" in e for e in errs_nan)


# ==============================================================================
# 2. UNIT TESTS: MODEL EVALUATION & BASELINE METRICS
# ==============================================================================

def test_model_evaluator_forecasting_and_regression_metrics():
    y_true = [100.0, 110.0, 120.0, 130.0, 140.0]
    y_pred = [102.0, 108.0, 122.0, 128.0, 142.0]
    history = [80.0, 85.0, 90.0, 95.0, 100.0]

    fc_metrics = ModelEvaluator.calculate_forecasting_metrics(y_true, y_pred, history)
    assert "mae" in fc_metrics
    assert "rmse" in fc_metrics
    assert "mape" in fc_metrics
    assert "smape" in fc_metrics
    assert "mase" in fc_metrics
    assert fc_metrics["mae"] == 2.0
    assert fc_metrics["rmse"] == 2.0

    reg_metrics = ModelEvaluator.calculate_regression_metrics(y_true, y_pred)
    assert reg_metrics["r2"] > 0.95


def test_model_evaluator_classification_and_anomaly_metrics():
    y_true = [1, 0, 1, 1, 0, 0, 1, 0]
    y_pred = [1, 0, 1, 0, 0, 0, 1, 0]

    cls_metrics = ModelEvaluator.calculate_classification_metrics(y_true, y_pred)
    assert cls_metrics["accuracy"] == 0.875
    assert cls_metrics["precision"] == 1.0
    assert cls_metrics["recall"] == 0.75
    assert cls_metrics["f1"] > 0.8

    anom_metrics = ModelEvaluator.calculate_anomaly_metrics(y_true, y_pred, latency_ms=12.5)
    assert anom_metrics["detection_latency_ms"] == 12.5


def test_baseline_comparison():
    candidate_metrics = {"mae": 5.0, "rmse": 7.0}
    naive_metrics = {"mae": 10.0, "rmse": 14.0}

    passed, comp, warnings = ModelEvaluator.compare_with_baseline(
        candidate_metrics, naive_metrics, MLModelType.FORECASTING
    )
    assert passed is True
    assert comp["mae_improvement_pct"] == 50.0
    assert comp["superior_to_baseline"] is True
    assert len(warnings) == 0

    # Test underperforming model
    poor_metrics = {"mae": 15.0, "rmse": 20.0}
    failed_pass, failed_comp, failed_warn = ModelEvaluator.compare_with_baseline(
        poor_metrics, naive_metrics, MLModelType.FORECASTING
    )
    assert failed_pass is False
    assert failed_comp["superior_to_baseline"] is False
    assert len(failed_warn) > 0


# ==============================================================================
# 3. UNIT TESTS: STATISTICAL DRIFT & DATA QUALITY
# ==============================================================================

def test_psi_calculation():
    # Identical distributions -> PSI near 0
    ref_data = [float(i) for i in range(100)]
    cur_data = [float(i) for i in range(100)]
    psi_identical = DriftEngine.calculate_psi(ref_data, cur_data)
    assert psi_identical < 0.05

    # Drastically shifted distribution -> PSI > 0.25
    shifted_data = [float(i + 150) for i in range(100)]
    psi_shifted = DriftEngine.calculate_psi(ref_data, shifted_data)
    assert psi_shifted > 0.25


def test_ks_test_and_categorical_drift():
    ref_num = [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0]
    cur_num = [10.0, 20.0, 30.0, 40.0, 50.0, 60.0, 70.0, 80.0]
    ks_res = DriftEngine.calculate_ks_test(ref_num, cur_num)
    assert ks_res["p_value"] < 0.05
    assert ks_res["drift_detected"] == 1.0

    ref_cat = ["A", "A", "A", "B", "B", "C"]
    cur_cat = ["D", "D", "D", "E", "E", "F"]
    cat_res = DriftEngine.calculate_categorical_drift(ref_cat, cur_cat)
    assert cat_res["drift_detected"] is True
    assert "D" in cat_res["new_categories"]


def test_data_quality_audit():
    records = [
        {"a": 1, "b": 2, "c": None},
        {"a": 2, "b": None, "c": None},
        {"a": 3, "b": 4, "c": None},
    ]
    dq_res = DriftEngine.audit_data_quality(records, expected_columns=["a", "b", "c"])
    assert dq_res["row_count"] == 3
    assert dq_res["column_count"] == 3
    assert dq_res["null_spikes"]["c"] == 100.0


# ==============================================================================
# 4. UNIT TESTS: MODEL HEALTH & LINEAGE
# ==============================================================================

def test_model_health_engine():
    # 1. Healthy model
    health_good = ModelHealthEngine.evaluate_model_health(
        data_quality_info={"overall_missingness_pct": 0.0, "schema_match": True},
        drift_info={"max_psi": 0.04, "overall_drift_detected": False, "drifted_features_count": 0},
        performance_info={"superior_to_baseline": True, "mae_improvement_pct": 12.0},
    )
    assert health_good["overall_health"] == "GOOD"
    assert health_good["retraining_recommended"] is False

    # 2. Severe drift model
    health_crit = ModelHealthEngine.evaluate_model_health(
        data_quality_info={"overall_missingness_pct": 5.0, "schema_match": True},
        drift_info={"max_psi": 0.45, "overall_drift_detected": True, "drifted_features_count": 4},
        performance_info={"superior_to_baseline": False, "mae_improvement_pct": -15.0},
    )
    assert health_crit["overall_health"] == "CRITICAL"
    assert health_crit["retraining_recommended"] is True


# ==============================================================================
# 5. INTEGRATION TESTS: MLOPS SERVICE & LIFECYCLE WORKFLOW
# ==============================================================================

@pytest.mark.asyncio
async def test_mlops_lifecycle_end_to_end():
    async with TestingSessionLocal() as db:
        user = User(
            id=str(uuid.uuid4()),
            email=f"mlops_user_{uuid.uuid4().hex[:6]}@example.com",
            password_hash="hashed_pw",
            full_name="MLOps Tester",
        )
        db.add(user)
        await db.commit()

        service = MLOpsService(db)

        # 1. Create Model
        create_req = MLModelCreateRequest(
            name="Q4 Revenue Forecast Model",
            description="SARIMA enterprise revenue predictor",
            model_type=MLModelType.FORECASTING,
            task_type="TIME_SERIES_FORECAST",
            framework="statsmodels",
            provider="insightflow_native",
            tags=["revenue", "finance", "production_candidate"],
        )
        model = await service.create_model(user, create_req)
        assert model.name == "Q4 Revenue Forecast Model"
        assert model.model_type == MLModelType.FORECASTING

        # 2. Create Model Version v1.0.0
        v1_req = MLModelVersionCreateRequest(
            version="v1.0.0",
            artifact_location="models/forecast/revenue_v1.0.0.pkl",
            feature_schema={
                "features": {
                    "revenue": {"data_type": "numeric", "is_required": True, "min_value": 0.0, "max_value": 1000000.0},
                    "region": {"data_type": "categorical", "is_required": True, "allowed_categories": ["North", "South", "East", "West"]},
                }
            },
            preprocessing_version="v1.0.0",
            parameters={"order": [1, 1, 1], "seasonal_order": [1, 1, 0, 12]},
            metrics={"mae": 1500.0, "rmse": 2200.0, "mape": 4.5},
            baseline_metrics={"mae": 2500.0, "rmse": 3500.0, "mape": 8.0},
        )
        v1 = await service.create_model_version(model.id, user, v1_req)
        assert v1.version == "v1.0.0"
        assert v1.status == MLModelVersionStatus.DRAFT

        # 3. Create Experiment
        exp_req = MLExperimentCreateRequest(
            name="Grid Search SARIMA Tuning",
            features=["revenue", "region"],
            preprocessing_config={"outlier_treatment": "iqr_cap"},
            parameters={"p": 1, "d": 1, "q": 1},
            metrics={"mae": 1500.0, "rmse": 2200.0},
            evaluation_config={"cv_folds": 5},
        )
        exp = await service.create_experiment(model.id, user, exp_req)
        assert exp.name == "Grid Search SARIMA Tuning"

        # 4. Evaluate Model Version
        eval_req = MLModelEvaluationRequest(
            evaluation_type="HOLDOUT",
            require_improvement_over_baseline=True,
        )
        eval_record = await service.evaluate_model_version(v1.id, user, eval_req)
        assert eval_record.passed_validation is True
        assert eval_record.baseline_comparison["superior_to_baseline"] is True

        # 5. Promote Model Version (VALIDATED -> STAGED -> PRODUCTION)
        promote_stage = MLModelPromotionRequest(
            target_status=MLModelVersionStatus.STAGED,
            reason="Completed offline backtesting with 40% MAE improvement over seasonal naive.",
            environment=MLDeploymentEnvironment.STAGING,
        )
        staged_v = await service.promote_model_version(v1.id, user, promote_stage)
        assert staged_v.status == MLModelVersionStatus.STAGED

        promote_prod = MLModelPromotionRequest(
            target_status=MLModelVersionStatus.PRODUCTION,
            reason="Approved for enterprise revenue dashboard deployment by VP of Analytics.",
            environment=MLDeploymentEnvironment.PRODUCTION,
        )
        prod_v = await service.promote_model_version(v1.id, user, promote_prod)
        assert prod_v.status == MLModelVersionStatus.PRODUCTION

        # 6. Verify Lineage Graph
        lineage = await service.get_model_lineage(v1.id, user)
        assert len(lineage["nodes"]) >= 3
        assert len(lineage["edges"]) >= 2

        # 7. Create Model Version v2.0.0 and Rollback Test
        v2_req = MLModelVersionCreateRequest(
            version="v2.0.0",
            artifact_location="models/forecast/revenue_v2.0.0.pkl",
            feature_schema={"features": {"revenue": {"data_type": "numeric"}}},
            metrics={"mae": 1200.0, "rmse": 1800.0},
            baseline_metrics={"mae": 2500.0, "rmse": 3500.0},
        )
        v2 = await service.create_model_version(model.id, user, v2_req)
        await service.promote_model_version(
            v2.id, user,
            MLModelPromotionRequest(target_status=MLModelVersionStatus.VALIDATED, reason="Passed benchmark.")
        )
        await service.promote_model_version(
            v2.id, user,
            MLModelPromotionRequest(target_status=MLModelVersionStatus.PRODUCTION, reason="Deploying v2.")
        )

        # Rollback back to v1.0.0
        rollback_req = MLModelRollbackRequest(
            target_version_id=v1.id,
            reason="Unstable variance observed in Q4 regional predictions; reverting to stable v1.",
            environment=MLDeploymentEnvironment.PRODUCTION,
        )
        rolled_back_to = await service.rollback_model_version(v2.id, user, rollback_req)
        assert rolled_back_to.version == "v1.0.0"
        assert rolled_back_to.status == MLModelVersionStatus.PRODUCTION

        # 8. Check Alerts
        alerts = await service.list_alerts(user)
        assert len(alerts) >= 1
        assert any(a.alert_type == "MODEL_ROLLBACK" for a in alerts)


# ==============================================================================
# 6. API INTEGRATION TESTS
# ==============================================================================

def test_mlops_api_endpoints(client: TestClient):
    client.post(
        "/api/v1/auth/register",
        json={"email": "mlops_api_tester@example.com", "password": "Password123!", "full_name": "API Tester"},
    )
    login_res = client.post(
        "/api/v1/auth/login",
        json={"email": "mlops_api_tester@example.com", "password": "Password123!"},
    )
    token = login_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 1. Create Model
    m_res = client.post(
        "/api/v1/mlops/models",
        headers=headers,
        json={
            "name": "Customer Churn Classifier",
            "model_type": "CLASSIFICATION",
            "task_type": "BINARY_CLASSIFICATION",
            "framework": "scikit-learn",
            "tags": ["churn", "retention"],
        },
    )
    assert m_res.status_code == 201
    model_data = m_res.json()
    model_id = model_data["id"]

    # 2. List Models
    list_res = client.get("/api/v1/mlops/models", headers=headers)
    assert list_res.status_code == 200
    assert list_res.json()["total"] >= 1

    # 3. Create Version
    v_res = client.post(
        f"/api/v1/mlops/models/{model_id}/versions",
        headers=headers,
        json={
            "version": "v1.0.0",
            "artifact_location": "artifacts/churn_v1.pkl",
            "feature_schema": {"features": {"usage_hours": {"data_type": "numeric"}}},
            "metrics": {"accuracy": 0.91, "f1": 0.88},
            "baseline_metrics": {"accuracy": 0.70, "f1": 0.60},
        },
    )
    assert v_res.status_code == 201
    version_id = v_res.json()["id"]

    # 4. Get Health
    h_res = client.get(f"/api/v1/mlops/versions/{version_id}/health", headers=headers)
    assert h_res.status_code == 200
    health_data = h_res.json()
    assert health_data["overall_health"] in ("GOOD", "WARNING", "HEALTHY")

    # 5. Get Lineage
    l_res = client.get(f"/api/v1/mlops/versions/{version_id}/lineage", headers=headers)
    assert l_res.status_code == 200
    assert len(l_res.json()["nodes"]) >= 2
