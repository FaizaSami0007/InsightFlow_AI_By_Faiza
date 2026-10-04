
from app.profiling.quality.quality_engine import DataQualityEngine


def test_data_quality_perfect_score():
    engine = DataQualityEngine()
    columns_profile = [
        {"column_name": "id", "null_percentage": 0.0, "null_count": 0, "is_constant": False, "is_near_constant": False, "outlier_count": 0},
        {"column_name": "val", "null_percentage": 0.0, "null_count": 0, "is_constant": False, "is_near_constant": False, "outlier_count": 0, "numeric_stats": {"lower_bound": 0, "upper_bound": 10}},
    ]
    report = engine.evaluate_quality(
        row_count=100,
        column_count=2,
        duplicate_rows=0,
        duplicate_percentage=0.0,
        columns_profile=columns_profile,
    )

    assert report["overall_score"] == 100.0
    assert report["grade"] == "A"
    assert report["total_issues"] == 0
    assert report["score_breakdown"]["base_score"] == 100.0
    assert report["score_breakdown"]["missing_penalty"] == 0.0
    assert report["score_breakdown"]["duplicate_penalty"] == 0.0


def test_data_quality_penalties_and_warnings():
    engine = DataQualityEngine()
    columns_profile = [
        {"column_name": "id", "null_percentage": 10.0, "null_count": 10, "is_constant": False, "is_near_constant": False, "outlier_count": 0},
        {"column_name": "const", "null_percentage": 0.0, "null_count": 0, "is_constant": True, "unique_count": 1, "is_near_constant": False, "outlier_count": 0},
        {"column_name": "num", "null_percentage": 30.0, "null_count": 30, "is_constant": False, "is_near_constant": False, "outlier_count": 5, "outlier_percentage": 5.0, "numeric_stats": {"lower_bound": 0, "upper_bound": 100}},
    ]
    report = engine.evaluate_quality(
        row_count=100,
        column_count=3,
        duplicate_rows=10,
        duplicate_percentage=10.0,
        columns_profile=columns_profile,
    )

    # Average null = (10 + 0 + 30)/3 = 13.33% -> missing penalty = 13.33 * 0.35 = 4.67
    # Duplicate penalty = 10 * 0.25 = 2.5
    # Constant penalty = (1/3 * 100) * 0.20 = 6.67
    # Outlier penalty = 5.0 * 0.20 = 1.0
    # Expected overall = ~85.2
    assert 84.0 <= report["overall_score"] <= 86.0
    assert report["grade"] == "B"
    assert len(report["warnings"]) > 0
    assert report["constant_columns"] == ["const"]
    assert report["missing_summary"]["buckets"]["moderate_5_to_20"] == 1
    assert report["missing_summary"]["buckets"]["high_20_to_50"] == 1
