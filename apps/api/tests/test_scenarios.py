"""Unit and integration tests for Phase 13 Decision Intelligence, What-If Analysis & Scenarios."""

import uuid

import pytest

from app.database.models.dataset import Dataset, DatasetVersion
from app.database.models.scenarios import (
    AssumptionOperation,
    ScenarioStatus,
    ScenarioType,
)
from app.database.models.user import User
from app.scenarios.engine import ScenarioEngine, ScenarioEngineError
from app.scenarios.schemas import (
    AssumptionSpec,
    ScenarioComparisonRequest,
    SensitivityAnalysisRequest,
    WhatIfScenarioRequest,
)
from app.scenarios.service import ScenarioService, ScenarioServiceError
from tests.conftest import TestingSessionLocal

# ==============================================================================
# 1. SCENARIO ENGINE NUMERICAL & BOUNDARY UNIT TESTS
# ==============================================================================

def test_what_if_percentage_positive_and_negative() -> None:
    """Verify deterministic percentage increase and decrease calculations."""
    # Baseline 1,000,000 +10% -> 1,100,000 (+100k / +10%)
    spec_inc = AssumptionSpec(variable="revenue", operation=AssumptionOperation.PERCENTAGE_CHANGE, value=10.0)
    val_inc, abs_inc, pct_inc, narrative_inc = ScenarioEngine.simulate_what_if(
        baseline_value=1_000_000.0,
        target_metric="revenue",
        assumptions=[spec_inc],
    )
    assert val_inc == 1_100_000.0
    assert abs_inc == 100_000.0
    assert pct_inc == 10.0
    assert "increase" in narrative_inc

    # Baseline 1,000,000 -15% -> 850,000 (-150k / -15%)
    spec_dec = AssumptionSpec(variable="revenue", operation=AssumptionOperation.PERCENTAGE_CHANGE, value=-15.0)
    val_dec, abs_dec, pct_dec, narrative_dec = ScenarioEngine.simulate_what_if(
        baseline_value=1_000_000.0,
        target_metric="revenue",
        assumptions=[spec_dec],
    )
    assert val_dec == 850_000.0
    assert abs_dec == -150_000.0
    assert pct_dec == -15.0
    assert "decrease" in narrative_dec


def test_what_if_absolute_and_multiplier_operations() -> None:
    """Verify absolute addition and multiplier transformations."""
    # Absolute +5,000
    spec_abs = AssumptionSpec(variable="revenue", operation=AssumptionOperation.ABSOLUTE_CHANGE, value=5000.0)
    val_abs, abs_delta, pct_delta, _ = ScenarioEngine.simulate_what_if(
        baseline_value=20_000.0,
        target_metric="revenue",
        assumptions=[spec_abs],
    )
    assert val_abs == 25_000.0
    assert abs_delta == 5000.0
    assert pct_delta == 25.0

    # Multiplier x1.25
    spec_mult = AssumptionSpec(variable="revenue", operation=AssumptionOperation.MULTIPLIER, value=1.25)
    val_mult, abs_m, pct_m, _ = ScenarioEngine.simulate_what_if(
        baseline_value=100.0,
        target_metric="revenue",
        assumptions=[spec_mult],
    )
    assert val_mult == 125.0
    assert abs_m == 25.0
    assert pct_m == 25.0


def test_zero_baseline_safe_division() -> None:
    """Verify zero baseline calculates absolute delta without crashing on percentage division."""
    spec = AssumptionSpec(variable="new_metric", operation=AssumptionOperation.ABSOLUTE_CHANGE, value=500.0)
    val, abs_delta, pct_delta, narrative = ScenarioEngine.simulate_what_if(
        baseline_value=0.0,
        target_metric="new_metric",
        assumptions=[spec],
    )
    assert val == 500.0
    assert abs_delta == 500.0
    assert pct_delta is None  # Percentage change undefined for 0 baseline


def test_bounded_variable_validation_and_non_negative() -> None:
    """Verify bounds constraints (e.g. discount rate 0-100%) and non-negative physical bounds."""
    # Disallow discount > 100%
    with pytest.raises(ScenarioEngineError) as exc_info:
        ScenarioEngine.validate_assumptions([
            AssumptionSpec(variable="discount_rate", operation=AssumptionOperation.DIRECT_SET, value=150.0)
        ])
    assert "bounded between 0% and 100%" in str(exc_info.value)

    # Non-negative clamping: Baseline 100 -200 -> 0.0 when is_non_negative=True
    spec_clamp = AssumptionSpec(
        variable="price",
        operation=AssumptionOperation.ABSOLUTE_CHANGE,
        value=-200.0,
        is_non_negative=True,
    )
    val_clamp, _, _, _ = ScenarioEngine.simulate_what_if(
        baseline_value=100.0,
        target_metric="price",
        assumptions=[spec_clamp],
    )
    assert val_clamp == 0.0


