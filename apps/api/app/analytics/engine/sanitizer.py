import math
from datetime import date, datetime
from decimal import Decimal
from typing import Any


class ResultSanitizer:
    """
    Ensures all analytical results are clean, deterministic, and strictly JSON-serializable.
    Replaces NaN, Infinity, and non-serializable objects with safe primitives.
    """

    @classmethod
    def sanitize_value(cls, val: Any) -> Any:
        if val is None:
            return None

        # Float checks (NaN, Inf)
        if isinstance(val, float):
            if math.isnan(val) or math.isinf(val):
                return None
            return round(val, 6) if abs(val) < 1e12 else val

        # Decimals
        if isinstance(val, Decimal):
            f_val = float(val)
            if math.isnan(f_val) or math.isinf(f_val):
                return None
            return f_val

        # Dates & Datetimes
        if isinstance(val, (datetime, date)):
            return val.isoformat()

        # Dictionaries
        if isinstance(val, dict):
            return {k: cls.sanitize_value(v) for k, v in val.items()}

        # Lists & Sets & Tuples
        if isinstance(val, (list, tuple, set)):
            return [cls.sanitize_value(v) for v in val]

        # NumPy & Polars scalars (if numpy/polars dtypes leak)
        type_name = type(val).__name__
        if "int" in type_name.lower():
            try:
                return int(val)
            except Exception:
                pass
        if "float" in type_name.lower():
            try:
                f = float(val)
                return None if (math.isnan(f) or math.isinf(f)) else round(f, 6)
            except Exception:
                pass

        return val

    @classmethod
    def sanitize_rows(cls, rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
        return [cls.sanitize_value(row) for row in rows]
