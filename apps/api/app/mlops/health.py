"""Model Health Scoring and Multi-Factor Explainability Engine for Phase 16 MLOps."""

from datetime import datetime, timezone
from typing import Any, Dict, List, Optional


class ModelHealthEngine:
    """Computes transparent, multi-dimensional model health indicators and retraining recommendations."""

    @staticmethod
    def evaluate_model_health(
        data_quality_info: Dict[str, Any],
        drift_info: Dict[str, Any],
        performance_info: Dict[str, Any],
        last_evaluated_at: Optional[datetime] = None,
        latency_ms: float = 25.0,
    ) -> Dict[str, Any]:
        """Evaluates health across 5 explicit dimensions without collapsing into an opaque black-box score."""
        recommendations: List[str] = []

        # 1. Data Quality Dimension
        dq_missingness = data_quality_info.get("overall_missingness_pct", 0.0)
        dq_schema_match = data_quality_info.get("schema_match", True)
        dq_null_spikes = data_quality_info.get("null_spikes", {})

        dq_score = 100.0 - (dq_missingness * 2.0)
        if not dq_schema_match:
            dq_score -= 40.0
        if dq_null_spikes:
            dq_score -= 20.0
        dq_score = max(0.0, min(100.0, dq_score))

        dq_status = "HEALTHY" if dq_score >= 80 else ("WARNING" if dq_score >= 50 else "CRITICAL")
        if dq_status != "HEALTHY":
            recommendations.append("Investigate upstream data quality and null spikes in inference pipeline.")

        # 2. Drift Dimension
        max_psi = drift_info.get("max_psi", 0.0)
        drift_detected = drift_info.get("overall_drift_detected", False)
        drift_count = drift_info.get("drifted_features_count", 0)

        if not drift_detected and max_psi < 0.1:
            drift_score = 100.0
        elif max_psi <= 0.2:
            drift_score = 75.0
        elif max_psi <= 0.3:
            drift_score = 45.0
        else:
            drift_score = 20.0

        if drift_count > 2:
            drift_score -= 15.0
        drift_score = max(0.0, min(100.0, drift_score))

        drift_status = "HEALTHY" if drift_score >= 80 else ("WARNING" if drift_score >= 50 else "CRITICAL")
        if drift_status == "CRITICAL":
            recommendations.append(
                "Significant feature drift detected (PSI > 0.2). Retraining or policy review recommended."
            )
        elif drift_status == "WARNING":
            recommendations.append("Moderate feature drift observed. Monitor inference distributions closely.")

        # 3. Performance / Accuracy Dimension
        sup_baseline = performance_info.get("superior_to_baseline", True)
        mae_impr = performance_info.get("mae_improvement_pct", 5.0)
        f1_impr = performance_info.get("f1_improvement_pct", 5.0)

        perf_score = 90.0
        if not sup_baseline:
            perf_score = 40.0
        elif mae_impr < 0 or f1_impr < 0:
            perf_score = 65.0
        else:
            perf_score = min(100.0, 90.0 + max(mae_impr, f1_impr))

        perf_status = "HEALTHY" if perf_score >= 80 else ("WARNING" if perf_score >= 50 else "CRITICAL")
        if perf_status != "HEALTHY":
            recommendations.append("Model accuracy degraded below baseline thresholds. Review model performance.")

        # 4. Latency Dimension
        if latency_ms <= 100.0:
            lat_score = 100.0
        elif latency_ms <= 500.0:
            lat_score = 80.0
        elif latency_ms <= 2000.0:
            lat_score = 50.0
        else:
            lat_score = 20.0

        lat_status = "HEALTHY" if lat_score >= 80 else ("WARNING" if lat_score >= 50 else "CRITICAL")
        if lat_status != "HEALTHY":
            recommendations.append("Inference latency elevated above SLA boundaries.")

        # 5. Freshness Dimension
        fresh_score = 100.0
        days_since_eval = 0
        if last_evaluated_at:
            now = datetime.now(timezone.utc)
            if last_evaluated_at.tzinfo is None:
                last_eval = last_evaluated_at.replace(tzinfo=timezone.utc)
            else:
                last_eval = last_evaluated_at
            delta = now - last_eval
            days_since_eval = delta.days

            if days_since_eval > 90:
                fresh_score = 40.0
                recommendations.append(
                    f"Model has not been evaluated for {days_since_eval} days (stale model warning)."
                )
            elif days_since_eval > 30:
                fresh_score = 75.0

        fresh_status = "HEALTHY" if fresh_score >= 80 else ("WARNING" if fresh_score >= 50 else "CRITICAL")

        # Overall Health Score (Weighted average)
        overall_score = round(
            (dq_score * 0.25) + (drift_score * 0.25) + (perf_score * 0.25) + (lat_score * 0.15) + (fresh_score * 0.10),
            1,
        )

        if dq_status == "CRITICAL" or drift_status == "CRITICAL" or perf_status == "CRITICAL":
            overall_health = "CRITICAL"
        elif (
            dq_status == "WARNING" or drift_status == "WARNING" or perf_status == "WARNING" or fresh_status == "WARNING"
        ):
            overall_health = "WARNING"
        else:
            overall_health = "GOOD"

        retraining_recommended = drift_status == "CRITICAL" or perf_status != "HEALTHY" or fresh_status == "CRITICAL"
        if not recommendations:
            recommendations.append("All monitoring dimensions are healthy and operating within nominal parameters.")

        return {
            "overall_health": overall_health,
            "overall_score": overall_score,
            "retraining_recommended": retraining_recommended,
            "data_quality": {
                "score": dq_score,
                "status": dq_status,
                "details": {"missingness_pct": dq_missingness, "schema_match": dq_schema_match},
            },
            "drift": {
                "score": drift_score,
                "status": drift_status,
                "details": {"max_psi": max_psi, "drifted_features": drift_count},
            },
            "performance": {
                "score": perf_score,
                "status": perf_status,
                "details": performance_info,
            },
            "latency": {
                "score": lat_score,
                "status": lat_status,
                "details": {"latency_ms": latency_ms},
            },
            "freshness": {
                "score": fresh_score,
                "status": fresh_status,
                "details": {"days_since_evaluation": days_since_eval},
            },
            "recommendations": recommendations,
        }