def test_model_based_coefficient_scenario() -> None:
    """Verify regression model based simulation: Revenue = 1000 + 2 * marketing_spend."""
    # marketing_spend +100 -> Delta = 100 * 2 = +200 -> New Revenue = 1200
    spec = AssumptionSpec(variable="marketing_spend", operation=AssumptionOperation.ABSOLUTE_CHANGE, value=100.0)
    val, abs_delta, pct_delta, _ = ScenarioEngine.simulate_what_if(
        baseline_value=1000.0,
        target_metric="revenue",
        assumptions=[spec],
        variable_baselines={"marketing_spend": 500.0},
        regression_coefficients={"marketing_spend": 2.0},
    )
    assert val == 1200.0
    assert abs_delta == 200.0
    assert pct_delta == 20.0


def test_multi_variable_driver_compounding() -> None:
    """Verify multi-variable compounding: Price +5% and Quantity -10% -> 1.05 * 0.90 = 0.945."""
    spec_price = AssumptionSpec(variable="price", operation=AssumptionOperation.PERCENTAGE_CHANGE, value=5.0)
    spec_qty = AssumptionSpec(variable="quantity", operation=AssumptionOperation.PERCENTAGE_CHANGE, value=-10.0)

    val, abs_delta, pct_delta, _ = ScenarioEngine.simulate_what_if(
        baseline_value=100_000.0,
        target_metric="revenue",
        assumptions=[spec_price, spec_qty],
        variable_baselines={"price": 50.0, "quantity": 2000.0},
    )
    assert val == 94_500.0
    assert abs_delta == -5500.0
    assert pct_delta == -5.5


def test_sensitivity_analysis_sweep_and_step_limits() -> None:
    """Verify sensitivity sweep generation from -20% to +20% with step 5% (9 steps)."""
    steps = ScenarioEngine.simulate_sensitivity(
        baseline_value=1000.0,
        target_metric="revenue",
        variable="price",
        range_min_pct=-20.0,
        range_max_pct=20.0,
        step_pct=5.0,
        max_scenarios=25,
    )
    assert len(steps) == 9
    assert steps[0].variation_pct == -20.0
    assert steps[0].simulated_target == 800.0
    assert steps[4].variation_pct == 0.0
    assert steps[4].simulated_target == 1000.0
    assert steps[-1].variation_pct == 20.0
    assert steps[-1].simulated_target == 1200.0


def test_scenario_comparison_optimistic_and_conservative() -> None:
    """Verify side-by-side branch comparison evaluated against identical baseline."""
    scenarios = {
        "Optimistic": [AssumptionSpec(variable="revenue", operation=AssumptionOperation.PERCENTAGE_CHANGE, value=15.0)],
        "Conservative": [AssumptionSpec(variable="revenue", operation=AssumptionOperation.PERCENTAGE_CHANGE, value=-10.0)],
    }
    items = ScenarioEngine.simulate_comparison(
        baseline_value=1_000_000.0,
        target_metric="revenue",
        scenarios=scenarios,
    )
    assert len(items) == 2
    opt = next(i for i in items if i.scenario_name == "Optimistic")
    cons = next(i for i in items if i.scenario_name == "Conservative")

    assert opt.simulated_value == 1_150_000.0
    assert opt.absolute_change == 150_000.0
    assert opt.percentage_change == 15.0

    assert cons.simulated_value == 900_000.0
    assert cons.absolute_change == -100_000.0
    assert cons.percentage_change == -10.0


# ==============================================================================
# 2. DATABASE INTEGRATION & SERVICE LIFECYCLE TESTS
# ==============================================================================

