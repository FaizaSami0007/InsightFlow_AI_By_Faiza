from app.database.models.profiling import ConceptualType, SemanticRole
from app.profiling.semantics.semantic_classifier import SemanticClassifier


def test_measure_and_currency_classification():
    classifier = SemanticClassifier()
    col = {
        "column_name": "total_revenue",
        "normalized_name": "total_revenue",
        "conceptual_type": ConceptualType.FLOAT.value,
        "unique_count": 95,
        "unique_percentage": 95.0,
        "null_count": 0,
    }
    sem = classifier.classify_column(col, total_rows=100)

    assert sem["inferred_role"] == SemanticRole.MEASURE.value
    assert sem["is_measure"] is True
    assert sem["possible_currency"] is True
    assert sem["inferred_confidence"] >= 0.90


def test_dimension_classification():
    classifier = SemanticClassifier()
    col = {
        "column_name": "region",
        "normalized_name": "region",
        "conceptual_type": ConceptualType.STRING.value,
        "unique_count": 5,
        "unique_percentage": 5.0,
        "null_count": 0,
    }
    sem = classifier.classify_column(col, total_rows=100)

    assert sem["inferred_role"] == SemanticRole.DIMENSION.value
    assert sem["is_dimension"] is True
    assert sem["inferred_confidence"] >= 0.85


def test_identifier_classification():
    classifier = SemanticClassifier()
    col = {
        "column_name": "customer_id",
        "normalized_name": "customer_id",
        "conceptual_type": ConceptualType.INTEGER.value,
        "unique_count": 100,
        "unique_percentage": 100.0,
        "null_count": 0,
    }
    sem = classifier.classify_column(col, total_rows=100)

    assert sem["inferred_role"] == SemanticRole.IDENTIFIER.value
    assert sem["is_identifier"] is True
    assert sem["inferred_confidence"] >= 0.90


def test_temporal_classification():
    classifier = SemanticClassifier()
    col = {
        "column_name": "order_date",
        "normalized_name": "order_date",
        "conceptual_type": ConceptualType.DATE.value,
        "unique_count": 50,
        "unique_percentage": 50.0,
        "null_count": 0,
    }
    sem = classifier.classify_column(col, total_rows=100)

    assert sem["inferred_role"] in (SemanticRole.DATE.value, SemanticRole.DATETIME.value)
    assert sem["is_temporal"] is True
    assert sem["inferred_confidence"] >= 0.90
