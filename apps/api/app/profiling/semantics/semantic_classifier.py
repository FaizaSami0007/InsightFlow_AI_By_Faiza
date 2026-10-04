import re
from typing import Any, Dict, List

from app.database.models.profiling import ConceptualType, SemanticRole


class SemanticClassifier:
    """Deterministic semantic classification engine producing explainable role inferences and confidence scores."""

    IDENTIFIER_KEYWORDS = {"id", "uuid", "key", "code", "guid", "pk", "fk", "num", "number"}
    MEASURE_KEYWORDS = {
        "revenue", "sales", "profit", "cost", "price", "amount", "salary", "wage",
        "qty", "quantity", "discount", "spend", "rate", "total", "margin", "score",
        "balance", "fee", "tax", "budget", "target", "value", "unit_price", "units",
    }
    CURRENCY_KEYWORDS = {
        "revenue", "sales", "profit", "cost", "price", "amount", "salary", "wage",
        "balance", "fee", "tax", "budget", "spend", "unit_price", "dollar", "eur", "pkr", "usd",
    }
    DIMENSION_KEYWORDS = {
        "region", "country", "city", "state", "category", "status", "department",
        "gender", "segment", "type", "tier", "plan", "channel", "source", "medium",
        "brand", "product", "role", "group", "class", "industry", "sector",
    }
    TEMPORAL_KEYWORDS = {
        "date", "time", "timestamp", "created_at", "updated_at", "year", "month",
        "day", "hour", "period", "quarter", "week", "datetime", "dt", "dob",
    }
    BOOLEAN_KEYWORDS = {"is_", "has_", "can_", "should_", "active", "enabled", "deleted", "flag"}

    def classify_column(self, col_profile: Dict[str, Any], total_rows: int) -> Dict[str, Any]:
        """Classify an individual column into semantic role, confidence, and dimensional flags."""
        col_name = col_profile.get("column_name", "")
        norm_name = col_profile.get("normalized_name", "").lower()
        conceptual_type = col_profile.get("conceptual_type", ConceptualType.UNKNOWN.value)
        unique_cnt = col_profile.get("unique_count", 0)
        unique_pct = col_profile.get("unique_percentage", 0.0)

        # Tokenize normalized column name
        tokens = set(re.split(r"[_\s]+", norm_name))

        # Flags to compute
        inferred_role = SemanticRole.UNKNOWN
        confidence = 0.50
        is_dimension = False
        is_measure = False
        is_identifier = False
        is_temporal = False
        possible_currency = False

        # 1. Identifier Check (Heuristic: name contains identifier pattern & high uniqueness)
        is_id_name = bool(tokens & self.IDENTIFIER_KEYWORDS or norm_name.endswith("_id") or norm_name.startswith("id_") or norm_name == "id")
        if is_id_name:
            if unique_pct >= 90.0 or (total_rows > 0 and unique_cnt == total_rows):
                inferred_role = SemanticRole.IDENTIFIER
                confidence = 0.95 if unique_pct == 100.0 else 0.85
                is_identifier = True
            elif conceptual_type in (ConceptualType.STRING, ConceptualType.INTEGER):
                inferred_role = SemanticRole.IDENTIFIER
                confidence = 0.75
                is_identifier = True

        # 2. Temporal Check (Heuristic: Date/Datetime conceptual type or temporal keywords)
        if not is_identifier:
            is_temp_name = bool(tokens & self.TEMPORAL_KEYWORDS)
            if conceptual_type in (ConceptualType.DATE, ConceptualType.DATETIME, ConceptualType.TIME):
                inferred_role = SemanticRole.DATETIME if conceptual_type == ConceptualType.DATETIME else SemanticRole.DATE
                confidence = 0.98 if is_temp_name else 0.90
                is_temporal = True
            elif is_temp_name:
                inferred_role = SemanticRole.DATE
                confidence = 0.70
                is_temporal = True

        # 3. Boolean Check
        if not is_identifier and not is_temporal:
            is_bool_name = any(norm_name.startswith(p) or norm_name == p for p in self.BOOLEAN_KEYWORDS)
            if conceptual_type == ConceptualType.BOOLEAN:
                inferred_role = SemanticRole.BOOLEAN
                confidence = 0.99
            elif is_bool_name and unique_cnt <= 2:
                inferred_role = SemanticRole.BOOLEAN
                confidence = 0.85

        # 4. Measure / Metric Check (Heuristic: Numeric type + not identifier + measure keyword or continuous values)
        if inferred_role == SemanticRole.UNKNOWN and conceptual_type in (ConceptualType.INTEGER, ConceptualType.FLOAT):
            is_meas_name = bool(tokens & self.MEASURE_KEYWORDS)
            is_curr_name = bool(tokens & self.CURRENCY_KEYWORDS)

            if is_curr_name:
                possible_currency = True

            if is_meas_name:
                inferred_role = SemanticRole.MEASURE
                confidence = 0.92
                is_measure = True
            elif conceptual_type == ConceptualType.FLOAT:
                inferred_role = SemanticRole.MEASURE
                confidence = 0.80
                is_measure = True
            elif unique_cnt > 20 or unique_pct > 10.0:
                inferred_role = SemanticRole.MEASURE
                confidence = 0.70
                is_measure = True
            else:
                # Low cardinality integer might be a dimension (e.g. status code, priority)
                inferred_role = SemanticRole.DIMENSION
                confidence = 0.65
                is_dimension = True

        # 5. Dimension / Categorical Check (String types)
        if inferred_role == SemanticRole.UNKNOWN and conceptual_type == ConceptualType.STRING:
            is_dim_name = bool(tokens & self.DIMENSION_KEYWORDS)
            if is_dim_name or unique_pct < 50.0:
                inferred_role = SemanticRole.DIMENSION
                confidence = 0.90 if is_dim_name else 0.80
                is_dimension = True
            else:
                inferred_role = SemanticRole.TEXT
                confidence = 0.75

        # Fallback
        if inferred_role == SemanticRole.UNKNOWN:
            inferred_role = SemanticRole.UNKNOWN
            confidence = 0.30

        return {
            "column_name": col_name,
            "inferred_role": inferred_role.value,
            "inferred_confidence": round(confidence, 2),
            "user_role": None,
            "is_dimension": is_dimension,
            "is_measure": is_measure,
            "is_identifier": is_identifier,
            "is_temporal": is_temporal,
            "possible_currency": possible_currency,
            "description": f"Inferred {inferred_role.value.lower()} field based on data type and distribution.",
            "unit": "currency_units" if possible_currency else None,
            "format_hint": None,
        }

    def classify_all(self, columns_profile: List[Dict[str, Any]], total_rows: int) -> List[Dict[str, Any]]:
        """Classify all columns in a dataset profile."""
        return [self.classify_column(col, total_rows) for col in columns_profile]
