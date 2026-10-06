"""Statistical Drift Detection and Data Quality Monitoring Engine for Phase 16 MLOps."""

import math
from typing import Any, Dict, List, Optional, Union

import numpy as np
from scipy import stats


class DriftEngine:
    """Computes statistical drift, distribution distances, and data quality indicators."""

    @staticmethod
    def calculate_psi(
        reference_data: Union[List[float], np.ndarray],
        current_data: Union[List[float], np.ndarray],
        num_bins: int = 10,
    ) -> float:
        """Calculates the Population Stability Index (PSI) between reference and current distribution.

        PSI Interpretation:
        - PSI < 0.1: No significant change / stable
        - 0.1 <= PSI <= 0.2: Moderate shift / monitor closely
        - PSI > 0.2: Significant distribution shift / drift alert
        """
        ref = np.array(reference_data, dtype=float)
        cur = np.array(current_data, dtype=float)

        # Filter NaNs
        ref = ref[~np.isnan(ref)]
        cur = cur[~np.isnan(cur)]

        if len(ref) == 0 or len(cur) == 0:
            return 0.0

        # Create quantiles on reference data
        percentiles = np.linspace(0, 100, num_bins + 1)
        try:
            bins = np.percentile(ref, percentiles)
            bins = np.unique(bins)
            if len(bins) < 2:
                return 0.0
            bins[0] = -np.inf
            bins[-1] = np.inf
        except Exception:
            return 0.0

        # Calculate frequency in bins
        ref_counts, _ = np.histogram(ref, bins=bins)
        cur_counts, _ = np.histogram(cur, bins=bins)

        # Convert to percentages with Laplace smoothing to prevent division by zero or divergence
        ref_pct = (ref_counts + 1.0) / (len(ref) + len(ref_counts))
        cur_pct = (cur_counts + 1.0) / (len(cur) + len(cur_counts))

        # Normalize
        ref_pct /= np.sum(ref_pct)
        cur_pct /= np.sum(cur_pct)

        # PSI = sum((Actual - Expected) * ln(Actual / Expected))
        psi_val = np.sum((cur_pct - ref_pct) * np.log(cur_pct / ref_pct))
        return float(round(max(0.0, psi_val), 4))

    @staticmethod
    def calculate_ks_test(
        reference_data: Union[List[float], np.ndarray],
        current_data: Union[List[float], np.ndarray],
    ) -> Dict[str, float]:
        """Performs two-sample Kolmogorov-Smirnov test for continuous distribution equivalence."""
        ref = np.array(reference_data, dtype=float)
        cur = np.array(current_data, dtype=float)

        ref = ref[~np.isnan(ref)]
        cur = cur[~np.isnan(cur)]

        if len(ref) < 2 or len(cur) < 2:
            return {"ks_statistic": 0.0, "p_value": 1.0, "drift_detected": 0.0}

        res = stats.ks_2samp(ref, cur)
        stat = float(res.statistic)
        pval = float(res.pvalue)

        return {
            "ks_statistic": round(stat, 4),
            "p_value": round(pval, 4),
            "drift_detected": 1.0 if pval < 0.05 else 0.0,
        }

    @staticmethod
    def calculate_categorical_drift(
        reference_categories: List[str],
        current_categories: List[str],
    ) -> Dict[str, Any]:
        """Calculates category frequency shift and Total Variation Distance (TVD)."""
        if not reference_categories or not current_categories:
            return {"tvd": 0.0, "new_categories": [], "missing_categories": []}

        ref_total = len(reference_categories)
        cur_total = len(current_categories)

        ref_counts: Dict[str, int] = {}
        for c in reference_categories:
            ref_counts[c] = ref_counts.get(c, 0) + 1

        cur_counts: Dict[str, int] = {}
        for c in current_categories:
            cur_counts[c] = cur_counts.get(c, 0) + 1

        all_cats = set(ref_counts.keys()).union(set(cur_counts.keys()))

        tvd = 0.0
        for c in all_cats:
            p = ref_counts.get(c, 0) / ref_total
            q = cur_counts.get(c, 0) / cur_total
            tvd += abs(p - q)

        tvd = tvd / 2.0  # TVD is bounded in [0, 1]

        new_cats = list(set(cur_counts.keys()) - set(ref_counts.keys()))
        missing_cats = list(set(ref_counts.keys()) - set(cur_counts.keys()))

        return {
            "tvd": round(tvd, 4),
            "drift_detected": tvd > 0.15,
            "new_categories": new_cats,
            "missing_categories": missing_cats,
        }

    @staticmethod
    def evaluate_feature_drift(
        training_records: List[Dict[str, Any]],
        inference_records: List[Dict[str, Any]],
        psi_threshold: float = 0.2,
    ) -> Dict[str, Any]:
        """Evaluates per-feature drift across all numerical and categorical columns."""
        if not training_records or not inference_records:
            return {"features": {}, "overall_drift_detected": False, "max_psi": 0.0}

        all_features = set()
        for r in training_records:
            all_features.update(r.keys())

        results: Dict[str, Any] = {}
        max_psi = 0.0
        drift_count = 0

        for feat in all_features:
            ref_vals = [r.get(feat) for r in training_records if r.get(feat) is not None]
            cur_vals = [r.get(feat) for r in inference_records if r.get(feat) is not None]

            if not ref_vals or not cur_vals:
                continue

            # Check if numerical
            is_num = all(isinstance(v, (int, float)) for v in ref_vals[:20] if v is not None)
            if is_num:
                ref_num = [float(v) for v in ref_vals if isinstance(v, (int, float))]
                cur_num = [float(v) for v in cur_vals if isinstance(v, (int, float))]

                psi = DriftEngine.calculate_psi(ref_num, cur_num)
                ks_res = DriftEngine.calculate_ks_test(ref_num, cur_num)

                max_psi = max(max_psi, psi)
                has_drift = psi > psi_threshold or bool(ks_res["drift_detected"])
                if has_drift:
                    drift_count += 1

                results[feat] = {
                    "type": "numeric",
                    "psi": psi,
                    "ks_statistic": ks_res["ks_statistic"],
                    "p_value": ks_res["p_value"],
                    "drift_detected": has_drift,
                    "mean_training": round(float(np.mean(ref_num)), 4) if ref_num else 0.0,
                    "mean_inference": round(float(np.mean(cur_num)), 4) if cur_num else 0.0,
                }
            else:
                ref_cat = [str(v) for v in ref_vals]
                cur_cat = [str(v) for v in cur_vals]

                cat_res = DriftEngine.calculate_categorical_drift(ref_cat, cur_cat)
                if cat_res["drift_detected"]:
                    drift_count += 1

                results[feat] = {
                    "type": "categorical",
                    "tvd": cat_res["tvd"],
                    "drift_detected": cat_res["drift_detected"],
                    "new_categories": cat_res["new_categories"],
                    "missing_categories": cat_res["missing_categories"],
                }

        overall_drift = max_psi > psi_threshold or drift_count > 0

        return {
            "features": results,
            "overall_drift_detected": overall_drift,
            "max_psi": round(max_psi, 4),
            "drifted_features_count": drift_count,
        }

    @staticmethod
    def audit_data_quality(
        records: List[Dict[str, Any]],
        expected_columns: Optional[List[str]] = None,
    ) -> Dict[str, Any]:
        """Audits missingness, null spikes, and schema integrity of an incoming batch."""
        if not records:
            return {"row_count": 0, "missingness_pct": 0.0, "schema_match": True, "warnings": []}

        n_rows = len(records)
        warnings: List[str] = []

        # Column set
        present_cols = set()
        for r in records:
            present_cols.update(r.keys())

        missing_cols = []
        extra_cols = []
        if expected_columns:
            exp_set = set(expected_columns)
            missing_cols = list(exp_set - present_cols)
            extra_cols = list(present_cols - exp_set)
            if missing_cols:
                warnings.append(f"Missing expected columns: {missing_cols}")
            if extra_cols:
                warnings.append(f"Found unexpected columns: {extra_cols}")

        # Missingness per column
        col_null_counts: Dict[str, int] = {}
        for r in records:
            for c in present_cols:
                v = r.get(c)
                if v is None or (isinstance(v, float) and math.isnan(v)):
                    col_null_counts[c] = col_null_counts.get(c, 0) + 1

        total_cells = n_rows * len(present_cols) if present_cols else 1
        total_nulls = sum(col_null_counts.values())
        overall_missingness_pct = round((total_nulls / total_cells) * 100.0, 2)

        null_spikes = {
            c: round((cnt / n_rows) * 100.0, 2) for c, cnt in col_null_counts.items() if (cnt / n_rows) > 0.20
        }
        if null_spikes:
            warnings.append(f"High null rate detected in columns: {null_spikes}")

        return {
            "row_count": n_rows,
            "column_count": len(present_cols),
            "overall_missingness_pct": overall_missingness_pct,
            "null_rates": {c: round((cnt / n_rows) * 100.0, 2) for c, cnt in col_null_counts.items()},
            "null_spikes": null_spikes,
            "schema_match": len(missing_cols) == 0,
            "missing_columns": missing_cols,
            "extra_columns": extra_cols,
            "warnings": warnings,
        }
