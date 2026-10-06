"""Feature contracts and input/output validation engine for Phase 16 MLOps."""

import math
from typing import Any, Dict, List, Optional, Tuple, Union


class FeatureContractViolationError(ValueError):
    """Raised when inference input data violates a model's registered feature contract."""


class OutputContractViolationError(ValueError):
    """Raised when model predictions violate output validation rules."""


class FeatureContract:
    """Encapsulates the expected schema, types, bounds and categorical values for model features."""

    def __init__(self, schema: Dict[str, Any]):
        """Initializes with a feature schema dict."""
        self.features: Dict[str, Dict[str, Any]] = schema.get("features", {})
        self.allow_extra_columns: bool = schema.get("allow_extra_columns", True)
        self.strict_types: bool = schema.get("strict_types", True)

    def validate_inputs(
        self, records: List[Dict[str, Any]]
    ) -> Tuple[bool, List[str]]:
        """Validates an incoming batch of tabular records against the registered feature contract.

        Returns:
            (is_valid, list_of_violations)
        """
        violations: List[str] = []
        if not records:
            return True, []

        for row_idx, row in enumerate(records):
            # 1. Required Features Presence & Missingness
            for feat_name, spec in self.features.items():
                is_required = spec.get("is_required", True)
                nullable = spec.get("nullable", False)
                data_type = spec.get("data_type", "numeric")
                min_val = spec.get("min_value")
                max_val = spec.get("max_value")
                allowed_cats = spec.get("allowed_categories")

                if feat_name not in row:
                    if is_required:
                        violations.append(f"Row {row_idx}: Missing required feature '{feat_name}'")
                    continue

                val = row[feat_name]

                # Null Check
                if val is None or (isinstance(val, float) and math.isnan(val)):
                    if not nullable and is_required:
                        violations.append(f"Row {row_idx}: Feature '{feat_name}' is null but marked non-nullable")
                    continue

                # Type & Range Checks
                if data_type in ("numeric", "float", "int", "integer"):
                    try:
                        num_val = float(val)
                        if min_val is not None and num_val < min_val:
                            violations.append(
                                f"Row {row_idx}: Value {num_val} for '{feat_name}' below min bound {min_val}"
                            )
                        if max_val is not None and num_val > max_val:
                            violations.append(
                                f"Row {row_idx}: Value {num_val} for '{feat_name}' exceeds max bound {max_val}"
                            )
                    except (ValueError, TypeError):
                        violations.append(
                            f"Row {row_idx}: Value '{val}' for numeric feature '{feat_name}' is not a valid number"
                        )

                elif data_type in ("categorical", "string", "text"):
                    str_val = str(val)
                    if allowed_cats and str_val not in allowed_cats:
                        violations.append(
                            f"Row {row_idx}: Category '{str_val}' for '{feat_name}' not in allowed categories: {allowed_cats}"
                        )

            # 2. Unexpected Extra Columns check if disallowed
            if not self.allow_extra_columns:
                for col in row.keys():
                    if col not in self.features:
                        violations.append(f"Row {row_idx}: Unexpected feature column '{col}' not in contract")

            # Limit reported violations to avoid massive error arrays
            if len(violations) >= 20:
                violations.append("... additional violations truncated")
                break

        is_valid = len(violations) == 0
        return is_valid, violations

    def enforce_input_validation(self, records: List[Dict[str, Any]]) -> None:
        """Enforces input validation and raises FeatureContractViolationError if invalid."""
        is_valid, violations = self.validate_inputs(records)
        if not is_valid:
            error_msg = f"Feature contract validation failed with {len(violations)} violation(s): " + "; ".join(violations[:5])
            raise FeatureContractViolationError(error_msg)


class OutputValidator:
    """Validates model predictions and forecast intervals before returning to callers."""

    @staticmethod
    def validate_predictions(
        predictions: Union[List[float], List[Dict[str, Any]], Dict[str, Any]],
        output_type: str = "numeric",
        allow_negative: bool = True,
        min_bound: Optional[float] = None,
        max_bound: Optional[float] = None,
    ) -> Tuple[bool, List[str]]:
        """Validates prediction array for non-finite values (NaN, Inf) and domain constraints."""
        violations: List[str] = []

        if isinstance(predictions, list):
            for idx, p in enumerate(predictions):
                val: Optional[float] = None
                if isinstance(p, (int, float)):
                    val = float(p)
                elif isinstance(p, dict) and "predicted_value" in p:
                    val = float(p["predicted_value"])
                elif isinstance(p, dict) and "value" in p:
                    val = float(p["value"])

                if val is not None:
                    if math.isnan(val) or math.isinf(val):
                        violations.append(f"Prediction at index {idx} contains non-finite value ({val})")
                    elif not allow_negative and val < 0.0:
                        violations.append(f"Prediction at index {idx} contains negative value ({val}) where prohibited")
                    elif min_bound is not None and val < min_bound:
                        violations.append(f"Prediction {val} below minimum allowed output bound {min_bound}")
                    elif max_bound is not None and val > max_bound:
                        violations.append(f"Prediction {val} exceeds maximum allowed output bound {max_bound}")

        is_valid = len(violations) == 0
        return is_valid, violations
