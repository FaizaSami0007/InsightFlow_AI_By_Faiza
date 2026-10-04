from typing import Any, Dict, List


class DataQualityEngine:
    """Transparent and explainable data quality auditor generating deterministic score breakdowns."""

    def __init__(
        self,
        weight_missing: float = 0.35,
        weight_duplicates: float = 0.25,
        weight_constant: float = 0.20,
        weight_outliers: float = 0.20,
    ):
        self.w_missing = weight_missing
        self.w_dup = weight_duplicates
        self.w_const = weight_constant
        self.w_outliers = weight_outliers

    def evaluate_quality(
        self,
        row_count: int,
        column_count: int,
        duplicate_rows: int,
        duplicate_percentage: float,
        columns_profile: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """Evaluate dataset quality metrics and compute explainable quality score and grade."""
        warnings: List[Dict[str, Any]] = []

        # 1. Missingness Analysis
        missing_buckets = {
            "zero_missing": 0,
            "low_0_to_5": 0,
            "moderate_5_to_20": 0,
            "high_20_to_50": 0,
            "critical_over_50": 0,
        }
        column_missing_breakdown = []
        total_null_pct_sum = 0.0

        for col in columns_profile:
            null_pct = col.get("null_percentage", 0.0)
            null_cnt = col.get("null_count", 0)
            col_name = col.get("column_name", "")
            total_null_pct_sum += null_pct

            if null_pct == 0.0:
                bucket = "zero_missing"
                missing_buckets["zero_missing"] += 1
            elif null_pct <= 5.0:
                bucket = "low_0_to_5"
                missing_buckets["low_0_to_5"] += 1
            elif null_pct <= 20.0:
                bucket = "moderate_5_to_20"
                missing_buckets["moderate_5_to_20"] += 1
            elif null_pct <= 50.0:
                bucket = "high_20_to_50"
                missing_buckets["high_20_to_50"] += 1
                warnings.append({
                    "rule": "MISSING_VALUES",
                    "severity": "WARNING",
                    "column": col_name,
                    "message": f"Column '{col_name}' has high missingness ({null_pct}% nulls).",
                    "details": {"null_count": null_cnt, "null_percentage": null_pct},
                })
            else:
                bucket = "critical_over_50"
                missing_buckets["critical_over_50"] += 1
                warnings.append({
                    "rule": "MISSING_VALUES",
                    "severity": "ERROR",
                    "column": col_name,
                    "message": f"Column '{col_name}' has critical missingness ({null_pct}% nulls).",
                    "details": {"null_count": null_cnt, "null_percentage": null_pct},
                })

            column_missing_breakdown.append({
                "column_name": col_name,
                "null_count": null_cnt,
                "null_percentage": null_pct,
                "bucket": bucket,
            })

        avg_null_pct = (total_null_pct_sum / column_count) if column_count > 0 else 0.0
        missing_penalty = avg_null_pct * self.w_missing

        missing_summary = {
            "average_null_percentage": round(avg_null_pct, 2),
            "buckets": missing_buckets,
            "columns": column_missing_breakdown,
        }

        # 2. Duplicate Analysis
        duplicate_penalty = duplicate_percentage * self.w_dup
        if duplicate_percentage > 0.0:
            severity = "ERROR" if duplicate_percentage > 20.0 else "WARNING"
            warnings.append({
                "rule": "DUPLICATES",
                "severity": severity,
                "message": f"Dataset contains {duplicate_rows} duplicate rows ({duplicate_percentage}%).",
                "details": {"duplicate_rows": duplicate_rows, "duplicate_percentage": duplicate_percentage},
            })

        duplicate_summary = {
            "duplicate_rows": duplicate_rows,
            "duplicate_percentage": duplicate_percentage,
        }

        # 3. Constant & Near-Constant Analysis
        constant_columns = []
        near_constant_columns = []

        for col in columns_profile:
            col_name = col.get("column_name", "")
            if col.get("is_constant", False):
                constant_columns.append(col_name)
                warnings.append({
                    "rule": "CONSTANT_COLUMN",
                    "severity": "INFO",
                    "column": col_name,
                    "message": f"Column '{col_name}' is constant (<=1 unique value) and offers no variance for analytics.",
                    "details": {"unique_count": col.get("unique_count", 0)},
                })
            elif col.get("is_near_constant", False):
                near_constant_columns.append(col_name)
                warnings.append({
                    "rule": "NEAR_CONSTANT_COLUMN",
                    "severity": "INFO",
                    "column": col_name,
                    "message": f"Column '{col_name}' is near-constant (dominated by >=99% single value).",
                    "details": {},
                })

        constant_ratio = (len(constant_columns) / column_count) if column_count > 0 else 0.0
        constant_penalty = (constant_ratio * 100.0) * self.w_const

        # 4. Outlier Analysis (Tukey IQR)
        numeric_col_count = 0
        outlier_col_count = 0
        total_outlier_pct_sum = 0.0
        outlier_breakdown = []

        for col in columns_profile:
            if col.get("numeric_stats") is not None:
                numeric_col_count += 1
                outlier_cnt = col.get("outlier_count", 0)
                outlier_pct = col.get("outlier_percentage", 0.0)
                col_name = col.get("column_name", "")

                if outlier_cnt > 0:
                    outlier_col_count += 1
                    total_outlier_pct_sum += outlier_pct
                    outlier_breakdown.append({
                        "column_name": col_name,
                        "outlier_count": outlier_cnt,
                        "outlier_percentage": outlier_pct,
                        "lower_bound": col["numeric_stats"].get("lower_bound"),
                        "upper_bound": col["numeric_stats"].get("upper_bound"),
                    })
                    if outlier_pct > 10.0:
                        warnings.append({
                            "rule": "OUTLIERS",
                            "severity": "WARNING",
                            "column": col_name,
                            "message": f"Column '{col_name}' contains {outlier_cnt} statistical outliers ({outlier_pct}%) outside 1.5x IQR.",
                            "details": {"outlier_count": outlier_cnt, "outlier_percentage": outlier_pct},
                        })

        avg_outlier_pct = (total_outlier_pct_sum / numeric_col_count) if numeric_col_count > 0 else 0.0
        outlier_penalty = avg_outlier_pct * self.w_outliers

        outlier_summary = {
            "numeric_columns_analyzed": numeric_col_count,
            "columns_with_outliers": outlier_col_count,
            "average_outlier_percentage": round(avg_outlier_pct, 2),
            "outlier_columns": outlier_breakdown,
        }

        # 5. Total Explainable Quality Score Calculation
        total_penalty = missing_penalty + duplicate_penalty + constant_penalty + outlier_penalty
        overall_score = max(0.0, min(100.0, round(100.0 - total_penalty, 1)))

        # Letter Grade
        if overall_score >= 90.0:
            grade = "A"
        elif overall_score >= 80.0:
            grade = "B"
        elif overall_score >= 70.0:
            grade = "C"
        elif overall_score >= 60.0:
            grade = "D"
        else:
            grade = "F"

        return {
            "overall_score": overall_score,
            "grade": grade,
            "total_issues": len(warnings),
            "score_breakdown": {
                "base_score": 100.0,
                "missing_penalty": round(missing_penalty, 2),
                "duplicate_penalty": round(duplicate_penalty, 2),
                "constant_penalty": round(constant_penalty, 2),
                "outlier_penalty": round(outlier_penalty, 2),
            },
            "missing_summary": missing_summary,
            "duplicate_summary": duplicate_summary,
            "constant_columns": constant_columns,
            "near_constant_columns": near_constant_columns,
            "outlier_summary": outlier_summary,
            "warnings": warnings,
        }
