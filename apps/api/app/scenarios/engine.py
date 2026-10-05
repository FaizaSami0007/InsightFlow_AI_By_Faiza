"""Deterministic Scenario & Decision Intelligence Simulation Engine."""

from typing import Dict, List, Optional, Tuple

from app.database.models.scenarios import AssumptionOperation
from app.scenarios.schemas import (
    AssumptionSpec,
    ScenarioComparisonItem,
    SensitivityStep,
)

ENGINE_VERSION = "scenario_engine_v1"


class ScenarioEngineError(Exception):
    """Raised when assumption validation or scenario simulation fails."""

    pass


class ScenarioEngine:
    """Orchestrates deterministic what-if simulations, sensitivity sweeps, and multi-scenario comparisons."""

    @classmethod
    def validate_assumptions(cls, assumptions: List[AssumptionSpec]) -> None:
        """Enforce domain rules, non-negativity, and boundary constraints on assumptions."""
        for a in assumptions:
            if a.min_bound is not None and a.value < a.min_bound:
                raise ScenarioEngineError(
                    f"Assumption value {a.value} for '{a.variable}' violates configured minimum bound {a.min_bound}."
                )
            if a.max_bound is not None and a.value > a.max_bound:
                raise ScenarioEngineError(
                    f"Assumption value {a.value} for '{a.variable}' violates configured maximum bound {a.max_bound}."
                )

            # Special known bounded metrics (e.g. rates and discounts)
            var_lower = a.variable.lower()
            if any(k in var_lower for k in ["discount", "rate", "churn", "margin", "tax"]):
                if a.operation == AssumptionOperation.DIRECT_SET:
                    if a.value < 0 or a.value > 100:
                        raise ScenarioEngineError(
                            f"Percentage metric '{a.variable}' must be bounded between 0% and 100%. Received: {a.value}%."
                        )

    @classmethod
    def apply_assumption(
        cls,
        base_val: float,
        assumption: AssumptionSpec,
    ) -> float:
        """Apply a single mathematical transformation to a baseline variable."""
        op = assumption.operation
        val = assumption.value

        if op == AssumptionOperation.PERCENTAGE_CHANGE:
            simulated = base_val * (1.0 + (val / 100.0))
        elif op == AssumptionOperation.ABSOLUTE_CHANGE:
            simulated = base_val + val
        elif op == AssumptionOperation.MULTIPLIER:
            simulated = base_val * val
        elif op == AssumptionOperation.DIRECT_SET:
            simulated = val
        else:
            raise ScenarioEngineError(f"Unsupported assumption operation: {op}")

        if assumption.is_non_negative and simulated < 0:
            simulated = 0.0

        if assumption.min_bound is not None:
            simulated = max(assumption.min_bound, simulated)
        if assumption.max_bound is not None:
            simulated = min(assumption.max_bound, simulated)

        return float(simulated)

    @classmethod
    def simulate_what_if(
        cls,
        baseline_value: float,
        target_metric: str,
        assumptions: List[AssumptionSpec],
        variable_baselines: Optional[Dict[str, float]] = None,
        regression_coefficients: Optional[Dict[str, float]] = None,
    ) -> Tuple[float, float, Optional[float], str]:
        """
        Execute deterministic what-if scenario simulation.
        Returns: (scenario_value, absolute_change, percentage_change, narrative)
        """
        cls.validate_assumptions(assumptions)
        v_baselines = variable_baselines or {}
        coefficients = regression_coefficients or {}

        # 1. Direct simulation on target metric itself
        direct_target_assumptions = [a for a in assumptions if a.variable.lower() == target_metric.lower()]
        indirect_assumptions = [a for a in assumptions if a.variable.lower() != target_metric.lower()]

        current_val = float(baseline_value)

        if direct_target_assumptions:
            for a in direct_target_assumptions:
                current_val = cls.apply_assumption(current_val, a)

        # 2. Driver-outcome simulation for indirect feature drivers
        if indirect_assumptions:
            # Check if linear regression coefficients exist for these drivers
            if coefficients:
                for a in indirect_assumptions:
                    coef = coefficients.get(a.variable, 0.0)
                    driver_base = v_baselines.get(a.variable, 1.0)
                    sim_driver = cls.apply_assumption(driver_base, a)
                    delta_driver = sim_driver - driver_base
                    current_val += coef * delta_driver
            else:
                # Direct multiplicative driver compounding (e.g. Revenue = Price * Quantity)
                compound_multiplier = 1.0
                for a in indirect_assumptions:
                    driver_base = v_baselines.get(a.variable, 100.0)
                    sim_driver = cls.apply_assumption(driver_base, a)
                    if driver_base != 0:
                        compound_multiplier *= (sim_driver / driver_base)
                current_val *= compound_multiplier

        scenario_val = round(float(current_val), 2)
        abs_change = round(float(scenario_val - baseline_value), 2)

        pct_change: Optional[float] = None
        if baseline_value != 0:
            pct_change = round(float(((scenario_val - baseline_value) / abs(baseline_value)) * 100.0), 2)

        # Build grounded analytical narrative
        assumptions_text = ", ".join(
            [f"{a.variable} ({'+' if a.value > 0 else ''}{a.value}{a.unit or ''})" for a in assumptions]
        )
        direction = "increase" if abs_change >= 0 else "decrease"
        pct_text = f" ({'+' if pct_change and pct_change > 0 else ''}{pct_change}%)" if pct_change is not None else ""

        narrative = (
            f"Under assumptions [{assumptions_text}], simulated {target_metric} is estimated at "
            f"{scenario_val:,.2f} ({direction} of {abs(abs_change):,.2f}{pct_text} relative to baseline {baseline_value:,.2f})."
        )

        return scenario_val, abs_change, pct_change, narrative

    @classmethod
    def simulate_sensitivity(
        cls,
        baseline_value: float,
        target_metric: str,
        variable: str,
        range_min_pct: float = -20.0,
        range_max_pct: float = 20.0,
        step_pct: float = 5.0,
        max_scenarios: int = 25,
        variable_baseline: Optional[float] = None,
        coefficient: Optional[float] = None,
    ) -> List[SensitivityStep]:
        """Generate deterministic sensitivity curve varying a single driver across percentage steps."""
        if step_pct <= 0:
            step_pct = 5.0

        steps: List[SensitivityStep] = []
        var_base = variable_baseline if variable_baseline is not None else (baseline_value if variable.lower() == target_metric.lower() else 100.0)

        current_pct = range_min_pct
        count = 0

        while current_pct <= (range_max_pct + 1e-4) and count < max_scenarios:
            pct = round(current_pct, 2)
            spec = AssumptionSpec(
                variable=variable,
                operation=AssumptionOperation.PERCENTAGE_CHANGE,
                value=pct,
                unit="%",
            )

            sim_var = cls.apply_assumption(var_base, spec)

            if variable.lower() == target_metric.lower():
                sim_target = cls.apply_assumption(baseline_value, spec)
            elif coefficient is not None:
                delta_var = sim_var - var_base
                sim_target = baseline_value + coefficient * delta_var
            else:
                # Multiplier ratio
                multiplier = sim_var / var_base if var_base != 0 else 1.0
                sim_target = baseline_value * multiplier

            sim_target = round(float(sim_target), 2)
            abs_delta = round(float(sim_target - baseline_value), 2)
            pct_delta = round(float(((sim_target - baseline_value) / abs(baseline_value)) * 100.0), 2) if baseline_value != 0 else None

            steps.append(
                SensitivityStep(
                    variation_pct=pct,
                    variable_value=round(sim_var, 2),
                    simulated_target=sim_target,
                    absolute_change=abs_delta,
                    percentage_change=pct_delta,
                )
            )

            current_pct += step_pct
            count += 1

        return steps

    @classmethod
    def simulate_comparison(
        cls,
        baseline_value: float,
        target_metric: str,
        scenarios: Dict[str, List[AssumptionSpec]],
        variable_baselines: Optional[Dict[str, float]] = None,
        regression_coefficients: Optional[Dict[str, float]] = None,
    ) -> List[ScenarioComparisonItem]:
        """Evaluate named scenario branches (e.g. Optimistic, Conservative) side-by-side."""
        items: List[ScenarioComparisonItem] = []

        for name, branch_assumptions in scenarios.items():
            sim_val, abs_delta, pct_delta, _ = cls.simulate_what_if(
                baseline_value=baseline_value,
                target_metric=target_metric,
                assumptions=branch_assumptions,
                variable_baselines=variable_baselines,
                regression_coefficients=regression_coefficients,
            )

            summary_text = ", ".join(
                [f"{a.variable}: {'+' if a.value > 0 else ''}{a.value}{a.unit or ''}" for a in branch_assumptions]
            )

            items.append(
                ScenarioComparisonItem(
                    scenario_name=name,
                    simulated_value=sim_val,
                    absolute_change=abs_delta,
                    percentage_change=pct_delta,
                    assumptions_summary=summary_text,
                )
            )

        return items