@pytest.mark.asyncio
async def test_scenario_service_end_to_end() -> None:
    """Verify ScenarioService executes simulations, persists records, and supports listing and retrieval."""
    async with TestingSessionLocal() as session:
        # 1. Create test user
        user = User(
            id=str(uuid.uuid4()),
            email="scenario_user@example.com",
            password_hash="hashed_pw_scenario",
            full_name="Scenario User",
            is_active=True,
        )
        session.add(user)

        # 2. Create test dataset and persist file
        import pandas as pd

        from app.datasets.storage import get_storage_provider

        storage = get_storage_provider()
        df = pd.DataFrame({
            "revenue": [1000.0, 2000.0, 3000.0, 4000.0],
            "price": [100.0, 100.0, 100.0, 100.0],
            "cost": [500.0, 1000.0, 1500.0, 2000.0],
            "units": [10, 20, 30, 40],
        })
        csv_bytes = df.to_csv(index=False).encode("utf-8")
        storage_ref = storage.save_file(csv_bytes, "scenario_test.csv")

        ds = Dataset(
            id=str(uuid.uuid4()),
            name="Scenario Dataset",
            owner_id=user.id,
            status="READY",
        )
        session.add(ds)

        version = DatasetVersion(
            id=str(uuid.uuid4()),
            dataset_id=ds.id,
            version_number=1,
            file_name="scenario_test.csv",
            file_format="CSV",
            file_size=len(csv_bytes),
            storage_reference=storage_ref,
            checksum="checksum-scenario",
            status="READY",
            row_count=4,
            column_count=4,
        )
        session.add(version)
        await session.commit()

        service = ScenarioService(session)

        # 3. Test What-If Scenario Run
        what_if_req = WhatIfScenarioRequest(
            dataset_id=ds.id,
            name="Q4 Revenue Growth Scenario",
            target_metric="revenue",
            assumptions=[
                AssumptionSpec(variable="revenue", operation=AssumptionOperation.PERCENTAGE_CHANGE, value=12.5)
            ],
        )
        what_if_res = await service.run_what_if_scenario(user.id, what_if_req)
        assert what_if_res.name == "Q4 Revenue Growth Scenario"
        assert what_if_res.status == ScenarioStatus.COMPLETED
        assert what_if_res.percentage_change == 12.5

        # 4. Test Sensitivity Run
        sens_req = SensitivityAnalysisRequest(
            dataset_id=ds.id,
            name="Price Elasticity Sensitivity",
            target_metric="revenue",
            variable="price",
            range_min_pct=-10.0,
            range_max_pct=10.0,
            step_pct=5.0,
        )
        sens_res = await service.run_sensitivity_analysis(user.id, sens_req)
        assert sens_res.scenario_type == ScenarioType.SENSITIVITY
        assert sens_res.sensitivity_results is not None
        assert len(sens_res.sensitivity_results) == 5

        # 5. Test Comparison Run
        comp_req = ScenarioComparisonRequest(
            dataset_id=ds.id,
            name="Strategic Planning Comparison",
            target_metric="revenue",
            scenarios={
                "Bull Case": [AssumptionSpec(variable="revenue", operation=AssumptionOperation.PERCENTAGE_CHANGE, value=20.0)],
                "Bear Case": [AssumptionSpec(variable="revenue", operation=AssumptionOperation.PERCENTAGE_CHANGE, value=-20.0)],
            },
        )
        comp_res = await service.run_scenario_comparison(user.id, comp_req)
        assert comp_res.scenario_type == ScenarioType.COMPARISON
        assert comp_res.comparison_scenarios is not None
        assert len(comp_res.comparison_scenarios) == 2

        # 6. Test Listing
        listed = await service.list_scenarios(user.id, dataset_id=ds.id)
        assert len(listed) == 3

        # 7. Test Retrieval by ID
        fetched = await service.get_scenario(user.id, what_if_res.id)
        assert fetched.id == what_if_res.id

        # 8. Test Deletion
        deleted = await service.delete_scenario(user.id, what_if_res.id)
        assert deleted is True

        remaining = await service.list_scenarios(user.id, dataset_id=ds.id)
        assert len(remaining) == 2


@pytest.mark.asyncio
async def test_scenario_security_idor_isolation() -> None:
    """Verify IDOR prevention: unauthorized users cannot run scenarios or access other users' scenarios."""
    async with TestingSessionLocal() as session:
        user1 = User(
            id=str(uuid.uuid4()),
            email="owner_scen@example.com",
            password_hash="pw1",
            full_name="Owner User",
            is_active=True,
        )
        user2 = User(
            id=str(uuid.uuid4()),
            email="attacker_scen@example.com",
            password_hash="pw2",
            full_name="Attacker User",
            is_active=True,
        )
        session.add_all([user1, user2])

        ds = Dataset(
            id=str(uuid.uuid4()),
            name="Private Financials",
            owner_id=user1.id,
            status="READY",
        )
        session.add(ds)
        await session.commit()

        service = ScenarioService(session)

        # Attacker user2 attempts to run what-if on user1's dataset
        with pytest.raises(ScenarioServiceError) as exc_info:
            await service.run_what_if_scenario(
                user2.id,
                WhatIfScenarioRequest(
                    dataset_id=ds.id,
                    target_metric="revenue",
                    assumptions=[AssumptionSpec(variable="revenue", value=10.0)],
                ),
            )
        assert "access denied" in str(exc_info.value).lower() or "not found" in str(exc_info.value).lower()
